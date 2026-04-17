"""
GeoTruth — Layer 4: Inertial Motion (Production Inference)
===========================================================
Evaluates whether a worker's motion pattern is consistent with
a genuine delivery disruption or a fraud actor at home.

WHAT THIS LAYER DETECTS
------------------------
  GENUINE signal:
    Worker was actively delivering (high prior variance from road vibrations)
    → Storm/flood hit → Worker took shelter (sudden drop to near-zero variance)
    → Variance delta is strongly negative — the defining genuine signature

  FRAUD signals:
    1. Prolonged static: Both windows low — never left home
    2. Spoof activation: Current > prior — picked up phone to activate spoof app
    3. Normal driving: Near-zero delta — no disruption event occurred

ML MODEL
--------
  XGBoost classifier (JSON format, device-agnostic)
  Input: 7 engineered features from ClaimVector motion fields
  Output: P(genuine) — probability the worker is genuinely stranded
  Threshold: P(genuine) >= 0.7 → score=1.0 (approve)

FALLBACK STRATEGY
-----------------
  If model file is missing (not yet trained):  available=False, grace_flag=True
  If model fails to load (corrupt file):       available=False, grace_flag=True
  If input fields are None (budget phone):     available=False, grace_flag=True
  If mock location detected:                   score=0.0, reason explains penalty
  In all unavailable cases: weight is dropped from CoherenceEngine scoring
  and sensor_gap_grace is set so reviewers apply leniency.

INTEGRATION
-----------
  from geotruth.layers.inertial import score_inertial_layer
  result = score_inertial_layer(claim)
  # result.score: 0.0–1.0
  # result.available: bool
  # result.grace_flag: bool
  # result.confidence: float (model probability)
  # result.reason: human-readable explanation
"""

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

from geotruth.schemas import LayerResult

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
_MODEL_PATH = Path(__file__).parent.parent / "models" / "xgb_inertial_v1.json"
_META_PATH  = Path(__file__).parent.parent / "models" / "xgb_inertial_v1_meta.json"

# ── Layer configuration ────────────────────────────────────────────────────────
LAYER_ID        = "L4_inertial"
DEFAULT_WEIGHT  = 12       # Full weight when layer is active
REDUCED_WEIGHT  = 6        # Accelerometer-only fallback (no gyroscope)
GENUINE_THRESHOLD = 0.70   # P(genuine) >= this → score=1.0

# ── Feature column order — MUST match training order ──────────────────────────
FEATURE_COLS = [
    "variance_1h_to_30m_ago",
    "variance_last_30m",
    "variance_delta",
    "motion_ratio",
    "sudden_stillness",
    "prolonged_static",
    "reverse_delta",
]

# ── Lazy global model load ─────────────────────────────────────────────────────
# Model is loaded ONCE at first call, not on every request.
# This is the production pattern — avoids 50-200ms model reload per API call.
_model = None
_model_meta = None
_model_load_error: Optional[str] = None
_model_load_attempted = False


def _load_model_once():
    """
    Lazy singleton loader. Called once on first inference request.
    Sets module-level _model, _model_meta, or _model_load_error.
    Thread-safe for single-worker FastAPI (uvicorn default).
    For multi-worker: use --workers 1 or move load to FastAPI lifespan event.
    """
    global _model, _model_meta, _model_load_error, _model_load_attempted

    if _model_load_attempted:
        return  # Already tried — don't retry on every request

    _model_load_attempted = True

    # ── Import xgboost ─────────────────────────────────────────────────────────
    try:
        import xgboost as xgb
    except ImportError:
        _model_load_error = "xgboost not installed — run: pip install xgboost"
        logger.error(_model_load_error)
        return

    # ── Check model file exists ────────────────────────────────────────────────
    if not _MODEL_PATH.exists():
        _model_load_error = (
            f"Model file not found: {_MODEL_PATH}\n"
            f"Train the model first:\n"
            f"  python -m geotruth.training.generate_dataset\n"
            f"  python -m geotruth.training.train_model"
        )
        logger.warning(_model_load_error)
        return

    # ── Load model ─────────────────────────────────────────────────────────────
    try:
        model = xgb.XGBClassifier()
        model.load_model(str(_MODEL_PATH))
        _model = model
        logger.info(f"Inertial XGBoost model loaded from {_MODEL_PATH}")
    except Exception as e:
        _model_load_error = f"Model load failed: {type(e).__name__}: {e}"
        logger.error(_model_load_error)
        return

    # ── Load metadata (optional — used for logging/audit) ─────────────────────
    if _META_PATH.exists():
        try:
            _model_meta = json.loads(_META_PATH.read_text())
            logger.info(
                f"Model meta: accuracy={_model_meta.get('test_accuracy')}, "
                f"auc={_model_meta.get('test_roc_auc')}"
            )
        except Exception:
            pass  # Meta is non-critical — inference still works without it


