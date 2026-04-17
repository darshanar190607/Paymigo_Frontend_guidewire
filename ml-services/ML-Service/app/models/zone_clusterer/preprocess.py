import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

# Only high-signal features — drop pincode, city, avg_rainfall, avg_pressure, avg_wind_speed
FEATURES = ["storm_days", "heavy_rain_days", "avg_aqi"]

# Engineered interaction: captures combined rain intensity
ENGINEERED = "rain_stress"

MODEL_DIR = Path(__file__).parent


def preprocess_features(df: pd.DataFrame, features: list = None) -> pd.DataFrame:
    cols = features or FEATURES
    X = df[cols].copy()

    for col in cols:
        X[col] = X[col].fillna(X[col].median())

    if "avg_aqi" in cols:
        X["avg_aqi"] = X["avg_aqi"].clip(lower=1)
        X["avg_aqi"] = np.log1p(X["avg_aqi"])

    # Interaction feature: storm intensity × rain days
    if "storm_days" in cols and "heavy_rain_days" in cols:
        X[ENGINEERED] = X["storm_days"] * X["heavy_rain_days"]

    return X


def remove_outliers(X: pd.DataFrame, iqr_factor: float = 1.0) -> pd.Series:
    Q1, Q3 = X.quantile(0.25), X.quantile(0.75)
    IQR = Q3 - Q1
    return ~((X < (Q1 - iqr_factor * IQR)) | (X > (Q3 + iqr_factor * IQR))).any(axis=1)


def fit_scaler(X: np.ndarray, path: Path) -> np.ndarray:
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, path)
    return X_scaled


def apply_scaler(X: np.ndarray, path: Path) -> np.ndarray:
    return joblib.load(path).transform(X)


def apply_pca(X: np.ndarray, path: Path) -> np.ndarray:
    return joblib.load(path).transform(X)
