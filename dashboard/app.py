from flask import Flask, jsonify, render_template_string, render_template, request, redirect, url_for, flash
import os
import sys
import json
from datetime import datetime
import subprocess

# Add parent directory and blockchain to Python path to make imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
blockchain_dir = os.path.join(parent_dir, 'blockchain')
sys.path.extend([parent_dir, blockchain_dir])

from ai_anomaly.detect import detect_anomalies
import fabric_client
query_events_from_blockchain = fabric_client.query_events_from_blockchain
add_event_to_blockchain = fabric_client.add_event_to_blockchain

app = Flask(__name__)
app.secret_key = 'pq-tls-simulator-secret'  # Required for flash messages

# Custom template filters
@app.template_filter('format_timestamp')
def format_timestamp(timestamp):
    """Format ISO timestamp to a human-readable string"""
    from datetime import datetime
    dt = datetime.fromisoformat(timestamp)
    return dt.strftime('%B %d, %Y %H:%M:%S')

@app.template_filter('split')
def split_filter(value, delimiter=','):
    """Split a string by delimiter"""
    return value.split(delimiter)

@app.template_filter('format_json')
def format_json(value):
    """Format JSON string to pretty print"""
    if isinstance(value, str):
        try:
            return json.dumps(json.loads(value), indent=2)
        except:
            return value
    return json.dumps(value, indent=2)

def get_sample_logs():
    """Generate sample log data"""
    return [
        {
            'id': 1,
            'title': 'TLS 1.3 Handshake',
            'details': 'Client initiated PQ-TLS connection with Kyber768',
            'protocol': 'TLS 1.3',
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'cipher_suite': 'TLS_KYBER768_WITH_CHACHA20_POLY1305_SHA384'
        },
        {
            'id': 2,
            'title': 'Downgrade Attack Detected',
            'details': 'MITM attempted to strip PQ algorithms',
            'protocol': 'TLS 1.4',
            'status': 'warning',
            'timestamp': datetime.now().isoformat(),
            'cipher_suite': 'TLS_P256_KYBER512_WITH_AES_256_GCM_SHA384'
        },
        {
            'id': 3,
            'title': 'Certificate Validation',
            'details': 'Validated Dilithium5 server certificate',
            'protocol': 'TLS 1.3',
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'cipher_suite': 'TLS_KYBER1024_WITH_AES_256_GCM_SHA384'
        }
    ]

def get_sample_anomalies():
    """Generate sample anomaly data"""
    return [
        {
            'id': 1,
            'type': 'Downgrade Attack',
            'severity': 'high',
            'description': 'Attempted to force classical algorithms',
            'timestamp': datetime.now().isoformat(),
            'details': {
                'attack_vector': 'MITM proxy',
                'target': 'Key Exchange',
                'mitigation': 'Blocked connection attempt'
            },
            'status': 'blocked'
        },
        {
            'id': 2,
            'type': 'Algorithm Manipulation',
            'severity': 'critical',
            'description': 'Modified supported groups extension',
            'timestamp': datetime.now().isoformat(),
            'details': {
                'attack_vector': 'ClientHello modification',
                'target': 'PQ Groups',
                'mitigation': 'Detected and logged'
            },
            'status': 'detected'
        }
    ]

@app.route('/')
def index():
    """Dashboard homepage"""
    try:
        stats = {
            'total_scenarios': 15,
            'active_tests': 3,
            'anomalies_today': 5,
            'success_rate': 94
        }
        
        recent_events = [
            {
                'title': 'PQ-TLS Handshake Completed',
                'description': 'Successfully negotiated Kyber768 key exchange',
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            },
            {
                'title': 'Downgrade Attack Detected',
                'description': 'Attempted strip of PQ algorithms blocked',
                'timestamp': datetime.now().isoformat(),
                'status': 'warning'
            }
        ]
        
        return render_template('index.html', stats=stats, recent_events=recent_events)
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return render_template('index.html', stats={}, recent_events=[])

@app.route("/logs")
def view_logs():
    # Load all log files from data/logs directory
    logs = []
    log_dir = os.path.join('data', 'logs')
    if os.path.exists(log_dir):
        for filename in sorted(os.listdir(log_dir), reverse=True):
            if filename.endswith('.json'):
                with open(os.path.join(log_dir, filename)) as f:
                    logs.append(json.load(f))
    return render_template("logs.html", logs=logs)

