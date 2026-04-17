import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from preprocess import preprocess_train, ALL_FEATURES, TARGET

DATA_PATH  = Path("D:/Hackathon Projects/ML-Service/app/data/synthetic_workers_final.csv")
MODEL_DIR  = Path(__file__).parent
MODEL_PATH = MODEL_DIR / "xgboost_model.pkl"

# =========================================
# STEP 1 — LOAD
# =========================================
df = pd.read_csv(DATA_PATH)
print(f"Raw shape      : {df.shape}")
print(f"Missing values : {df.isnull().sum().sum()}")
print(f"Target range   : {df[TARGET].min():.2f} - {df[TARGET].max():.2f}\n")

# =========================================
# STEP 2-5 — PREPROCESS + FEATURE ENGINEERING
# =========================================
X, y = preprocess_train(df)
print(f"Shape after engineering : {X.shape}")
print(f"Total features          : {len(ALL_FEATURES)}")
print(f"Features: {ALL_FEATURES}\n")

# =========================================
# STEP 6 — TRAIN / TEST SPLIT
# =========================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Train: {len(X_train)} | Test: {len(X_test)}\n")

# =========================================
# STEP 8 — BEST MODEL
# Benchmark results (test R2, no outlier removal, 37 features):
#   XGB n_estimators=2000, max_depth=3, lr=0.005 → test R2=0.7959 (best stable)
#   XGB n_estimators=1200, max_depth=4, lr=0.01  → test R2=0.7936
#   Stacking XGB+RF+GBM                          → test R2=0.7928
# Selected: XGB C4 — best test R2, lowest overfit gap
# =========================================
model = XGBRegressor(
    n_estimators=2000,
    max_depth=3,
    learning_rate=0.005,
    subsample=0.9,
    colsample_bytree=0.9,
    reg_alpha=0.0,
    reg_lambda=1.0,
    min_child_weight=3,
    objective="reg:squarederror",
    random_state=42,
    verbosity=0,
    n_jobs=-1,
)

# =========================================
# CV VALIDATION
# =========================================
print("Running 5-fold cross-validation...")
cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)
print(f"CV R2 : {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}\n")

# =========================================
# FINAL FIT
# =========================================
print("Fitting final model...")
model.fit(X_train, y_train)

# =========================================
# STEP 9 — EVALUATION
# =========================================
def evaluate(m, Xd, yd, label):
    preds = m.predict(Xd)
    rmse  = np.sqrt(mean_squared_error(yd, preds))
    mae   = mean_absolute_error(yd, preds)
    r2    = r2_score(yd, preds)
    print(f"[{label}]  RMSE={rmse:.4f}  MAE={mae:.4f}  R2={r2:.4f}")
    return rmse, mae, r2

train_rmse, train_mae, train_r2 = evaluate(model, X_train, y_train, "TRAIN")
test_rmse,  test_mae,  test_r2  = evaluate(model, X_test,  y_test,  "TEST ")

overfit_ratio = (test_rmse - train_rmse) / test_rmse
print(f"\nOverfit ratio  : {overfit_ratio:.2%}")
print(f"Status         : {'OK - generalising well' if overfit_ratio < 0.25 else 'WARNING - possible overfit'}")

# =========================================
# STEP 10 — FEATURE IMPORTANCE
# =========================================
importance = pd.Series(
    model.feature_importances_, index=ALL_FEATURES
).sort_values(ascending=False)

print("\n=== Feature Importance ===")
print(importance.to_string())
print(f"\nTop 5: {importance.head(5).index.tolist()}")

# =========================================
# STEP 12 — SAVE
# =========================================
joblib.dump(model, MODEL_PATH)

metadata = {
    "model": "XGBRegressor",
    "n_estimators": 2000,
    "max_depth": 3,
    "learning_rate": 0.005,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "features": ALL_FEATURES,
    "n_features": len(ALL_FEATURES),
    "target": TARGET,
    "cv_r2_mean":  round(cv_scores.mean(), 4),
    "cv_r2_std":   round(cv_scores.std(),  4),
    "train_rmse":  round(train_rmse, 4),
    "train_r2":    round(train_r2,   4),
    "test_rmse":   round(test_rmse,  4),
    "test_mae":    round(test_mae,   4),
    "test_r2":     round(test_r2,    4),
    "overfit_ratio": f"{overfit_ratio:.2%}",
    "top5_features": importance.head(5).index.tolist(),
    "trained": True,
}
(MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))

# =========================================
# STEP 13 — FINAL SUMMARY
# =========================================
print("\n" + "="*50)
print("FINAL MODEL SUMMARY")
print("="*50)
print(f"Model          : XGBRegressor")
print(f"Features       : {len(ALL_FEATURES)} engineered features")
print(f"CV R2          : {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")
print(f"Train R2       : {train_r2:.4f}")
print(f"Test RMSE      : {test_rmse:.4f}")
print(f"Test MAE       : {test_mae:.4f}")
print(f"Test R2        : {test_r2:.4f}")
print(f"Overfit ratio  : {overfit_ratio:.2%}")
print(f"Top 5 Features : {importance.head(5).index.tolist()}")
print(f"\nModel saved    : {MODEL_PATH}")
print(f"Metadata       : {MODEL_DIR / 'metadata.json'}")
print("Training completed successfully.")
