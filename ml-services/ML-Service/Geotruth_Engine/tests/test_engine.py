"""
GeoTruth — pytest Suite
========================
Final gatekeeper tests for the geotruth package.

Run:
    cd "Hackathon Projects/Geotruth"
    pytest tests/test_engine.py -v

The engine safely falls back to heuristic scoring when XGBoost models are
not present (CI/CD environments), so all tests pass without trained models.
"""

import pytest
from geotruth import GeoTruthEngine, ClaimVector, WorkerProfile

# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine() -> GeoTruthEngine:
    """
    Single engine instance shared across all tests in this module.
    Models load once; falls back to heuristic if not trained yet.
    """
    return GeoTruthEngine()


@pytest.fixture
def genuine_claim() -> ClaimVector:
    """Full-sensor genuine Chennai worker caught in a cyclonic storm."""
    return ClaimVector(
        worker_id="W-TEST-GENUINE",
        claimed_pincode="600001",
        timestamp=1711900000,
        device_barometer_hpa=991.5,
        has_barometer=True,
        acoustic_feature_vector=[0.85, 0.22, 0.04, 0.02, 0.01],
        has_microphone=True,
        variance_1h_to_30m_ago=0.82,
        variance_last_30m=0.04,
        gyroscope_available=True,
        cell_tower_ids=["404-20-12345", "404-20-12346", "404-45-1001"],
        wifi_ssid_hashes=["a3f2c1d4", "9c1b2e3f"],
        is_from_mock_provider=False,
        is_mock_location=False,
        connection_type="4G",
        screen_unlock_count_1h=3,
    )


@pytest.fixture
def budget_phone_claim() -> ClaimVector:
    """Genuine worker on a ₹5,000 Redmi — no barometer, no mic, no WiFi."""
    return ClaimVector(
        worker_id="W-TEST-BUDGET",
        claimed_pincode="641601",
        timestamp=1711900000,
        device_barometer_hpa=None,
        has_barometer=False,
        acoustic_feature_vector=None,
        has_microphone=False,
        variance_1h_to_30m_ago=0.73,
        variance_last_30m=0.05,
        gyroscope_available=False,
        cell_tower_ids=["404-20-15001", "404-45-15002"],
        wifi_ssid_hashes=[],
        is_from_mock_provider=False,
        is_mock_location=False,
        connection_type="2G",
    )


@pytest.fixture
def mock_gps_claim() -> ClaimVector:
    """Fraud actor — Android OS reports isFromMockProvider=True."""
    return ClaimVector(
        worker_id="W-TEST-FRAUD",
        claimed_pincode="560001",
        timestamp=1711900000,
        device_barometer_hpa=1013.2,
        has_barometer=True,
        acoustic_feature_vector=[0.01, 0.02, 0.03, 0.88, 0.12],
        has_microphone=True,
        variance_1h_to_30m_ago=0.008,
        variance_last_30m=0.006,
        gyroscope_available=True,
        cell_tower_ids=["404-20-99001"],
        wifi_ssid_hashes=["home_router_hash"],
        is_from_mock_provider=True,
        is_mock_location=True,
        connection_type="WiFi",
    )


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestGenuineClaim:
    def test_auto_approve_tier(self, engine, genuine_claim):
        """
        Full sensors + genuine motion pattern + clean profile.
        Without a trained coherence model, the heuristic weighted scorer
        should place this in one of the two top tiers (auto_approve or
        passive_enrich). The live barometric API reading may vary, so we
        accept both. With a trained model this will consistently be auto_approve.
        """
        clean_profile = WorkerProfile(
            worker_id="W-TEST-GENUINE",
            baseline_accelerometer_variance=0.05,
            historical_fraud_flags=0,
        )
        result = engine.verify(genuine_claim, profile=clean_profile, claim_burst_rate=0.0)

        assert result.tier in ("auto_approve", "passive_enrich"), (
            f"Expected auto_approve or passive_enrich, got {result.tier}. "
            f"Score={result.coherence_score}, recommendation={result.recommendation}"
        )
        assert result.recommendation in ("APPROVE", "ENRICH")
        assert result.coherence_score <= 55

    def test_no_flagged_signals(self, engine, genuine_claim):
        result = engine.verify(genuine_claim, claim_burst_rate=0.0)
        assert "mock_location_detected" not in result.flagged_signals
        assert "social_ring_detected" not in result.flagged_signals

    def test_no_hardware_sensor_gaps(self, engine, genuine_claim):
        """Full-sensor claim must have no hardware gaps (barometer/mic/motion)."""
        result = engine.verify(genuine_claim, claim_burst_rate=0.0)
        assert "barometer_absent" not in result.sensor_gaps
        assert "mic_permission_missing" not in result.sensor_gaps
        assert "motion_permission_missing" not in result.sensor_gaps

    def test_high_confidence(self, engine, genuine_claim):
        """Hardware sensors all present — confidence must be 0.95."""
        result = engine.verify(genuine_claim, claim_burst_rate=0.0)
        assert result.confidence == 0.95


