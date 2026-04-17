"""
GeoTruth — FastAPI Server
=========================
Thin HTTP adapter. All scoring logic lives in GeoTruthEngine.

Run:
    uvicorn geotruth.server:app --reload
"""

from fastapi import FastAPI, Query

from geotruth.engine import GeoTruthEngine
from geotruth.schemas import ClaimVector, ScoringResult, WorkerProfile

app = FastAPI(
    title="GeoTruth MCP Server",
    version="1.0.0",
    description="Multi-Modal Environmental Coherence Verification API",
)

# Engine is instantiated once at startup — both XGBoost models load here.
_engine = GeoTruthEngine()


@app.post("/verify", response_model=ScoringResult)
async def verify_claim(
    claim: ClaimVector,
    claim_burst_rate: float = Query(default=0.0, description="Claims/min for this pincode zone"),
    baseline_deviation: float = Query(default=0.0, description="Unused — kept for backwards compat"),
) -> ScoringResult:
    """
    Verify a parametric insurance claim against the 7-layer GeoTruth stack.

    - **claim_burst_rate**: Zone-wide claims per minute (L5/L7 signal).
    """
    return await _engine.verify_async(
        claim=claim,
        profile=None,          # WorkerProfile lookup is a platform concern
        claim_burst_rate=claim_burst_rate,
    )


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "coherence_model_loaded": _engine._coherence_model is not None,
    }
