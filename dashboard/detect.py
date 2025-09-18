# Copied AI anomaly detection for dashboard import
# In sync with ai_anomaly/detect.py

def detect_anomalies(logs):
    # Dummy: flag if 'downgrade' or 'mismatch' in any log line
    return [line for line in logs if 'downgrade' in line or 'mismatch' in line]


if __name__ == "__main__":
    import sys
    import os
    import json
    if len(sys.argv) < 2:
        print("Usage: python detect.py <logfile>")
        sys.exit(1)
    logfile = sys.argv[1]
    try:
        with open(logfile) as f:
            lines = f.readlines()
        flagged = detect_anomalies(lines)
        print("AI Anomaly Detection Results:")
        for line in flagged:
            print(line.strip())
        # Save anomalies to the absolute data/anomalies/ directory
        if flagged:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            anomalies_dir = os.path.join(base_dir, "data", "anomalies")
            os.makedirs(anomalies_dir, exist_ok=True)
            outpath = os.path.join(anomalies_dir, os.path.basename(logfile) + ".anomaly.json")
            with open(outpath, "w") as out:
                json.dump(flagged, out, indent=2)
    except Exception as e:
        print(f"Error: {e}")
