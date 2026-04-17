"""
GeoTruth — Master Coherence XGBoost Trainer
============================================
Trains the final decision engine that replaces hardcoded math in server.py.
The model receives all 4 layer scores + derived signals and outputs a
probability: P(is_genuine | all_signals).

Exports: geotruth/models/xgb_coherence_v1.json

Run AFTER generate_coherence.py:
    python geotruth/training/train_coherence.py
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    confusion_matrix,
    accuracy_score,
)
from sklearn.preprocessing import StandardScaler
import joblib

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("train_coherence")

# ── Paths ──────────────────────────────────────────────────────────────────────

BASE_DIR   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH  = os.path.join(BASE_DIR, "models", "coherence_training.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "xgb_coherence_v1.json")
META_PATH  = os.path.join(BASE_DIR, "models", "xgb_coherence_v1_meta.json")

# ── Feature Engineering ────────────────────────────────────────────────────────

FEATURE_COLUMNS = [
    # Raw layer scores
    "l1_baro_score",
    "l2_acoustic_score",
    "l3_network_score",
    "l4_inertial_score",
    # Availability flags (for graceful degradation awareness)
    "l1_baro_available",
    "l2_acoustic_available",
    "l3_network_available",
    "l4_inertial_available",
    # Fraud signals
    "mock_flag",
    "claim_burst_rate",
    "baseline_deviation",
    # Engineered features (added below)
    "available_sensor_count",
    "available_layer_mean_score",
    "max_score",
    "min_score",
    "score_variance",
    "mock_x_inertial",       # Interaction: mock flag × inertial score
    "burst_x_deviation",     # Interaction: burst rate × baseline deviation
]

TARGET_COLUMN = "is_genuine"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features that capture cross-layer signal interactions."""
    df = df.copy()

    score_cols = ["l1_baro_score", "l2_acoustic_score", "l3_network_score", "l4_inertial_score"]
    avail_cols = ["l1_baro_available", "l2_acoustic_available", "l3_network_available", "l4_inertial_available"]

    # Effective scores (0 if sensor unavailable — already the case from generator,
    # but we explicitly enforce it here)
    for score_col, avail_col in zip(score_cols, avail_cols):
        df[score_col] = df[score_col] * df[avail_col]

    # Number of available sensors (0–4)
    df["available_sensor_count"] = df[avail_cols].sum(axis=1)

    # Mean score across AVAILABLE layers only (avoid penalising budget phones)
    sensor_sum   = df[score_cols].sum(axis=1)
    sensor_count = df["available_sensor_count"].replace(0, 1)  # avoid div-by-zero
    df["available_layer_mean_score"] = sensor_sum / sensor_count

    # Score spread
    df["max_score"]      = df[score_cols].max(axis=1)
    df["min_score"]      = df[score_cols].min(axis=1)
    df["score_variance"] = df[score_cols].var(axis=1)

    # Interaction terms
    df["mock_x_inertial"]    = df["mock_flag"] * df["l4_inertial_score"]
    df["burst_x_deviation"]  = df["claim_burst_rate"] * df["baseline_deviation"]

    return df


# ── Model Training ─────────────────────────────────────────────────────────────

