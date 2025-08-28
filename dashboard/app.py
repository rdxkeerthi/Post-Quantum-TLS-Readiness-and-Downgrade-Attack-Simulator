
from flask import Flask, jsonify, render_template_string
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../ai_anomaly')))
from detect import detect_anomalies

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string("""
    <h1>PQ-TLS Dashboard</h1>
    <ul>
      <li><a href='/logs'>View Handshake Logs</a></li>
      <li><a href='/anomalies'>View AI Anomaly Detections</a></li>
    </ul>
    """)

@app.route('/logs')
def logs():
    log_path = '/data/handshake.log'
    if not os.path.exists(log_path):
        return 'No logs found.'
    with open(log_path) as f:
        content = f.read()
    return f"<pre>{content}</pre>"

@app.route('/anomalies')
def anomalies():
    log_path = '/data/handshake.log'
    if not os.path.exists(log_path):
        return jsonify([])
    with open(log_path) as f:
        lines = f.readlines()
    flagged = detect_anomalies(lines)
    return render_template_string("""
    <h2>AI Anomaly Detection Results</h2>
    <ul>
    {% for line in flagged %}
      <li>{{ line }}</li>
    {% endfor %}
    </ul>
    <a href='/'>Back</a>
    """, flagged=flagged)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
