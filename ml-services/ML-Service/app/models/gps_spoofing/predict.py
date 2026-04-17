"""
GeoTruth™ GPS Spoofing — Inference Module
Loads the trained StackingClassifier (XGBoost + RF → LR) and
applies the same 8 derived features used during training before
passing the 46-dim vector through the fitted StandardScaler.

Model artefacts (from Fraud_detection_and_geospoofing/models_saved/):
  gps_spoof_model.pkl    — stacking pipeline (model + threshold + feature_cols)
  gps_preprocessor.pkl   — fitted StandardScaler
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# ── Artefact paths ────────────────────────────────────────────────────
# The saved models live in the training directory, not in app/models.
# We resolve the path relative to this file so it works regardless of
# the working directory the FastAPI server is started from.
_THIS_DIR    = Path(__file__).resolve().parent
_MODELS_SAVED = _THIS_DIR.parents[2] / "Fraud_detection_and_geospoofing" / "models_saved"

GPS_MODEL_PATH = _MODELS_SAVED / "gps_spoof_model.pkl"
GPS_PREP_PATH  = _MODELS_SAVED / "gps_preprocessor.pkl"

# ── Lazy-loaded globals (loaded once on first call) ───────────────────
_artifact  = None   # dict: model, threshold, feature_cols
_scaler    = None

def _load():
    global _artifact, _scaler
    if _artifact is None:
        _artifact = joblib.load(str(GPS_MODEL_PATH))
        _scaler   = joblib.load(str(GPS_PREP_PATH))


# ── 38 base GPS features (matches config.GPS_FEATURES) ───────────────
BASE_FEATURES = [
    # Barometric pressure layer (5)
    "baro_alt_m", "gps_alt_m", "alt_discrepancy_m",
    "baro_pressure_hpa", "baro_altitude_rate",
    # Acoustic fingerprinting (4)
    "ambient_noise_db", "noise_consistency_score",
    "location_acoustic_match", "acoustic_anomaly_flag",
    # Network topology (6)
    "cell_tower_count", "wifi_ap_count", "expected_tower_match",
    "network_latency_ms", "signal_strength_dbm", "network_loc_consistency",
    # Inertial motion (7)
    "accel_magnitude", "accel_variance_1min", "reported_speed_kmph",
    "inertial_speed_est", "speed_discrepancy",
    "heading_change_rate", "motion_consistency",
    # Zone coherence (5)
    "zone_pincode_match", "expected_zone_transition",
    "geofence_violations", "route_feasibility", "delivery_density_match",
    # Behavioral baseline (6)
    "session_duration_min", "deliveries_per_hour", "break_frequency",
    "speed_vs_baseline", "earnings_vs_baseline", "behavioral_anomaly",
    # Social ring detection (5)
    "peer_proximity_count", "sync_movement_score",
    "device_fingerprint_match", "platform_login_consistency",
    "social_anomaly_score",
]


def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adds the 8 derived interaction features used during training."""
    df = df.copy()
    eps = 1e-6

    df["speed_baro_interaction"] = (
        df["speed_discrepancy"] * np.log1p(df["alt_discrepancy_m"] + 1)
    ).round(4)

    df["network_zone_coherence"] = (
        df["network_loc_consistency"] * df["route_feasibility"]
    ).round(4)

    df["inertial_consistency_ratio"] = (
        df["inertial_speed_est"] / (df["reported_speed_kmph"] + eps)
    ).clip(0, 5).round(4)

    df["baro_accel_interaction"] = (
        df["baro_altitude_rate"].abs() * df["accel_magnitude"]
    ).round(4)

    df["social_behavioral_combined"] = (
        0.5 * df["social_anomaly_score"] + 0.5 * df["behavioral_anomaly"]
    ).round(4)

    df["altitude_network_score"] = (
        (df["alt_discrepancy_m"] / 50).clip(0, 1) *
        (1 - df["network_loc_consistency"])
    ).round(4)

    df["multi_layer_anomaly_score"] = (
        0.20 * (1 - df["motion_consistency"]) +
        0.20 * (1 - df["network_loc_consistency"]) +
        0.15 * df["social_anomaly_score"] +
        0.15 * (df["alt_discrepancy_m"] / 100).clip(0, 1) +
        0.15 * (df["speed_discrepancy"] / 200).clip(0, 1) +
        0.15 * df["behavioral_anomaly"]
    ).round(4)

    df["overall_geotrust_score"] = (
        0.25 * df["motion_consistency"] +
        0.20 * df["network_loc_consistency"] +
        0.15 * df["route_feasibility"] +
        0.15 * df["expected_zone_transition"] +
        0.15 * (1 - df["social_anomaly_score"]) +
        0.10 * df["noise_consistency_score"]
    ).round(4)

    return df


def predict_gps_spoof(features: dict) -> dict:
    """
    Args:
        features: dict with (at minimum) the 38 BASE_FEATURES as keys.
                  Missing keys default to 0. Extra keys are ignored.

    Returns:
        {
          "gps_anomaly":        bool,
          "spoof_probability":  float  (0.0–1.0),
          "confidence":         float,
          "threshold":          float,
          "geotrust_score":     float  (0.0–1.0, higher = more trusted),
          "status":             "active"
        }
    """
    _load()

    # Build a single-row DataFrame with all 38 base features
    row = {f: features.get(f, 0.0) for f in BASE_FEATURES}
    df  = pd.DataFrame([row])

    # Apply the 8 derived features (same logic as training pipeline)
    df = _engineer_features(df)

    # Align to the exact feature order the model was trained on
    feature_cols = _artifact["feature_cols"]
    df = df.reindex(columns=feature_cols, fill_value=0.0)

    # Scale using the fitted StandardScaler
    X_scaled = _scaler.transform(df.values)

    # Predict
    model     = _artifact["model"]
    threshold = _artifact["threshold"]
    prob      = float(model.predict_proba(X_scaled)[0][1])
    is_spoof  = prob >= threshold

    # Derive geotrust score (inverse of spoof probability, weighted)
    geotrust = round(float(df["overall_geotrust_score"].iloc[0]), 4)

    return {
        "gps_anomaly":       is_spoof,
        "spoof_probability": round(prob, 4),
        "confidence":        round(abs(prob - threshold) / max(threshold, 1 - threshold), 4),
        "threshold":         round(threshold, 4),
        "geotrust_score":    geotrust,
        "status":            "active",
    }
