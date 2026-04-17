import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

# Create simple fraud detector
print("Creating fraud detector...")
X = np.array([
    [1000, 1.0, 30, 1],    # Normal claims
    [2000, 2.0, 60, 2],    # Normal claims  
    [1500, 1.5, 45, 1],    # Normal claims
    [50000, 5.0, 5, 10],   # Fraudulent (high amount)
    [100000, 5.0, 2, 15],  # Fraudulent (very high amount)
    [20000, 4.0, 10, 8],   # Fraudulent (high amount, new policy)
])

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = IsolationForest(contamination=0.3, random_state=42)
model.fit(X_scaled)

# Save models
joblib.dump(model, 'app/models/fraud_detector/isolation_forest.pkl')
joblib.dump(scaler, 'app/models/fraud_detector/scaler.pkl')

print("Fraud detector created and saved!")
print("Test prediction:")
test_data = [[5000, 4.0, 45, 2]]
test_scaled = scaler.transform(test_data)
prediction = model.predict(test_scaled)
print(f"Prediction: {prediction[0]} (-1=fraud, 1=normal)")
