"""
GeoTruth™ — Hybrid Data Collection
Strategy:
  1. Kaggle  → Porto taxi GPS traces (real movement patterns as normal baseline)
  2. API     → Open-Meteo zone weather context (realistic baro/pressure ranges)
  3. Synthetic → GPS spoofing patterns + fraud events using real physics rules

Outputs (saved to data/):
  gps_spoof_dataset.csv   — 20,000 rows, 38 features, label_spoofed
  fraud_dataset.csv       — 22,000 rows, 20 features, label_fraud
"""

import os, sys, json, time, zipfile
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (DATA_DIR, ZONE_COORDS, RANDOM_STATE,
                    N_NORMAL_GPS, N_SPOOFED_GPS,
                    N_NORMAL_FRAUD, N_FRAUD_POS)

np.random.seed(RANDOM_STATE)

# ══════════════════════════════════════════════════════════════════════
# SECTION 1 ── KAGGLE DOWNLOAD
# ══════════════════════════════════════════════════════════════════════

def download_kaggle_datasets() -> bool:
    """
    Downloads Porto Taxi and IEEE-CIS datasets.
    Prerequisites:
      pip install kaggle
      Place kaggle.json at ~/.kaggle/kaggle.json  (from kaggle.com > Account > API)
      OR place kaggle.json in the current project directory.
      OR export KAGGLE_USERNAME=xxx KAGGLE_KEY=yyy
    """
    # Check for local kaggle.json in the project root
    local_kaggle = os.path.join(os.getcwd(), "kaggle.json")
    if os.path.exists(local_kaggle):
        os.environ["KAGGLE_CONFIG_DIR"] = os.getcwd()
        print(f"[KAGGLE] Using local config: {local_kaggle}")

    try:
        import kaggle  # noqa: F401
        raw = os.path.join(DATA_DIR, "kaggle_raw")
        os.makedirs(raw, exist_ok=True)

        print("[KAGGLE] Downloading Porto Taxi GPS traces (~2 GB)...")
        kaggle.api.competition_download_files(
            "pkdd-15-predict-taxi-service-trajectory-i",
            path=raw, quiet=False
        )

        print("[KAGGLE] Downloading IEEE-CIS Fraud Detection...")
        kaggle.api.competition_download_files(
            "ieee-fraud-detection", path=raw, quiet=False
        )
        return True
    except (Exception, BaseException) as e:
        # Catching BaseException handles SystemExit raised by the kaggle library on auth failure
        print(f"[KAGGLE] Skipping — {e}")
        print("         Full-synthetic mode activated. "
              "Set up kaggle.json for real-data augmentation.\n")
        return False


