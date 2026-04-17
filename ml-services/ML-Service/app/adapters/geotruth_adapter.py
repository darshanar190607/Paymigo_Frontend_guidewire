"""
GeoTruth Adapter Layer
======================
Isolates GeoTruth engine from the ML service API layer.
Provides clean interface for backend orchestration.
"""

import sys
from pathlib import Path

# Add GeoTruth package to path (fallback handles case-sensitivity on Windows)
GEOTRUTH_PATH = Path(__file__).parent.parent.parent / "Geotruth"
if not GEOTRUTH_PATH.exists():
    GEOTRUTH_PATH = Path(__file__).parent.parent.parent / "geotruth"
sys.path.insert(0, str(GEOTRUTH_PATH))

from geotruth import GeoTruthEngine, ClaimVector, WorkerProfile


class GeoTruthAdapter:
    """
    Adapter for GeoTruth engine.
    Converts between API payloads and GeoTruth internal schemas.
    """
    
    def __init__(self):
        self.engine = GeoTruthEngine()
    
    async def verify_claim_async(self, claim_data: dict, profile_data: dict = None, claim_burst_rate: float = 0.0):
        """
        Async verification for FastAPI endpoints.
        
        Args:
            claim_data: Raw claim payload from backend
            profile_data: Worker profile data (optional)
            claim_burst_rate: Claims per minute in zone
            
        Returns:
            dict: Standardized verification result
        """
        claim = ClaimVector(**claim_data)
        profile = WorkerProfile(**profile_data) if profile_data else None
        
        result = await self.engine.verify_async(claim, profile, claim_burst_rate)
        
        return {
            "truth_score": 100 - result.coherence_score,  # Invert to trust score
            "coherence_score": result.coherence_score,
            "confidence": result.confidence,
            "decision": result.tier,
            "recommendation": result.recommendation,
            "signals": result.flagged_signals,
            "gaps": result.sensor_gaps,
        }
    
    def verify_claim(self, claim_data: dict, profile_data: dict = None, claim_burst_rate: float = 0.0):
        """
        Sync verification for scripts and testing.
        
        Args:
            claim_data: Raw claim payload from backend
            profile_data: Worker profile data (optional)
            claim_burst_rate: Claims per minute in zone
            
        Returns:
            dict: Standardized verification result
        """
        claim = ClaimVector(**claim_data)
        profile = WorkerProfile(**profile_data) if profile_data else None
        
        result = self.engine.verify(claim, profile, claim_burst_rate)
        
        return {
            "truth_score": 100 - result.coherence_score,
            "coherence_score": result.coherence_score,
            "confidence": result.confidence,
            "decision": result.tier,
            "recommendation": result.recommendation,
            "signals": result.flagged_signals,
            "gaps": result.sensor_gaps,
        }
