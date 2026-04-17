"""
GigKavach Curfew NLP — Model Training
══════════════════════════════════════════════════════════════
Architecture:
  Base models (3):
    1. Logistic Regression  (TF-IDF → linear baseline, strong for text)
    2. LinearSVC            (fast, high-dimensional sparse input)
    3. XGBoost              (tree-based, captures keyword interactions)

  Ensemble:
    • Soft voting ensemble of LR + SVC (calibrated) + XGB
    • Optuna tunes LR (C), SVC (C), XGB params independently
    • Final model = VotingClassifier with tuned weights

  Output: curfew_full_pipeline.pkl
    Contains: vectorizer + ensemble model + threshold map
══════════════════════════════════════════════════════════════
"""

import os, sys, warnings
import numpy as np
import pandas as pd
import joblib
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore")

from scipy.sparse import load_npz
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import (
    classification_report, f1_score,
    roc_auc_score, accuracy_score,
    confusion_matrix, average_precision_score,
)
from sklearn.preprocessing import label_binarize
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    DATA_PROC, MODEL_DIR, PLOTS_DIR, TFIDF_PATH,
    MODEL_PATH, PIPELINE_PATH, RANDOM_STATE,
)
from utils import get_logger

logger = get_logger("train")
np.random.seed(RANDOM_STATE)

# ── Load preprocessed data ────────────────────────────────────────────
logger.info("[LOAD] Loading preprocessed sparse matrices...")
X_train = load_npz(os.path.join(DATA_PROC, "X_train.npz"))
X_val   = load_npz(os.path.join(DATA_PROC, "X_val.npz"))
X_test  = load_npz(os.path.join(DATA_PROC, "X_test.npz"))

splits      = joblib.load(os.path.join(MODEL_DIR, "splits.pkl"))
y_train     = splits["y_train"].values
y_val       = splits["y_val"].values
y_test      = splits["y_test"].values
class_wt    = splits["class_weight"]
label_names = splits["label_names"]   # {0: "normal", 1: "curfew", 2: "strike"}

logger.info(f"[LOAD] Train: {X_train.shape}  Val: {X_val.shape}  Test: {X_test.shape}")
logger.info(f"       Class weights: {class_wt}")


# ══════════════════════════════════════════════════════════════════════
# OPTUNA OBJECTIVE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def lr_objective(trial):
    C       = trial.suggest_float("C", 0.01, 20.0, log=True)
    solver  = trial.suggest_categorical("solver", ["lbfgs", "saga"])
    model = LogisticRegression(
        C=C, solver=solver,
        max_iter=2000,
        class_weight=class_wt,
        
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_val)
    return f1_score(y_val, preds, average="macro")


def svc_objective(trial):
    C = trial.suggest_float("C", 0.01, 20.0, log=True)
    svc = LinearSVC(
        C=C, max_iter=5000,
        class_weight=class_wt,
        random_state=RANDOM_STATE,
    )
    # Calibrate for probability output
    cal_svc = CalibratedClassifierCV(svc, method="sigmoid", cv=3)
    cal_svc.fit(X_train, y_train)
    preds = cal_svc.predict(X_val)
    return f1_score(y_val, preds, average="macro")


