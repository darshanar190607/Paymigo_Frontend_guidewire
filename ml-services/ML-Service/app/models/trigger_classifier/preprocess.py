import numpy as np
import pandas as pd
import joblib
from pathlib import Path

MODEL_DIR = Path(__file__).parent
TARGET    = "label_trigger"

# Drop: constant (threshold_value, trigger_type), identifiers (event_id, pincode, start_time)
DROP_COLS = ["event_id", "trigger_type", "threshold_value", "pincode", "start_time"]

BASE_FEATURES = [
    "duration_minutes", "raw_value", "source_confidence",
    "multi_source_match", "sustained_event", "variability", "trend",
]

ALL_FEATURES = [
    "duration_minutes", "raw_value", "source_confidence",
    "multi_source_match", "sustained_event", "variability", "trend",
    "threshold_ratio", "intensity_score", "reliability_score",
    "duration_flag", "conf_x_duration", "variability_inv",
]


def _fill(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for col in BASE_FEATURES:
        if col in d.columns:
            d[col] = d[col].fillna(d[col].median() if len(d) > 1 else 0)
    return d


def _engineer(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    # Use fixed threshold=25 since threshold_value is constant in dataset
    d["threshold_ratio"]   = d["raw_value"] / 26.0
    d["intensity_score"]   = d["raw_value"] * d["duration_minutes"]
    d["reliability_score"] = d["source_confidence"] * d["multi_source_match"]
    d["duration_flag"]     = (d["duration_minutes"] > 120).astype(int)
    d["conf_x_duration"]   = d["source_confidence"] * d["duration_minutes"]
    d["variability_inv"]   = 1.0 / (d["variability"] + 1)
    return d


def preprocess_train(df: pd.DataFrame):
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
    df = _fill(df)
    df = _engineer(df)
    assert df[ALL_FEATURES].isnull().sum().sum() == 0, "NaN values remain after preprocessing"
    joblib.dump(ALL_FEATURES, MODEL_DIR / "features.pkl")
    return df[ALL_FEATURES], df[TARGET]


def preprocess_inference(input_dict: dict) -> pd.DataFrame:
    df = pd.DataFrame([input_dict])
    df = _fill(df)
    df = _engineer(df)
    features = joblib.load(MODEL_DIR / "features.pkl")
    return df[features]
