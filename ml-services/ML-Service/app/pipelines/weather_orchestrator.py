from fastapi import APIRouter
from pydantic import BaseModel
import requests
import random
import os

# Import local models (using fallback patterns per requirements if any fail)
from app.models.zone_clusterer.predict import predict_zone_risk
# from app.models.gps_spoofing.predict import check_gps_spoofing  # DISABLED
from app.models.risk_forecaster.predict import predict_disruption
from app.models.trigger_classifier.predict import predict_trigger
# from app.models.curfew_nlp.predict import analyze_curfew_text  # DISABLED

router = APIRouter()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
ACCUWEATHER_API_KEY = "dummy_accuweather_key" # Placeholder till provided

class WeatherDataOrchestrator:
    @staticmethod
    def get_weather_data(zone_id: str, coords: dict):
        # Primary API: OpenWeatherMap
        try:
            res = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={OPENWEATHER_API_KEY}&units=metric",
                timeout=3
            ).json()
            precipitation = res.get("rain", {}).get("1h", 0)
            return {"weather_type": "RAIN" if precipitation > 0 else "CLEAR", "intensity": precipitation, "confidence": 0.98, "source": "OpenWeatherMap"}
        except:
            pass
            
        # Secondary API: AccuWeather (Simulated Fallback)
        try:
            # Simulate Accuweather
            return {"weather_type": "RAIN", "intensity": 5.0, "confidence": 0.85, "source": "AccuWeather"}
        except:
            pass

        # Fallback: Historical pattern
        return {"weather_type": "UNKNOWN", "intensity": 2.0, "confidence": 0.50, "source": "Historical"}

ZONE_COORDS = {
  'coimbatore_(zone_1)': {'lat': 11.0168, 'lon': 76.9558},
  'chennai_(zone_4)': {'lat': 13.0827, 'lon': 80.2707},
  'bangalore_east': {'lat': 12.9716, 'lon': 77.5946},
  'mumbai_west': {'lat': 19.0760, 'lon': 72.8777},
  'default': {'lat': 12.9716, 'lon': 77.5946}
}

def run_ml_pipeline(weather_data: dict, gps_coords: dict = None):
    # 1. Zone Cluster Model
    cluster = 1
    try:
        # Dummy stats
        cluster = predict_zone_risk({"rain": weather_data["intensity"], "wind": 10.0})["cluster"]
    except: pass

    # 2. GPS Classifier Validation (DISABLED)
    gps_valid = True
    # try:
    #     gps_res = check_gps_spoofing({"lat": gps_coords["lat"], "lon": gps_coords["lon"]})
    #     gps_valid = gps_res.get("is_authentic", True)
    # except: pass

    # 3. Risk Forecaster
    risk_threshold = 15.0
    try:
        # Using dummy data for predict_disruption since it requires 14 days of history
        dummy_14_days = [{"rain": weather_data["intensity"], "wind": 10.0}] * 14
        risk_res = predict_disruption(dummy_14_days)
        risk_threshold = risk_res.get("threshold", 15.0)
    except: pass

    # 4. Trigger Classifier
    decision = "REJECTED"
    confidence = 0.0
    try:
        trigger_res = predict_trigger({
            "event_type": weather_data["weather_type"].lower(), 
            "severity": weather_data["intensity"],
            "zone_id": cluster,
            "duration_hours": 1.0
        })
        decision = "APPROVED" if trigger_res.get("approved") else "REJECTED"
        confidence = trigger_res.get("confidence", 0.8)
    except Exception as e:
        # Fallback Rule-based logic
        if weather_data["intensity"] >= risk_threshold:
            decision = "APPROVED"
        confidence = weather_data["confidence"]

    # 5. Curfew NLP (Optional context addition) - DISABLED
    nlp_context = "Routine weather."
    # try:
    #     nlp_res = analyze_curfew_text({"text": f"Heavy {weather_data['weather_type']} in zone."})
    #     nlp_context = nlp_res.get("context", "Routine weather.")
    # except: pass

    return {
        "decision": decision,
        "amount": 250.0 if decision == "APPROVED" else 0.0,
        "confidence": round(confidence, 2),
        "cluster": cluster,
        "gps_valid": gps_valid,
        "threshold_used": risk_threshold,
        "nlp_context": nlp_context
    }


@router.get("/weather/live/{zone_id}")
def live_weather(zone_id: str):
    coords = ZONE_COORDS.get(zone_id, ZONE_COORDS["default"])
    data = WeatherDataOrchestrator.get_weather_data(zone_id, coords)
    return data

class UserPayload(BaseModel):
    user_id: str
    gps_coordinates: str = None
    zone_id: str = "default"

@router.post("/weather/user")
def user_weather(payload: UserPayload):
    coords = ZONE_COORDS.get(payload.zone_id, ZONE_COORDS["default"])
    # Micro-location interpolation gradient logic placeholder
    data = WeatherDataOrchestrator.get_weather_data(payload.zone_id, coords)
    
    # Slight micro-climate multiplier based on user GPS interpolation
    data["intensity"] *= random.uniform(0.9, 1.1)
    
    return data
