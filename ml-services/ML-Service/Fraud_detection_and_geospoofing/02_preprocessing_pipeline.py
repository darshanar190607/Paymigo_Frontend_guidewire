"""
GigKavach GeoTruth™ — Preprocessing Pipeline
Handles:
  • Missing value imputation
  • Feature engineering (derived interaction features)
  • Stratified train / val / test split
  • StandardScaler fit on train only
  • SMOTE oversampling on train set (handles class imbalance)
  • Serialises preprocessors for production inference

Outputs (saved to models_saved/):
  gps_preprocessor.pkl   — fitted scaler for GPS model
  fraud_preprocessor.pkl — fitted scaler for fraud model
  gps_splits.pkl         — (X_train, X_val, X_test, y_train, y_val, y_test)
  fraud_splits.pkl       — same structure for fraud
"""

import os, sys
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    DATA_DIR, MODEL_DIR,
    GPS_FEATURES, GPS_TARGET, GPS_META,
    FRAUD_FEATURES, FRAUD_TARGET, FRAUD_META,
    RANDOM_STATE, TEST_SIZE, VAL_SIZE,
    GPS_PREP_PATH, FRAUD_PREP_PATH,
)

np.random.seed(RANDOM_STATE)


# ══════════════════════════════════════════════════════════════════════
# SECTION 1 ── GPS FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════

def engineer_gps_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds 8 derived features to the 38-dim base:
      speed_baro_interaction, altitude_network_score,
      inertial_consistency_ratio, multi_layer_anomaly_score,
      baro_accel_interaction, network_zone_coherence,
      social_behavioral_combined, overall_geotrust_score
    Returns DataFrame with all original + derived columns.
    """
    df = df.copy()

    # Interaction: speed discrepancy × altitude mismatch
    df["speed_baro_interaction"] = (
        df["speed_discrepancy"] * np.log1p(df["alt_discrepancy_m"] + 1)
    ).round(4)

    # Network consistency × zone coherence
    df["network_zone_coherence"] = (
        df["network_loc_consistency"] * df["route_feasibility"]
    ).round(4)

    # Inertial consistency ratio
    eps = 1e-6
    df["inertial_consistency_ratio"] = (
        df["inertial_speed_est"] / (df["reported_speed_kmph"] + eps)
    ).clip(0, 5).round(4)

    # Baro × accelerometer agreement
    df["baro_accel_interaction"] = (
        df["baro_altitude_rate"].abs() * df["accel_magnitude"]
    ).round(4)

    # Social + behavioral combined threat
    df["social_behavioral_combined"] = (
        0.5 * df["social_anomaly_score"] + 0.5 * df["behavioral_anomaly"]
    ).round(4)

    # Altitude × network mismatch composite
    df["altitude_network_score"] = (
        (df["alt_discrepancy_m"] / 50).clip(0, 1) *
        (1 - df["network_loc_consistency"])
    ).round(4)

    # Multi-layer anomaly score (weighted sum of top indicator features)
    df["multi_layer_anomaly_score"] = (
        0.20 * (1 - df["motion_consistency"]) +
        0.20 * (1 - df["network_loc_consistency"]) +
        0.15 * df["social_anomaly_score"] +
        0.15 * (df["alt_discrepancy_m"] / 100).clip(0, 1) +
        0.15 * (df["speed_discrepancy"] / 200).clip(0, 1) +
        0.15 * df["behavioral_anomaly"]
    ).round(4)

    # Overall GeoTrust score (inverse = more trustworthy)
    df["overall_geotrust_score"] = (
        0.25 * df["motion_consistency"] +
        0.20 * df["network_loc_consistency"] +
        0.15 * df["route_feasibility"] +
        0.15 * df["expected_zone_transition"] +
        0.15 * (1 - df["social_anomaly_score"]) +
        0.10 * df["noise_consistency_score"]
    ).round(4)

    return df


# ══════════════════════════════════════════════════════════════════════
# SECTION 2 ── FRAUD FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════

def engineer_fraud_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds 5 derived fraud features:
      gps_claim_interaction, ring_score_composite,
      temporal_claim_pressure, device_login_risk,
      overall_fraud_risk_score
    """
    df = df.copy()

    # GPS spoof probability × location jumps
    df["gps_claim_interaction"] = (
        df["gps_spoof_probability"] * np.log1p(df["location_jump_count"])
    ).round(4)

    # Ring detection composite
    df["ring_score_composite"] = (
        0.5 * df["network_fraud_ring_score"] +
        0.5 * df["peer_claim_correlation"]
    ).round(4)

    # Temporal pressure: high-frequency + timing anomaly
    df["temporal_claim_pressure"] = (
        np.log1p(df["claim_frequency_30d"]) * df["claim_timing_anomaly"]
    ).round(4)

    # Device + login risk
    df["device_login_risk"] = (
        (df["device_change_count"] / 8).clip(0, 1) * 0.5 +
        df["login_anomaly_score"] * 0.5
    ).round(4)

    # Overall fraud risk composite
    df["overall_fraud_risk_score"] = (
        0.20 * df["gps_spoof_probability"] +
        0.15 * df["ring_score_composite"] +
        0.15 * df["temporal_claim_pressure"].clip(0, 1) +
        0.10 * df["duplicate_claim_score"] +
        0.10 * df["behavioral_baseline_deviation"] +
        0.10 * df["earnings_deviation"].abs().clip(0, 1) / 4 +
        0.10 * (1 - df["barometric_consistency"]) +
        0.10 * df["zone_transition_anomaly"]
    ).round(4)

    return df


