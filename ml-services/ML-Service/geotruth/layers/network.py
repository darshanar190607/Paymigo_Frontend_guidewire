from geotruth.schemas import ClaimVector, LayerResult

LAYER_WEIGHT = 20.0

# Spoofing multiple local WiFi MACs/SSIDs requires physical proximity to those
# access points — a GPS spoofing app cannot fabricate this. Two or more hashes
# is a strong physical presence signal.
_WIFI_BOOST        = 0.2
_WIFI_MIN_COUNT    = 2


def score_network_layer(claim: ClaimVector) -> LayerResult:
    """
    L3 — Network Topology Truth.

    Scores physical presence using two independent network signals:
      1. Cell tower triangulation — count of visible towers
      2. WiFi environment — count of visible SSID hashes (optional boost)

    A GPS spoofing app changes reported coordinates but cannot change which
    cell towers or WiFi access points the device physically sees.
    """
    if not claim.cell_tower_ids:
        return LayerResult(
            layer_name="NetworkTopology",
            score=0.0,
            available=False,
            weight=LAYER_WEIGHT,
            reason="No cell tower data provided — network layer unavailable",
            grace_flag=False,
            metadata={"towers": 0, "wifi_hashes": len(claim.wifi_ssid_hashes)},
        )

    towers = len(claim.cell_tower_ids)

    if towers >= 2:
        base_score = 1.0
        reason = f"Strong triangulation with {towers} cell towers"
    else:
        base_score = 0.5
        reason = "Single tower connection — low triangulation confidence"

    # WiFi environment boost — applied on top of cell tower base score
    wifi_count = len(claim.wifi_ssid_hashes)
    wifi_boosted = False

    if wifi_count >= _WIFI_MIN_COUNT:
        base_score = min(1.0, base_score + _WIFI_BOOST)
        wifi_boosted = True
        reason += f" | WiFi environment validated ({wifi_count} SSIDs — physical presence confirmed)"

    return LayerResult(
        layer_name="NetworkTopology",
        score=round(base_score, 3),
        available=True,
        weight=LAYER_WEIGHT,
        reason=reason,
        grace_flag=False,
        metadata={
            "towers": towers,
            "wifi_hashes": wifi_count,
            "wifi_boost_applied": wifi_boosted,
        },
    )
