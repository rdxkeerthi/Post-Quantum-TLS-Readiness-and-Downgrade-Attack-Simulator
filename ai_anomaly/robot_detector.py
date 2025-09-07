# ROBOT detection logic stub for AI anomaly module

def detect_rsa_padding_oracle(handshake_log):
    """Return True if RSA padding oracle detected in handshake log."""
    for entry in handshake_log:
        if entry.get("rsa_padding_oracle", False):
            return True
    return False
