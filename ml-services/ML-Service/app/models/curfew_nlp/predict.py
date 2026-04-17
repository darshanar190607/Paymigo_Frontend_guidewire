"""
Curfew NLP predict stub.
No trained model exists yet — returns a rule-based risk score
based on keyword matching until a real NLP model is trained.
"""

CURFEW_KEYWORDS = {
    "high": ["curfew", "lockdown", "shutdown", "ban", "prohibited", "restricted", "emergency", "riot", "protest"],
    "medium": ["advisory", "warning", "alert", "caution", "delay", "disruption", "closure"],
}


def predict(payload: dict) -> dict:
    headline = payload.get("headline", "").lower()

    for word in CURFEW_KEYWORDS["high"]:
        if word in headline:
            return {"risk_level": "high", "score": 0.9, "matched_keyword": word, "model": "rule_based"}

    for word in CURFEW_KEYWORDS["medium"]:
        if word in headline:
            return {"risk_level": "medium", "score": 0.5, "matched_keyword": word, "model": "rule_based"}

    return {"risk_level": "low", "score": 0.1, "matched_keyword": None, "model": "rule_based"}
