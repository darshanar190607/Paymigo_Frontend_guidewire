import joblib
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from pathlib import Path

# The 11 features:
# ["rain_mm", "temp_c", "humidity_pct", "wind_speed_kmph", "pressure_hpa",
#  "storm_alert_flag", "flood_alert_flag", "heatwave_flag", "high_wind_flag",
#  "rain_3day_avg", "rain_7day_avg"]

min_vals = [0.0, 10.0, 20.0, 0.0, 980.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
max_vals = [100.0, 45.0, 100.0, 60.0, 1030.0, 1.0, 1.0, 1.0, 1.0, 80.0, 50.0]

X_dummy = np.array([min_vals, max_vals])
scaler = MinMaxScaler()
scaler.fit(X_dummy)

scaler_path = Path(r"c:\Guidewire_Devtrails\PayMigo_Final\ml-services\ML-Service\app\models\risk_forecaster\scaler.pkl")
joblib.dump(scaler, scaler_path)
print("Saved fitted MinMaxScaler to:", scaler_path)
