from fastapi import APIRouter
from pydantic import BaseModel
from app.pipelines.weather_orchestrator import run_ml_pipeline

router = APIRouter()

class PayoutValidationRequest(BaseModel):
    user_id: str
    weather_event_id: str
    intensity: float
    weather_type: str

@router.post("/validate")
def validate_payout(req: PayoutValidationRequest):
    weather_data = {
        "weather_type": req.weather_type,
        "intensity": req.intensity,
        "confidence": 0.95, # Assuming high since it's already an event
        "source": "Database"
    }
    
    # Run through the 5-step ML Sequence
    result = run_ml_pipeline(weather_data, gps_coords={"lat": 0, "lon": 0})
    
    return result
