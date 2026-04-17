import pandas as pd
from app.core.logger import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = {
    "workers_final_10k.csv": ["latitude", "longitude", "risk_score", "incident_count", "premium_amount"],
    "trigger_events_10k.csv": ["event_type", "severity", "zone_id", "duration_hours", "trigger_label"],
    "curfew_headlines_10k.csv": ["headline", "curfew_risk"],
    "zone_weather_sequences.csv": ["risk_score", "incident_count", "temperature", "humidity", "wind_speed"],
    "synthetic_workers_20k.csv": ["claim_amount", "zone_risk", "days_since_policy", "incident_count"],
}

def validate():
    all_valid = True
    for filename, columns in REQUIRED_COLUMNS.items():
        path = f"app/data/{filename}"
        try:
            df = pd.read_csv(path)
            missing = [c for c in columns if c not in df.columns]
            if missing:
                logger.warning(f"{filename}: missing columns {missing}")
                all_valid = False
            else:
                logger.info(f"{filename}: OK ({len(df)} rows)")
        except FileNotFoundError:
            logger.error(f"{filename}: file not found")
            all_valid = False
    return all_valid

if __name__ == "__main__":
    validate()
