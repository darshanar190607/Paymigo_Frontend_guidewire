import json
import joblib
import pandas as pd
from pathlib import Path

from .preprocess import preprocess_features, apply_scaler, apply_pca, FEATURES

MODEL_DIR    = Path(__file__).parent
_metadata    = json.loads((MODEL_DIR / "metadata.json").read_text())
_model       = joblib.load(MODEL_DIR / "kmeans_model.pkl")
_scaler_path = MODEL_DIR / "scaler.pkl"
_pca_path    = MODEL_DIR / "pca.pkl"


def predict_zone_risk(input_dict: dict) -> dict:
    df = pd.DataFrame([input_dict])
    X = preprocess_features(df, FEATURES)
    X_scaled = apply_scaler(X.values, _scaler_path)
    X_pca    = apply_pca(X_scaled, _pca_path)
    cluster  = int(_model.predict(X_pca)[0])
    
    # Cluster 0 is the high-risk centroid (high rain, storms)
    # Cluster 1 is the low-risk centroid (defaults/safe)
    mapped_tier = 4 if cluster == 0 else 1
    
    return {"cluster": cluster, "zone_risk_tier": mapped_tier}
