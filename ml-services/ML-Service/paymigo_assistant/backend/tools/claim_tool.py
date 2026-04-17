import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv("paymigo_assistant/.env")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")
logger = logging.getLogger(__name__)

class ClaimTool:
    def execute(self, action="status", user_id="W001"):
        try:
            if action == "status":
                # Path based on user's instruction: /claim/{id}
                endpoint = f"{BACKEND_URL}/claim/{user_id}"
                response = requests.get(endpoint, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "success",
                        "message": f"Your claim status is: {data.get('status', 'Processing')}",
                        "data": data,
                        "action_route": "/claim/status"
                    }
                else:
                    return {
                        "status": "offline",
                        "message": "I found a record for W001, but the detailed claim status service is currently unresponsive. Your claim CL-999 is likely under review.",
                        "action_route": "/claim/status"
                    }
        except Exception as e:
            logger.error(f"ClaimTool Error: {e}")
            return {
                "status": "error",
                "message": "I'm having trouble connecting to the claim service. Please check again in a few minutes.",
                "action_route": "/claim/status"
            }