def train(data_path: str = DATA_PATH) -> XGBClassifier:
    """
    Load data, engineer features, train XGBClassifier with cross-validation,
    and return the fitted model.
    """
    # ── Load data ────────────────────────────────────────────────────────────
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Training data not found: {data_path}\n"
            "Run: python geotruth/training/generate_coherence.py first"
        )

    df = pd.read_csv(data_path)
    log.info(f"Loaded {len(df)} rows from {data_path}")
    log.info(f"Class balance: {df[TARGET_COLUMN].value_counts().to_dict()}")

    # ── Feature engineering ───────────────────────────────────────────────────
    df = engineer_features(df)

    X = df[FEATURE_COLUMNS].values.astype(np.float32)
    y = df[TARGET_COLUMN].values.astype(int)

    # ── Train/test split ─────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    log.info(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # ── Class weighting (handle slight imbalance) ─────────────────────────────
    genuine_count = y_train.sum()
    fraud_count   = len(y_train) - genuine_count
    scale_pos_weight = fraud_count / genuine_count
    log.info(f"scale_pos_weight: {scale_pos_weight:.3f}")

    # ── XGBoost model ────────────────────────────────────────────────────────
    model = XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.05,
        reg_lambda=1.0,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )

    # ── Cross-validation ──────────────────────────────────────────────────────
    log.info("Running 5-fold cross-validation …")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
    log.info(f"CV ROC-AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # ── Final fit with early stopping ─────────────────────────────────────────
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # ── Evaluation ────────────────────────────────────────────────────────────
    y_pred      = model.predict(X_test)
    y_pred_prob = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    roc_auc  = roc_auc_score(y_test, y_pred_prob)

    log.info(f"\n{'='*50}")
    log.info(f"Test Accuracy : {accuracy:.4f}")
    log.info(f"Test ROC-AUC  : {roc_auc:.4f}")
    log.info(f"\nClassification Report:\n{classification_report(y_test, y_pred, target_names=['Fraud', 'Genuine'])}")
    log.info(f"Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")

    # ── Feature importance ────────────────────────────────────────────────────
    importance = dict(zip(FEATURE_COLUMNS, model.feature_importances_))
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    log.info("\nTop Feature Importances:")
    for feat, imp in sorted_importance[:10]:
        bar = "█" * int(imp * 50)
        log.info(f"  {feat:<30} {bar} {imp:.4f}")

    return model, {
        "accuracy":   float(accuracy),
        "roc_auc":    float(roc_auc),
        "cv_auc_mean": float(cv_scores.mean()),
        "cv_auc_std":  float(cv_scores.std()),
        "n_train":    int(len(X_train)),
        "n_test":     int(len(X_test)),
        "features":   FEATURE_COLUMNS,
        "feature_importances": {k: float(v) for k, v in sorted_importance},
    }


def save(model: XGBClassifier, meta: dict, model_path: str = MODEL_PATH, meta_path: str = META_PATH):
    """Save XGBoost booster to JSON and write metadata."""
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.get_booster().save_model(model_path)
    log.info(f"Model saved → {model_path}")

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    log.info(f"Metadata saved → {meta_path}")


# ── Inference Helper ────────────────────────────────────────────────────────────

def build_feature_vector(
    l1_baro_score: float,       l1_baro_available: int,
    l2_acoustic_score: float,   l2_acoustic_available: int,
    l3_network_score: float,    l3_network_available: int,
    l4_inertial_score: float,   l4_inertial_available: int,
    mock_flag: int,
    claim_burst_rate: float,
    baseline_deviation: float,
) -> np.ndarray:
    """
    Build a single feature row for inference (matches FEATURE_COLUMNS order).
    Call this from server.py before model.predict_proba().
    """
    row = {
        "l1_baro_score":          l1_baro_score    * l1_baro_available,
        "l2_acoustic_score":      l2_acoustic_score * l2_acoustic_available,
        "l3_network_score":       l3_network_score  * l3_network_available,
        "l4_inertial_score":      l4_inertial_score * l4_inertial_available,
        "l1_baro_available":      float(l1_baro_available),
        "l2_acoustic_available":  float(l2_acoustic_available),
        "l3_network_available":   float(l3_network_available),
        "l4_inertial_available":  float(l4_inertial_available),
        "mock_flag":              float(mock_flag),
        "claim_burst_rate":       float(claim_burst_rate),
        "baseline_deviation":     float(baseline_deviation),
    }

    score_vals = [
        row["l1_baro_score"], row["l2_acoustic_score"],
        row["l3_network_score"], row["l4_inertial_score"],
    ]
    avail_count = (l1_baro_available + l2_acoustic_available +
                   l3_network_available + l4_inertial_available)

    row["available_sensor_count"]    = float(avail_count)
    row["available_layer_mean_score"] = sum(score_vals) / max(avail_count, 1)
    row["max_score"]     = max(score_vals)
    row["min_score"]     = min(score_vals)
    row["score_variance"] = float(np.var(score_vals))
    row["mock_x_inertial"]   = float(mock_flag) * l4_inertial_score
    row["burst_x_deviation"] = float(claim_burst_rate) * float(baseline_deviation)

    return np.array([row[col] for col in FEATURE_COLUMNS], dtype=np.float32).reshape(1, -1)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Auto-generate data if missing
    if not os.path.exists(DATA_PATH):
        log.info("Training data not found — running generate_coherence.py first …")
        import subprocess, sys
        script = os.path.join(os.path.dirname(__file__), "generate_coherence.py")
        subprocess.run([sys.executable, script], check=True)

    model, meta = train()
    save(model, meta)

    print(f"\nGeoTruth Coherence Engine v1 trained and saved.")
    print(f"   Model : {MODEL_PATH}")
    print(f"   AUC   : {meta['roc_auc']:.4f}")
    print(f"   Acc   : {meta['accuracy']:.4f}")
    