# Copied AI anomaly detection for dashboard import
# In sync with ai_anomaly/detect.py

def detect_anomalies(logs):
    # Dummy: flag if 'downgrade' or 'mismatch' in any log line
    return [line for line in logs if 'downgrade' in line or 'mismatch' in line]
