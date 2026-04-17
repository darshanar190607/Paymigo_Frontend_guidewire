"""
GeoTruth — End-to-End Integration Test
=======================================
Tests the full pipeline via GeoTruthEngine across 5 real-world scenarios.

Run:
    python examples/test_end_to_end.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from geotruth import GeoTruthEngine, ClaimVector, WorkerProfile

BASE_TS = 1711900000
engine  = GeoTruthEngine()


# ── Claim factories ────────────────────────────────────────────────────────────

def make_genuine_storm_worker() -> ClaimVector:
    """Scenario 1: Genuine Chennai worker caught in cyclonic storm."""
    return ClaimVector(
        worker_id="W-GENUINE-001",
        claimed_pincode="600001",
        timestamp=BASE_TS,
        has_barometer=True,
        has_microphone=True,
        connection_type="4G",
        device_barometer_hpa=991.5,
        acoustic_feature_vector=[0.82, 0.21, 0.04, 0.02, 0.01],
        cell_tower_ids=["404-20-12345", "404-20-12346", "404-45-1001"],
        wifi_ssid_hashes=["a3f2c1d4", "9c1b2e3f"],
        variance_1h_to_30m_ago=0.623,
        variance_last_30m=0.047,
        gyroscope_available=True,
        is_mock_location=False,
        screen_unlock_count_1h=3,
    )


def make_solo_fraud() -> ClaimVector:
    """Scenario 2: Solo fraud actor using GPS spoofing app from home."""
    return ClaimVector(
        worker_id="W-FRAUD-001",
        claimed_pincode="600001",
        timestamp=BASE_TS,
        has_barometer=True,
        has_microphone=True,
        connection_type="WiFi",
        device_barometer_hpa=1013.2,
        acoustic_feature_vector=[0.01, 0.02, 0.03, 0.88, 0.12],
        cell_tower_ids=["404-20-99001"],
        wifi_ssid_hashes=["home_router_hash"],
        variance_1h_to_30m_ago=0.012,
        variance_last_30m=0.008,
        gyroscope_available=True,
        is_from_mock_provider=True,
        is_mock_location=True,
        screen_unlock_count_1h=1,
    )


def make_budget_phone_genuine() -> ClaimVector:
    """Scenario 3: Genuine worker on ₹5,000 Redmi — no barometer, no mic."""
    return ClaimVector(
        worker_id="W-BUDGET-001",
        claimed_pincode="641601",
        timestamp=BASE_TS,
        has_barometer=False,
        has_microphone=False,
        connection_type="2G",
        device_barometer_hpa=None,
        acoustic_feature_vector=None,
        cell_tower_ids=["404-20-15001", "404-45-15002"],
        wifi_ssid_hashes=[],
        variance_1h_to_30m_ago=0.558,
        variance_last_30m=0.731,
        gyroscope_available=False,
        is_mock_location=False,
        screen_unlock_count_1h=2,
    )


def make_ring_fraud() -> ClaimVector:
    """Scenario 4: Ring fraud member — high burst rate passed at verify time."""
    return ClaimVector(
        worker_id="W-RING-042",
        claimed_pincode="560001",
        timestamp=BASE_TS,
        has_barometer=True,
        has_microphone=True,
        connection_type="4G",
        device_barometer_hpa=1011.8,
        acoustic_feature_vector=[0.02, 0.03, 0.05, 0.84, 0.09],
        cell_tower_ids=["404-20-88001"],
        wifi_ssid_hashes=["ring_member_wifi"],
        variance_1h_to_30m_ago=0.014,
        variance_last_30m=0.011,
        gyroscope_available=True,
        is_mock_location=False,
        screen_unlock_count_1h=1,
    )


def make_ambiguous_genuine() -> ClaimVector:
    """Scenario 5: Genuine worker at zone boundary — mixed signals."""
    return ClaimVector(
        worker_id="W-AMBIGUOUS-001",
        claimed_pincode="560034",
        timestamp=BASE_TS,
        has_barometer=True,
        has_microphone=True,
        connection_type="4G",
        device_barometer_hpa=1002.1,
        acoustic_feature_vector=[0.35, 0.18, 0.22, 0.19, 0.08],
        cell_tower_ids=["404-20-60001"],
        wifi_ssid_hashes=[],
        variance_1h_to_30m_ago=0.391,
        variance_last_30m=0.243,
        gyroscope_available=True,
        is_mock_location=False,
        screen_unlock_count_1h=5,
    )


# ── Display helpers ────────────────────────────────────────────────────────────

def print_banner(title: str):
    print(f"\n{'═' * 62}")
    print(f"  {title}")
    print(f"{'═' * 62}")


def print_result(result):
    tier_icons = {
        "auto_approve":   "✅",
        "passive_enrich": "🔄",
        "soft_proof":     "⚠️ ",
        "human_review":   "🔍",
        "ring_alert":     "🚨",
        "FROZEN":         "🔒",
    }
    icon = tier_icons.get(result.tier, "❓")
    print(f"\n  {icon}  Tier            : {result.tier}")
    print(f"  📊  Coherence Score : {result.coherence_score}/100")
    print(f"  🎯  Confidence      : {result.confidence:.0%}")
    print(f"  💬  Recommendation  : {result.recommendation}")
    if result.flagged_signals:
        print(f"  🚩  Flagged         : {', '.join(result.flagged_signals)}")
    if result.sensor_gaps:
        print(f"  ⬜  Sensor Gaps     : {', '.join(result.sensor_gaps)}")


# ── Scenario runner ────────────────────────────────────────────────────────────

def run_scenario(label: str, claim: ClaimVector, burst_rate: float = 0.0,
                 profile: WorkerProfile = None):
    print_banner(f"Scenario: {label}")
    print(f"  Worker  : {claim.worker_id}")
    print(f"  Pincode : {claim.claimed_pincode}")
    print(f"  Mock GPS: {claim.is_from_mock_provider}")

    result = engine.verify(claim, profile=profile, claim_burst_rate=burst_rate)
    print_result(result)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🛡️  GeoTruth — End-to-End Integration Test")
    print("=" * 62)

    run_scenario(
        "Genuine Worker in Storm (Full Sensors)",
        make_genuine_storm_worker(),
        burst_rate=7.0,   # Moderate zone burst — validates real event (L5)
        profile=WorkerProfile(
            worker_id="W-GENUINE-001",
            baseline_accelerometer_variance=0.5,
            historical_fraud_flags=0,
        ),
    )

    run_scenario(
        "Solo Fraud — Mock GPS + Indoor",
        make_solo_fraud(),
        burst_rate=0.5,
    )

    run_scenario(
        "Budget Phone Genuine Worker",
        make_budget_phone_genuine(),
        burst_rate=6.0,
    )

    run_scenario(
        "Ring Fraud Member (Telegram burst=18/min)",
        make_ring_fraud(),
        burst_rate=18.0,  # Triggers L7 ring_alert override
    )

    run_scenario(
        "Ambiguous Genuine (Zone Boundary)",
        make_ambiguous_genuine(),
        burst_rate=2.0,
    )

    print(f"\n{'═' * 62}")
    print("  All scenarios complete.")
    print(f"{'═' * 62}\n")
