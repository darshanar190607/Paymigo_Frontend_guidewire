import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv("paymigo_assistant/.env")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8000")
logger = logging.getLogger(__name__)

class RiskTool:
    def execute(self, zone="Chennai"):
        try:
            endpoint = f"{ML_SERVICE_URL}/analytics/forecast"
            response = requests.get(endpoint, timeout=5, params={"zone": zone})
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": f"Demand Forecast for {zone}: {data.get('forecast', 'Stable')}. Risk Score: {data.get('risk_score', '0.1')}.",
                    "data": data,
                    "action_route": "/analytics"
                }
            else:
                return {
                    "status": "fallback",
                    "message": f"I can't get the live forecast for {zone} right now, but historically this zone has low risk on Fridays.",
                    "action_route": "/analytics"
                }
        except Exception as e:
            logger.error(f"RiskTool Error: {e}")
            return {
                "status": "error",
                "message": "The risk analysis service is offline. Predicting based on general trends...",
                "action_route": "/analytics"
            }
