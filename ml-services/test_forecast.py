import sys
from pathlib import Path

# Add ML-Service directory to path to allow absolute imports
sys.path.insert(0, str(Path(r"c:\Guidewire_Devtrails\PayMigo_Final\ml-services\ML-Service").absolute()))

try:
    from app.models.risk_forecaster.predict import predict_disruption
    
    # Mock data with exactly 14 rows, each with 11 features
    features_keys = [
        "rain_mm", "temp_c", "humidity_pct", "wind_speed_kmph", "pressure_hpa",
        "storm_alert_flag", "flood_alert_flag", "heatwave_flag", "high_wind_flag",
        "rain_3day_avg", "rain_7day_avg"
    ]
    # create dummy values representing the last 14 days
    last_14_days = []
    for i in range(14):
        last_14_days.append({k: 1.0 for k in features_keys})

    result = predict_disruption(last_14_days)
    print("SUCCESS")
    print(result)

except Exception as e:
    import traceback
    traceback.print_exc()
