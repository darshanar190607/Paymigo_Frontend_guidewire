import re

class IntentRouter:
    def __init__(self):
        # Keywords for direct tool routing if needed
        self.tool_keywords = {
            "claim": ["claim", "status", "track", "payout"],
            "pricing": ["price", "plan", "cost", "lite", "pro", "elite"],
            "geotruth": ["location", "verify", "spoof", "gps", "geotruth"],
            "trigger": ["trigger", "weather", "demand", "rain", "snow"],
            "analytics": ["forecast", "dashboard", "trend", "income"],
            "support": ["help", "human", "talk", "agent", "escalate"]
        }

    def detect_intent(self, user_query):
        query = user_query.lower()
        
        # Priority 1: Check for explicit tool mentions
        for intent, keywords in self.tool_keywords.items():
            if any(keyword in query for keyword in keywords):
                return intent
        
        # Priority 2: Default to "knowledge" (RAG)
        return "knowledge"

    def get_routing_instruction(self, intent):
        if intent == "knowledge":
            return "Search the knowledge base for relevant information."
        else:
            return f"Use the {intent}_tool to handle this request."
