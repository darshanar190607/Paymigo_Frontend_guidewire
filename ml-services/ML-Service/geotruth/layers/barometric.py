"""
GeoTruth — Layer 1: Barometric Pressure Coherence
==================================================
Validates device barometer reading against live Open-Meteo surface pressure.
Genuine workers in storm zones show a measurable pressure drop that cannot
be faked by a GPS spoofing app.

Open-Meteo API: https://api.open-meteo.com  (free, no API key required)

Pincode → Coordinate Lookup:
    For v1 we use a static lookup table of Indian metro pincodes.
    In production this is replaced by a PostGIS query or Google Maps Geocoding API.
"""

import asyncio
import logging
from typing import Optional

import httpx

# Lazy import — schemas loaded at runtime to avoid circular imports
from geotruth.schemas import ClaimVector, LayerResult

log = logging.getLogger("geotruth.barometric")

# ── Pincode → (lat, lon) lookup table ─────────────────────────────────────────
# Top Indian delivery metro pincodes. Expand as needed.
PINCODE_COORDS: dict[str, tuple[float, float]] = {
    # Chennai
    "600001": (13.0827, 80.2707),
    "600006": (13.0569, 80.2425),
    "600020": (13.0569, 80.2425),
    "600028": (13.0067, 80.2206),
    "600040": (12.9762, 80.2206),
    "600042": (12.9900, 80.2100),
    "600096": (13.0451, 80.1687),
    # Bengaluru
    "560001": (12.9716, 77.5946),
    "560034": (12.9352, 77.6245),
    "560047": (12.9010, 77.6390),
    "560068": (12.9352, 77.6900),
    "560103": (12.8963, 77.5956),
    # Mumbai
    "400001": (18.9388, 72.8354),
    "400050": (19.0596, 72.8295),
    "400072": (19.0760, 72.8777),
    "400076": (19.0595, 72.8972),
    # Hyderabad
    "500001": (17.3850, 78.4867),
    "500032": (17.4126, 78.4771),
    "500072": (17.3880, 78.4982),
    # Delhi
    "110001": (28.6139, 77.2090),
    "110029": (28.5672, 77.1865),
    "110045": (28.6100, 77.0500),
    # Kolkata
    "700001": (22.5726, 88.3639),
    "700064": (22.4975, 88.3712),
    # Pune
    "411001": (18.5204, 73.8567),
    "411028": (18.5895, 73.7650),
    # Tiruppur
    "641601": (11.1085, 77.3411),
    "641602": (11.1141, 77.3534),
    "641604": (11.0733, 77.3290),
}

# Default fallback coords (geometric centre of India) if pincode unknown
DEFAULT_COORDS = (20.5937, 78.9629)

# Pressure thresholds (hPa)
TIGHT_THRESHOLD  = 3.0   # ≤ 3 hPa delta → strong match
MEDIUM_THRESHOLD = 8.0   # ≤ 8 hPa delta → partial match
WIDE_THRESHOLD   = 15.0  # > 15 hPa delta → likely spoofed

API_TIMEOUT_SECONDS = 8.0

LAYER_WEIGHT = 0.22   # Weight in coherence scoring


def _pincode_to_coords(pincode: str) -> tuple[float, float]:
    """Resolve a 6-digit Indian pincode to (lat, lon). Falls back to India centre."""
    coords = PINCODE_COORDS.get(pincode)
    if coords is None:
        log.warning(f"Pincode {pincode!r} not in lookup table — using default coords")
        return DEFAULT_COORDS
    return coords


