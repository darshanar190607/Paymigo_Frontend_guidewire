from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List
from app.adapters import GeoTruthAdapter

router = APIRouter()
geotruth_adapter = GeoTruthAdapter()


class ClaimVerificationRequest(BaseModel):
    worker_id: str
    claimed_pincode: str
    timestamp: int
    
    # Barometric
    device_barometer_hpa: Optional[float] = None
    has_barometer: bool = True
    
    # Acoustic
    acoustic_feature_vector: Optional[List[float]] = None
    has_microphone: bool = True
    
    # Inertial
    variance_1h_to_30m_ago: Optional[float] = None
    variance_last_30m: Optional[float] = None
    gyroscope_available: bool = True
    
    # Network
    cell_tower_ids: List[str] = Field(default_factory=list)
    wifi_ssid_hashes: List[str] = Field(default_factory=list)
    
    # Device signals
    is_from_mock_provider: bool = False
    is_mock_location: bool = False
    connection_type: Optional[str] = None
    screen_unlock_count_1h: Optional[int] = None
    
    # Platform context
    claim_burst_rate: float = 0.0


class WorkerProfileRequest(BaseModel):
    worker_id: str
    baseline_accelerometer_variance: float = 0.5
    historical_fraud_flags: int = 0


@router.post("/verify")
async def verify_claim(req: ClaimVerificationRequest):
    """
    GeoTruth multi-modal environmental coherence verification.
    
    Returns trust score, decision tier, and flagged signals.
    """
    claim_data = req.dict(exclude={"claim_burst_rate"})
    result = await geotruth_adapter.verify_claim_async(
        claim_data=claim_data,
        claim_burst_rate=req.claim_burst_rate
    )
    return result


@router.post("/verify-with-profile")
async def verify_claim_with_profile(
    claim: ClaimVerificationRequest,
    profile: WorkerProfileRequest
):
    """
    GeoTruth verification with worker behavioral profile.
    """
    claim_data = claim.dict(exclude={"claim_burst_rate"})
    profile_data = profile.dict()
    
    result = await geotruth_adapter.verify_claim_async(
        claim_data=claim_data,
        profile_data=profile_data,
        claim_burst_rate=claim.claim_burst_rate
    )
    return result
