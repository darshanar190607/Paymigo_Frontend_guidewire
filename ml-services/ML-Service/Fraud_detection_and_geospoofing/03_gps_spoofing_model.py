"""
GigKavach GeoTruth™ — GPS Spoofing Detection Model
Architecture:
  • Base models  : XGBoost  +  Random Forest
  • Meta-learner : Logistic Regression  (StackingClassifier)
  • Tuning       : Optuna (50 trials, maximise ROC-AUC on val set)
  • Threshold    : PR-curve optimised for F1 on val set
  • Output       : gps_spoof_model.pkl  (complete stacking pipeline)

  # --- HACKATHON WOW FACTOR ---
  # Random Forest: Robust to overfitting on sparse spatial data
  # Stacking Meta Learner: Calibrates probabilities dynamically across both models
"""

import os, sys, warnings
import numpy as np
import pandas as pd
import joblib
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore")

from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score,
    average_precision_score,
)
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import MODEL_DIR, GPS_MODEL_PATH, RANDOM_STATE, CV_FOLDS

# ── Load preprocessed splits ──────────────────────────────────────────
splits = joblib.load(os.path.join(MODEL_DIR, "gps_splits.pkl"))
X_train      = splits["X_train"]
X_val        = splits["X_val"]
X_test       = splits["X_test"]
y_train      = splits["y_train"]
y_val        = splits["y_val"]
y_test       = splits["y_test"]
FEATURE_COLS = splits["feature_cols"]

print(f"[GPS MODEL] Features: {len(FEATURE_COLS)}")
print(f"            Train: {len(X_train):,}  Val: {len(X_val):,}  Test: {len(X_test):,}")


# ══════════════════════════════════════════════════════════════════════
# SECTION 1 ── OPTUNA HYPERPARAMETER SEARCH
# ══════════════════════════════════════════════════════════════════════

def xgb_objective(trial):
    params = {
        "n_estimators":      trial.suggest_int("n_estimators", 200, 600),
        "max_depth":         trial.suggest_int("max_depth", 4, 10),
        "learning_rate":     trial.suggest_float("learning_rate", 0.02, 0.20, log=True),
        "subsample":         trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree":  trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight":  trial.suggest_int("min_child_weight", 1, 10),
        "gamma":             trial.suggest_float("gamma", 0.0, 2.0),
        "reg_alpha":         trial.suggest_float("reg_alpha", 1e-8, 1.0, log=True),
        "reg_lambda":        trial.suggest_float("reg_lambda", 1e-8, 1.0, log=True),
        "scale_pos_weight":  trial.suggest_float("scale_pos_weight", 1.0, 4.0),
        "random_state":      RANDOM_STATE,
        "eval_metric":       "auc",
        "use_label_encoder": False,
        "verbosity":         0,
    }
    model = XGBClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    probs = model.predict_proba(X_val)[:, 1]
    return roc_auc_score(y_val, probs)


def rf_objective(trial):
    params = {
        "n_estimators":       trial.suggest_int("n_estimators", 200, 500),
        "max_depth":          trial.suggest_int("max_depth", 8, 30),
        "min_samples_split":  trial.suggest_int("min_samples_split", 2, 20),
        "min_samples_leaf":   trial.suggest_int("min_samples_leaf", 1, 10),
        "max_features":       trial.suggest_categorical("max_features", ["sqrt", "log2", 0.5]),
        "class_weight":       "balanced",
        "random_state":       RANDOM_STATE,
        "n_jobs":             -1,
    }
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    probs = model.predict_proba(X_val)[:, 1]
    return roc_auc_score(y_val, probs)


# ══════════════════════════════════════════════════════════════════════
# SECTION 2 ── THRESHOLD OPTIMISATION
# ══════════════════════════════════════════════════════════════════════

