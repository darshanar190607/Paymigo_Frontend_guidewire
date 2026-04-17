from typing import Optional

from geotruth.schemas import ClaimVector, LayerResult, WorkerProfile

LAYER_WEIGHT = 8.0

# Variance delta above this is considered a massive deviation (score → 0)
_MAX_DEVIATION = 1.0


def score_baseline_layer(
    claim: ClaimVector,
    profile: Optional[WorkerProfile],
) -> LayerResult:
    """
    L6 — Personal Behavioral Baseline.

    Compares the claim's current motion variance against the worker's
    historical baseline. A worker who suddenly files from a zone or
    motion pattern they've never shown before scores lower.

    Graceful degradation: if no profile exists (new worker), layer is
    skipped with grace_flag=True so they aren't penalised.

    Parameters
    ----------
    claim : ClaimVector
        The incoming claim. Uses variance_last_30m as the current signal.
    profile : WorkerProfile or None
        The worker's historical profile. None for new/unknown workers.
    """
    if profile is None:
        return LayerResult(
            layer_name="BehavioralBaseline",
            score=0.5,
            available=False,
            weight=LAYER_WEIGHT,
            grace_flag=True,
            reason="No worker profile available — new worker or profile not loaded. Grace flag applied.",
        )

    current_variance = claim.variance_last_30m
    if current_variance is None:
        return LayerResult(
            layer_name="BehavioralBaseline",
            score=0.5,
            available=False,
            weight=LAYER_WEIGHT,
            grace_flag=True,
            reason="variance_last_30m missing — cannot compute baseline deviation. Grace flag applied.",
        )

    delta = abs(current_variance - profile.baseline_accelerometer_variance)

    # Normalise delta to [0, 1] — clamp at _MAX_DEVIATION
    normalised = min(delta / _MAX_DEVIATION, 1.0)
    score = round(1.0 - normalised, 3)

    # Historical fraud flags reduce confidence in the score
    fraud_penalty = min(profile.historical_fraud_flags * 0.1, 0.3)
    score = round(max(0.0, score - fraud_penalty), 3)

    if delta <= 0.15:
        reason = f"Variance delta {delta:.3f} — within normal baseline range ✅"
    elif delta <= 0.40:
        reason = f"Variance delta {delta:.3f} — moderate deviation from baseline ⚠️"
    else:
        reason = f"Variance delta {delta:.3f} — large deviation from personal baseline ❌"

    if profile.historical_fraud_flags > 0:
        reason += f" | {profile.historical_fraud_flags} prior fraud flag(s) applied as penalty"

    return LayerResult(
        layer_name="BehavioralBaseline",
        score=score,
        available=True,
        weight=LAYER_WEIGHT,
        reason=reason,
        metadata={
            "current_variance": current_variance,
            "baseline_variance": profile.baseline_accelerometer_variance,
            "delta": round(delta, 4),
            "historical_fraud_flags": profile.historical_fraud_flags,
        },
    )