# ══════════════════════════════════════════════════════════════════════
# SECTION 3 ── SPLIT + SCALE + SMOTE
# ══════════════════════════════════════════════════════════════════════

def split_scale_smote(
    df: pd.DataFrame,
    feature_cols: list,
    target_col: str,
    smote_ratio: float = 0.5,
    label: str = "dataset",
) -> tuple:
    """
    1. Stratified train / val / test split
    2. StandardScaler fit on train only
    3. SMOTE on train set only
    Returns (X_tr, X_val, X_te, y_tr, y_val, y_te, scaler)
    """
    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # Handle any remaining NaN (safety net)
    imputer = SimpleImputer(strategy="median")
    X = pd.DataFrame(imputer.fit_transform(X), columns=feature_cols)

    # ── Stratified split: train + (val + test) ──
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y,
        test_size=TEST_SIZE + VAL_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    val_ratio = VAL_SIZE / (TEST_SIZE + VAL_SIZE)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp,
        test_size=1 - val_ratio,
        stratify=y_temp,
        random_state=RANDOM_STATE,
    )

    # ── Scale ──
    scaler = StandardScaler()
    X_train_s = pd.DataFrame(scaler.fit_transform(X_train), columns=feature_cols)
    X_val_s   = pd.DataFrame(scaler.transform(X_val),       columns=feature_cols)
    X_test_s  = pd.DataFrame(scaler.transform(X_test),      columns=feature_cols)

    # ── SMOTE on train only ──
    pos_count = int(y_train.sum())
    neg_count = len(y_train) - pos_count
    smote_target = max(int(neg_count * smote_ratio), pos_count)
    sm = SMOTE(
        sampling_strategy=smote_target / neg_count,
        random_state=RANDOM_STATE,
        k_neighbors=5,
    )
    X_res, y_res = sm.fit_resample(X_train_s, y_train)

    print(f"\n[{label}] Split summary:")
    print(f"  Train (before SMOTE): {len(X_train):,}  (pos={int(y_train.sum()):,})")
    print(f"  Train (after  SMOTE): {len(X_res):,}   (pos={int(y_res.sum()):,})")
    print(f"  Val:                  {len(X_val):,}    (pos={int(y_val.sum()):,})")
    print(f"  Test:                 {len(X_test):,}   (pos={int(y_test.sum()):,})")

    return X_res, X_val_s, X_test_s, y_res, y_val, y_test, scaler


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  GigKavach GeoTruth™ — Preprocessing Pipeline")
    print("=" * 65)

    # ── GPS Spoofing ─────────────────────────────────────────────────
    print("\n[GPS] Loading gps_spoof_dataset.csv ...")
    gps_df = pd.read_csv(os.path.join(DATA_DIR, "gps_spoof_dataset.csv"))
    print(f"      Loaded: {gps_df.shape}  |  Spoof: {gps_df[GPS_TARGET].mean()*100:.1f}%")

    gps_df = engineer_gps_features(gps_df)
    gps_feat_cols = GPS_FEATURES + [
        "speed_baro_interaction", "network_zone_coherence",
        "inertial_consistency_ratio", "baro_accel_interaction",
        "social_behavioral_combined", "altitude_network_score",
        "multi_layer_anomaly_score", "overall_geotrust_score",
    ]

    gps_splits = split_scale_smote(
        gps_df, gps_feat_cols, GPS_TARGET,
        smote_ratio=0.5, label="GPS",
    )
    X_tr_g, X_val_g, X_te_g, y_tr_g, y_val_g, y_te_g, scaler_g = gps_splits
    joblib.dump(scaler_g, GPS_PREP_PATH)
    joblib.dump(
        {"X_train": X_tr_g, "X_val": X_val_g, "X_test": X_te_g,
         "y_train": y_tr_g, "y_val": y_val_g, "y_test": y_te_g,
         "feature_cols": gps_feat_cols},
        os.path.join(MODEL_DIR, "gps_splits.pkl"),
    )
    print(f"\n[GPS] Preprocessor saved → {GPS_PREP_PATH}")

    # ── Fraud Detection ──────────────────────────────────────────────
    print("\n[FRAUD] Loading fraud_dataset.csv ...")
    fraud_df = pd.read_csv(os.path.join(DATA_DIR, "fraud_dataset.csv"))
    print(f"        Loaded: {fraud_df.shape}  |  Fraud: {fraud_df[FRAUD_TARGET].mean()*100:.1f}%")

    fraud_df = engineer_fraud_features(fraud_df)
    fraud_feat_cols = FRAUD_FEATURES + [
        "gps_claim_interaction", "ring_score_composite",
        "temporal_claim_pressure", "device_login_risk",
        "overall_fraud_risk_score",
    ]

    fraud_splits = split_scale_smote(
        fraud_df, fraud_feat_cols, FRAUD_TARGET,
        smote_ratio=0.5, label="FRAUD",
    )
    X_tr_f, X_val_f, X_te_f, y_tr_f, y_val_f, y_te_f, scaler_f = fraud_splits
    joblib.dump(scaler_f, FRAUD_PREP_PATH)
    joblib.dump(
        {"X_train": X_tr_f, "X_val": X_val_f, "X_test": X_te_f,
         "y_train": y_tr_f, "y_val": y_val_f, "y_test": y_te_f,
         "feature_cols": fraud_feat_cols},
        os.path.join(MODEL_DIR, "fraud_splits.pkl"),
    )
    print(f"\n[FRAUD] Preprocessor saved → {FRAUD_PREP_PATH}")

    print("\n[DONE] Preprocessing complete.\n")