def generate_suggestions(context):
    suggestions = []

    # Risk-based suggestions
    if context.get("risk") == "high":
        suggestions.append("Upgrade plan for protection")
        suggestions.append("View safety tips")
    
    # Claim-based suggestions
    if context.get("claim_status") == "processing":
        suggestions.append("Track my claim")
        suggestions.append("Upload proof to speed up")
    elif context.get("claim_status") == "delayed":
        suggestions.append("Talk to human support")
        suggestions.append("Why is it delayed?")

    # Premium/Loyalty suggestions
    if context.get("premium_tier") != "Elite":
        suggestions.append("Elite plan benefits")
    
    # General/Always helpful
    if not suggestions:
        suggestions = ["Is it safe today?", "How do triggers work?", "Tell me about GeoTruth"]
    
    # Return top 3 unique suggestions
    return list(dict.fromkeys(suggestions))[:3]
