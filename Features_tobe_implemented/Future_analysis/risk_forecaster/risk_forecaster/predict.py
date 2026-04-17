import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"]  = "2"

import json
import numpy as np
import pandas as pd
from pathlib import Path
from tensorflow.keras.models import load_model

from preprocess import scale_inference_input, FEATURES, SEQ_IN, SEQ_OUT

MODEL_DIR  = Path(__file__).parent
_model     = None
_threshold = None


def _load():
    global _model, _threshold
    if _model is None:
        _model     = load_model(str(MODEL_DIR / "lstm_model.keras"), compile=False)
        _threshold = json.loads((MODEL_DIR / "threshold.json").read_text())["threshold"]


def predict_disruption(last_14_days: list) -> dict:
    """
    Args:
        last_14_days: list of 14 dicts with keys matching FEATURES,
                      ordered oldest -> newest

    Returns:
        {
          "forecast_days":          [1..7],
          "disruption_probability": [float x7],
          "disruption_predicted":   [0/1 x7],
          "threshold":              float
        }

    Uses rolling single-step inference:
    - Day 1: predict from days 1-14
    - Day 2: predict from days 2-14 + day1 prediction appended
    - ...up to day 7
    """
    _load()

    if len(last_14_days) != SEQ_IN:
        raise ValueError(f"Expected {SEQ_IN} days of input, got {len(last_14_days)}")

    df_input = pd.DataFrame(last_14_days)[FEATURES].astype(float)
    window   = df_input.values.copy()   # (14, N_FEATURES)

    probabilities = []
    for _ in range(SEQ_OUT):
        X_scaled = scale_inference_input(window)          # (1, 14, N_FEATURES)
        prob     = float(_model.predict(X_scaled, verbose=0)[0][0])
        probabilities.append(prob)
        # Slide window: drop oldest day, append a synthetic next row
        # Use last known feature values as proxy for unknown future features
        next_row = window[-1].copy()
        window   = np.vstack([window[1:], next_row[np.newaxis, :]])

    return {
        "forecast_days":          list(range(1, SEQ_OUT + 1)),
        "disruption_probability": [round(p, 4) for p in probabilities],
        "disruption_predicted":   [int(p >= _threshold) for p in probabilities],
        "threshold":              _threshold,
    }
