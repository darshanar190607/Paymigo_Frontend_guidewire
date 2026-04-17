from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ClaimVector(BaseModel):
    worker_id: str
    claimed_pincode: str
    timestamp: int

    # Barometric
    device_barometer_hpa: Optional[float] = Field(None, description="Hardware barometer reading")
    has_barometer: bool = True

    # Acoustic
    acoustic_feature_vector: Optional[List[float]] = Field(None, description="5-dim YAMNet output")
    has_microphone: bool = True

    # Inertial / Motion
    variance_1h_to_30m_ago: Optional[float] = None
    variance_last_30m: Optional[float] = None
    gyroscope_available: bool = True

    # Network
    cell_tower_ids: List[str] = Field(..., description="Hashed Cell IDs")
    wifi_ssid_hashes: List[str] = Field(default_factory=list, description="Hashed WiFi SSIDs")

    # Device / fraud signals
    is_from_mock_provider: bool = False
    is_mock_location: bool = False
    connection_type: Optional[str] = None
    screen_unlock_count_1h: Optional[int] = None


class LayerResult(BaseModel):
    layer_name: str
    score: float
    available: bool
    weight: float
    reason: str
    grace_flag: bool = False
    confidence: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkerProfile(BaseModel):
    worker_id: str
    baseline_accelerometer_variance: float = 0.5
    historical_fraud_flags: int = 0


class ScoringResult(BaseModel):
    coherence_score: int
    confidence: float
    tier: str
    flagged_signals: List[str]
    sensor_gaps: List[str]
    recommendation: str
