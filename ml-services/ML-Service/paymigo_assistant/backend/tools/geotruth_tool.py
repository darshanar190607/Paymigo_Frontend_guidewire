import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv("paymigo_assistant/.env")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8000")
logger = logging.getLogger(__name__)

class GeoTruthTool:
    def execute(self, claim_data=None):
        if not claim_data:
            claim_data = {"user_id": "W001", "lat": 13.0827, "lng": 80.2707, "type": "gps_check"}
            
        try:
            endpoint = f"{ML_SERVICE_URL}/claim/verify"
            response = requests.post(endpoint, json=claim_data, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": f"GeoTruth Verification: {data.get('result', 'VERIFIED')}. Confidence: {data.get('confidence', '99.9%')}.",
                    "data": data,
                    "action_route": "/claim/verify"
                }
            else:
                return {
                    "status": "fallback",
                    "message": "GeoTruth validation service is under maintenance. Manual verification may be required.",
                    "action_route": "/claim/verify"
                }
        except Exception as e:
            logger.error(f"GeoTruthTool Error: {e}")
            return {
                "status": "error",
                "message": "I couldn't reach the GeoTruth verification engine.",
                "action_route": "/claim/verify"
            }