def _engineer_features(
    variance_prior: float,
    variance_current: float
) -> np.ndarray:
    """
    Compute the 7 engineered features from raw variance inputs.
    Must match the exact order and logic used in generate_dataset.py.
    """
    eps = 1e-6
    variance_delta    = variance_current - variance_prior
    motion_ratio      = variance_current / (variance_prior + eps)
    sudden_stillness  = int(variance_prior > 0.35 and variance_current < 0.15)
    prolonged_static  = int(variance_prior < 0.12 and variance_current < 0.12)
    reverse_delta     = int(variance_delta > 0.05)

    return np.array([[
        variance_prior,
        variance_current,
        variance_delta,
        motion_ratio,
        sudden_stillness,
        prolonged_static,
        reverse_delta,
    ]], dtype=np.float32)


def score_inertial_layer(claim) -> LayerResult:
    """
    Main entry point. Called by CoherenceEngine for every claim.

    Parameters
    ----------
    claim : ClaimVector
        Pydantic model with fields:
          - variance_1h_to_30m_ago : Optional[float]
          - variance_last_30m      : Optional[float]
          - gyroscope_available    : Optional[bool]
          - is_mock_location       : Optional[bool]

    Returns
    -------
    LayerResult
        available=False → layer excluded from scoring, weight dropped to 0
        available=True  → score (0.0–1.0) and weight used in coherence average
    """
    # ── Step 1: Lazy load model ────────────────────────────────────────────────
    _load_model_once()

    # ── Step 2: Model unavailable — return graceful fallback ──────────────────
    if _model is None:
        return LayerResult(
            layer_name=LAYER_ID,
            available=False,
            score=0.0,
            weight=0,
            grace_flag=True,
            reason=f"Model unavailable: {_model_load_error or 'unknown error'}. "
                   f"Layer excluded from scoring. sensor_gap_grace=True applied.",
        )

    # ── Step 3: Check input fields ────────────────────────────────────────────
    variance_prior   = getattr(claim, "variance_1h_to_30m_ago", None)
    variance_current = getattr(claim, "variance_last_30m", None)

    if variance_prior is None or variance_current is None:
        # Budget phone — accelerometer data not collected or permission denied
        return LayerResult(
            layer_name=LAYER_ID,
            available=False,
            score=0.0,
            weight=0,
            grace_flag=True,
            reason="Variance fields missing — device may lack accelerometer access "
                   "or permission was not granted. Grace flag applied.",
        )

    # Clamp values to valid physical range
    variance_prior   = float(np.clip(variance_prior, 0.0, 5.0))
    variance_current = float(np.clip(variance_current, 0.0, 5.0))

    # ── Step 4: Mock location penalty ─────────────────────────────────────────
    # isFromMockProvider=True means the Android OS itself reported fake GPS.
    # This is the most reliable signal — we apply immediate high suspicion.
    is_mock = getattr(claim, "is_mock_location", False) or False
    if is_mock:
        return LayerResult(
            layer_name=LAYER_ID,
            available=True,
            score=0.0,
            weight=DEFAULT_WEIGHT,
            confidence=0.0,
            grace_flag=False,
            reason="Android isFromMockProvider=True detected. "
                   "GPS spoofing app active. Score set to 0.0.",
            metadata={"mock_location_detected": True},
        )

    # ── Step 5: Engineer features ──────────────────────────────────────────────
    features = _engineer_features(variance_prior, variance_current)

    # ── Step 6: Run inference ──────────────────────────────────────────────────
    try:
        proba = _model.predict_proba(features)   # shape: (1, 2)
        p_genuine = float(proba[0][1])           # probability of class 1 (genuine)
    except Exception as e:
        logger.error(f"Inertial inference failed: {e}")
        return LayerResult(
            layer_name=LAYER_ID,
            available=False,
            score=0.0,
            weight=0,
            grace_flag=True,
            reason=f"Inference error: {type(e).__name__}. Layer excluded.",
        )

    # ── Step 7: Classify result ────────────────────────────────────────────────
    score = 1.0 if p_genuine >= GENUINE_THRESHOLD else 0.0

    # Gyroscope-absent devices get reduced weight (less precise motion analysis)
    gyro_available = getattr(claim, "gyroscope_available", True)
    weight = DEFAULT_WEIGHT if gyro_available else REDUCED_WEIGHT
    grace  = not gyro_available  # Grace flag if gyro absent

    # Build human-readable reason for audit trail
    variance_delta = variance_current - variance_prior
    if score == 1.0:
        if variance_delta < -0.3:
            pattern = "sudden shelter-taking detected (high prior → low current)"
        else:
            pattern = "gradual deceleration consistent with disruption"
        reason = (
            f"Genuine — P(genuine)={p_genuine:.3f} >= {GENUINE_THRESHOLD}. "
            f"Pattern: {pattern}. "
            f"Prior variance={variance_prior:.3f}, Current={variance_current:.3f}."
        )
    else:
        if variance_prior < 0.12 and variance_current < 0.12:
            pattern = "prolonged static — no delivery activity detected"
        elif variance_current > variance_prior + 0.05:
            pattern = "reverse delta — possible spoof app activation"
        else:
            pattern = "near-zero delta — no disruption event in motion data"
        reason = (
            f"Suspicious — P(genuine)={p_genuine:.3f} < {GENUINE_THRESHOLD}. "
            f"Pattern: {pattern}. "
            f"Prior variance={variance_prior:.3f}, Current={variance_current:.3f}."
        )

    return LayerResult(
        layer_name=LAYER_ID,
        available=True,
        score=score,
        weight=weight,
        confidence=p_genuine,
        grace_flag=grace,
        reason=reason,
        metadata={
            "p_genuine": round(p_genuine, 4),
            "p_fraud": round(1 - p_genuine, 4),
            "variance_prior": variance_prior,
            "variance_current": variance_current,
            "variance_delta": round(variance_current - variance_prior, 4),
            "gyroscope_available": gyro_available,
            "threshold_used": GENUINE_THRESHOLD,
            "model_version": _model_meta.get("model_version") if _model_meta else "unknown",
        }
    )


# ── Convenience function for testing ──────────────────────────────────────────
def score_raw(
    variance_prior: float,
    variance_current: float,
    gyroscope_available: bool = True,
    is_mock_location: bool = False,
) -> LayerResult:
    """
    Test the inertial layer without a full ClaimVector.
    Useful for unit tests and direct scripting.

    Usage:
        from geotruth.layers.inertial import score_raw
        result = score_raw(variance_prior=0.8, variance_current=0.05)
        print(result.score, result.reason)
    """
    class _MinimalClaim:
        pass

    claim = _MinimalClaim()
    claim.variance_1h_to_30m_ago = variance_prior
    claim.variance_last_30m      = variance_current
    claim.gyroscope_available    = gyroscope_available
    claim.is_mock_location       = is_mock_location

    return score_inertial_layer(claim)

