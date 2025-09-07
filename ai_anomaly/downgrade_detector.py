# Downgrade attack detection logic stub for AI anomaly module

def detect_pq_downgrade(handshake_log):
    """Return True if PQ/hybrid ciphers are stripped and TLS 1.2 is negotiated."""
    for entry in handshake_log:
        if entry.get("version") == "TLS1.2" and not any(k.startswith("KYBER") or k.startswith("HYBRID") for k in entry.get("kem", [])):
            return True
    return False

# Integrate this in ai_anomaly/ or dashboard/detect.py