class TestBudgetPhoneGracefulDegradation:
    def test_does_not_crash(self, engine, budget_phone_claim):
        """Must not raise any exception — graceful degradation is a core promise."""
        result = engine.verify(budget_phone_claim, claim_burst_rate=0.0)
        assert result is not None

    def test_barometer_grace_flag(self, engine, budget_phone_claim):
        result = engine.verify(budget_phone_claim, claim_burst_rate=0.0)
        assert "barometer_absent" in result.sensor_gaps

    def test_mic_grace_flag(self, engine, budget_phone_claim):
        result = engine.verify(budget_phone_claim, claim_burst_rate=0.0)
        assert "mic_permission_missing" in result.sensor_gaps

    def test_reduced_confidence(self, engine, budget_phone_claim):
        """Sensor gaps must reduce confidence to 0.70."""
        result = engine.verify(budget_phone_claim, claim_burst_rate=0.0)
        assert result.confidence == 0.70

    def test_not_frozen(self, engine, budget_phone_claim):
        """Budget phone worker must never be auto-frozen — grace-first principle."""
        result = engine.verify(budget_phone_claim, claim_burst_rate=0.0)
        assert result.tier != "FROZEN"
        assert result.tier != "ring_alert"


class TestMockGpsInstantFreeze:
    def test_tier_is_frozen(self, engine, mock_gps_claim):
        result = engine.verify(mock_gps_claim, claim_burst_rate=0.0)
        assert result.tier == "FROZEN"

    def test_recommendation_is_freeze(self, engine, mock_gps_claim):
        result = engine.verify(mock_gps_claim, claim_burst_rate=0.0)
        assert result.recommendation == "FREEZE"

    def test_mock_flag_in_signals(self, engine, mock_gps_claim):
        result = engine.verify(mock_gps_claim, claim_burst_rate=0.0)
        assert "mock_location_detected" in result.flagged_signals

    def test_short_circuits_before_layers(self, engine, mock_gps_claim):
        """
        is_from_mock_provider=True must short-circuit immediately.
        Coherence score should be the hardcoded penalty value (10), not
        a model-computed value.
        """
        result = engine.verify(mock_gps_claim, claim_burst_rate=0.0)
        assert result.coherence_score == 10
        assert result.confidence == 0.99


class TestSocialRingAttack:
    def test_ring_alert_tier(self, engine, genuine_claim):
        """
        Even a genuine-looking claim must be ring_alert when burst rate
        exceeds the L7 threshold. L7 overrides XGBoost output.
        """
        result = engine.verify(genuine_claim, claim_burst_rate=18.0)
        assert result.tier in ("ring_alert", "FROZEN"), (
            f"Expected ring_alert or FROZEN, got {result.tier}"
        )

    def test_freeze_recommendation(self, engine, genuine_claim):
        result = engine.verify(genuine_claim, claim_burst_rate=18.0)
        assert result.recommendation == "FREEZE"

    def test_social_ring_in_flagged_signals(self, engine, genuine_claim):
        result = engine.verify(genuine_claim, claim_burst_rate=18.0)
        assert "social_ring_detected" in result.flagged_signals

    def test_below_threshold_is_not_ring(self, engine, genuine_claim):
        """Burst rate of 5.0 is a genuine zone event — must not trigger ring alert."""
        result = engine.verify(genuine_claim, claim_burst_rate=5.0)
        assert result.tier != "ring_alert"
        assert "social_ring_detected" not in result.flagged_signals


