"""
GigKavach GeoTruth™ — Central Configuration
All paths, feature lists, dataset sizes, hyperparameter grids.
"""
import os

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
MODEL_DIR  = os.path.join(BASE_DIR, "models_saved")
PLOTS_DIR  = os.path.join(BASE_DIR, "plots")

for _d in [DATA_DIR, MODEL_DIR, PLOTS_DIR]:
    os.makedirs(_d, exist_ok=True)

# ── Dataset Sizes ──────────────────────────────────────────────────────
N_NORMAL_GPS   = 15_000   # non-spoofed GPS sessions
N_SPOOFED_GPS  =  5_000   # spoofed GPS sessions  (25 % spoof rate)
N_NORMAL_FRAUD = 20_000   # legitimate worker claims
N_FRAUD_POS    =  2_000   # fraudulent claims     (9.1 % fraud rate)

# ── Reproducibility ────────────────────────────────────────────────────
RANDOM_STATE = 42
TEST_SIZE    = 0.20
VAL_SIZE     = 0.10   # of training set
CV_FOLDS     = 5

# ── GeoTruth™ 38-dim feature vector ────────────────────────────────────
GPS_FEATURES = [
    # 1-5  Barometric pressure layer
    "baro_alt_m", "gps_alt_m", "alt_discrepancy_m",
    "baro_pressure_hpa", "baro_altitude_rate",
    # 6-9  Acoustic fingerprinting layer
    "ambient_noise_db", "noise_consistency_score",
    "location_acoustic_match", "acoustic_anomaly_flag",
    # 10-15 Network topology layer
    "cell_tower_count", "wifi_ap_count", "expected_tower_match",
    "network_latency_ms", "signal_strength_dbm", "network_loc_consistency",
    # 16-22 Inertial motion layer
    "accel_magnitude", "accel_variance_1min", "reported_speed_kmph",
    "inertial_speed_est", "speed_discrepancy",
    "heading_change_rate", "motion_consistency",
    # 23-27 Zone coherence layer
    "zone_pincode_match", "expected_zone_transition",
    "geofence_violations", "route_feasibility", "delivery_density_match",
    # 28-33 Behavioral baseline layer
    "session_duration_min", "deliveries_per_hour", "break_frequency",
    "speed_vs_baseline", "earnings_vs_baseline", "behavioral_anomaly",
    # 34-38 Social ring detection layer
    "peer_proximity_count", "sync_movement_score",
    "device_fingerprint_match", "platform_login_consistency",
    "social_anomaly_score",
]
GPS_TARGET   = "label_spoofed"
GPS_META     = ["session_id", "pincode", "spoof_type"]

# ── Fraud Detection 20-feature vector ──────────────────────────────────
FRAUD_FEATURES = [
    "zone_risk_tier", "claim_frequency_30d", "claim_amount_zscore",
    "location_jump_count", "gps_spoof_probability",
    "policy_tenure_weeks", "earnings_deviation",
    "claim_timing_anomaly", "peer_claim_correlation",
    "device_change_count", "login_anomaly_score",
    "route_deviation_score", "delivery_speed_anomaly",
    "duplicate_claim_score", "network_fraud_ring_score",
    "barometric_consistency", "zone_transition_anomaly",
    "claim_photo_similarity_score", "platform_switch_frequency",
    "behavioral_baseline_deviation",
]
FRAUD_TARGET = "label_fraud"
FRAUD_META   = ["worker_id", "fraud_type"]

# ── Zone coordinates ────────────────────────────────────────────────────
ZONE_COORDS = {
    "641001": (11.0168, 76.9558, "Coimbatore", "TN"),
    "600001": (13.0827, 80.2707, "Chennai",    "TN"),
    "400001": (19.0760, 72.8777, "Mumbai",     "MH"),
    "560001": (12.9716, 77.5946, "Bengaluru",  "KA"),
    "500001": (17.3850, 78.4867, "Hyderabad",  "TG"),
    "110001": (28.6139, 77.2090, "Delhi",      "DL"),
}

# ── Kaggle dataset identifiers ──────────────────────────────────────────
KAGGLE_DATASETS = {
    # Free download after kaggle.com signup + kaggle.json setup
    "porto_taxi":  "pkdd-15-predict-taxi-service-trajectory-i",  # competition
    "ieee_fraud":  "ieee-fraud-detection",                        # competition
    "gps_anomaly": "yasserh/uber-fares-dataset",                  # proxy traces
}

# ── Model save paths ────────────────────────────────────────────────────
GPS_MODEL_PATH   = os.path.join(MODEL_DIR, "gps_spoof_model.pkl")
FRAUD_MODEL_PATH = os.path.join(MODEL_DIR, "fraud_model.pkl")
GPS_PREP_PATH    = os.path.join(MODEL_DIR, "gps_preprocessor.pkl")
FRAUD_PREP_PATH  = os.path.join(MODEL_DIR, "fraud_preprocessor.pkl")

