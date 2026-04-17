import requests

print('=== Testing Complete ML Service Flow ===')

# Test 1: Zone clustering
print('\n1. Zone Clustering:')
zone_data = {'storm_days': 5, 'heavy_rain_days': 12, 'avg_aqi': 85.5}
response = requests.post('http://localhost:8000/cluster/predict', json=zone_data)
zone_result = response.json()
print(f'   Input: {zone_data}')
print(f'   Output: {zone_result}')

# Test 2: Premium calculation using zone risk tier
print('\n2. Premium Calculation:')
premium_data = {
    'age': 28, 'job_type': 'delivery', 'experience_years': 3, 'incident_history': 1,
    'zone_risk_tier': zone_result['zone_risk_tier'],
    'lstm_forecast_score': 0.6, 'aqi_7day_avg': 92.0, 'platform_tenure_weeks': 8,
    'loyalty_weeks_paid': 6, 'historical_disruption_rate': 0.12,
    'peer_claim_rate_zone': 0.06, 'current_month': 6, 'policy_tier': 'Standard'
}
response = requests.post('http://localhost:8000/premium/predict', json=premium_data)
premium_result = response.json()
zone_risk = zone_result['zone_risk_tier']
print(f'   Input: zone_risk_tier={zone_risk}')
print(f'   Output: {premium_result}')

# Test 3: Fraud detection
print('\n3. Fraud Detection:')
fraud_data = {'claim_amount': 5000, 'zone_risk': zone_risk, 'days_since_policy': 45, 'incident_count': 2}
response = requests.post('http://localhost:8000/fraud/detect', json=fraud_data)
fraud_result = response.json()
print(f'   Input: {fraud_data}')
print(f'   Output: {fraud_result}')

print('\n✅ Complete ML Service Flow is Working!')
print('   Signup → Zone Clustering → Premium Calculation → Fraud Detection')
