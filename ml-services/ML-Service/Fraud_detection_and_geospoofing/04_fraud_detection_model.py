"""
GigKavach GeoTruth™ — Fraud Detection Model
Architecture:
  • Primary    : LightGBM (gradient boosting)
  • Auxiliary  : Isolation Forest (unsupervised anomaly score)
  • Fusion     : Calibrated weighted blend of LGB prob + IF score
  • Tuning     : Optuna (60 trials, maximise PR-AUC on val set)
  • Output     : fraud_model.pkl

Why LightGBM + Isolation Forest?
  LightGBM handles the supervised signal well.
  Isolation Forest catches unseen fraud patterns not represented in training.
  Blending both gives higher recall with controlled precision.

  # --- HACKATHON WOW FACTOR ---
  # XGBoost/LightGBM: Handles non-linear risk interactions (monsoon × zone)
  # Isolation Forest: Unsupervised fraud detection without labeled data
"""

import os, sys, warnings
import numpy as np
import pandas as pd
import joblib
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore")

from sklearn.ensemble import IsolationForest
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score,
    average_precision_score,
)
from lightgbm import LGBMClassifier

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import MODEL_DIR, FRAUD_MODEL_PATH, RANDOM_STATE, CV_FOLDS

# ── Load preprocessed splits ──────────────────────────────────────────
splits = joblib.load(os.path.join(MODEL_DIR, "fraud_splits.pkl"))
X_train      = splits["X_train"]
X_val        = splits["X_val"]
X_test       = splits["X_test"]
y_train      = splits["y_train"]
y_val        = splits["y_val"]
y_test       = splits["y_test"]
FEATURE_COLS = splits["feature_cols"]

n_pos = int(y_train.sum())
n_neg = len(y_train) - n_pos
scale_pos = n_neg / max(n_pos, 1)

print(f"[FRAUD MODEL] Features: {len(FEATURE_COLS)}")
print(f"              Train: {len(X_train):,}  Val: {len(X_val):,}  Test: {len(X_test):,}")
print(f"              Scale-pos-weight: {scale_pos:.2f}")


# ══════════════════════════════════════════════════════════════════════
# SECTION 1 ── LIGHTGBM OPTUNA TUNING
# ══════════════════════════════════════════════════════════════════════

def lgb_objective(trial):
    params = {
        "n_estimators":      trial.suggest_int("n_estimators", 300, 1000),
        "max_depth":         trial.suggest_int("max_depth", 4, 12),
        "num_leaves":        trial.suggest_int("num_leaves", 20, 150),
        "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 10, 100),
        "subsample":         trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree":  trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_alpha":         trial.suggest_float("reg_alpha", 1e-8, 1.0, log=True),
        "reg_lambda":        trial.suggest_float("reg_lambda", 1e-8, 1.0, log=True),
        "scale_pos_weight":  trial.suggest_float("scale_pos_weight", 1.0, scale_pos * 2),
        "random_state":      RANDOM_STATE,
        "n_jobs":            -1,
        "verbosity":         -1,
        "objective":         "binary",
        "metric":            "average_precision",
    }
    lgb = LGBMClassifier(**params)
    lgb.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[],
    )
    probs = lgb.predict_proba(X_val)[:, 1]
    return average_precision_score(y_val, probs)


# ══════════════════════════════════════════════════════════════════════
# SECTION 2 ── ISOLATION FOREST ANOMALY SCORER
# ══════════════════════════════════════════════════════════════════════

