"""
GeoTruth — Coherence Training Data Generator
=============================================
Generates 10,000 synthetic rows representing the aggregated outputs of the
four GeoTruth detection layers (L1–L4), plus derived flags.

Each row represents a single insurance claim verification event.

Output: geotruth/models/coherence_training.csv

Columns:
    l1_baro_score      — Barometric coherence (0–1)
    l1_baro_available  — Device had barometer (bool)
    l2_acoustic_score  — Acoustic coherence (0–1)
    l2_acoustic_available — Device had microphone (bool)
    l3_network_score   — Cell tower/WiFi coherence (0–1)
    l3_network_available — Network data present (bool)
    l4_inertial_score  — Motion pattern coherence (0–1)
    l4_inertial_available — IMU data present (bool)
    mock_flag          — Android isFromMockProvider flag (bool)
    claim_burst_rate   — Claims per pincode per minute (float)
    baseline_deviation — Deviation from personal baseline (0–1)
    is_genuine         — Ground truth label (1=genuine, 0=fraud)

Run:
    python geotruth/training/generate_coherence.py
"""

import os
import numpy as np
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("generate_coherence")

RANDOM_SEED = 42
N_SAMPLES   = 10_000

OUTPUT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "models", "coherence_training.csv")
)

rng = np.random.default_rng(RANDOM_SEED)


# ── Archetype Generators ───────────────────────────────────────────────────────

def _genuine_worker(n: int) -> dict:
    """
    Simulate a real worker caught in a genuine disruption event.
    High scores across all available layers, no mock flag.
    """
    # ~30% of genuine workers have budget phones without barometer
    has_baro = rng.random(n) > 0.30
    # ~20% of genuine workers have no mic permission
    has_mic  = rng.random(n) > 0.20

    l1_score = np.where(
        has_baro,
        rng.beta(8, 2, n),     # Skewed high (genuine pressure match)
        0.0                     # Not available
    )
    l2_score = np.where(
        has_mic,
        rng.beta(7, 2, n),     # Mostly high (genuine rain/wind acoustic)
        0.0
    )
    l3_score = rng.beta(7, 2, n)     # Cell towers almost always genuine
    l4_score = rng.beta(8, 2, n)     # Motion is strong signal for genuine

    # Network always available; small chance of poor signal
    has_network = rng.random(n) > 0.05

    # Burst rate: genuine workers trickle in (low burst)
    burst = rng.exponential(0.8, n)    # Claims per minute, mostly <3

    # Baseline deviation: genuine workers work their usual routes
    deviation = rng.beta(2, 8, n)     # Skewed low

    return {
        "l1_baro_score":           l1_score,
        "l1_baro_available":       has_baro.astype(int),
        "l2_acoustic_score":       l2_score,
        "l2_acoustic_available":   has_mic.astype(int),
        "l3_network_score":        l3_score,
        "l3_network_available":    has_network.astype(int),
        "l4_inertial_score":       l4_score,
        "l4_inertial_available":   np.ones(n, dtype=int),
        "mock_flag":               np.zeros(n, dtype=int),
        "claim_burst_rate":        burst,
        "baseline_deviation":      deviation,
        "is_genuine":              np.ones(n, dtype=int),
    }


