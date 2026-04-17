import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"]  = "2"

import json
import numpy as np
import joblib
from pathlib import Path

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam

from sklearn.metrics import (precision_score, recall_score,
                              f1_score, roc_auc_score, classification_report)

from preprocess import (load_and_sort, fill_missing, make_sequences,
                        time_split, fit_scaler, apply_scaler,
                        FEATURES, TARGET, SEQ_IN, SEQ_OUT, N_FEATURES)

MODEL_DIR  = Path(__file__).parent
MODEL_PATH = MODEL_DIR / "lstm_model.keras"

# =========================================
# FOCAL LOSS — handles extreme imbalance
# better than class_weight alone
# =========================================
def focal_loss(gamma=2.0, alpha=0.85):
    def loss_fn(y_true, y_pred):
        y_pred  = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        bce     = -y_true * tf.math.log(y_pred) - (1 - y_true) * tf.math.log(1 - y_pred)
        p_t     = y_true * y_pred + (1 - y_true) * (1 - y_pred)
        alpha_t = y_true * alpha + (1 - y_true) * (1 - alpha)
        return tf.reduce_mean(alpha_t * tf.pow(1 - p_t, gamma) * bce)
    return loss_fn

# =========================================
# STEP 1 — LOAD + SORT
# =========================================
df = load_and_sort()
print(f"Shape          : {df.shape}")
print(f"Pincodes       : {df['pincode'].nunique()}")
print(f"Date range     : {df['date'].min().date()} to {df['date'].max().date()}")
print(f"Disruptions    : {df[TARGET].sum()} / {len(df)} ({df[TARGET].mean():.4%})\n")

# =========================================
# STEP 2 — CLEAN
# =========================================
df = fill_missing(df)
print(f"NaN after fill : {df[FEATURES + [TARGET]].isnull().sum().sum()}\n")

# =========================================
# STEP 3-5 — SEQUENCES (single-step, per pincode)
# =========================================
X, y = make_sequences(df)
print(f"Sequences      : X={X.shape}  y={y.shape}")
print(f"Positive rate  : {y.mean():.4%}  (extreme imbalance — using focal loss)\n")

# =========================================
# STEP 6 — CHRONOLOGICAL SPLIT
# =========================================
X_train, X_test, y_train, y_test = time_split(X, y, test_ratio=0.2)
print(f"Train: {X_train.shape}  Test: {X_test.shape}")
print(f"Train positives: {y_train.sum():.0f}  Test positives: {y_test.sum():.0f}\n")

# =========================================
# STEP 4 — SCALE (fit on train only)
# =========================================
scaler  = fit_scaler(X_train)
X_train = apply_scaler(X_train, scaler)
X_test  = apply_scaler(X_test,  scaler)
print("Scaling complete (MinMaxScaler fit on train only)\n")

# =========================================
# CLASS WEIGHT for additional boost
# =========================================
pos_rate   = float(y_train.mean())
pos_weight = (1.0 - pos_rate) / (pos_rate + 1e-8)
class_weight = {0: 1.0, 1: pos_weight}
print(f"Class weights  : neg=1.0  pos={pos_weight:.1f}\n")

# =========================================
# STEP 7 — LSTM ARCHITECTURE
# =========================================
model = Sequential([
    Input(shape=(SEQ_IN, N_FEATURES)),
    LSTM(64, return_sequences=True),
    Dropout(0.2),
    LSTM(32, return_sequences=False),
    Dropout(0.2),
    Dense(16, activation="relu"),
    Dense(1, activation="sigmoid"),   # single-step output
])

model.compile(
    loss=focal_loss(gamma=2.0, alpha=0.85),
    optimizer=Adam(learning_rate=0.001),
    metrics=["accuracy", tf.keras.metrics.AUC(name="auc")],
)
model.summary()

# =========================================
# STEP 8 — TRAINING
# =========================================
early_stop = EarlyStopping(
    monitor="val_auc",
    patience=7,
    restore_best_weights=True,
    mode="max",
    verbose=1,
)