def train_isolation_forest(X_train: pd.DataFrame, contamination: float = 0.1) -> IsolationForest:
    """
    Trained on FULL training set (including fraud) — models overall distribution.
    score_samples() returns negative anomaly scores; we flip for probability-like value.
    """
    iso = IsolationForest(
        n_estimators=200,
        max_samples="auto",
        contamination=contamination,
        max_features=1.0,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    iso.fit(X_train)
    return iso


def iso_to_prob(iso: IsolationForest, X: pd.DataFrame) -> np.ndarray:
    """
    Convert raw IF scores to [0,1] anomaly probability.
    score_samples() returns negative scores; more negative = more anomalous.
    We min-max scale to [0,1] so 1 = most anomalous.
    """
    raw = iso.score_samples(X)
    lo, hi = raw.min(), raw.max()
    if hi == lo:
        return np.zeros(len(raw))
    normalised = (raw - lo) / (hi - lo)  # 1 = least anomalous
    return 1.0 - normalised              # flip: 1 = most anomalous


# ══════════════════════════════════════════════════════════════════════
# SECTION 3 ── FUSION + THRESHOLD
# ══════════════════════════════════════════════════════════════════════

def fused_probability(
    lgb_prob: np.ndarray,
    iso_prob: np.ndarray,
    w_lgb: float = 0.75,
) -> np.ndarray:
    """Weighted blend: 75% supervised LGB + 25% unsupervised IF."""
    return w_lgb * lgb_prob + (1 - w_lgb) * iso_prob


def find_best_threshold(probs: np.ndarray, y_true: pd.Series) -> float:
    best_t, best_f1 = 0.5, 0.0
    for t in np.arange(0.10, 0.91, 0.02):
        preds = (probs >= t).astype(int)
        if preds.sum() == 0:
            continue
        f1 = f1_score(y_true, preds, zero_division=0)
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return float(round(best_t, 2))


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  Fraud Detection — Model Training (LightGBM + Isolation Forest)")
    print("=" * 65)

    N_TRIALS = 60

    # ── Tune LightGBM ────────────────────────────────────────────────
    print(f"\n[OPTUNA] Tuning LightGBM ({N_TRIALS} trials)...")
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE),
    )
    study.optimize(lgb_objective, n_trials=N_TRIALS, show_progress_bar=False)
    best_params = {
        **study.best_params,
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
        "verbosity": -1,
        "objective": "binary",
    }
    print(f"         Best LGB PR-AUC (val): {study.best_value:.4f}")

    # ── Train final LightGBM ──────────────────────────────────────────
    print("\n[TRAIN] Fitting final LightGBM model...")
    lgb_model = LGBMClassifier(**best_params)
    lgb_model.fit(X_train, y_train)

    # Calibrate probabilities (Platt scaling via cross-validation)
    print("[CALIBRATE] Platt-scaling LGB probabilities...")
    calibrated_lgb = CalibratedClassifierCV(lgb_model, method="sigmoid", cv=CV_FOLDS)
    calibrated_lgb.fit(X_train, y_train)

    # ── Train Isolation Forest ────────────────────────────────────────
    print("\n[TRAIN] Fitting Isolation Forest (contamination=0.10)...")
    iso_model = train_isolation_forest(X_train, contamination=0.10)

    # ── Fused probabilities on val ────────────────────────────────────
    lgb_val_probs = calibrated_lgb.predict_proba(X_val)[:, 1]
    iso_val_probs = iso_to_prob(iso_model, X_val)
    fused_val     = fused_probability(lgb_val_probs, iso_val_probs)

    # ── Threshold optimisation ────────────────────────────────────────
    best_threshold = find_best_threshold(fused_val, y_val)
    val_preds      = (fused_val >= best_threshold).astype(int)
    print(f"\n[THRESHOLD] Optimal threshold: {best_threshold}")

    # ── Val metrics ───────────────────────────────────────────────────
    print("\n[VAL METRICS]")
    print(f"  ROC-AUC  : {roc_auc_score(y_val, fused_val):.4f}")
    print(f"  PR-AUC   : {average_precision_score(y_val, fused_val):.4f}")
    print(f"  F1 Score : {f1_score(y_val, val_preds):.4f}")
    print(f"  Precision: {precision_score(y_val, val_preds):.4f}")
    print(f"  Recall   : {recall_score(y_val, val_preds):.4f}")

    # ── LGB-only metrics (for comparison) ────────────────────────────
    lgb_preds = (lgb_val_probs >= best_threshold).astype(int)
    print("\n[VAL METRICS — LGB only (before fusion)]")
    print(f"  ROC-AUC  : {roc_auc_score(y_val, lgb_val_probs):.4f}")
    print(f"  F1 Score : {f1_score(y_val, lgb_preds):.4f}")

    # ── Feature importance (top 15) ───────────────────────────────────
    print("\n[FEATURE IMPORTANCE — Top 15]")
    imp = lgb_model.feature_importances_
    fi_df = pd.DataFrame({"feature": FEATURE_COLS, "importance": imp})
    fi_df = fi_df.sort_values("importance", ascending=False).head(15)
    for _, row in fi_df.iterrows():
        bar = "█" * int(row["importance"] / fi_df["importance"].max() * 30)
        print(f"  {row['feature']:<40} {bar}")

    # ── Save model ────────────────────────────────────────────────────
    artifact = {
        "lgb_model":      calibrated_lgb,
        "iso_model":      iso_model,
        "threshold":      best_threshold,
        "w_lgb":          0.75,
        "feature_cols":   FEATURE_COLS,
        "best_lgb_params": best_params,
    }
    joblib.dump(artifact, FRAUD_MODEL_PATH)
    print(f"\n[SAVED] Fraud model → {FRAUD_MODEL_PATH}")
    print("\n[DONE] Fraud detection model training complete.\n")