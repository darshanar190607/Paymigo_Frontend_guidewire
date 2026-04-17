from pydantic import BaseModel
from typing import List

class ConsentRecord(BaseModel):
    """Data model tracking explicit user permissions."""
    microphone_granted: bool = False
    motion_granted: bool = False

def get_consented_sensors(consent: ConsentRecord) -> List[str]:
    """
    Returns a list of sensors the Coherence Engine is legally allowed to use.
    """
    allowed_sensors = []
    
    if consent.microphone_granted:
        allowed_sensors.append("acoustic")
    if consent.motion_granted:
        allowed_sensors.append("inertial")
        
    return allowed_sensors