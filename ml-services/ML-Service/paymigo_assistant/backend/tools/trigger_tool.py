import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv("paymigo_assistant/.env")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8000")
logger = logging.getLogger(__name__)

class TriggerTool:
    def execute(self, zone="Chennai"):
        try:
            endpoint = f"{ML_SERVICE_URL}/triggers/current"
            response = requests.get(endpoint, timeout=5, params={"zone": zone})
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": f"Active Triggers in {zone}: {', '.join(data.get('active', ['None']))}.",
                    "data": data,
                    "action_route": "/dashboard"
                }
            else:
                return {
                    "status": "fallback",
                    "message": f"I can't access live triggers for {zone} right now. Typically, low demand triggers during off-peak hours.",
                    "action_route": "/dashboard"
                }
        except Exception as e:
            logger.error(f"TriggerTool Error: {e}")
            return {
                "status": "error",
                "message": "Trigger detection service is offline.",
                "action_route": "/dashboard"
            }
