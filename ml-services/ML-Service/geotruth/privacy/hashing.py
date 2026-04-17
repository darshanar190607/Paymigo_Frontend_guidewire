import hashlib
from typing import List

def hash_identifier(raw_id: str) -> str:
    """
    Takes a raw string (like a WiFi SSID or Cell Tower ID) and returns a SHA-256 hash.
    This ensures we never store personally identifiable information (PII).
    """
    if not raw_id:
        return ""
    # .encode('utf-8') converts the string to bytes, which the hasher requires
    return hashlib.sha256(raw_id.encode('utf-8')).hexdigest()

def hash_network_list(network_ids: List[str]) -> List[str]:
    """
    Takes a list of raw network IDs and returns a list of hashed IDs.
    Uses list comprehension for speed.
    """
    return [hash_identifier(net_id) for net_id in network_ids]