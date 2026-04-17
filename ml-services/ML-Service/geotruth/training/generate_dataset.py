"""
GeoTruth — Inertial Layer Synthetic Dataset Generator
======================================================
Generates 10,000 labeled motion variance samples covering
5 real-world behavioral archetypes observed in delivery workers.

WHY SYNTHETIC FIRST (Cold Start Strategy)
------------------------------------------
Real accelerometer logs from delivery workers don't exist yet.
We model the physics of motion instead:
  - A worker delivering has HIGH variance (bike vibrations, stops)
  - A worker taking shelter shows SUDDEN DROP in variance
  - A fraud actor at home shows LOW variance throughout
  - A fraud actor who just activated a spoof app shows a
    telltale SPIKE then immediate stillness pattern

REAL DATA AUGMENTATION (Phase 2 — once you have users)
--------------------------------------------------------
Replace or supplement this script with:
  1. UCI HAR Dataset (Human Activity Recognition)
     URL: https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones
     Use: Real accelerometer data for walking/sitting/lying archetypes
     Download: pip install ucimlrepo
     Code:
       from ucimlrepo import fetch_ucirepo
       har = fetch_ucirepo(id=240)
       X = har.data.features   # 561 features including variance cols
       y = har.data.targets

  2. WISDM Activity Dataset
     URL: https://www.cis.fordham.edu/wisdm/dataset.php
     Use: Real smartphone accelerometer at 20Hz — walking, jogging, sitting
     Download: Direct CSV from their site (free, academic license)

  3. Your own GigShield telemetry (Phase 2+)
     Once workers enroll, log anonymized variance windows per shift.
     10 workers x 30 days = ~8,640 genuine samples. Retrain monthly.

COLUMNS GENERATED
-----------------
variance_1h_to_30m_ago  : float  Motion variance 1hr–30min before claim
variance_last_30m       : float  Motion variance in final 30min before claim
variance_delta          : float  Engineered: last30m - prior30m (shelter signal)
motion_ratio            : float  Engineered: last30m / (prior + 1e-6)
sudden_stillness        : int    1 if delta < -0.3 (rapid shelter-taking)
prolonged_static        : int    1 if both windows < 0.05 (stayed home all day)
is_genuine              : int    LABEL — 1=genuine stranded, 0=fraud
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
N_SAMPLES = 10_000
OUTPUT_PATH = Path(__file__).parent.parent / "models" / "training_data.csv"

rng = np.random.default_rng(SEED)


def generate_archetype_genuine_stranded(n: int) -> pd.DataFrame:
    """
    ARCHETYPE 1 — Genuine worker caught mid-delivery.
    Pattern: Was actively delivering (high variance) → storm hit → took shelter (low variance).
    This is the TRUE POSITIVE we must correctly approve.

    Physics rationale:
      - Delivery bike on Indian roads: variance ~0.6–1.0 (potholes, acceleration)
      - Parked under shop awning in rain: variance ~0.01–0.08 (hand tremor only)
      - Delta is strongly negative — the defining signature of genuine shelter
    """
    prior = rng.uniform(0.55, 1.0, n)       # Active delivery high variance
    current = rng.uniform(0.01, 0.12, n)    # Took shelter — near stationary
    noise = rng.normal(0, 0.02, n)
    current = np.clip(current + noise, 0.001, 0.2)
    return pd.DataFrame({
        "variance_1h_to_30m_ago": prior,
        "variance_last_30m": current,
        "is_genuine": 1,
        "archetype": "genuine_stranded"
    })


def generate_archetype_genuine_slow_stop(n: int) -> pd.DataFrame:
    """
    ARCHETYPE 2 — Genuine worker who stopped gradually (traffic jam, waterlogging).
    Pattern: Moderate prior variance → gradual slowdown → low variance.
    Harder case — less dramatic delta than archetype 1.
    """
    prior = rng.uniform(0.3, 0.65, n)
    current = rng.uniform(0.05, 0.2, n)
    noise = rng.normal(0, 0.03, n)
    current = np.clip(current + noise, 0.001, 0.25)
    return pd.DataFrame({
        "variance_1h_to_30m_ago": prior,
        "variance_last_30m": current,
        "is_genuine": 1,
        "archetype": "genuine_slow_stop"
    })


def generate_archetype_fraud_stayed_home(n: int) -> pd.DataFrame:
    """
    ARCHETYPE 3 — Classic fraud: worker never left home.
    Pattern: LOW variance throughout — no delivery activity at all.
    This is the most common fraud pattern in Telegram rings.

    Key insight: A genuine delivery worker CANNOT have low prior variance
    — Indian road conditions guarantee motion noise even at idle.
    """
    prior = rng.uniform(0.0, 0.12, n)      # Sedentary — watching TV, sleeping
    current = rng.uniform(0.0, 0.08, n)    # Still sedentary when claim filed
    noise = rng.normal(0, 0.01, n)
    prior = np.clip(prior + noise, 0.001, 0.15)
    current = np.clip(current + noise, 0.001, 0.1)
    return pd.DataFrame({
        "variance_1h_to_30m_ago": prior,
        "variance_last_30m": current,
        "is_genuine": 0,
        "archetype": "fraud_stayed_home"
    })


def generate_archetype_fraud_spoof_activation(n: int) -> pd.DataFrame:
    """
    ARCHETYPE 4 — Fraud actor who activated spoof app mid-session.
    Pattern: Normal home variance → SUDDEN spike when they pick up phone
             to activate the spoofing app → back to stationary.

    Telltale: Prior variance is low (home), current variance has a
    brief spike from phone manipulation then drops back. The variance
    window captures the transient spike but overall current is HIGHER
    than prior — OPPOSITE of genuine shelter pattern.
    """
    prior = rng.uniform(0.02, 0.15, n)      # Sitting at home
    # Current is slightly elevated from picking up phone to activate spoof
    current = rng.uniform(0.1, 0.35, n)     # Brief activity from phone grab
    noise = rng.normal(0, 0.02, n)
    current = np.clip(current + noise, 0.05, 0.4)
    return pd.DataFrame({
        "variance_1h_to_30m_ago": prior,
        "variance_last_30m": current,
        "is_genuine": 0,
        "archetype": "fraud_spoof_activation"
    })


def generate_archetype_fraud_normal_driving(n: int) -> pd.DataFrame:
    """
    ARCHETYPE 5 — Fraud actor still driving/moving but filing a false claim.
    Pattern: Both windows show normal variance — no shelter-taking event.
    The delta is near zero — there was no disruption that stopped them.
    """
    prior = rng.uniform(0.3, 0.8, n)
    # Current is similar to prior — no shelter event happened
    delta = rng.uniform(-0.1, 0.1, n)      # Near-zero delta
    current = np.clip(prior + delta, 0.1, 1.0)
    return pd.DataFrame({
        "variance_1h_to_30m_ago": prior,
        "variance_last_30m": current,
        "is_genuine": 0,
        "archetype": "fraud_driving_and_claiming"
    })


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add engineered features that make the XGBoost model's job easier.
    These capture domain knowledge that raw variance alone misses.
    """
    eps = 1e-6
    df["variance_delta"] = df["variance_last_30m"] - df["variance_1h_to_30m_ago"]
    df["motion_ratio"] = df["variance_last_30m"] / (df["variance_1h_to_30m_ago"] + eps)
    # sudden_stillness: was active, now stopped — core genuine signal
    df["sudden_stillness"] = (
        (df["variance_1h_to_30m_ago"] > 0.35) &
        (df["variance_last_30m"] < 0.15)
    ).astype(int)
    # prolonged_static: never moved — core fraud signal
    df["prolonged_static"] = (
        (df["variance_1h_to_30m_ago"] < 0.12) &
        (df["variance_last_30m"] < 0.12)
    ).astype(int)
    # reverse_delta: current > prior — spoof activation signal
    df["reverse_delta"] = (df["variance_delta"] > 0.05).astype(int)
    return df


