import os
import logging
from typing import List, Dict, Any
from paymigo_assistant.backend.services.llm_service import LLMService
from paymigo_assistant.backend.rag.retrieve import Retriever
from paymigo_assistant.backend.core.router import IntentRouter
from paymigo_assistant.backend.core.suggestions import generate_suggestions

# Tool Imports
from paymigo_assistant.backend.tools.claim_tool import ClaimTool
from paymigo_assistant.backend.tools.pricing_tool import PricingTool
from paymigo_assistant.backend.tools.risk_tool import RiskTool
from paymigo_assistant.backend.tools.trigger_tool import TriggerTool
from paymigo_assistant.backend.tools.geotruth_tool import GeoTruthTool
from paymigo_assistant.backend.tools.nlp_tool import NLPTool

logger = logging.getLogger(__name__)

DEMO_SCENARIOS = {
    "claim_stuck": {
        "keywords": ["stuck", "slow", "taking long", "pending"],
        "answer": "I see your claim CL-999 is currently in the 'Verification' stage. To speed this up, you can upload a screenshot of your gig app's earnings page for that period.",
        "actions": [
            {"label": "Upload Proof", "type": "navigate", "target": "/claim/verify"},
            {"label": "Track status", "type": "navigate", "target": "/claim/status"}
        ]
    },
    "best_plan": {
        "keywords": ["best plan", "recommend", "which plan", "price"],
        "answer": "Based on your activity in Chennai, I recommend the **Pro Plan**. It offers a $500 payout cap and includes GeoTruth protection, which is essential for your zone right now.",
        "actions": [
            {"label": "View Plans", "type": "navigate", "target": "/pricing"}
        ]
    },
    "safe_today": {
        "keywords": ["safe", "risk", "weather", "forecast"],
        "answer": "The risk level in Chennai is currently **High** due to incoming weather disruptions. I recommend staying near the T-Nagar hub for better connectivity and safety.",
        "actions": [
            {"label": "View Forecast", "type": "navigate", "target": "/analytics"}
        ]
    },
    "payout_delay": {
        "keywords": ["payout", "late", "missing", "money"],
        "answer": "I apologize for the wait. Your payout of $120 is confirmed but delayed due to bank processing. It should arrive in your wallet within 4 hours.",
        "actions": [
            {"label": "View Wallet", "type": "navigate", "target": "/dashboard"}
        ]
    },
    "fraud_verification": {
        "keywords": ["fraud", "verification", "identity", "wrong"],
        "answer": "Our GeoTruth system flagged a slight location mismatch earlier. Please perform a quick selfie-check in the app to clear your verification status.",
        "actions": [
            {"label": "Verify Now", "type": "navigate", "target": "/claim/verify"}
        ]
    }
}

class MigoAgent:
    def __init__(self):
        self.llm = LLMService()
        self.retriever = Retriever()
        self.router = IntentRouter()
        
        self.tools = {
            "claim": ClaimTool(),
            "pricing": PricingTool(),
            "risk": RiskTool(),
            "trigger": TriggerTool(),
            "geotruth": GeoTruthTool(),
            "curfew": NLPTool()
        }
        
        # Expanded Demo Context
        self.user_context = {
            "id": "W001",
            "zone": "Chennai",
            "claim_status": "processing",
            "premium_tier": "Pro",
            "risk": "high"
        }

    def generate_response(self, user_query: str, history: List[Dict[str, str]] = []) -> Dict[str, Any]:
        query_lower = user_query.lower()

        # 1. Check for Demo Scenarios (Priority)
        for scenario_id, data in DEMO_SCENARIOS.items():
            if any(keyword in query_lower for keyword in data["keywords"]):
                return {
                    "answer": data["answer"],
                    "actions": data["actions"],
                    "suggestions": generate_suggestions(self.user_context),
                    "system_meta": {"scenario": scenario_id}
                }

        # 2. Normal Agent Logic
        intent = self.router.detect_intent(user_query)
        tool_result = None
        actions = []
        
        if intent in self.tools:
            try:
                if intent == "claim":
                    tool_result = self.tools["claim"].execute(user_id=self.user_context["id"])
                elif intent == "pricing":
                    tool_result = self.tools["pricing"].execute(user_id=self.user_context["id"])
                elif intent == "risk":
                    tool_result = self.tools["risk"].execute(zone=self.user_context["zone"])
                elif intent == "trigger":
                    tool_result = self.tools["trigger"].execute(zone=self.user_context["zone"])
                elif intent == "geotruth":
                    tool_result = self.tools["geotruth"].execute()
                elif intent == "curfew":
                    tool_result = self.tools["curfew"].detect_curfew(user_query)
                
                if tool_result and "action_route" in tool_result:
                    actions.append({
                        "label": f"Go to {intent.capitalize()}",
                        "type": "navigate",
                        "target": tool_result["action_route"]
                    })
            except Exception as e:
                logger.error(f"Tool error: {e}")
                tool_result = {"message": "System busy."}

        # 3. RAG Context
        search_results = self.retriever.search(user_query)
        context = "\n".join(search_results)

        # 4. System Prompt
        system_prompt = (
            "You are Migo, a friendly AI financial co-pilot for gig workers at PayMigo.\n"
            "Rules:\n"
            "- Always explain simply and empathy.\n"
            "- Be concise (max 3 sentences).\n"
            "- suggest next steps if clear.\n"
            "- Use the user's current context below.\n\n"
            f"USER CONTEXT: {self.user_context}\n"
            f"KNOWLEDGE: {context}\n"
            f"LIVE UPDATE: {tool_result['message'] if tool_result else 'None'}"
        )

        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_query}]
        try:
            llm_response = self.llm.chat_completion(messages)
            answer = llm_response.choices[0].message.content if llm_response else "I'm having trouble thinking, but I can still help you track your claim."
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return {
                "answer": "I'm here to help. Let me guide you step by step with our core tools.",
                "actions": [
                    {"label": "Check claim", "type": "navigate", "target": "/claim/status"},
                    {"label": "View plans", "type": "navigate", "target": "/pricing"}
                ],
                "suggestions": ["How does PayMigo work?", "Is it safe today?"],
                "system_meta": {"error": True}
            }

        # 6. Final Polish: Ensure at least 1 action
        if not actions:
            actions = [
                {"label": "Track claim", "type": "navigate", "target": "/claim/status"}
            ]

        return {
            "answer": answer,
            "actions": actions,
            "suggestions": generate_suggestions(self.user_context),
            "system_meta": {"intent": intent}
        }
