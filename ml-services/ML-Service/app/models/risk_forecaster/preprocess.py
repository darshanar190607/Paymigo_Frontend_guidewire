import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

MODEL_DIR   = Path(__file__).parent
DATA_PATH   = Path("D:/Hackathon Projects/ML-Service/app/data/zone_weather_sequences.csv")
SCALER_PATH = MODEL_DIR / "scaler.pkl"

TARGET  = "disruption_happened"
SEQ_IN  = 14   # lookback window (days)
SEQ_OUT = 7    # forecast horizon (days) — used only at inference

# curfew_alert_flag dropped — all zeros (NaN corr), no signal
# flood_alert_flag kept — highest corr (0.95) with disruption
# rain_3day_avg, rain_7day_avg kept — past rolling data, no leakage
FEATURES = [
    "rain_mm", "temp_c", "humidity_pct", "wind_speed_kmph", "pressure_hpa",
    "storm_alert_flag", "flood_alert_flag", "heatwave_flag", "high_wind_flag",
    "rain_3day_avg", "rain_7day_avg",
]
N_FEATURES = len(FEATURES)


def load_and_sort(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["pincode", "date"]).reset_index(drop=True)
    return df


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[FEATURES + [TARGET]] = (
        df.groupby("pincode")[FEATURES + [TARGET]]
        .transform(lambda g: g.ffill().bfill())
    )
    assert df[FEATURES + [TARGET]].isnull().sum().sum() == 0, "NaN values remain"
    return df


def make_sequences(df: pd.DataFrame):
    """
    Single-step prediction: predict next day disruption from last 14 days.
    X: (samples, SEQ_IN, N_FEATURES)
    y: (samples,) — binary next-day disruption label
    Built per pincode — no cross-zone mixing.
    """
    X_list, y_list = [], []
    for _, grp in df.groupby("pincode"):
        feat_vals   = grp[FEATURES].values
        target_vals = grp[TARGET].values
        n = len(grp)
        for i in range(n - SEQ_IN):
            X_list.append(feat_vals[i : i + SEQ_IN])
            y_list.append(target_vals[i + SEQ_IN])
    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.float32)


def time_split(X: np.ndarray, y: np.ndarray, test_ratio: float = 0.2):
    """Chronological split — NO shuffling."""
    split = int(len(X) * (1 - test_ratio))
    return X[:split], X[split:], y[:split], y[split:]


def fit_scaler(X_train: np.ndarray) -> MinMaxScaler:
    n, t, f = X_train.shape
    scaler = MinMaxScaler()
    scaler.fit(X_train.reshape(-1, f))
    joblib.dump(scaler, SCALER_PATH)
    return scaler


def apply_scaler(X: np.ndarray, scaler: MinMaxScaler = None) -> np.ndarray:
    if scaler is None:
        scaler = joblib.load(SCALER_PATH)
    n, t, f = X.shape
    return scaler.transform(X.reshape(-1, f)).reshape(n, t, f)


def scale_inference_input(raw_14days: np.ndarray) -> np.ndarray:
    """
    raw_14days: (14, N_FEATURES) — last 14 days of features
    Returns: (1, 14, N_FEATURES) scaled
    """
    scaler = joblib.load(SCALER_PATH)
    scaled = scaler.transform(raw_14days)
    return scaled[np.newaxis, :, :]
