from geotruth.schemas import LayerResult

# A moderate burst (5–10 claims/min across a pincode) is a positive signal —
# it means many workers in the same zone stopped simultaneously, which is
# consistent with a real weather disruption.
_ZONE_GENUINE_LOW  = 5.0
_ZONE_GENUINE_HIGH = 10.0
LAYER_WEIGHT = 10.0


def score_zone_layer(claim_burst_rate: float) -> LayerResult:
    """
    L5 — Platform Zone Coherence.

    Interprets the zone-wide claim burst rate as a disruption signal.
    A moderate burst validates a real event; near-zero is neutral.
    Extreme burst (ring attack) is handled by L7, not here.

    Parameters
    ----------
    claim_burst_rate : float
        Claims per minute arriving for the worker's pincode zone.
    """
    if _ZONE_GENUINE_LOW <= claim_burst_rate <= _ZONE_GENUINE_HIGH:
        return LayerResult(
            layer_name="ZoneCoherence",
            score=1.0,
            available=True,
            weight=LAYER_WEIGHT,
            reason=f"Zone burst rate {claim_burst_rate:.1f}/min — consistent with real disruption event",
            metadata={"claim_burst_rate": claim_burst_rate},
        )

    if claim_burst_rate < _ZONE_GENUINE_LOW:
        return LayerResult(
            layer_name="ZoneCoherence",
            score=0.5,
            available=True,
            weight=LAYER_WEIGHT,
            reason=f"Zone burst rate {claim_burst_rate:.1f}/min — low activity, no zone-wide confirmation",
            metadata={"claim_burst_rate": claim_burst_rate},
        )

    # claim_burst_rate > _ZONE_GENUINE_HIGH but below ring threshold —
    # elevated but not yet a confirmed ring; score degrades linearly.
    score = max(0.1, 1.0 - (claim_burst_rate - _ZONE_GENUINE_HIGH) / 10.0)
    return LayerResult(
        layer_name="ZoneCoherence",
        score=round(score, 3),
        available=True,
        weight=LAYER_WEIGHT,
        reason=f"Zone burst rate {claim_burst_rate:.1f}/min — elevated, approaching ring threshold",
        metadata={"claim_burst_rate": claim_burst_rate},
    )