def load_porto_traces(max_rows: int = 30_000) -> list:
    """
    Parse Porto taxi POLYLINE JSON → list of [[lon, lat], ...] sequences.
    Used as normal-movement seed for speed/heading feature calibration.
    """
    raw = os.path.join(DATA_DIR, "kaggle_raw")
    candidates = [
        os.path.join(raw, "train.csv.zip"),
        os.path.join(raw, "train.csv"),
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    if path is None:
        print("[PORTO] Not found — using pure synthetic movement.")
        return []

    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            with z.open("train.csv") as f:
                df = pd.read_csv(f, nrows=max_rows, usecols=["POLYLINE"])
    else:
        df = pd.read_csv(path, nrows=max_rows, usecols=["POLYLINE"])

    traces = []
    for pl in df["POLYLINE"]:
        try:
            pts = json.loads(pl)
            if len(pts) >= 10:
                traces.append(pts)
        except Exception:
            pass
    print(f"[PORTO] Loaded {len(traces):,} real GPS trajectories.")
    return traces


def derive_porto_speed_stats(traces: list) -> dict:
    """Compute mean/std of inter-point speed from Porto traces (15-sec intervals)."""
    speeds = []
    for pts in traces[:5_000]:
        for i in range(1, len(pts)):
            dx = (pts[i][0] - pts[i-1][0]) * 111_000 * np.cos(np.radians(pts[i][1]))
            dy = (pts[i][1] - pts[i-1][1]) * 111_000
            dist_m = np.hypot(dx, dy)
            spd_kmh = (dist_m / 15) * 3.6
            if 0 < spd_kmh < 120:
                speeds.append(spd_kmh)
    if speeds:
        return {"mean": float(np.mean(speeds)), "std": float(np.std(speeds))}
    return {"mean": 22.0, "std": 12.0}


# ══════════════════════════════════════════════════════════════════════
# SECTION 2 ── OPEN-METEO API (zone weather context)
# ══════════════════════════════════════════════════════════════════════

def fetch_zone_weather_context() -> dict:
    """
    Pulls current surface pressure from Open-Meteo for each zone.
    No API key required. Used to calibrate barometric ranges per city.
    """
    zone_data = {}
    for pc, (lat, lon, city, _state) in ZONE_COORDS.items():
        try:
            r = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat, "longitude": lon,
                    "hourly": "surface_pressure,temperature_2m",
                    "forecast_days": 1,
                    "timezone": "Asia/Kolkata",
                },
                timeout=8,
            )
            hourly = r.json()["hourly"]
            p = [v for v in hourly["surface_pressure"] if v is not None]
            zone_data[pc] = {
                "pressure_mean": float(np.mean(p)) if p else 1013.0,
                "pressure_std": 2.5,
                "lat": lat, "lon": lon, "city": city,
            }
            time.sleep(0.25)
        except Exception:
            zone_data[pc] = {
                "pressure_mean": 1013.0, "pressure_std": 3.0,
                "lat": lat, "lon": lon, "city": city,
            }
    print(f"[API] Barometric context for {len(zone_data)} zones collected.")
    return zone_data


# ══════════════════════════════════════════════════════════════════════
# SECTION 3 ── GPS SPOOFING DATASET GENERATOR
# ══════════════════════════════════════════════════════════════════════

SPOOF_PATTERNS = [
    "teleport",        # impossible speed jump — GPS location jumps across city
    "altitude_spoof",  # GPS altitude contradicts barometric pressure
    "network_mismatch",# cell towers don't match reported GPS coords
    "frozen_gps",      # GPS frozen / replayed while phone physically moves
    "drone_sdr",       # SDR signal injection — affects acoustics + altitude
    "social_ring",     # coordinated group moves in sync (fraud ring)
    "zone_jump",       # claims to be in zone but network topology disagrees
]