async def _fetch_open_meteo_pressure(lat: float, lon: float) -> Optional[float]:
    """
    Async call to Open-Meteo API to get current surface pressure (hPa).
    Returns None on timeout or API error.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":        lat,
        "longitude":       lon,
        "current":         "surface_pressure",
        "forecast_days":   1,
        "timeformat":      "unixtime",
    }

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        pressure = data.get("current", {}).get("surface_pressure")
        if pressure is None:
            log.warning("Open-Meteo response missing 'surface_pressure' field")
            return None

        log.info(f"Open-Meteo surface pressure @ ({lat:.3f},{lon:.3f}): {pressure} hPa")
        return float(pressure)

    except httpx.TimeoutException:
        log.warning(f"Open-Meteo request timed out after {API_TIMEOUT_SECONDS}s")
        return None
    except httpx.HTTPStatusError as e:
        log.warning(f"Open-Meteo HTTP error: {e.response.status_code}")
        return None
    except Exception as e:
        log.warning(f"Open-Meteo unexpected error: {e}")
        return None


def _compute_score(device_hpa: float, api_hpa: float) -> tuple[float, str]:
    """
    Compute barometric coherence score from pressure delta.

    Returns:
        (score: float in [0, 1], reason: str)
    """
    delta = abs(device_hpa - api_hpa)

    if delta <= TIGHT_THRESHOLD:
        score  = 1.0
        reason = f"Pressure delta {delta:.1f} hPa — tight match ✅"
    elif delta <= MEDIUM_THRESHOLD:
        # Linear interpolation between 1.0 and 0.5
        score  = 1.0 - 0.5 * ((delta - TIGHT_THRESHOLD) / (MEDIUM_THRESHOLD - TIGHT_THRESHOLD))
        reason = f"Pressure delta {delta:.1f} hPa — moderate match ⚠️"
    elif delta <= WIDE_THRESHOLD:
        # Linear interpolation between 0.5 and 0.1
        score  = 0.5 - 0.4 * ((delta - MEDIUM_THRESHOLD) / (WIDE_THRESHOLD - MEDIUM_THRESHOLD))
        reason = f"Pressure delta {delta:.1f} hPa — large divergence ❌"
    else:
        score  = 0.0
        reason = f"Pressure delta {delta:.1f} hPa — severe mismatch, likely indoor fraud ❌❌"

    return round(score, 4), reason


async def evaluate(claim: ClaimVector) -> LayerResult:
    """
    Layer 1: Barometric Pressure Coherence.

    Compares device sensor reading to Open-Meteo live API for the
    claimed pincode location.

    Graceful degradation:
      - Device has no barometer → available=False (budget phone grace flag)
      - API timeout / network error → available=False
      - Both present → score computed from pressure delta
    """
    layer_name = "barometric"

    # ── 1. Check device sensor availability ────────────────────────────────────
    device_hpa = claim.device_barometer_hpa
    if device_hpa is None or device_hpa <= 0:
        return LayerResult(
            layer_name=layer_name,
            score=0.0,
            weight=LAYER_WEIGHT,
            available=False,
            grace_flag=True,
            confidence=0.0,
            reason="Device has no barometer sensor (budget phone) — layer skipped",
        )

    # Sanity check: valid atmospheric pressure is 870–1084 hPa
    if not (870.0 <= device_hpa <= 1084.0):
        return LayerResult(
            layer_name=layer_name,
            score=0.0,
            weight=LAYER_WEIGHT,
            available=True,
            grace_flag=False,
            confidence=0.95,
            reason=f"Device barometer value {device_hpa} hPa out of physical range — sensor error or tampered",
        )

    # ── 2. Resolve pincode → coordinates ───────────────────────────────────────
    lat, lon = _pincode_to_coords(claim.claimed_pincode)

    # ── 3. Fetch live weather pressure ─────────────────────────────────────────
    api_hpa = await _fetch_open_meteo_pressure(lat, lon)

    if api_hpa is None:
        return LayerResult(
            layer_name=layer_name,
            score=0.0,
            weight=LAYER_WEIGHT,
            available=False,
            grace_flag=True,
            confidence=0.0,
            reason="Open-Meteo API unavailable — barometric layer skipped (network timeout)",
        )

    # ── 4. Compute delta score ──────────────────────────────────────────────────
    score, reason = _compute_score(device_hpa, api_hpa)

    # Confidence is high when we have both values and a clear delta signal
    delta = abs(device_hpa - api_hpa)
    confidence = 0.95 if delta > MEDIUM_THRESHOLD or delta < TIGHT_THRESHOLD else 0.75

    log.info(
        f"Barometric | device={device_hpa} hPa | api={api_hpa} hPa | "
        f"delta={delta:.1f} | score={score}"
    )

    return LayerResult(
        layer_name=layer_name,
        score=score,
        weight=LAYER_WEIGHT,
        available=True,
        grace_flag=False,
        confidence=confidence,
        reason=reason,
        metadata={
            "device_hpa":  device_hpa,
            "api_hpa":     api_hpa,
            "delta_hpa":   round(delta, 2),
            "pincode":     claim.claimed_pincode,
            "coords":      {"lat": lat, "lon": lon},
        },
    )


# ── Synchronous wrapper for non-async callers ──────────────────────────────────

def evaluate_sync(claim: ClaimVector) -> LayerResult:
    """Synchronous wrapper around evaluate() for testing and CLI usage."""
    return asyncio.run(evaluate(claim))


# ── CLI test ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    from geotruth.schemas import ClaimVector

    # Simulate a genuine Chennai worker during a storm (low pressure ~990 hPa)
    test_claim = ClaimVector(
        worker_id="W-TEST-001",
        claimed_pincode="600001",
        timestamp=1711900000,
        device_barometer_hpa=991.5,   # Storm conditions
        acoustic_feature_vector=[0.8, 0.2, 0.05, 0.02, 0.01],
        cell_tower_ids=["404-20-12345"],
        wifi_ssid_hashes=[],
        accelerometer_variance_30m=0.85,
        is_mock_location=False,
        screen_unlock_count_1h=3,
        has_barometer=True,
        has_microphone=True,
        connection_type="4G",
    )

    result = evaluate_sync(test_claim)
    print(json.dumps(result.model_dump(), indent=2, default=str))