# Heartbleed detection logic stub for AI anomaly module

def detect_heartbeat_overflow(handshake_log):
    """Return True if a malicious heartbeat request is detected."""
    for entry in handshake_log:
        if entry.get("heartbeat_overflow", False):
            return True
    return False
