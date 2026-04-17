from typing import Dict, Any

def evaluate_mock_status(is_from_mock_provider: bool) -> Dict[str, Any]:
    """
    Evaluates if the GPS coordinates are coming from a spoofing app.
    Returns a dictionary with penalty instructions for the Coherence Engine.
    """
    if is_from_mock_provider:
        return {
            "is_flagged": True,
            "flag_name": "mock_location_detected",
            "recommended_tier": "FROZEN", # Pushes the claim to Tier 4
            "penalty_score": 90           # Subtracts 90 points from Truth Score
        }
    
    return {
        "is_flagged": False,
        "flag_name": None,
        "recommended_tier": None,
        "penalty_score": 0
    }