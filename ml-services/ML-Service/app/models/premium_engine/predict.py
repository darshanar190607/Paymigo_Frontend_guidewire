import joblib
from pathlib import Path
from .preprocess import preprocess_inference

MODEL_DIR = Path(__file__).parent
_model = None


def _load():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_DIR / "xgboost_model.pkl")


def predict_premium(input_dict: dict) -> dict:
    _load()
    X = preprocess_inference(input_dict)
    premium = float(_model.predict(X)[0])
    return {"predicted_premium": round(premium, 2)}