def main():
    print("GeoTruth — Generating synthetic inertial training dataset...")
    print(f"Target: {N_SAMPLES:,} samples across 5 archetypes\n")

    # Distribute samples across archetypes
    # Genuine: 40% (2 archetypes), Fraud: 60% (3 archetypes)
    # Slight fraud majority reflects real-world class imbalance in parametric schemes
    n_each = {
        "genuine_stranded":       2_000,   # 20%
        "genuine_slow_stop":      2_000,   # 20%
        "fraud_stayed_home":      2_500,   # 25%
        "fraud_spoof_activation": 2_000,   # 20%
        "fraud_driving":          1_500,   # 15%
    }

    frames = [
        generate_archetype_genuine_stranded(n_each["genuine_stranded"]),
        generate_archetype_genuine_slow_stop(n_each["genuine_slow_stop"]),
        generate_archetype_fraud_stayed_home(n_each["fraud_stayed_home"]),
        generate_archetype_fraud_spoof_activation(n_each["fraud_spoof_activation"]),
        generate_archetype_fraud_normal_driving(n_each["fraud_driving"]),
    ]

    df = pd.concat(frames, ignore_index=True)
    df = engineer_features(df)

    # Shuffle so archetypes don't cluster
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    # Summary report
    print(f"Dataset saved to: {OUTPUT_PATH}")
    print(f"Total rows: {len(df):,}")
    print(f"\nClass distribution:")
    print(df["is_genuine"].value_counts().rename({1: "Genuine (1)", 0: "Fraud (0)"}))
    print(f"\nArchetype breakdown:")
    print(df["archetype"].value_counts())
    print(f"\nFeature statistics:")
    print(df[["variance_1h_to_30m_ago","variance_last_30m",
              "variance_delta","sudden_stillness","prolonged_static"]].describe().round(3))
    print("\nDataset generation complete.")


if __name__ == "__main__":
    main()