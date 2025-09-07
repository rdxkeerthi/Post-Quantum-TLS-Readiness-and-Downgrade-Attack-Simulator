# OpenSSL DoS detection logic stub for AI anomaly module

def detect_renegotiation_dos(handshake_log):
    """Return True if renegotiation loop detected in handshake log."""
    for entry in handshake_log:
        if entry.get("renegotiation_loop", False):
            return True
    return False

# Integrate this in ai_anomaly/ or dashboard/detect.py
