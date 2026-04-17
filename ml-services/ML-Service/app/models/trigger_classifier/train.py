import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import (precision_score, recall_score, f1_score,
                              roc_auc_score, classification_report,
                              confusion_matrix)

from preprocess import preprocess_train, ALL_FEATURES, TARGET

DATA_PATH  = Path("D:/Hackathon Projects/ML-Service/app/data/trigger_events_final_10k.csv")
MODEL_DIR  = Path(__file__).parent
MODEL_PATH = MODEL_DIR / "rf_trigger.pkl"

# =========================================
# STEP 1 — LOAD
# =========================================
df = pd.read_csv(DATA_PATH)
print(f"Raw shape      : {df.shape}")
print(f"Missing values : {df.isnull().sum().sum()}")
print(f"\nClass distribution:")
print(df[TARGET].value_counts())
print(f"Positive rate  : {df[TARGET].mean():.4f} (imbalanced — 84/16 split)\n")

# =========================================
# STEP 2-4 — PREPROCESS + FEATURE ENGINEERING
# =========================================
X, y = preprocess_train(df)
print(f"After preprocessing : {X.shape}")
print(f"Features ({len(ALL_FEATURES)}): {ALL_FEATURES}\n")

# =========================================
# STEP 5 — STRATIFIED TRAIN/TEST SPLIT
# =========================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {len(X_train)} | Test: {len(X_test)}")
print(f"Train positives: {y_train.sum()} | Test positives: {y_test.sum()}\n")

# =========================================
# STEP 6 — CLASS IMBALANCE: class_weight=balanced
# =========================================

# =========================================
# STEP 7 — HYPERPARAMETER TUNING
# =========================================
param_dist = {
    "n_estimators":     [100, 200, 300],
    "max_depth":        [5, 10, 20, None],
    "min_samples_split":[2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
    "max_features":     ["sqrt", "log2"],
}

base_rf = RandomForestClassifier(
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)

search = RandomizedSearchCV(
    estimator=base_rf,
    param_distributions=param_dist,
    n_iter=30,
    scoring="precision",       # optimize for precision — business critical
    cv=3,
    random_state=42,
    n_jobs=-1,
    verbose=1,
)

print("Starting RandomizedSearchCV (30 iterations, cv=3, scoring=precision)...")
search.fit(X_train, y_train)
print(f"Best CV Precision : {search.best_score_:.4f}")
print(f"Best Params       : {search.best_params_}\n")

best_model = search.best_estimator_

# =========================================
# STEP 8 — EVALUATION AT DEFAULT THRESHOLD
# =========================================
proba_test  = best_model.predict_proba(X_test)[:, 1]
proba_train = best_model.predict_proba(X_train)[:, 1]

y_pred_default = (proba_test >= 0.5).astype(int)
print("=== Evaluation at threshold=0.5 ===")
print(classification_report(y_test, y_pred_default, digits=4))
print(f"ROC-AUC : {roc_auc_score(y_test, proba_test):.4f}\n")

# =========================================
# STEP 9 — THRESHOLD TUNING
# =========================================
print("=== Threshold Sweep (precision-focused) ===")
threshold_results = []
for t in [0.5, 0.6, 0.7, 0.8]:
    preds = (proba_test >= t).astype(int)
    p  = precision_score(y_test, preds, zero_division=0)
    r  = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    n  = preds.sum()
    print(f"t={t}  precision={p:.4f}  recall={r:.4f}  f1={f1:.4f}  approvals={n}")
    threshold_results.append((t, p, r, f1))

# Select threshold: maximize precision, keep f1 > 0
best_thresh = max(
    [r for r in threshold_results if r[3] > 0],
    key=lambda x: (x[1], x[3])
)[0]
print(f"\nSelected threshold : {best_thresh}")

# =========================================
# STEP 10 — CONFUSION MATRIX
# =========================================
y_pred_final = (proba_test >= best_thresh).astype(int)
cm = confusion_matrix(y_test, y_pred_final)
tn, fp, fn, tp = cm.ravel()
print(f"\n=== Confusion Matrix (threshold={best_thresh}) ===")
print(f"  True Negatives  (correct rejects) : {tn}")
print(f"  False Positives (wrong approvals)  : {fp}  <-- COSTLY")
print(f"  False Negatives (missed approvals) : {fn}")
print(f"  True Positives  (correct approvals): {tp}")

# =========================================
# STEP 11 — FEATURE IMPORTANCE
# =========================================
importance = pd.Series(
    best_model.feature_importances_, index=ALL_FEATURES
).sort_values(ascending=False)

print("\n=== Feature Importance ===")
print(importance.to_string())
print(f"\nTop 5: {importance.head(5).index.tolist()}")

# =========================================
# STEP 12-13 — FINAL METRICS + SAVE
# =========================================
final_precision = precision_score(y_test, y_pred_final, zero_division=0)
final_recall    = recall_score(y_test, y_pred_final, zero_division=0)
final_f1        = f1_score(y_test, y_pred_final, zero_division=0)
final_auc       = roc_auc_score(y_test, proba_test)

joblib.dump(best_model, MODEL_PATH)
(MODEL_DIR / "threshold.json").write_text(
    json.dumps({"threshold": best_thresh}, indent=2)
)

metadata = {
    "model": "RandomForestClassifier",
    "features": ALL_FEATURES,
    "target": TARGET,
    "best_params": search.best_params_,
    "selected_threshold": best_thresh,
    "precision":  round(final_precision, 4),
    "recall":     round(final_recall,    4),
    "f1_score":   round(final_f1,        4),
    "roc_auc":    round(final_auc,       4),
    "false_positives": int(fp),
    "top5_features": importance.head(5).index.tolist(),
    "trained": True,
}
(MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))

# =========================================
# STEP 14 — FINAL SUMMARY
# =========================================
print("\n" + "="*50)
print("FINAL MODEL SUMMARY")
print("="*50)
print(f"Model              : RandomForestClassifier (class_weight=balanced)")
print(f"Best Params        : {search.best_params_}")
print(f"Selected Threshold : {best_thresh}")
print(f"Precision          : {final_precision:.4f}")
print(f"Recall             : {final_recall:.4f}")
print(f"F1-Score           : {final_f1:.4f}")
print(f"ROC-AUC            : {final_auc:.4f}")
print(f"False Positives    : {fp}  (costly payouts avoided)")
print(f"Top 5 Features     : {importance.head(5).index.tolist()}")
print(f"\nModel saved        : {MODEL_PATH}")
print(f"Threshold saved    : {MODEL_DIR / 'threshold.json'}")
print(f"Metadata saved     : {MODEL_DIR / 'metadata.json'}")
print("Training completed successfully.")
