from geotruth.schemas import LayerResult

# Matches ideation doc: "20+ claims in 4 min → RING ALERT"
# 20 claims / 4 min = 5/min minimum, but engine uses 15/min as the confirmed threshold
_RING_THRESHOLD = 15.0
LAYER_WEIGHT = 20.0


def score_social_ring_layer(claim_burst_rate: float) -> LayerResult:
    """
    L7 — Social Coordination Ring Detector.

    Detects Telegram-coordinated fraud rings via temporal burst analysis.
    A burst rate >= 15 claims/min for a single pincode is statistically
    impossible for genuine stranded workers (who trickle in over 20–40 min).

    A score of 0.0 from this layer MUST override the final tier to ring_alert
    regardless of the XGBoost coherence output. This is enforced in engine.py.

    Parameters
    ----------
    claim_burst_rate : float
        Claims per minute arriving for the worker's pincode zone.
    """
    if claim_burst_rate >= _RING_THRESHOLD:
        return LayerResult(
            layer_name="SocialRingDetector",
            score=0.0,
            available=True,
            weight=LAYER_WEIGHT,
            reason=(
                f"RING ALERT — burst rate {claim_burst_rate:.1f}/min exceeds threshold "
                f"of {_RING_THRESHOLD}/min. Coordinated Telegram ring attack pattern detected."
            ),
            metadata={
                "claim_burst_rate": claim_burst_rate,
                "ring_threshold": _RING_THRESHOLD,
                "ring_detected": True,
            },
        )

    return LayerResult(
        layer_name="SocialRingDetector",
        score=1.0,
        available=True,
        weight=LAYER_WEIGHT,
        reason=f"Burst rate {claim_burst_rate:.1f}/min — below ring threshold. No coordinated attack detected.",
        metadata={
            "claim_burst_rate": claim_burst_rate,
            "ring_threshold": _RING_THRESHOLD,
            "ring_detected": False,
        },
    )