def _solo_fraud(n: int) -> dict:
    """
    Simulate a solo fraud actor using a GPS spoofing app at home.
    Mock flag is ON. Low sensor coherence (indoor conditions).
    """
    has_baro = rng.random(n) > 0.4   # May have barometer but shows indoor pressure
    has_mic  = rng.random(n) > 0.3

    l1_score = np.where(
        has_baro,
        rng.beta(2, 8, n),     # Low — indoor ~1012 hPa vs storm ~990 hPa
        0.0
    )
    l2_score = np.where(
        has_mic,
        rng.beta(1, 9, n),     # Very low — indoor silence detected
        0.0
    )
    l3_score = rng.beta(2, 8, n)     # Low — cell towers don't match claimed zone
    l4_score = rng.beta(1, 9, n)     # Very low — stationary at home

    burst    = rng.exponential(0.5, n)   # Solo = low burst
    deviation = rng.beta(6, 3, n)       # High deviation (unusual zone, time)

    # Most solo fraudsters use mock GPS → flag is ON
    mock = (rng.random(n) > 0.15).astype(int)

    return {
        "l1_baro_score":           l1_score,
        "l1_baro_available":       has_baro.astype(int),
        "l2_acoustic_score":       l2_score,
        "l2_acoustic_available":   has_mic.astype(int),
        "l3_network_score":        l3_score,
        "l3_network_available":    np.ones(n, dtype=int),
        "l4_inertial_score":       l4_score,
        "l4_inertial_available":   np.ones(n, dtype=int),
        "mock_flag":               mock,
        "claim_burst_rate":        burst,
        "baseline_deviation":      deviation,
        "is_genuine":              np.zeros(n, dtype=int),
    }


def _ring_fraud(n: int) -> dict:
    """
    Simulate a coordinated Telegram ring (500-worker scenario).
    Extremely high burst rate. All spoofed to the same pincode.
    Layer scores are low but mock flag may be inconsistent (sophisticated actors).
    """
    has_baro = rng.random(n) > 0.35
    has_mic  = rng.random(n) > 0.25

    l1_score = np.where(has_baro, rng.beta(2, 7, n), 0.0)
    l2_score = np.where(has_mic,  rng.beta(1, 8, n), 0.0)
    l3_score = rng.beta(2, 8, n)
    l4_score = rng.beta(1, 8, n)   # Uniform stationary — all sitting at home

    # Burst rate is the KEY signal: 20–100 claims per minute in a ring
    burst = rng.uniform(15, 80, n)

    deviation = rng.beta(7, 2, n)   # High deviation

    # Sophisticated rings may disable mock flag or use rooted phones
    mock = (rng.random(n) > 0.40).astype(int)

    return {
        "l1_baro_score":           l1_score,
        "l1_baro_available":       has_baro.astype(int),
        "l2_acoustic_score":       l2_score,
        "l2_acoustic_available":   has_mic.astype(int),
        "l3_network_score":        l3_score,
        "l3_network_available":    np.ones(n, dtype=int),
        "l4_inertial_score":       l4_score,
        "l4_inertial_available":   np.ones(n, dtype=int),
        "mock_flag":               mock,
        "claim_burst_rate":        burst,
        "baseline_deviation":      deviation,
        "is_genuine":              np.zeros(n, dtype=int),
    }


def _genuine_with_sensor_gaps(n: int) -> dict:
    """
    Simulate genuine workers on very cheap phones (₹4,000–₹7,000 range).
    Multiple sensors unavailable, but motion + network still show genuine patterns.
    This archetype tests graceful degradation — the model should still approve.
    """
    return {
        "l1_baro_score":           np.zeros(n),
        "l1_baro_available":       np.zeros(n, dtype=int),   # No barometer
        "l2_acoustic_score":       np.zeros(n),
        "l2_acoustic_available":   np.zeros(n, dtype=int),   # No mic permission
        "l3_network_score":        rng.beta(6, 2, n),        # Cell towers genuine
        "l3_network_available":    np.ones(n, dtype=int),
        "l4_inertial_score":       rng.beta(7, 2, n),        # Motion genuine
        "l4_inertial_available":   np.ones(n, dtype=int),
        "mock_flag":               np.zeros(n, dtype=int),
        "claim_burst_rate":        rng.exponential(0.9, n),
        "baseline_deviation":      rng.beta(2, 7, n),
        "is_genuine":              np.ones(n, dtype=int),
    }


