"""
GeoTruth — Core Engine
======================
The single entry point for the geotruth package.

Usage:
    from geotruth import GeoTruthEngine, ClaimVector

    engine = GeoTruthEngine()
    result = engine.verify(claim)

    # result.coherence_score  → 0–100
    # result.tier             → "auto_approve" | "passive_enrich" | "soft_proof"
    #                           "human_review" | "ring_alert" | "FROZEN"
    # result.flagged_signals  → ["mock_location_detected", ...]
    # result.sensor_gaps      → ["barometer_absent", ...]
    # result.recommendation   → "APPROVE" | "ENRICH" | "SOFT_PROOF" | "REVIEW" | "FREEZE"
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np

from geotruth.schemas import ClaimVector, LayerResult, ScoringResult, WorkerProfile
from geotruth.layers.barometric import evaluate as _evaluate_barometric, evaluate_sync as _evaluate_barometric_sync
from geotruth.layers.acoustic import score_acoustic_layer
from geotruth.layers.network import score_network_layer
from geotruth.layers.inertial import score_inertial_layer
from geotruth.layers.zone import score_zone_layer
from geotruth.layers.baseline import score_baseline_layer
from geotruth.layers.social import score_social_ring_layer

logger = logging.getLogger(__name__)

# ── Model paths ────────────────────────────────────────────────────────────────
_MODELS_DIR = Path(__file__).parent / "models"
_COHERENCE_MODEL_PATH = _MODELS_DIR / "xgb_coherence_v1.json"

# ── Coherence feature column order — MUST match train_coherence.py ─────────────
_FEATURE_COLUMNS = [
    "l1_baro_score",
    "l2_acoustic_score",
    "l3_network_score",
    "l4_inertial_score",
    "l1_baro_available",
    "l2_acoustic_available",
    "l3_network_available",
    "l4_inertial_available",
    "mock_flag",
    "claim_burst_rate",
    "baseline_deviation",
    "available_sensor_count",
    "available_layer_mean_score",
    "max_score",
    "min_score",
    "score_variance",
    "mock_x_inertial",
    "burst_x_deviation",
]

# ── Tier thresholds (p_genuine from coherence model) ──────────────────────────
# Mapped from the ideation doc's 5-tier UX workflow.
# p_genuine is inverted from coherence_score: high p_genuine = low suspicion.
_TIER_AUTO_APPROVE   = 0.80   # Score 0–35  in doc  → p_genuine >= 0.80
_TIER_PASSIVE_ENRICH = 0.60   # Score 36–55 in doc  → p_genuine >= 0.60
_TIER_SOFT_PROOF     = 0.40   # Score 56–74 in doc  → p_genuine >= 0.40
_TIER_HUMAN_REVIEW   = 0.20   # Score 75–100 in doc → p_genuine >= 0.20
# Below 0.20 → ring_alert

# ── Ring burst threshold ───────────────────────────────────────────────────────
# If claim_burst_rate exceeds this, override tier to ring_alert regardless of
# p_genuine. Matches ideation doc: "20+ claims in 4 min → RING ALERT".
_RING_BURST_THRESHOLD = 15.0


class GeoTruthEngine:
    """
    Multi-Modal Environmental Coherence Verifier.

    Loads both XGBoost models once at instantiation and keeps them in memory.
    Thread-safe for single-worker uvicorn. For multi-worker deployments,
    instantiate inside a FastAPI lifespan event and share via app.state.

    Parameters
    ----------
    coherence_model_path : Path, optional
        Override path to xgb_coherence_v1.json. Defaults to the bundled model.
    claim_burst_rate : float, optional
        Claims-per-minute for the current pincode zone. Passed in at verify()
        time by the platform layer. Defaults to 0.0 (unknown).
    baseline_deviation : float, optional
        Worker's deviation from their personal behavioral baseline (0–1).
        Passed in at verify() time. Defaults to 0.0 (unknown / new worker).
    """

    def __init__(
        self,
        coherence_model_path: Optional[Path] = None,
    ) -> None:
        self._coherence_model = None
        self._coherence_model_path = coherence_model_path or _COHERENCE_MODEL_PATH
        self._load_coherence_model()

    # ── Model loading ──────────────────────────────────────────────────────────

    def _load_coherence_model(self) -> None:
        """Load the master coherence XGBoost model. Logs a warning if missing."""
        try:
            import xgboost as xgb
        except ImportError:
            logger.error("xgboost not installed. Run: pip install xgboost")
            return

        if not self._coherence_model_path.exists():
            logger.warning(
                f"Coherence model not found at {self._coherence_model_path}. "
                "Engine will fall back to weighted heuristic scoring. "
                "Train the model: python -m geotruth.training.train_coherence"
            )
            return

        try:
            model = xgb.XGBClassifier()
            model.load_model(str(self._coherence_model_path))
            self._coherence_model = model
            logger.info(f"Coherence model loaded from {self._coherence_model_path}")
        except Exception as exc:
            logger.error(f"Coherence model load failed: {exc}")

    # ── Public entry point ─────────────────────────────────────────────────────

    def verify(
        self,
        claim: ClaimVector,
        profile: Optional[WorkerProfile] = None,
        claim_burst_rate: float = 0.0,
    ) -> ScoringResult:
        """
        Run all 7 detection layers synchronously and return a ScoringResult.
        Use this for CLI, scripts, and unit tests.
        FastAPI endpoints must call verify_async() to avoid event loop conflicts.

        Parameters
        ----------
        claim : ClaimVector
            The incoming claim payload from the mobile client.
        profile : WorkerProfile, optional
            Worker's historical behavioral profile. None for new workers.
        claim_burst_rate : float
            Claims per minute for this pincode zone (L5/L7 signal).
        """
        sensor_gaps: list[str] = []
        flagged_signals: list[str] = []

        if claim.is_from_mock_provider:
            flagged_signals.append("mock_location_detected")
            return ScoringResult(
                coherence_score=10,
                confidence=0.99,
                tier="FROZEN",
                flagged_signals=flagged_signals,
                sensor_gaps=sensor_gaps,
                recommendation="FREEZE",
            )

        # L1–L4: device sensor layers
        baro_result     = _evaluate_barometric_sync(claim)
        acoustic_result = score_acoustic_layer(claim)
        network_result  = score_network_layer(claim)
        inertial_result = score_inertial_layer(claim)
        # L5–L7: platform / social layers
        zone_result     = score_zone_layer(claim_burst_rate)
        baseline_result = score_baseline_layer(claim, profile)
        social_result   = score_social_ring_layer(claim_burst_rate)

        return self._build_result(
            claim, sensor_gaps, flagged_signals,
            baro_result, acoustic_result, network_result, inertial_result,
            zone_result, baseline_result, social_result,
            claim_burst_rate,
        )

    # ── Internal scoring ───────────────────────────────────────────────────────

    def _score(
        self,
        layers: list[LayerResult],
        mock_flag: int,
        claim_burst_rate: float,
        baseline_deviation: float,
    ) -> float:
        """
        Return p_genuine (0–1) using the coherence XGBoost model.
        Falls back to a weighted heuristic if the model is not loaded.
        """
        baro, acoustic, network, inertial = layers

        l1_score = baro.score     * int(baro.available)
        l2_score = acoustic.score * int(acoustic.available)
        l3_score = network.score  * int(network.available)
        l4_score = inertial.score * int(inertial.available)

        avail_flags = [
            int(baro.available),
            int(acoustic.available),
            int(network.available),
            int(inertial.available),
        ]
        score_vals = [l1_score, l2_score, l3_score, l4_score]
        avail_count = sum(avail_flags)

        if self._coherence_model is not None:
            row = {
                "l1_baro_score":           l1_score,
                "l2_acoustic_score":       l2_score,
                "l3_network_score":        l3_score,
                "l4_inertial_score":       l4_score,
                "l1_baro_available":       float(avail_flags[0]),
                "l2_acoustic_available":   float(avail_flags[1]),
                "l3_network_available":    float(avail_flags[2]),
                "l4_inertial_available":   float(avail_flags[3]),
                "mock_flag":               float(mock_flag),
                "claim_burst_rate":        float(claim_burst_rate),
                "baseline_deviation":      float(baseline_deviation),
                "available_sensor_count":  float(avail_count),
                "available_layer_mean_score": (
                    sum(score_vals) / max(avail_count, 1)
                ),
                "max_score":      max(score_vals),
                "min_score":      min(score_vals),
                "score_variance": float(np.var(score_vals)),
                "mock_x_inertial":   float(mock_flag) * l4_score,
                "burst_x_deviation": float(claim_burst_rate) * float(baseline_deviation),
            }
            X = np.array(
                [row[col] for col in _FEATURE_COLUMNS], dtype=np.float32
            ).reshape(1, -1)
            try:
                return float(self._coherence_model.predict_proba(X)[0][1])
            except Exception as exc:
                logger.error(f"Coherence model inference failed: {exc}. Using heuristic.")

        # Heuristic fallback — weighted mean using each layer's declared weight
        if avail_count == 0:
            return 0.5
        weighted_sum = (
            (baro.score    * baro.weight    * int(baro.available)) +
            (acoustic.score * acoustic.weight * int(acoustic.available)) +
            (network.score  * network.weight  * int(network.available)) +
            (inertial.score * inertial.weight * int(inertial.available))
        )
        total_weight = sum(
            layer.weight for layer in [baro, acoustic, network, inertial]
            if layer.available
        )
        return weighted_sum / total_weight if total_weight > 0 else 0.5

    async def verify_async(
        self,
        claim: ClaimVector,
        profile: Optional[WorkerProfile] = None,
        claim_burst_rate: float = 0.0,
    ) -> ScoringResult:
        """
        Async variant of verify() — use this inside FastAPI endpoints.
        Awaits the barometric layer directly instead of spawning a new loop.
        """
        sensor_gaps: list[str] = []
        flagged_signals: list[str] = []

        if claim.is_from_mock_provider:
            flagged_signals.append("mock_location_detected")
            return ScoringResult(
                coherence_score=10,
                confidence=0.99,
                tier="FROZEN",
                flagged_signals=flagged_signals,
                sensor_gaps=sensor_gaps,
                recommendation="FREEZE",
            )

        baro_result     = await _evaluate_barometric(claim)
        acoustic_result = score_acoustic_layer(claim)
        network_result  = score_network_layer(claim)
        inertial_result = score_inertial_layer(claim)
        zone_result     = score_zone_layer(claim_burst_rate)
        baseline_result = score_baseline_layer(claim, profile)
        social_result   = score_social_ring_layer(claim_burst_rate)

        return self._build_result(
            claim, sensor_gaps, flagged_signals,
            baro_result, acoustic_result, network_result, inertial_result,
            zone_result, baseline_result, social_result,
            claim_burst_rate,
        )

    def _build_result(
        self,
        claim: ClaimVector,
        sensor_gaps: list[str],
        flagged_signals: list[str],
        baro_result: LayerResult,
        acoustic_result: LayerResult,
        network_result: LayerResult,
        inertial_result: LayerResult,
        zone_result: LayerResult,
        baseline_result: LayerResult,
        social_result: LayerResult,
        claim_burst_rate: float,
    ) -> ScoringResult:
        """Shared result-building logic used by both verify() and verify_async()."""

        # ── Sensor gap collection ─────────────────────────────────────────────
        if baro_result.grace_flag:
            sensor_gaps.append("barometer_absent")
        if acoustic_result.grace_flag:
            sensor_gaps.append("mic_permission_missing")
        if inertial_result.grace_flag:
            sensor_gaps.append("motion_permission_missing")
        if baseline_result.grace_flag:
            sensor_gaps.append("worker_profile_absent")

        # ── L7 hard override — ring detected before XGBoost runs ──────────────
        if social_result.score == 0.0:
            flagged_signals.append("social_ring_detected")
            return ScoringResult(
                coherence_score=95,
                confidence=0.97,
                tier="ring_alert",
                flagged_signals=flagged_signals,
                sensor_gaps=sensor_gaps,
                recommendation="FREEZE",
            )

        # ── Derive baseline_deviation from L6 for coherence model ─────────────
        # L6 score is already normalised to [0,1] where 1=no deviation.
        # Invert it so 0=no deviation, 1=max deviation (matches training data).
        baseline_deviation = round(1.0 - baseline_result.score, 4) if baseline_result.available else 0.0

        # ── XGBoost coherence scoring (L1–L4 only — matches training features) ─
        core_layers = [baro_result, acoustic_result, network_result, inertial_result]
        p_genuine = self._score(
            layers=core_layers,
            mock_flag=int(claim.is_mock_location),
            claim_burst_rate=claim_burst_rate,
            baseline_deviation=baseline_deviation,
        )

        # ── Blend L5 zone signal into p_genuine ───────────────────────────────
        # Zone coherence is a soft boost/penalty on top of the model output.
        # Weight: 10% influence so it can't override a strong model signal alone.
        if zone_result.available:
            p_genuine = round(p_genuine * 0.90 + zone_result.score * 0.10, 4)

        coherence_score = int((1.0 - p_genuine) * 100)

        tier, recommendation = self._classify_tier(
            p_genuine=p_genuine,
            claim_burst_rate=claim_burst_rate,
            flagged_signals=flagged_signals,
        )
        # Confidence drops only for missing HARDWARE sensors, not platform data gaps.
        # worker_profile_absent is a platform gap — excluded from this check.
        hardware_gaps = [g for g in sensor_gaps if g != "worker_profile_absent"]
        confidence = 0.95 if not hardware_gaps else 0.70

        return ScoringResult(
            coherence_score=coherence_score,
            confidence=confidence,
            tier=tier,
            flagged_signals=flagged_signals,
            sensor_gaps=sensor_gaps,
            recommendation=recommendation,
        )

    @staticmethod
    def _classify_tier(
        p_genuine: float,
        claim_burst_rate: float,
        flagged_signals: list[str],
    ) -> tuple[str, str]:
        """
        Map p_genuine + burst signals to the 5-tier ideation workflow.

        Returns (tier, recommendation).
        """
        # Ring alert overrides everything — burst rate is the L7 proxy signal
        if claim_burst_rate >= _RING_BURST_THRESHOLD or "claim_burst_ring_alert" in flagged_signals:
            return "ring_alert", "FREEZE"

        if p_genuine >= _TIER_AUTO_APPROVE:
            return "auto_approve", "APPROVE"
        if p_genuine >= _TIER_PASSIVE_ENRICH:
            return "passive_enrich", "ENRICH"
        if p_genuine >= _TIER_SOFT_PROOF:
            return "soft_proof", "SOFT_PROOF"
        if p_genuine >= _TIER_HUMAN_REVIEW:
            return "human_review", "REVIEW"

        return "ring_alert", "FREEZE"