class GPSSpoofingDataGenerator:
    """
    Generates 38-dimensional GeoTruth™ feature vectors.
    Normal rows follow real physics (Porto-calibrated where available).
    Spoofed rows have physics-violating artifacts injected per attack type.
    """

    def __init__(self, zone_ctx: dict, speed_stats: dict):
        self.zones = zone_ctx
        self.zone_keys = list(zone_ctx.keys())
        self.spd_mean = speed_stats["mean"]
        self.spd_std  = speed_stats["std"]

    # ── helpers ──────────────────────────────────────────────────────

    def _sample_speed(self) -> float:
        s = np.random.normal(self.spd_mean, self.spd_std)
        return float(np.clip(s, 0, 70))

    def _normal_row(self, zone_key: str) -> dict:
        zd    = self.zones[zone_key]
        speed = self._sample_speed()

        # Altitude: ground-level delivery worker; baro and GPS nearly agree
        true_alt = float(np.random.uniform(5, 60))
        baro_alt = true_alt + float(np.random.normal(0, 1.5))
        gps_alt  = true_alt + float(np.random.normal(0, 3.0))

        # Inertial: accel ~ physical speed
        accel_mag = float(np.clip(0.3 + (speed / 80) * 1.8 + np.random.normal(0, 0.15), 0.1, 4))
        inertial_speed = float(max(0, speed + np.random.normal(0, 2.0)))

        return {
            # ── Barometric (1-5)
            "baro_alt_m":          round(baro_alt, 2),
            "gps_alt_m":           round(gps_alt, 2),
            "alt_discrepancy_m":   round(abs(baro_alt - gps_alt), 2),
            "baro_pressure_hpa":   round(zd["pressure_mean"] + np.random.normal(0, zd["pressure_std"]), 2),
            "baro_altitude_rate":  round(float(np.random.normal(0, 0.08)), 4),
            # ── Acoustic (6-9)
            "ambient_noise_db":        round(float(np.random.normal(63, 9)), 1),
            "noise_consistency_score": round(float(np.random.uniform(0.78, 1.00)), 3),
            "location_acoustic_match": round(float(np.random.uniform(0.82, 1.00)), 3),
            "acoustic_anomaly_flag":   0,
            # ── Network (10-15)
            "cell_tower_count":      int(np.random.randint(2, 9)),
            "wifi_ap_count":         int(np.random.randint(3, 22)),
            "expected_tower_match":  round(float(np.random.uniform(0.82, 1.00)), 3),
            "network_latency_ms":    round(float(np.random.lognormal(3.5, 0.4)), 1),
            "signal_strength_dbm":   int(np.random.randint(-84, -54)),
            "network_loc_consistency": round(float(np.random.uniform(0.82, 1.00)), 3),
            # ── Inertial (16-22)
            "accel_magnitude":     round(accel_mag, 3),
            "accel_variance_1min": round(float(np.random.uniform(0.1, 0.75)), 3),
            "reported_speed_kmph": round(speed, 2),
            "inertial_speed_est":  round(inertial_speed, 2),
            "speed_discrepancy":   round(abs(speed - inertial_speed), 2),
            "heading_change_rate": round(float(np.random.uniform(0, 14)), 2),
            "motion_consistency":  round(float(np.random.uniform(0.83, 1.00)), 3),
            # ── Zone coherence (23-27)
            "zone_pincode_match":        1,
            "expected_zone_transition":  round(float(np.random.uniform(0.85, 1.00)), 3),
            "geofence_violations":       0,
            "route_feasibility":         round(float(np.random.uniform(0.82, 1.00)), 3),
            "delivery_density_match":    round(float(np.random.uniform(0.75, 1.00)), 3),
            # ── Behavioral (28-33)
            "session_duration_min": round(float(np.random.lognormal(4.5, 0.45)), 1),
            "deliveries_per_hour":  round(float(np.random.uniform(1.5, 4.5)), 2),
            "break_frequency":      round(float(np.random.uniform(0.5, 2.5)), 2),
            "speed_vs_baseline":    round(float(np.random.normal(1.0, 0.10)), 3),
            "earnings_vs_baseline": round(float(np.random.normal(1.0, 0.14)), 3),
            "behavioral_anomaly":   round(float(np.random.uniform(0.0, 0.18)), 3),
            # ── Social ring (34-38)
            "peer_proximity_count":       int(np.random.randint(0, 5)),
            "sync_movement_score":        round(float(np.random.uniform(0.0, 0.28)), 3),
            "device_fingerprint_match":   1,
            "platform_login_consistency": round(float(np.random.uniform(0.85, 1.00)), 3),
            "social_anomaly_score":       round(float(np.random.uniform(0.0, 0.18)), 3),
            # ── Meta
            "pincode":       zone_key,
            "label_spoofed": 0,
            "spoof_type":    "none",
        }

    def _inject_spoof(self, row: dict, pattern: str) -> dict:
        row = row.copy()
        row["label_spoofed"] = 1
        row["spoof_type"]    = pattern

        if pattern == "teleport":
            fake_spd = float(np.random.uniform(350, 1400))
            row["reported_speed_kmph"] = round(fake_spd, 2)
            row["inertial_speed_est"]  = round(float(np.random.uniform(5, 40)), 2)
            row["speed_discrepancy"]   = round(abs(row["reported_speed_kmph"] - row["inertial_speed_est"]), 2)
            row["motion_consistency"]  = round(float(np.random.uniform(0.00, 0.22)), 3)
            row["route_feasibility"]   = round(float(np.random.uniform(0.00, 0.18)), 3)
            row["behavioral_anomaly"]  = round(float(np.random.uniform(0.60, 1.00)), 3)
            row["geofence_violations"] = int(np.random.randint(3, 10))

        elif pattern == "altitude_spoof":
            gps_alt_fake = float(np.random.uniform(250, 900))
            row["gps_alt_m"]          = round(gps_alt_fake, 2)
            row["alt_discrepancy_m"]  = round(abs(gps_alt_fake - row["baro_alt_m"]), 2)
            row["baro_altitude_rate"] = round(float(np.random.normal(0, 0.04)), 4)

        elif pattern == "network_mismatch":
            row["expected_tower_match"]    = round(float(np.random.uniform(0.0, 0.22)), 3)
            row["network_loc_consistency"] = round(float(np.random.uniform(0.0, 0.28)), 3)
            row["cell_tower_count"]        = int(np.random.randint(0, 2))
            row["signal_strength_dbm"]     = int(np.random.randint(-112, -90))
            row["wifi_ap_count"]           = int(np.random.randint(0, 2))

        elif pattern == "frozen_gps":
            row["reported_speed_kmph"]  = 0.0
            row["inertial_speed_est"]   = round(float(np.random.uniform(18, 55)), 2)
            row["speed_discrepancy"]    = row["inertial_speed_est"]
            row["accel_magnitude"]      = round(float(np.random.uniform(1.4, 3.2)), 3)
            row["motion_consistency"]   = round(float(np.random.uniform(0.0, 0.12)), 3)
            row["heading_change_rate"]  = 0.0

        elif pattern == "drone_sdr":
            gps_alt_fake = float(np.random.uniform(100, 400))
            row["gps_alt_m"]               = round(gps_alt_fake, 2)
            row["alt_discrepancy_m"]       = round(abs(gps_alt_fake - row["baro_alt_m"]), 2)
            row["acoustic_anomaly_flag"]   = 1
            row["noise_consistency_score"] = round(float(np.random.uniform(0.0, 0.28)), 3)
            row["location_acoustic_match"] = round(float(np.random.uniform(0.0, 0.18)), 3)
            row["reported_speed_kmph"]     = round(float(np.random.uniform(0, 4)), 2)
            row["inertial_speed_est"]      = round(float(np.random.uniform(14, 48)), 2)
            row["speed_discrepancy"]       = round(abs(row["reported_speed_kmph"] - row["inertial_speed_est"]), 2)

        elif pattern == "social_ring":
            row["sync_movement_score"]        = round(float(np.random.uniform(0.78, 1.00)), 3)
            row["peer_proximity_count"]       = int(np.random.randint(4, 9))
            row["social_anomaly_score"]       = round(float(np.random.uniform(0.62, 1.00)), 3)
            row["device_fingerprint_match"]   = 0
            row["behavioral_anomaly"]         = round(float(np.random.uniform(0.50, 0.92)), 3)
            row["platform_login_consistency"] = round(float(np.random.uniform(0.0, 0.35)), 3)

        elif pattern == "zone_jump":
            row["zone_pincode_match"]       = 0
            row["expected_zone_transition"] = round(float(np.random.uniform(0.0, 0.18)), 3)
            row["geofence_violations"]      = int(np.random.randint(3, 10))
            row["delivery_density_match"]   = round(float(np.random.uniform(0.0, 0.22)), 3)
            row["network_loc_consistency"]  = round(float(np.random.uniform(0.0, 0.30)), 3)

        return row

    def generate(self, n_normal: int, n_spoofed: int) -> pd.DataFrame:
        rows = []

        # Normal
        for _ in range(n_normal):
            zk = str(np.random.choice(self.zone_keys))
            rows.append(self._normal_row(zk))

        # Spoofed — balanced across all attack patterns
        per_pat   = n_spoofed // len(SPOOF_PATTERNS)
        remainder = n_spoofed  % len(SPOOF_PATTERNS)
        for i, pat in enumerate(SPOOF_PATTERNS):
            cnt = per_pat + (1 if i < remainder else 0)
            for _ in range(cnt):
                zk = str(np.random.choice(self.zone_keys))
                rows.append(self._inject_spoof(self._normal_row(zk), pat))

        df = pd.DataFrame(rows).sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
        df.insert(0, "session_id", [f"SES{i:07d}" for i in range(len(df))])
        return df


