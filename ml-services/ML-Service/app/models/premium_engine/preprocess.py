import numpy as np
import pandas as pd
import joblib
from pathlib import Path

MODEL_DIR = Path(__file__).parent
TARGET    = "actual_premium"

POLICY_TIER_MAP = {"Basic": 0, "Standard": 1, "Premium": 2}

BASE_FEATURES = [
    "zone_risk_tier", "lstm_forecast_score", "aqi_7day_avg",
    "platform_tenure_weeks", "loyalty_weeks_paid",
    "historical_disruption_rate", "peer_claim_rate_zone", "current_month",
]

ALL_FEATURES = [
    "zone_risk_tier", "lstm_forecast_score", "aqi_7day_avg",
    "platform_tenure_weeks", "loyalty_weeks_paid",
    "historical_disruption_rate", "peer_claim_rate_zone",
    "pt", "rxd", "rxp", "dxp", "axl", "tr",
    "ptxr", "ptxd", "ptxpeer", "full_risk",
    "ptxrxd", "ptxrxp", "zone_sq", "pt_sq",
    "month_sin", "month_cos", "risk_density",
    "aqi_log", "tenure_log", "loyalty_log",
    "pt3way", "risk_aqi", "peer_lstm", "zone_lstm", "pt_tr",
    "rxd_sq", "full_risk_sq", "ptxr_sq",
    "pt_te", "zone_te",
]


def _engineer(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["pt"]           = d["policy_tier"].map(POLICY_TIER_MAP)
    d["rxd"]          = d["zone_risk_tier"] * d["historical_disruption_rate"]
    d["rxp"]          = d["zone_risk_tier"] * d["peer_claim_rate_zone"]
    d["dxp"]          = d["historical_disruption_rate"] * d["peer_claim_rate_zone"]
    d["axl"]          = d["aqi_7day_avg"] * d["lstm_forecast_score"]
    d["tr"]           = d["loyalty_weeks_paid"] / (d["platform_tenure_weeks"] + 1)
    d["ptxr"]         = d["pt"] * d["zone_risk_tier"]
    d["ptxd"]         = d["pt"] * d["historical_disruption_rate"]
    d["ptxpeer"]      = d["pt"] * d["peer_claim_rate_zone"]
    d["full_risk"]    = d["pt"] * d["zone_risk_tier"] * d["historical_disruption_rate"] * d["peer_claim_rate_zone"]
    d["ptxrxd"]       = d["pt"] * d["rxd"]
    d["ptxrxp"]       = d["pt"] * d["rxp"]
    d["zone_sq"]      = d["zone_risk_tier"] ** 2
    d["pt_sq"]        = d["pt"] ** 2
    d["month_sin"]    = np.sin(2 * np.pi * d["current_month"] / 12)
    d["month_cos"]    = np.cos(2 * np.pi * d["current_month"] / 12)
    d["risk_density"] = d["full_risk"] / (d["platform_tenure_weeks"] + 1)
    d["aqi_log"]      = np.log1p(d["aqi_7day_avg"])
    d["tenure_log"]   = np.log1p(d["platform_tenure_weeks"])
    d["loyalty_log"]  = np.log1p(d["loyalty_weeks_paid"])
    d["pt3way"]       = d["pt"] * d["zone_risk_tier"] * d["lstm_forecast_score"]
    d["risk_aqi"]     = d["rxd"] * d["aqi_log"]
    d["peer_lstm"]    = d["peer_claim_rate_zone"] * d["lstm_forecast_score"]
    d["zone_lstm"]    = d["zone_risk_tier"] * d["lstm_forecast_score"]
    d["pt_tr"]        = d["pt"] * d["tr"]
    d["rxd_sq"]       = d["rxd"] ** 2
    d["full_risk_sq"] = d["full_risk"] ** 2
    d["ptxr_sq"]      = d["ptxr"] ** 2
    return d


def _fill(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for col in BASE_FEATURES:
        if col in d.columns:
            d[col] = d[col].fillna(d[col].median() if len(d) > 1 else 0)
    d["aqi_7day_avg"] = d["aqi_7day_avg"].clip(lower=1)
    return d


def preprocess_train(df: pd.DataFrame):
    df = df.drop(columns=["worker_id"], errors="ignore")
    df = _fill(df)
    df = _engineer(df)

    # Target encoding — fit on full train, save maps for inference
    global_mean = df[TARGET].mean()
    pt_te_map   = df.groupby("pt")[TARGET].mean().to_dict()
    zone_te_map = df.groupby("zone_risk_tier")[TARGET].mean().to_dict()

    df["pt_te"]   = df["pt"].map(pt_te_map).fillna(global_mean)
    df["zone_te"] = df["zone_risk_tier"].map(zone_te_map).fillna(global_mean)

    joblib.dump({"pt_te": pt_te_map, "zone_te": zone_te_map,
                 "global_mean": global_mean}, MODEL_DIR / "encoders.pkl")
    joblib.dump(ALL_FEATURES, MODEL_DIR / "features.pkl")

    return df[ALL_FEATURES], df[TARGET]


def preprocess_inference(input_dict: dict) -> pd.DataFrame:
    df = pd.DataFrame([input_dict])
    df = _fill(df)
    df = _engineer(df)

    enc = joblib.load(MODEL_DIR / "encoders.pkl")
    df["pt_te"]   = df["pt"].map(enc["pt_te"]).fillna(enc["global_mean"])
    df["zone_te"] = df["zone_risk_tier"].map(enc["zone_te"]).fillna(enc["global_mean"])

    features = joblib.load(MODEL_DIR / "features.pkl")
    return df[features]