def find_best_threshold(model, X_val: pd.DataFrame, y_val: pd.Series) -> float:
    """
    Sweep thresholds 0.1–0.9; pick the one maximising F1 on val set.
    High recall preferred for fraud/spoofing (catch more, alert later).
    """
    probs = model.predict_proba(X_val)[:, 1]
    best_t, best_f1 = 0.5, 0.0
    for t in np.arange(0.10, 0.91, 0.02):
        preds = (probs >= t).astype(int)
        if preds.sum() == 0:
            continue
        f1 = f1_score(y_val, preds, zero_division=0)
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return float(round(best_t, 2))


# ══════════════════════════════════════════════════════════════════════
# SECTION 3 ── STACKING ENSEMBLE
# ══════════════════════════════════════════════════════════════════════

def build_stacking_model(xgb_params: dict, rf_params: dict) -> StackingClassifier:
    xgb = XGBClassifier(**xgb_params)
    rf  = RandomForestClassifier(**rf_params)
    meta = LogisticRegression(C=1.0, max_iter=1000, random_state=RANDOM_STATE)

    stack = StackingClassifier(
        estimators=[("xgb", xgb), ("rf", rf)],
        final_estimator=meta,
        cv=CV_FOLDS,
        passthrough=False,
        n_jobs=-1,
    )
    return stack


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  GPS Spoofing Detection — Model Training")
    print("=" * 65)

    N_TRIALS = 50

    # ── Tune XGBoost ──────────────────────────────────────────────────
    print(f"\n[OPTUNA] Tuning XGBoost ({N_TRIALS} trials)...")
    xgb_study = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    xgb_study.optimize(xgb_objective, n_trials=N_TRIALS, show_progress_bar=False)
    best_xgb_params = {**xgb_study.best_params,
                       "random_state": RANDOM_STATE,
                       "eval_metric": "auc",
                       "use_label_encoder": False,
                       "verbosity": 0}
    print(f"         Best XGB ROC-AUC (val): {xgb_study.best_value:.4f}")

    # ── Tune Random Forest ────────────────────────────────────────────
    print(f"\n[OPTUNA] Tuning Random Forest ({N_TRIALS} trials)...")
    rf_study = optuna.create_study(direction="maximize",
                                   sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE + 1))
    rf_study.optimize(rf_objective, n_trials=N_TRIALS, show_progress_bar=False)
    best_rf_params = {**rf_study.best_params,
                      "class_weight": "balanced",
                      "random_state": RANDOM_STATE,
                      "n_jobs": -1}
    print(f"         Best RF  ROC-AUC (val): {rf_study.best_value:.4f}")

    # ── Build + train stacking model ──────────────────────────────────
    print("\n[TRAIN] Building StackingClassifier (XGB + RF -> LR)...")
    stacking_model = build_stacking_model(best_xgb_params, best_rf_params)
    stacking_model.fit(X_train, y_train)
    print("        Stacking model trained.")

    # ── Threshold optimisation ────────────────────────────────────────
    best_threshold = find_best_threshold(stacking_model, X_val, y_val)
    print(f"\n[THRESHOLD] Optimal threshold: {best_threshold}")

    # ── Val metrics ───────────────────────────────────────────────────
    val_probs = stacking_model.predict_proba(X_val)[:, 1]
    val_preds = (val_probs >= best_threshold).astype(int)
    print("\n[VAL METRICS]")
    print(f"  ROC-AUC  : {roc_auc_score(y_val, val_probs):.4f}")
    print(f"  PR-AUC   : {average_precision_score(y_val, val_probs):.4f}")
    print(f"  F1 Score : {f1_score(y_val, val_preds):.4f}")
    print(f"  Precision: {precision_score(y_val, val_preds):.4f}")
    print(f"  Recall   : {recall_score(y_val, val_preds):.4f}")

    # ── Save model ────────────────────────────────────────────────────
    artifact = {
        "model":          stacking_model,
        "threshold":      best_threshold,
        "feature_cols":   FEATURE_COLS,
        "best_xgb_params": best_xgb_params,
        "best_rf_params":  best_rf_params,
    }
    joblib.dump(artifact, GPS_MODEL_PATH)
    print(f"\n[SAVED] GPS spoof model -> {GPS_MODEL_PATH}")
    print("\n[DONE] GPS Spoofing model training complete.\n")