class TestWorkerProfileBaselinePenalty:
    def test_fraud_flags_lower_score(self, engine, genuine_claim):
        """
        A worker with 2 historical fraud flags should produce a higher
        coherence_score (more suspicious) than a clean worker.
        """
        clean_profile = WorkerProfile(
            worker_id="W-TEST-GENUINE",
            baseline_accelerometer_variance=0.5,
            historical_fraud_flags=0,
        )
        flagged_profile = WorkerProfile(
            worker_id="W-TEST-GENUINE",
            baseline_accelerometer_variance=0.5,
            historical_fraud_flags=2,
        )

        clean_result   = engine.verify(genuine_claim, profile=clean_profile,   claim_burst_rate=0.0)
        flagged_result = engine.verify(genuine_claim, profile=flagged_profile, claim_burst_rate=0.0)

        assert flagged_result.coherence_score >= clean_result.coherence_score, (
            f"Fraud flags should raise suspicion. "
            f"Clean={clean_result.coherence_score}, Flagged={flagged_result.coherence_score}"
        )

    def test_no_profile_applies_grace(self, engine, genuine_claim):
        """No profile → worker_profile_absent in sensor_gaps."""
        result = engine.verify(genuine_claim, profile=None, claim_burst_rate=0.0)
        assert "worker_profile_absent" in result.sensor_gaps

    def test_profile_with_matching_variance_scores_well(self, engine, genuine_claim):
        """
        Profile baseline matches claim variance → minimal deviation → high L6 score.
        genuine_claim has variance_last_30m=0.04, so set baseline close to that.
        Must not land in the two worst tiers.
        """
        matching_profile = WorkerProfile(
            worker_id="W-TEST-GENUINE",
            baseline_accelerometer_variance=0.05,
            historical_fraud_flags=0,
        )
        result = engine.verify(genuine_claim, profile=matching_profile, claim_burst_rate=0.0)
        assert result.tier not in ("human_review", "ring_alert", "FROZEN")


class TestNetworkWifiBoost:
    def test_wifi_boost_applied(self):
        """Two WiFi hashes on top of 2 towers should produce score=1.0."""
        from geotruth.layers.network import score_network_layer

        claim = ClaimVector(
            worker_id="W-NET-TEST",
            claimed_pincode="600001",
            timestamp=1711900000,
            cell_tower_ids=["tower-1", "tower-2"],
            wifi_ssid_hashes=["hash-a", "hash-b"],
        )
        result = score_network_layer(claim)
        assert result.score == 1.0
        assert "WiFi environment validated" in result.reason
        assert result.metadata["wifi_boost_applied"] is True

    def test_single_wifi_no_boost(self):
        """Only 1 WiFi hash — boost threshold not met."""
        from geotruth.layers.network import score_network_layer

        claim = ClaimVector(
            worker_id="W-NET-TEST",
            claimed_pincode="600001",
            timestamp=1711900000,
            cell_tower_ids=["tower-1", "tower-2"],
            wifi_ssid_hashes=["hash-a"],
        )
        result = score_network_layer(claim)
        assert result.score == 1.0                          # base score from 2 towers
        assert result.metadata["wifi_boost_applied"] is False

    def test_single_tower_with_wifi_boost(self):
        """1 tower (score=0.5) + 2 WiFi hashes → score=0.7."""
        from geotruth.layers.network import score_network_layer

        claim = ClaimVector(
            worker_id="W-NET-TEST",
            claimed_pincode="600001",
            timestamp=1711900000,
            cell_tower_ids=["tower-1"],
            wifi_ssid_hashes=["hash-a", "hash-b"],
        )
        result = score_network_layer(claim)
        assert result.score == pytest.approx(0.7, abs=0.001)
        assert result.metadata["wifi_boost_applied"] is True
