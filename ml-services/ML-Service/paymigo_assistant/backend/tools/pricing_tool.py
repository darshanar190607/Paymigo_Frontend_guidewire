import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv("paymigo_assistant/.env")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8000")
logger = logging.getLogger(__name__)

class PricingTool:
    def execute(self, user_id="W001"):
        try:
            endpoint = f"{ML_SERVICE_URL}/pricing/intelligence"
            response = requests.get(endpoint, timeout=5, params={"user_id": user_id})
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": f"AI-optimized pricing for you: {data.get('recommended_plan', 'Pro')} at {data.get('price', '$15')}/month.",
                    "data": data,
                    "action_route": "/pricing"
                }
            else:
                return {
                    "status": "fallback",
                    "message": "The pricing engine is currently recalibrating. Standard plans: Lite ($5), Pro ($15), Elite ($25).",
                    "action_route": "/pricing"
                }
        except Exception as e:
            logger.error(f"PricingTool Error: {e}")
            return {
                "status": "error",
                "message": "I couldn't reach the pricing engine. Please try again later.",
                "action_route": "/pricing"
            }