# ══════════════════════════════════════════════════════════════════════
# SECTION 4 ── FRAUD DETECTION DATASET GENERATOR
# ══════════════════════════════════════════════════════════════════════

FRAUD_TYPES = [
    "fake_rain_claim",     # fabricates weather-based payout claim
    "location_fraud",      # GPS spoofing to claim income in another zone
    "duplicate_claim",     # same incident filed multiple times with similar photos
    "fraud_ring",          # coordinated network of workers filing together
    "earnings_manipulation",# inflates baseline to boost premium/payout calculation
]


class FraudDataGenerator:
    """Generates gig worker insurance fraud feature rows."""

    def _normal_worker(self) -> dict:
        tenure = int(np.random.randint(4, 200))
        return {
            "zone_risk_tier":            int(np.random.randint(1, 6)),
            "claim_frequency_30d":       int(np.random.poisson(0.8)),
            "claim_amount_zscore":       round(float(np.random.normal(0, 1)), 3),
            "location_jump_count":       int(np.random.randint(0, 3)),
            "gps_spoof_probability":     round(float(np.random.beta(1, 9)), 3),
            "policy_tenure_weeks":       tenure,
            "earnings_deviation":        round(float(np.random.normal(0, 0.20)), 3),
            "claim_timing_anomaly":      round(float(np.random.uniform(0.0, 0.28)), 3),
            "peer_claim_correlation":    round(float(np.random.uniform(0.0, 0.38)), 3),
            "device_change_count":       int(np.random.randint(0, 2)),
            "login_anomaly_score":       round(float(np.random.uniform(0.0, 0.24)), 3),
            "route_deviation_score":     round(float(np.random.uniform(0.0, 0.28)), 3),
            "delivery_speed_anomaly":    round(float(np.random.uniform(0.0, 0.24)), 3),
            "duplicate_claim_score":     round(float(np.random.uniform(0.0, 0.14)), 3),
            "network_fraud_ring_score":  round(float(np.random.uniform(0.0, 0.18)), 3),
            "barometric_consistency":    round(float(np.random.uniform(0.80, 1.00)), 3),
            "zone_transition_anomaly":   round(float(np.random.uniform(0.0, 0.18)), 3),
            "claim_photo_similarity_score": round(float(np.random.uniform(0.0, 0.28)), 3),
            "platform_switch_frequency": round(float(np.random.uniform(0.0, 0.18)), 3),
            "behavioral_baseline_deviation": round(float(np.random.uniform(0.0, 0.24)), 3),
            "label_fraud": 0,
            "fraud_type":  "none",
        }

    def _inject_fraud(self, row: dict, ftype: str) -> dict:
        row = row.copy()
        row["label_fraud"] = 1
        row["fraud_type"]  = ftype

        if ftype == "fake_rain_claim":
            row["claim_frequency_30d"]   = int(np.random.randint(5, 16))
            row["claim_amount_zscore"]   = round(float(np.random.uniform(2.5, 5.5)), 3)
            row["claim_timing_anomaly"]  = round(float(np.random.uniform(0.62, 1.00)), 3)
            row["barometric_consistency"] = round(float(np.random.uniform(0.0, 0.28)), 3)
            row["gps_spoof_probability"] = round(float(np.random.beta(6, 2)), 3)

        elif ftype == "location_fraud":
            row["location_jump_count"]     = int(np.random.randint(8, 26))
            row["gps_spoof_probability"]   = round(float(np.random.beta(8, 2)), 3)
            row["zone_transition_anomaly"] = round(float(np.random.uniform(0.68, 1.00)), 3)
            row["route_deviation_score"]   = round(float(np.random.uniform(0.62, 1.00)), 3)

        elif ftype == "duplicate_claim":
            row["duplicate_claim_score"]          = round(float(np.random.uniform(0.72, 1.00)), 3)
            row["claim_frequency_30d"]            = int(np.random.randint(6, 20))
            row["claim_photo_similarity_score"]   = round(float(np.random.uniform(0.78, 1.00)), 3)

        elif ftype == "fraud_ring":
            row["network_fraud_ring_score"] = round(float(np.random.uniform(0.72, 1.00)), 3)
            row["peer_claim_correlation"]   = round(float(np.random.uniform(0.75, 1.00)), 3)
            row["device_change_count"]      = int(np.random.randint(3, 9))
            row["login_anomaly_score"]      = round(float(np.random.uniform(0.62, 1.00)), 3)

        elif ftype == "earnings_manipulation":
            row["earnings_deviation"]              = round(float(np.random.uniform(1.5, 3.8)), 3)
            row["delivery_speed_anomaly"]          = round(float(np.random.uniform(0.62, 1.00)), 3)
            row["behavioral_baseline_deviation"]   = round(float(np.random.uniform(0.65, 1.00)), 3)

        return row

    def generate(self, n_normal: int, n_fraud: int) -> pd.DataFrame:
        rows = []
        for _ in range(n_normal):
            rows.append(self._normal_worker())
        per_type  = n_fraud // len(FRAUD_TYPES)
        remainder = n_fraud  % len(FRAUD_TYPES)
        for i, ft in enumerate(FRAUD_TYPES):
            cnt = per_type + (1 if i < remainder else 0)
            for _ in range(cnt):
                rows.append(self._inject_fraud(self._normal_worker(), ft))

        df = pd.DataFrame(rows).sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
        df.insert(0, "worker_id", [f"WK{i:07d}" for i in range(len(df))])
        return df


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  GigKavach GeoTruth™ — Hybrid Data Collection Pipeline")
    print("=" * 65)

    # ── Step 1: Kaggle ────────────────────────────────────────────────
    print("\n[STEP 1] Kaggle download (optional — needs kaggle.json)...")
    kaggle_ok  = download_kaggle_datasets()
    porto      = load_porto_trajectories(max_rows=30_000) if kaggle_ok else []
    spd_stats  = derive_porto_speed_stats(porto)
    print(f"         Speed baseline: mean={spd_stats['mean']:.1f}  std={spd_stats['std']:.1f} km/h")

    # ── Step 2: Open-Meteo API ────────────────────────────────────────
    print("\n[STEP 2] Fetching zone weather context from Open-Meteo API...")
    zone_ctx = fetch_zone_weather_context()

    # ── Step 3: GPS Spoofing Dataset ──────────────────────────────────
    print(f"\n[STEP 3] Generating GPS Spoofing dataset...")
    print(f"         Normal: {N_NORMAL_GPS:,}  |  Spoofed: {N_SPOOFED_GPS:,}")
    gps_gen = GPSSpoofingDataGenerator(zone_ctx, spd_stats)
    gps_df  = gps_gen.generate(N_NORMAL_GPS, N_SPOOFED_GPS)
    gps_path = os.path.join(DATA_DIR, "gps_spoof_dataset.csv")
    gps_df.to_csv(gps_path, index=False)
    print(f"         Saved → {gps_path}")
    print(f"         Shape: {gps_df.shape}  |  Spoof rate: {gps_df.label_spoofed.mean()*100:.1f}%")
    spoof_dist = gps_df[gps_df.label_spoofed == 1]["spoof_type"].value_counts().to_dict()
    for k, v in spoof_dist.items():
        print(f"           {k}: {v}")

    # ── Step 4: Fraud Dataset ────────────────────────────────────────
    print(f"\n[STEP 4] Generating Fraud Detection dataset...")
    print(f"         Normal: {N_NORMAL_FRAUD:,}  |  Fraud: {N_FRAUD_POS:,}")
    fraud_gen  = FraudDataGenerator()
    fraud_df   = fraud_gen.generate(N_NORMAL_FRAUD, N_FRAUD_POS)
    fraud_path = os.path.join(DATA_DIR, "fraud_dataset.csv")
    fraud_df.to_csv(fraud_path, index=False)
    print(f"         Saved → {fraud_path}")
    print(f"         Shape: {fraud_df.shape}  |  Fraud rate: {fraud_df.label_fraud.mean()*100:.1f}%")

    print("\n[DONE] Data collection complete.\n")