@app.route('/logs')
def logs():
    """Handshake logs page"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 10
        all_logs = get_sample_logs()
        
        # Simple pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        logs = all_logs[start_idx:end_idx]
        total_pages = (len(all_logs) + per_page - 1) // per_page
        
        return render_template('logs.html', 
                             logs=logs,
                             current_page=page,
                             total_pages=total_pages)
    except Exception as e:
        flash(f"Error loading logs: {str(e)}", "danger")
        return render_template('logs.html', logs=[], current_page=1, total_pages=1)

@app.route("/anomalies")
def view_anomalies():
    # Load all anomaly files from data/anomalies directory
    anomalies = []
    anomaly_dir = os.path.join('data', 'anomalies')
    if os.path.exists(anomaly_dir):
        for filename in sorted(os.listdir(anomaly_dir), reverse=True):
            if filename.endswith('.json'):
                with open(os.path.join(anomaly_dir, filename)) as f:
                    anomalies.append(json.load(f))
    return render_template("anomalies.html", anomalies=anomalies)

@app.route('/anomalies')
def anomalies():
    """Anomaly detection page"""
    try:
        anomalies = get_sample_anomalies()
        stats = {
            'total_anomalies': len(anomalies),
            'critical': sum(1 for a in anomalies if a['severity'] == 'critical'),
            'high': sum(1 for a in anomalies if a['severity'] == 'high'),
            'blocked': sum(1 for a in anomalies if a['status'] == 'blocked')
        }
        return render_template('anomalies.html', anomalies=anomalies, stats=stats)
    except Exception as e:
        flash(f"Error loading anomalies: {str(e)}", "danger")
        return render_template('anomalies.html', anomalies=[], stats={})

@app.route("/report")
def report():
    """Security reports page"""
    try:
        stats = {
            'pq_readiness': 87,
            'vulnerabilities': 2,
            'attacks_blocked': 98,
            'compliance_score': 100
        }
        
        vulnerabilities = [
            {
                'component': 'Key Exchange',
                'status': 'secure',
                'risk_level': 'Low',
                'action': 'No action required'
            },
            {
                'component': 'Certificate Chain',
                'status': 'warning',
                'risk_level': 'Medium',
                'action': 'Update root certificates'
            },
            {
                'component': 'Protocol Version',
                'status': 'secure',
                'risk_level': 'Low',
                'action': 'Monitor for new versions'
            }
        ]
        
        return render_template('report.html', 
                             stats=stats, 
                             vulnerabilities=vulnerabilities)
    except Exception as e:
        flash(f"Error loading report: {str(e)}", "danger")
        return render_template('report.html', stats={}, vulnerabilities=[])

@app.route("/run_scenario", methods=["POST"])
def run_scenario():
    scenario_id = request.form.get("scenario_id")
    scenarios_dir = os.path.join(parent_dir, 'scenarios')
    
    # Map of quantum scenarios
    QUANTUM_SCENARIOS = {
        "QUANTUM-2025-001": "quantum_logjam_2025.json",
        "QUANTUM-2025-002": "quantum_poodle_2025.json",
        "QUANTUM-2025-003": "quantum_heartbleed_2025.json",
        "QUANTUM-2025-004": "quantum_robot_2025.json",
        "QUANTUM-2025-005": "quantum_renegotiation_2025.json"
    }
    
    # Map of quantum scenarios and their attacks
    QUANTUM_ATTACKS = {
        "QUANTUM-2025-001": "strip_pq_groups",
        "QUANTUM-2025-002": "force_tls12",
        "QUANTUM-2025-003": "strip_pq_sigs",
        "QUANTUM-2025-004": "strip_hybrid_only",
        "QUANTUM-2025-005": "none"
    }
    
    scenario_file = QUANTUM_SCENARIOS.get(scenario_id)
    attack_type = QUANTUM_ATTACKS.get(scenario_id, "none")
    
    if not scenario_file:
        flash(f"Unknown scenario: {scenario_id}", "danger")
        return redirect(url_for("report"))

    scenario_path = os.path.join(scenarios_dir, scenario_file)
    if not os.path.exists(scenario_path):
        flash(f"Scenario file not found: {scenario_file}", "danger")
        return redirect(url_for("report"))

    # Set up the environment
    env = dict(os.environ)
    env['PYTHONPATH'] = parent_dir + os.pathsep + env.get('PYTHONPATH', '')

    # Run the simulation using the CLI with the appropriate attack type
    try:
        result = subprocess.run([
            "python3", "-m", "pq_tls_sim.cli",
            "--scenario", scenario_path,
            "--attack", attack_type
        ], capture_output=True, text=True, check=True, env=env, cwd=parent_dir)
        
        output = result.stdout
        alert = f"Quantum simulation complete for {scenario_id}. See blockchain for results."
        flash(alert, "info")
        
        # Store results in blockchain
        try:
            with open(scenario_path) as f:
                scenario_data = json.load(f)
            
            # Parse simulation output for key findings
            findings = {
                'quantum_vulnerability': 'quantum_unsafe' in output.lower(),
                'pq_algorithms_used': any(alg in output for alg in ['KYBER', 'Dilithium', 'Falcon']),
                'mitigation_success': 'mitigation successful' in output.lower(),
                'transcript': output
            }
            
            # Add to blockchain (handled by fabric_client.py)
            from blockchain.fabric_client import add_event_to_blockchain
            add_event_to_blockchain({
                'timestamp': datetime.now().isoformat(),
                'scenario': scenario_file,
                'scenario_id': scenario_id,
                'result': findings
            })
            
        except Exception as e:
            print(f"Failed to store in blockchain: {e}")
            
        return redirect(url_for("blockchain_events"))
        
    except subprocess.CalledProcessError as e:
        output = e.stdout + "\n" + e.stderr
        alert = f"Simulation failed: {e}"
        flash(alert, "danger")
        return render_template(
            "report.html",
            scenarios=[],
            stats={},
            pq_checks=[],
            pq_readiness=0,
            error_log=output
        )

@app.route("/blockchain")
def blockchain_events():
    # Get PQ-TLS simulation events
    try:
        print("[DEBUG] Querying blockchain events...")
        events = query_events_from_blockchain()
        print(f"[DEBUG] Found {len(events)} events")
        
        if not events:
            flash("No quantum simulation events found. Run a scenario to generate events.", "info")
            return render_template("blockchain.html", events=[])
            
        # Sort events by timestamp in reverse order (newest first)
        events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return render_template("blockchain.html", events=events)
        
    except Exception as e:
        print(f"[ERROR] Failed to query blockchain: {e}")
        flash(f"Error reading events: {str(e)}", "danger")
        return render_template("blockchain.html", events=[])
    # Enhance events with risk assessment
    for event in events:
        result = event.get('result', {})
        
        # Calculate risk score based on findings
        risk_score = 0
        if result.get('quantum_vulnerability'):
            risk_score += 5  # Critical vulnerability
        if not result.get('pq_algorithms_used'):
            risk_score += 3  # No quantum-safe algorithms
        if not result.get('mitigation_success'):
            risk_score += 2  # Failed mitigation
            
        # Add risk assessment
        event['risk_assessment'] = {
            'score': risk_score,
            'level': 'CRITICAL' if risk_score >= 8 else 'HIGH' if risk_score >= 5 else 'MEDIUM' if risk_score >= 3 else 'LOW',
            'recommendations': []
        }
        
        # Add specific recommendations
        if result.get('quantum_vulnerability'):
            event['risk_assessment']['recommendations'].append(
                "Deploy quantum-resistant algorithms immediately")
        if not result.get('pq_algorithms_used'):
            event['risk_assessment']['recommendations'].append(
                "Enable PQ-TLS with KYBER for key exchange and Dilithium/Falcon for signatures")
        if not result.get('mitigation_success'):
            event['risk_assessment']['recommendations'].append(
                "Review and strengthen quantum attack mitigations")
    
    return render_template(
        "blockchain.html",
        events=events,
        stats={
            'total_events': len(events),
            'high_risk': sum(1 for e in events if e['risk_assessment']['level'] in ['HIGH', 'CRITICAL']),
            'pq_ready': sum(1 for e in events if e['result'].get('pq_algorithms_used', False))
        }
    )

@app.route("/tests")
def view_tests():
    """List available test scenarios."""
    scenarios = []
    scenario_dir = os.path.join(parent_dir, 'scenarios')
    
    if os.path.exists(scenario_dir):
        for filename in sorted(os.listdir(scenario_dir)):
            if filename.endswith('.json'):
                scenario_name = os.path.splitext(filename)[0].replace('_', ' ').title()
                scenarios.append({
                    'name': scenario_name,
                    'file': filename
                })
                
    return render_template("tests.html", scenarios=scenarios)

@app.route("/run-test", methods=['POST'])
def run_test():
    """Run a specific test scenario."""
    scenario = request.form.get('scenario')
    if not scenario:
        flash("No scenario selected", "danger")
        return redirect(url_for('view_tests'))
        
    try:
        # Run the test in a subprocess to avoid blocking
        scenario_path = os.path.join(parent_dir, 'scenarios', scenario)
        if not os.path.exists(scenario_path):
            flash(f"Scenario file not found: {scenario}", "danger")
            return redirect(url_for('view_tests'))
            
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tests/test_cve_attacks.py', '-v'],
            cwd=parent_dir,
            capture_output=True,
            text=True,
            env={**os.environ, 'PQ_TLS_SCENARIO': scenario_path}
        )
        
        # Log the test event to blockchain
        event_data = {
            'scenario': scenario,
            'success': result.returncode == 0,
            'details': {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        }
        add_event_to_blockchain(event_data)
        
        if result.returncode == 0:
            flash("Test completed successfully! Check blockchain for details.", "success")
        else:
            flash("Test failed. Check blockchain for details.", "danger")
            
    except Exception as e:
        flash(f"Error running test: {str(e)}", "danger")
        
    return redirect(url_for('blockchain_events'))
