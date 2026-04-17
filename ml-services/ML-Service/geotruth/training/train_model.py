"""
GeoTruth — Inertial Layer XGBoost Model Trainer
=================================================
Reads training_data.csv, trains an XGBClassifier,
evaluates it, and saves the model as JSON for production inference.

GPU UTILIZATION (RTX 4050 — 6GB VRAM)
---------------------------------------
XGBoost uses your GPU with tree_method="hist" + device="cuda".
For 10k rows it finishes in seconds. For 1M+ rows it will be ~10x
faster than CPU. The JSON export is device-agnostic — inference
in production runs on CPU (no GPU required on the server).

HOW TO RUN
----------
  cd geotruth/
  python -m geotruth.training.train_model

OUTPUT
------
  geotruth/models/xgb_inertial_v1.json   — model weights (production)
  geotruth/models/training_report.txt    — accuracy, classification report
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split

# ── Paths ──────────────────────────────────────────────────────────────────────
MODELS_DIR   = Path(__file__).parent.parent / "models"
DATA_PATH    = MODELS_DIR / "training_data.csv"
MODEL_PATH   = MODELS_DIR / "xgb_inertial_v1.json"
REPORT_PATH  = MODELS_DIR / "training_report.txt"

# ── Feature columns used for training ─────────────────────────────────────────
FEATURE_COLS = [
    "variance_1h_to_30m_ago",
    "variance_last_30m",
    "variance_delta",
    "motion_ratio",
    "sudden_stillness",
    "prolonged_static",
    "reverse_delta",
]
LABEL_COL = "is_genuine"


def load_data() -> tuple[pd.DataFrame, pd.Series]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found at {DATA_PATH}\n"
            f"Run generate_dataset.py first:\n"
            f"  python -m geotruth.training.generate_dataset"
        )
    df = pd.read_csv(DATA_PATH)
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}")
    X = df[FEATURE_COLS]
    y = df[LABEL_COL]
    print(f"Loaded {len(df):,} samples | Features: {len(FEATURE_COLS)}")
    print(f"Class balance — Genuine: {y.sum():,} | Fraud: {(y==0).sum():,}")
    return X, y


def detect_gpu() -> dict:
    """
    Attempt to use RTX 4050 GPU. Falls back to CPU gracefully.
    XGBoost requires CUDA toolkit installed alongside the GPU drivers.
    If you get a CUDA error, install: pip install xgboost[gpu]
    """
    try:
        test_model = xgb.XGBClassifier(
            n_estimators=2,
            tree_method="hist",
            device="cuda",
            verbosity=0
        )
        test_X = np.random.rand(100, 2)
        test_y = np.random.randint(0, 2, 100)
        test_model.fit(test_X, test_y)
        print("RTX 4050 GPU detected — training with CUDA acceleration")
        return {"tree_method": "hist", "device": "cuda"}
    except Exception as e:
        print(f"GPU not available ({type(e).__name__}) — falling back to CPU")
        return {"tree_method": "hist", "device": "cpu"}


def build_model(gpu_params: dict) -> xgb.XGBClassifier:
    """
    XGBoost hyperparameters tuned for this specific fraud detection task.

    Key decisions:
    - n_estimators=300: Enough trees for the 5-archetype pattern space
    - max_depth=5: Prevents memorizing synthetic noise, good generalization
    - learning_rate=0.05: Lower LR + more trees = better than high LR + few trees
    - scale_pos_weight: Handles class imbalance (60% fraud, 40% genuine)
      Value = count(fraud) / count(genuine) ≈ 1.5
    - eval_metric="auc": AUC is the right metric for fraud detection —
      accuracy alone is misleading with imbalanced classes
    - early_stopping_rounds=30: Stops if val AUC doesn't improve for 30 rounds
    """
    return xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=1.5,       # Accounts for 60/40 fraud/genuine split
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        eval_metric="auc",
        early_stopping_rounds=30,
        random_state=42,
        verbosity=1,
        **gpu_params
    )


def cross_validate(X: pd.DataFrame, y: pd.Series, gpu_params: dict) -> float:
    """
    5-fold stratified cross-validation before final training.
    Stratified ensures each fold has the same genuine/fraud ratio.
    Returns mean AUC across folds.
    """
    print("\n--- 5-Fold Cross-Validation ---")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    auc_scores = []

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = build_model(gpu_params)
        model.fit(
            X_tr, y_tr,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        preds = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, preds)
        auc_scores.append(auc)
        print(f"  Fold {fold}: AUC = {auc:.4f}")

    mean_auc = np.mean(auc_scores)
    print(f"  Mean AUC: {mean_auc:.4f} ± {np.std(auc_scores):.4f}")
    return mean_auc


def train_final_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    gpu_params: dict
) -> xgb.XGBClassifier:
    """Train final model on full train split with validation for early stopping."""
    print("\n--- Training Final Model ---")
    model = build_model(gpu_params)
    t0 = time.time()
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=50
    )
    elapsed = time.time() - t0
    print(f"Training complete in {elapsed:.1f}s | Best iteration: {model.best_iteration}")
    return model


def evaluate(model: xgb.XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Full evaluation suite — accuracy, AUC, confusion matrix, per-class metrics."""
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    auc      = roc_auc_score(y_test, y_proba)
    cm       = confusion_matrix(y_test, y_pred)
    report   = classification_report(
        y_test, y_pred,
        target_names=["Fraud (0)", "Genuine (1)"]
    )

    print(f"\n--- Test Set Evaluation ---")
    print(f"Accuracy : {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"ROC-AUC  : {auc:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"  TN={cm[0,0]}  FP={cm[0,1]}")
    print(f"  FN={cm[1,0]}  TP={cm[1,1]}")
    print(f"\n  False Positive Rate (genuine flagged as fraud): {cm[0,1]/(cm[0,0]+cm[0,1]):.3f}")
    print(f"  False Negative Rate (fraud approved as genuine): {cm[1,0]/(cm[1,0]+cm[1,1]):.3f}")
    print(f"\nClassification Report:\n{report}")

    return {
        "accuracy": round(accuracy, 4),
        "roc_auc": round(auc, 4),
        "confusion_matrix": cm.tolist(),
        "false_positive_rate": round(cm[0,1]/(cm[0,0]+cm[0,1]), 4),
        "false_negative_rate": round(cm[1,0]/(cm[1,0]+cm[1,1]), 4),
    }


def print_feature_importance(model: xgb.XGBClassifier) -> None:
    importance = model.get_booster().get_score(importance_type="gain")
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print("\n--- Feature Importance (gain) ---")
    for feat, score in sorted_imp:
        bar = "█" * int(score / max(v for _, v in sorted_imp) * 20)
        print(f"  {feat:<30} {bar} {score:.1f}")


def save_report(metrics: dict, cv_auc: float) -> None:
    report_lines = [
        "GeoTruth — Inertial Layer XGBoost Training Report",
        "=" * 50,
        f"CV Mean AUC (5-fold):     {cv_auc:.4f}",
        f"Test Accuracy:            {metrics['accuracy']:.4f}",
        f"Test ROC-AUC:             {metrics['roc_auc']:.4f}",
        f"False Positive Rate:      {metrics['false_positive_rate']:.4f}",
        f"  (honest workers wrongly flagged)",
        f"False Negative Rate:      {metrics['false_negative_rate']:.4f}",
        f"  (fraud wrongly approved)",
        "",
        "Confusion Matrix:",
        f"  TN={metrics['confusion_matrix'][0][0]}  FP={metrics['confusion_matrix'][0][1]}",
        f"  FN={metrics['confusion_matrix'][1][0]}  TP={metrics['confusion_matrix'][1][1]}",
        "",
        f"Feature columns: {FEATURE_COLS}",
        f"Model path: {MODEL_PATH}",
    ]
    REPORT_PATH.write_text("\n".join(report_lines))
    print(f"\nReport saved to: {REPORT_PATH}")


def main():
    print("=" * 55)
    print("GeoTruth — XGBoost Inertial Layer Training Pipeline")
    print("=" * 55)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    X, y = load_data()

    # 2. Detect GPU
    gpu_params = detect_gpu()

    # 3. Split: 70% train, 15% val (early stopping), 15% test (final eval)
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval, y_trainval, test_size=0.176, random_state=42, stratify=y_trainval
    )
    print(f"\nSplit — Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")

    # 4. Cross-validate
    cv_auc = cross_validate(X, y, gpu_params)

    # 5. Train final model
    model = train_final_model(X_train, y_train, X_val, y_val, gpu_params)

    # 6. Evaluate on held-out test set
    metrics = evaluate(model, X_test, y_test)

    # 7. Feature importance
    print_feature_importance(model)

    # 8. Save model as JSON (device-agnostic — inference runs on CPU)
    model.get_booster().save_model(str(MODEL_PATH))
    print(f"\nModel saved to: {MODEL_PATH}")

    # 9. Save metadata alongside model for the inference layer
    metadata = {
        "feature_cols": FEATURE_COLS,
        "label_col": LABEL_COL,
        "model_version": "xgb_inertial_v1",
        "trained_on_samples": int(len(X)),
        "test_accuracy": metrics["accuracy"],
        "test_roc_auc": metrics["roc_auc"],
        "false_positive_rate": metrics["false_positive_rate"],
        "false_negative_rate": metrics["false_negative_rate"],
        "genuine_threshold": 0.7,
        "note": "probability >= 0.7 = genuine, < 0.7 = suspicious"
    }
    meta_path = MODELS_DIR / "xgb_inertial_v1_meta.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    print(f"Metadata saved to: {meta_path}")

    # 10. Save training report
    save_report(metrics, cv_auc)

    print("\n" + "=" * 55)
    print(f"PIPELINE COMPLETE")
    print(f"Accuracy: {metrics['accuracy']*100:.2f}% | AUC: {metrics['roc_auc']:.4f}")
    print(f"Ready for inference in geotruth/layers/inertial.py")
    print("=" * 55)


if __name__ == "__main__":
    main()
    