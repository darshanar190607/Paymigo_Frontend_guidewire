from fastapi import APIRouter
from pydantic import BaseModel
import re
from app.pipelines.weather_orchestrator import run_ml_pipeline

router = APIRouter()

class TestScenarioRequest(BaseModel):
    comment: str

@router.post("/parse")
def parse_trigger_command(req: TestScenarioRequest):
    # Example comment: "#trigger heavy_rain zone_12 duration_2h"
    comment = req.comment.strip().lower()
    
    parts = comment.split()
    if not parts or not (parts[0] in ["#trigger", "#test", "#simulate"]):
        return {"error": "Invalid command prefix"}
    
    action = parts[0]
    
    # Parse mock params
    weather_type = "RAIN"
    intensity = 5.0
    zone_id = "default"
    
    for part in parts[1:]:
        if "rain" in part or "storm" in part:
            weather_type = "RAIN"
            intensity = 25.0
        elif "drought" in part:
            weather_type = "DROUGHT"
            intensity = 0.0
        elif part.startswith("zone_"):
            zone_id = part
    
    weather_data = {
        "weather_type": weather_type,
        "intensity": intensity,
        "confidence": 1.0,
        "source": "Simulator"
    }

    # Run ML sequence to evaluate simulated conditions
    result = run_ml_pipeline(weather_data, gps_coords={"lat": 0, "lon": 0})
    
    return {
        "scenario": action,
        "simulated_data": weather_data,
        "orchestrator_decision": result
    }