def _ambiguous_genuine(n: int) -> dict:
    """
    Simulate edge cases: genuine workers with weak signal, poor connectivity,
    or unusual routes. Some signals look suspicious but overall genuine.
    """
    has_baro = rng.random(n) > 0.4
    has_mic  = rng.random(n) > 0.35

    l1_score = np.where(has_baro, rng.beta(4, 4, n), 0.0)   # Mixed
    l2_score = np.where(has_mic,  rng.beta(4, 4, n), 0.0)
    l3_score = rng.beta(4, 5, n)      # Moderate — worker at zone boundary
    l4_score = rng.beta(6, 3, n)      # Good motion

    burst     = rng.exponential(1.2, n)
    deviation = rng.beta(4, 5, n)     # Moderate deviation (new delivery zone)

    return {
        "l1_baro_score":           l1_score,
        "l1_baro_available":       has_baro.astype(int),
        "l2_acoustic_score":       l2_score,
        "l2_acoustic_available":   has_mic.astype(int),
        "l3_network_score":        l3_score,
        "l3_network_available":    np.ones(n, dtype=int),
        "l4_inertial_score":       l4_score,
        "l4_inertial_available":   np.ones(n, dtype=int),
        "mock_flag":               np.zeros(n, dtype=int),
        "claim_burst_rate":        burst,
        "baseline_deviation":      deviation,
        "is_genuine":              np.ones(n, dtype=int),
    }


# ── Main Generator ─────────────────────────────────────────────────────────────

def generate(n_total: int = N_SAMPLES, output_path: str = OUTPUT_PATH) -> pd.DataFrame:
    """
    Generate synthetic coherence training data.

    Archetype distribution:
        40% — Genuine workers (realistic sensors)
        15% — Genuine with sensor gaps (budget phones)
        10% — Ambiguous genuine (edge cases)
        20% — Solo fraud (GPS spoofing at home)
        15% — Ring fraud (coordinated Telegram attack)
    """
    counts = {
        "genuine":       int(n_total * 0.40),
        "sensor_gaps":   int(n_total * 0.15),
        "ambiguous":     int(n_total * 0.10),
        "solo_fraud":    int(n_total * 0.20),
        "ring_fraud":    int(n_total * 0.15),
    }
    # Ensure we hit exactly n_total
    counts["genuine"] += n_total - sum(counts.values())

    log.info(f"Generating {n_total} synthetic coherence samples:")
    for k, v in counts.items():
        log.info(f"  {k}: {v} rows")

    frames = [
        pd.DataFrame(_genuine_worker(counts["genuine"])),
        pd.DataFrame(_genuine_with_sensor_gaps(counts["sensor_gaps"])),
        pd.DataFrame(_ambiguous_genuine(counts["ambiguous"])),
        pd.DataFrame(_solo_fraud(counts["solo_fraud"])),
        pd.DataFrame(_ring_fraud(counts["ring_fraud"])),
    ]

    df = pd.concat(frames, ignore_index=True)
    df = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

    # Clip all score columns to [0, 1]
    score_cols = [c for c in df.columns if c.endswith("_score")]
    df[score_cols] = df[score_cols].clip(0.0, 1.0)
    df["claim_burst_rate"] = df["claim_burst_rate"].clip(0.0, 200.0)
    df["baseline_deviation"] = df["baseline_deviation"].clip(0.0, 1.0)

    # Cast boolean columns
    bool_cols = [c for c in df.columns if c.endswith("_available") or c in ("mock_flag", "is_genuine")]
    for col in bool_cols:
        df[col] = df[col].astype(int)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    genuine_rate = df["is_genuine"].mean() * 100
    log.info(f"Dataset saved → {output_path}")
    log.info(f"Class balance: {genuine_rate:.1f}% genuine | {100 - genuine_rate:.1f}% fraud")
    return df


if __name__ == "__main__":
    df = generate()
    print(f"\nShape: {df.shape}")
    print(f"\nFirst 5 rows:\n{df.head().to_string()}")
    print(f"\nClass distribution:\n{df['is_genuine'].value_counts()}")
    print(f"\nDescriptive stats:\n{df.describe().to_string()}")