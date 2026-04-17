import json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel, create_model
from app.models.zone_clusterer.predict import predict_zone_risk

router = APIRouter()

_metadata = json.loads(
    (Path(__file__).parent.parent / "models/zone_clusterer/metadata.json").read_text()
)
_features = _metadata["features"]

# Dynamically build request model from trained feature set
ClusterRequest = create_model(
    "ClusterRequest",
    **{f: (float, ...) for f in _features}
)


@router.post("/predict")
def cluster_predict(req: ClusterRequest):
    return predict_zone_risk(req.dict())
