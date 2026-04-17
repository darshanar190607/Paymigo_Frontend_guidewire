"""
GeoTruth — Multi-Modal Environmental Coherence Verification
===========================================================
Parametric insurance fraud detection for the Indian gig economy.

Quick start:
    from geotruth import GeoTruthEngine, ClaimVector

    engine = GeoTruthEngine()
    result = engine.verify(claim)
"""

from geotruth.engine import GeoTruthEngine
from geotruth.schemas import ClaimVector, LayerResult, ScoringResult, WorkerProfile
from geotruth.main import cli

__version__ = "1.0.0"
__all__ = ["GeoTruthEngine", "ClaimVector", "LayerResult", "ScoringResult", "WorkerProfile", "cli"]