def xgb_objective(trial):
    n_classes = 3
    params = {
        "n_estimators":     trial.suggest_int("n_estimators", 200, 500),
        "max_depth":        trial.suggest_int("max_depth", 3, 8),
        "learning_rate":    trial.suggest_float("lr", 0.02, 0.15, log=True),
        "subsample":        trial.suggest_float("ss", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("cb", 0.5, 1.0),
        "reg_alpha":        trial.suggest_float("ra", 1e-8, 1.0, log=True),
        "reg_lambda":       trial.suggest_float("rl", 1e-8, 1.0, log=True),
        "min_child_weight": trial.suggest_int("mcw", 1, 10),
        "objective":        "multi:softprob",
        "num_class":        n_classes,
        "eval_metric":      "mlogloss",
        "verbosity":        0,
        "random_state":     RANDOM_STATE,
        "n_jobs":           -1,
    }
    # Handle class weights via sample_weight
    sample_weight = np.array([class_wt[y] for y in y_train])
    model = XGBClassifier(**params)
    model.fit(X_train, y_train, sample_weight=sample_weight,
              eval_set=[(X_val, y_val)], verbose=False)
    preds = model.predict(X_val)
    return f1_score(y_val, preds, average="macro")


# ══════════════════════════════════════════════════════════════════════
# VOTING WEIGHT SEARCH
# ══════════════════════════════════════════════════════════════════════

def search_voting_weights(lr_model, svc_model, xgb_model) -> tuple[float, float, float]:
    """
    Grid search over weights [0.5..2.0] step 0.5 for the 3 models.
    Maximises macro F1 on validation set.
    """
    lr_probs  = lr_model.predict_proba(X_val)
    svc_probs = svc_model.predict_proba(X_val)
    xgb_probs = xgb_model.predict_proba(X_val)

    best_f1 = 0; best_w = (1.0, 1.0, 1.0)
    for w_lr in np.arange(0.5, 2.5, 0.5):
        for w_svc in np.arange(0.5, 2.5, 0.5):
            for w_xgb in np.arange(0.5, 2.5, 0.5):
                combined = (w_lr * lr_probs + w_svc * svc_probs + w_xgb * xgb_probs) / (w_lr + w_svc + w_xgb)
                preds = np.argmax(combined, axis=1)
                f1 = f1_score(y_val, preds, average="macro")
                if f1 > best_f1:
                    best_f1 = f1; best_w = (w_lr, w_svc, w_xgb)
    logger.info(f"[WEIGHTS] Best voting weights: LR={best_w[0]} SVC={best_w[1]} XGB={best_w[2]}  F1={best_f1:.4f}")
    return best_w


# ══════════════════════════════════════════════════════════════════════
# EVALUATION HELPERS
# ══════════════════════════════════════════════════════════════════════

def print_report(y_true, y_pred, proba, split_name: str):
    names = [label_names[i] for i in sorted(label_names)]
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    acc       = accuracy_score(y_true, y_pred)

    logger.info(f"\n{'═'*55}")
    logger.info(f"  {split_name}")
    logger.info(f"{'═'*55}")
    logger.info(f"  Accuracy  : {acc:.4f}")
    logger.info(f"  Macro F1  : {macro_f1:.4f}")

    # ROC-AUC (one-vs-rest)
    try:
        y_bin = label_binarize(y_true, classes=[0, 1, 2])
        auc   = roc_auc_score(y_bin, proba, multi_class="ovr", average="macro")
        logger.info(f"  ROC-AUC   : {auc:.4f}  (macro OvR)")
    except Exception:
        pass

    logger.info(f"\n{classification_report(y_true, y_pred, target_names=names)}")

    cm = confusion_matrix(y_true, y_pred)
    logger.info("  Confusion matrix (rows=actual, cols=predicted):")
    header = "          " + "  ".join(f"{n[:6]:>6}" for n in names)
    logger.info(header)
    for i, row in enumerate(cm):
        row_str = "  ".join(f"{v:>6}" for v in row)
        logger.info(f"  {names[i][:8]:<8}  {row_str}")

    return macro_f1


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("=" * 65)
    logger.info("  GigKavach Curfew NLP — Model Training")
    logger.info("=" * 65)

    N_TRIALS = 40

    # ── Tune Logistic Regression ──────────────────────────────────────
    logger.info(f"\n[OPTUNA] Tuning Logistic Regression ({N_TRIALS} trials)...")
    lr_study = optuna.create_study(direction="maximize",
                                   sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    lr_study.optimize(lr_objective, n_trials=N_TRIALS, show_progress_bar=False)
    logger.info(f"         Best LR macro-F1 (val): {lr_study.best_value:.4f}")
    best_lr_p = lr_study.best_params

    # ── Tune LinearSVC ────────────────────────────────────────────────
    logger.info(f"\n[OPTUNA] Tuning LinearSVC ({N_TRIALS} trials)...")
    svc_study = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE+1))
    svc_study.optimize(svc_objective, n_trials=N_TRIALS, show_progress_bar=False)
    logger.info(f"         Best SVC macro-F1 (val): {svc_study.best_value:.4f}")
    best_svc_c = svc_study.best_params["C"]

    # ── Tune XGBoost ──────────────────────────────────────────────────
    logger.info(f"\n[OPTUNA] Tuning XGBoost ({N_TRIALS} trials)...")
    xgb_study = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE+2))
    xgb_study.optimize(xgb_objective, n_trials=N_TRIALS, show_progress_bar=False)
    logger.info(f"         Best XGB macro-F1 (val): {xgb_study.best_value:.4f}")
    best_xgb_p = {
        k: v for k, v in xgb_study.best_params.items()
        if k not in ("lr","ss","cb","ra","rl","mcw")
    }
    # Remap trial param names back to XGB param names
    p = xgb_study.best_params
    best_xgb_params = {
        "n_estimators": p.get("n_estimators", 300),
        "max_depth":    p.get("max_depth", 5),
        "learning_rate": p.get("lr", 0.05),
        "subsample":    p.get("ss", 0.8),
        "colsample_bytree": p.get("cb", 0.8),
        "reg_alpha":    p.get("ra", 1e-4),
        "reg_lambda":   p.get("rl", 1e-4),
        "min_child_weight": p.get("mcw", 3),
        "objective":    "multi:softprob",
        "num_class":    3,
        "eval_metric":  "mlogloss",
        "verbosity":    0,
        "random_state": RANDOM_STATE,
        "n_jobs":       -1,
    }

    # ── Train final models ────────────────────────────────────────────
    logger.info("\n[TRAIN] Fitting final Logistic Regression...")
    lr_final = LogisticRegression(
        C=best_lr_p["C"],
        solver=best_lr_p.get("solver", "lbfgs"),
        max_iter=3000,
        class_weight=class_wt,
        
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    lr_final.fit(X_train, y_train)

    logger.info("[TRAIN] Fitting final LinearSVC + Platt calibration...")
    svc_base = LinearSVC(
        C=best_svc_c, max_iter=8000,
        class_weight=class_wt,
        random_state=RANDOM_STATE,
    )
    svc_final = CalibratedClassifierCV(svc_base, method="sigmoid", cv=5)
    svc_final.fit(X_train, y_train)

    logger.info("[TRAIN] Fitting final XGBoost...")
    sample_weight = np.array([class_wt[y] for y in y_train])
    xgb_final = XGBClassifier(**best_xgb_params)
    xgb_final.fit(X_train, y_train, sample_weight=sample_weight,
                  eval_set=[(X_val, y_val)], verbose=False)

    # ── Find best voting weights on val ───────────────────────────────
    logger.info("\n[SEARCH] Optimising voting weights on validation set...")
    w_lr, w_svc, w_xgb = search_voting_weights(lr_final, svc_final, xgb_final)

    # ── Ensemble predictions ──────────────────────────────────────────
    def ensemble_predict_proba(X):
        p1 = lr_final.predict_proba(X)
        p2 = svc_final.predict_proba(X)
        p3 = xgb_final.predict_proba(X)
        combined = (w_lr * p1 + w_svc * p2 + w_xgb * p3) / (w_lr + w_svc + w_xgb)
        return combined

    def ensemble_predict(X):
        return np.argmax(ensemble_predict_proba(X), axis=1)

    # ── Validation metrics ────────────────────────────────────────────
    val_preds  = ensemble_predict(X_val)
    val_proba  = ensemble_predict_proba(X_val)
    val_macro_f1 = print_report(y_val, val_preds, val_proba, "VALIDATION SET")

    # ── Individual model metrics for comparison ───────────────────────
    for name, model in [("LR", lr_final), ("SVC", svc_final), ("XGB", xgb_final)]:
        preds = model.predict(X_val)
        f1 = f1_score(y_val, preds, average="macro")
        acc = accuracy_score(y_val, preds)
        logger.info(f"  [{name}] Val macro-F1={f1:.4f}  Acc={acc:.4f}")

    # ── Test metrics ──────────────────────────────────────────────────
    test_preds = ensemble_predict(X_test)
    test_proba = ensemble_predict_proba(X_test)
    test_macro_f1 = print_report(y_test, test_preds, test_proba, "TEST SET (FINAL)")

    # ── Save model artifact ───────────────────────────────────────────
    vectorizer = joblib.load(TFIDF_PATH)

    pipeline_artifact = {
        "vectorizer":      vectorizer,
        "lr_model":        lr_final,
        "svc_model":       svc_final,
        "xgb_model":       xgb_final,
        "voting_weights":  (w_lr, w_svc, w_xgb),
        "label_names":     label_names,
        "class_weight":    class_wt,
        "val_macro_f1":    val_macro_f1,
        "test_macro_f1":   test_macro_f1,
        "best_lr_params":  best_lr_p,
        "best_svc_c":      best_svc_c,
        "best_xgb_params": best_xgb_params,
        # Inference helper info
        "n_kw_features":   15,
        "n_meta_features": 7,
    }
    joblib.dump(pipeline_artifact, PIPELINE_PATH)
    logger.info(f"\n[SAVED] Full pipeline → {PIPELINE_PATH}")

    logger.info("\n" + "═" * 65)
    logger.info("  TRAINING COMPLETE")
    logger.info(f"  Val  macro-F1 : {val_macro_f1:.4f}")
    logger.info(f"  Test macro-F1 : {test_macro_f1:.4f}")
    logger.info("═" * 65)