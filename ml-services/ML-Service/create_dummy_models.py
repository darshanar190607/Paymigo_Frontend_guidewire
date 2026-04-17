import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

# Create and save fraud detector model
print("Creating fraud detector model...")
fraud_data = np.random.rand(1000, 4) * 1000  # 1000 samples, 4 features
fraud_scaler = StandardScaler()
fraud_scaled = fraud_scaler.fit_transform(fraud_data)

fraud_model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
fraud_model.fit(fraud_scaled)

joblib.dump(fraud_model, "app/models/fraud_detector/isolation_forest.pkl")
joblib.dump(fraud_scaler, "app/models/fraud_detector/scaler.pkl")
print("Fraud detector model created!")

# Create GPS classifier model
print("Creating GPS classifier model...")
from sklearn.ensemble import RandomForestClassifier

gps_data = np.random.rand(1000, 5) * 100  # 1000 samples, 5 features
gps_labels = np.random.choice([0, 1], 1000)  # Binary classification

gps_model = RandomForestClassifier(n_estimators=100, random_state=42)
gps_model.fit(gps_data, gps_labels)

joblib.dump(gps_model, "app/models/gps_classifier/rf_gps.pkl")
joblib.dump(StandardScaler(), "app/models/gps_classifier/scaler.pkl")
print("GPS classifier model created!")

# Create trigger classifier model
print("Creating trigger classifier model...")
trigger_data = np.random.rand(1000, 4) * 10  # 1000 samples, 4 features
trigger_labels = np.random.choice([0, 1], 1000)  # Binary classification

trigger_model = RandomForestClassifier(n_estimators=100, random_state=42)
trigger_model.fit(trigger_data, trigger_labels)

joblib.dump(trigger_model, "app/models/trigger_classifier/rf_trigger.pkl")
with open("app/models/trigger_classifier/threshold.json", "w") as f:
    import json
    json.dump({"threshold": 0.5}, f)
print("Trigger classifier model created!")

# Create curfew NLP model (dummy)
print("Creating curfew NLP model...")
import os
os.makedirs("app/models/curfew_nlp", exist_ok=True)
with open("app/models/curfew_nlp/model.pkl", "wb") as f:
    f.write(b"dummy_model")
print("Curfew NLP model created!")

# Create risk forecaster model
print("Creating risk forecaster model...")
os.makedirs("app/models/risk_forecaster", exist_ok=True)
with open("app/models/risk_forecaster/lstm_model.h5", "wb") as f:
    f.write(b"dummy_lstm_model")
joblib.dump(StandardScaler(), "app/models/risk_forecaster/scaler.pkl")
print("Risk forecaster model created!")

print("All dummy models created successfully!")
