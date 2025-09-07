# POODLE detection logic stub for AI anomaly module

def detect_cbc_padding_oracle(handshake_log):
    """Return True if TLS 1.0 and CBC cipher with padding oracle detected."""
    for entry in handshake_log:
        if entry.get("version") == "TLS1.0" and entry.get("cbc_padding_oracle", False):
            return True
    return False

# Integrate this in ai_anomaly/ or dashboard/detect.py
