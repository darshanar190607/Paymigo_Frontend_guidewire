from fastapi import APIRouter
from pydantic import BaseModel
from app.models.trigger_classifier.predict import predict_trigger

router = APIRouter()

class TriggerRequest(BaseModel):
    event_type: str
    severity: float
    zone_id: int
    duration_hours: float

@router.post("/predict")
def trigger_predict(req: TriggerRequest):
    result = predict_trigger(req.dict())
    return {"trigger": result}
