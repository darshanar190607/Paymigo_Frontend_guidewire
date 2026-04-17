"""
Fraud detector predict — wraps the trained LightGBM + Isolation Forest
fusion model from Fraud_detection_and_geospoofing/models_saved/.
"""

import os
import numpy as np
import pandas as pd
import joblib

_BASE = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR = os.path.normpath(
    os.path.join(_BASE, "..", "..", "..", "Fraud_detection_and_geospoofing", "models_saved")
)

_artifact = None
_preprocessor = None


def _load():
    global _artifact, _preprocessor
    if _artifact is None:
        _artifact = joblib.load(os.path.join(_MODELS_DIR, "fraud_model.pkl"))
        _preprocessor = joblib.load(os.path.join(_MODELS_DIR, "fraud_preprocessor.pkl"))


def _iso_to_prob(iso_model, X: pd.DataFrame) -> np.ndarray:
    raw = iso_model.score_samples(X)
    lo, hi = raw.min(), raw.max()
    if hi == lo:
        return np.zeros(len(raw))
    return 1.0 - (raw - lo) / (hi - lo)


def predict(payload: dict) -> dict:
    _load()

    feature_cols = _artifact["feature_cols"]
    row = {col: payload.get(col, 0.0) for col in feature_cols}
    df = pd.DataFrame([row])[feature_cols]
    df_scaled = pd.DataFrame(_preprocessor.transform(df), columns=feature_cols)

    lgb_prob = float(_artifact["lgb_model"].predict_proba(df_scaled)[0, 1])
    iso_prob = float(_iso_to_prob(_artifact["iso_model"], df_scaled)[0])

    w = _artifact.get("w_lgb", 0.75)
    fused = w * lgb_prob + (1 - w) * iso_prob
    threshold = _artifact["threshold"]

    return {
        "is_fraud": bool(fused >= threshold),
        "fraud_probability": round(fused, 4),
        "threshold": threshold,
    }
