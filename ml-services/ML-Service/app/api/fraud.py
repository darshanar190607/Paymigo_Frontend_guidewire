from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.models.fraud_detector.predict import predict as fraud_predict
from app.models.gps_spoofing.predict import predict_gps_spoof

router = APIRouter()


class FraudRequest(BaseModel):
    # Core 20 features
    zone_risk_tier: float = 0.0
    claim_frequency_30d: float = 0.0
    claim_amount_zscore: float = 0.0
    location_jump_count: float = 0.0
    gps_spoof_probability: float = 0.0
    policy_tenure_weeks: float = 0.0
    earnings_deviation: float = 0.0
    claim_timing_anomaly: float = 0.0
    peer_claim_correlation: float = 0.0
    device_change_count: float = 0.0
    login_anomaly_score: float = 0.0
    route_deviation_score: float = 0.0
    delivery_speed_anomaly: float = 0.0
    duplicate_claim_score: float = 0.0
    network_fraud_ring_score: float = 0.0
    barometric_consistency: float = 1.0
    zone_transition_anomaly: float = 0.0
    claim_photo_similarity_score: float = 0.0
    platform_switch_frequency: float = 0.0
    behavioral_baseline_deviation: float = 0.0
    # Derived features (optional — computed by model if not provided)
    gps_claim_interaction: Optional[float] = None
    ring_score_composite: Optional[float] = None
    temporal_claim_pressure: Optional[float] = None
    device_login_risk: Optional[float] = None
    overall_fraud_risk_score: Optional[float] = None


class GPSRequest(BaseModel):
    # ── Barometric pressure layer (5) ─────────────────────────────────
    baro_alt_m: float = 0.0
    gps_alt_m: float = 0.0
    alt_discrepancy_m: float = 0.0
    baro_pressure_hpa: float = 1013.0
    baro_altitude_rate: float = 0.0
    # ── Acoustic fingerprinting (4) ───────────────────────────────────
    ambient_noise_db: float = 45.0
    noise_consistency_score: float = 0.8
    location_acoustic_match: float = 1.0
    acoustic_anomaly_flag: float = 0.0
    # ── Network topology (6) ──────────────────────────────────────────
    cell_tower_count: float = 3.0
    wifi_ap_count: float = 2.0
    expected_tower_match: float = 1.0
    network_latency_ms: float = 80.0
    signal_strength_dbm: float = -70.0
    network_loc_consistency: float = 0.9
    # ── Inertial motion (7) ───────────────────────────────────────────
    accel_magnitude: float = 0.5
    accel_variance_1min: float = 0.1
    reported_speed_kmph: float = 0.0
    inertial_speed_est: float = 0.0
    speed_discrepancy: float = 0.0
    heading_change_rate: float = 0.0
    motion_consistency: float = 0.9
    # ── Zone coherence (5) ────────────────────────────────────────────
    zone_pincode_match: float = 1.0
    expected_zone_transition: float = 1.0
    geofence_violations: float = 0.0
    route_feasibility: float = 1.0
    delivery_density_match: float = 1.0
    # ── Behavioral baseline (6) ───────────────────────────────────────
    session_duration_min: float = 30.0
    deliveries_per_hour: float = 3.0
    break_frequency: float = 2.0
    speed_vs_baseline: float = 1.0
    earnings_vs_baseline: float = 1.0
    behavioral_anomaly: float = 0.0
    # ── Social ring detection (5) ─────────────────────────────────────
    peer_proximity_count: float = 0.0
    sync_movement_score: float = 0.0
    device_fingerprint_match: float = 1.0
    platform_login_consistency: float = 1.0
    social_anomaly_score: float = 0.0


@router.post("/detect")
def fraud_detect(req: FraudRequest):
    result = fraud_predict(req.dict())
    return result


@router.post("/gps")
def gps_classify(req: GPSRequest):
    result = predict_gps_spoof(req.dict())
    return result
