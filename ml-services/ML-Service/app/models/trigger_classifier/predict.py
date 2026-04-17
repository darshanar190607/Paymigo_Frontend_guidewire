import json
import joblib
from pathlib import Path
from .preprocess import preprocess_inference

MODEL_DIR = Path(__file__).parent
_model     = None
_threshold = None


def _load():
    global _model, _threshold
    if _model is None:
        _model     = joblib.load(MODEL_DIR / "rf_trigger.pkl")
        _threshold = json.loads((MODEL_DIR / "threshold.json").read_text())["threshold"]


def predict_trigger(input_dict: dict) -> dict:
    _load()
    X          = preprocess_inference(input_dict)
    confidence = float(_model.predict_proba(X)[0][1])
    approved   = int(confidence >= _threshold)
    return {
        "approved":   approved,
        "confidence": round(confidence, 4),
        "threshold":  _threshold,
    }
