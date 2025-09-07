# TLS renegotiation injection detection logic stub for AI anomaly module

def detect_renegotiation_injection(handshake_log):
    """Return True if renegotiation injection detected in handshake log."""
    for entry in handshake_log:
        if entry.get("renegotiation_injection", False):
            return True
    return False
