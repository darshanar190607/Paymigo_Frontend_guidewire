from geotruth.schemas import ClaimVector, LayerResult

def score_acoustic_layer(claim: ClaimVector) -> LayerResult:
    # 1. Privacy / Permission Check
    if not claim.acoustic_feature_vector:
        return LayerResult(
            layer_name="AcousticEnvironment",
            score=0.0,
            available=False,
            weight=25,
            reason="No audio data provided (mic permission denied or unsupported)",
            grace_flag=True 
        )
    
    # 2. Mock Inference (Simulating YAMNet)
    rain_probability = claim.acoustic_feature_vector[0]
    
    if rain_probability > 0.8:
        return LayerResult(
            layer_name="AcousticEnvironment",
            score=1.0,
            available=True,
            weight=25,
            reason="Heavy rain/wind acoustic signature detected",
            grace_flag=False
        )
        
    return LayerResult(
        layer_name="AcousticEnvironment",
        score=0.0,
        available=True,
        weight=25,
        reason="Indoor or silent acoustic profile detected",
        grace_flag=False
    )