# Logjam detection logic stub for AI anomaly module

def detect_weak_dh_group(handshake_log):
    """Return True if a DH group < 2048 bits is detected in handshake log."""
    for entry in handshake_log:
        if entry.get("dh_group", 2048) < 2048:
            return True
    return False

# Integrate this in ai_anomaly/ or dashboard/detect.py
