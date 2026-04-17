from fastapi import APIRouter
from pydantic import BaseModel
from app.models.premium_engine.predict import predict_premium

router = APIRouter()

class PremiumRequest(BaseModel):
    # Basic user info (for mapping)
    age: int
    job_type: str
    experience_years: int
    incident_history: int
    
    # Required ML model features
    zone_risk_tier: float
    lstm_forecast_score: float = 0.5  # Default value
    aqi_7day_avg: float = 50.0  # Default value
    platform_tenure_weeks: int = 4  # Default: 1 month
    loyalty_weeks_paid: int = 4  # Default: 1 month
    historical_disruption_rate: float = 0.1  # Default low risk
    peer_claim_rate_zone: float = 0.05  # Default low rate
    current_month: int = 1  # Default January
    policy_tier: str = "Standard"  # Default tier

@router.post("/predict")
def premium_predict(req: PremiumRequest):
    result = predict_premium(req.dict())
    return {"premium": result.get("predicted_premium", 69)}