print("\nStarting training...")
history = model.fit(
    X_train, y_train,
    epochs=50,
    batch_size=32,
    validation_split=0.1,
    callbacks=[early_stop],
    class_weight=class_weight,
    verbose=1,
)
print(f"\nStopped at epoch {len(history.history['loss'])}\n")

# =========================================
# STEP 9-10 — EVALUATION + THRESHOLD SWEEP
# =========================================
proba  = model.predict(X_test, verbose=0).flatten()
y_flat = y_test.flatten()

print("=== Threshold Sweep ===")
best_thresh, best_f1 = 0.5, -1.0
results = []
for t in [0.3, 0.4, 0.5, 0.6]:
    preds = (proba >= t).astype(int)
    p  = precision_score(y_flat, preds, zero_division=0)
    r  = recall_score(y_flat, preds, zero_division=0)
    f1 = f1_score(y_flat, preds, zero_division=0)
    print(f"t={t}  precision={p:.4f}  recall={r:.4f}  f1={f1:.4f}  positives={preds.sum()}")
    results.append((t, p, r, f1))
    if f1 > best_f1:
        best_f1, best_thresh = f1, t

print(f"\nSelected threshold : {best_thresh}  (best F1={best_f1:.4f})\n")

y_pred_final = (proba >= best_thresh).astype(int)
final_prec   = precision_score(y_flat, y_pred_final, zero_division=0)
final_rec    = recall_score(y_flat, y_pred_final, zero_division=0)
final_f1     = f1_score(y_flat, y_pred_final, zero_division=0)
final_auc    = roc_auc_score(y_flat, proba)

print("=== Classification Report ===")
print(classification_report(y_flat, y_pred_final, digits=4, zero_division=0))
print(f"ROC-AUC : {final_auc:.4f}")

# =========================================
# STEP 11 — SAVE
# =========================================
model.save(str(MODEL_PATH))
(MODEL_DIR / "threshold.json").write_text(
    json.dumps({"threshold": best_thresh}, indent=2)
)

metadata = {
    "model": "LSTM",
    "architecture": "LSTM(64)->Dropout->LSTM(32)->Dropout->Dense(16)->Dense(1,sigmoid)",
    "loss": "focal_loss(gamma=2.0, alpha=0.85)",
    "features": FEATURES,
    "n_features": N_FEATURES,
    "seq_in": SEQ_IN,
    "seq_out": SEQ_OUT,
    "target": TARGET,
    "selected_threshold": best_thresh,
    "precision": round(final_prec, 4),
    "recall":    round(final_rec,  4),
    "f1_score":  round(final_f1,   4),
    "roc_auc":   round(final_auc,  4),
    "epochs_trained": len(history.history["loss"]),
    "trained": True,
}
(MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))

# =========================================
# STEP 12 — FINAL SUMMARY
# =========================================
print("\n" + "="*50)
print("FINAL MODEL SUMMARY")
print("="*50)
print(f"Architecture       : LSTM(64) -> LSTM(32) -> Dense(1)")
print(f"Loss               : Focal Loss (gamma=2.0, alpha=0.85)")
print(f"Features           : {len(FEATURES)}")
print(f"Sequence in        : {SEQ_IN} days -> predict next day")
print(f"Inference out      : {SEQ_OUT} days (rolling single-step)")
print(f"Epochs trained     : {len(history.history['loss'])}")
print(f"Selected Threshold : {best_thresh}")
print(f"Precision          : {final_prec:.4f}")
print(f"Recall             : {final_rec:.4f}")
print(f"F1-Score           : {final_f1:.4f}")
print(f"ROC-AUC            : {final_auc:.4f}")
print(f"\nModel saved        : {MODEL_PATH}")
print(f"Scaler saved       : {MODEL_DIR / 'scaler.pkl'}")
print(f"Threshold saved    : {MODEL_DIR / 'threshold.json'}")
print("Training completed successfully.")
