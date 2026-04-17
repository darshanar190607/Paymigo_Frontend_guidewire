from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.models.risk_forecaster.predict import predict_disruption

router = APIRouter()

class ForecastRequest(BaseModel):
    sequence: List[List[float]]  # shape: (timesteps, features)

@router.post("/predict")
def forecast_predict(req: ForecastRequest):
    features_keys = [
        "rain_mm", "temp_c", "humidity_pct", "wind_speed_kmph", "pressure_hpa",
        "storm_alert_flag", "flood_alert_flag", "heatwave_flag", "high_wind_flag",
        "rain_3day_avg", "rain_7day_avg"
    ]
    
    # Map the 2D array back to the expected list of dictionaries
    last_14_days = []
    for day_data in req.sequence:
        day_dict = {key: val for key, val in zip(features_keys, day_data)}
        last_14_days.append(day_dict)

    result = predict_disruption(last_14_days)
    return {"forecast": result}
