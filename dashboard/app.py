
from builtins import open, sorted, Exception, str, int, len, sum, dict, any, print
import sys
import os

# Ensure parent workspace on sys.path so local packages (pq_tls_sim, blockchain) import correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
import json
import importlib.util
import subprocess
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from pq_tls_sim.handshake.simulator import TLSSimulator, Policy
from pq_tls_sim.handshake.downgrade import (
    strip_pq_groups,
    strip_pq_sigs,
    force_tls12,
    strip_hybrid_only,
    noop,
)

app = Flask(__name__)
app.secret_key = 'pq-tls-simulator-secret'

ATTACKS = {
    'none': noop,
    'strip_pq_groups': strip_pq_groups,
    'strip_pq_sigs': strip_pq_sigs,
    'force_tls12': force_tls12,
    'strip_hybrid_only': strip_hybrid_only,
}


def load_policy(obj):
    return Policy(
        kem_offers=obj.get('kem_offers', []),
        sig_offers=obj.get('sig_offers', []),
        require_pq=obj.get('require_pq', False),
        require_hybrid=obj.get('require_hybrid', False),
        pq_allowed=obj.get('pq_allowed', True),
        grease=obj.get('grease', True),
        cert_sigalg=obj.get('cert_sigalg', None),
        impl=obj.get('impl', None),
    )


@app.route('/api/run_scenario', methods=['POST'])
def run_scenario_api():
    """Run a TLS handshake simulation scenario from the web UI."""
    data = request.get_json() or {}
    scenario_path = data.get('scenario_path')
    attack_name = data.get('attack', 'none')
    try:
        if not scenario_path or not os.path.exists(scenario_path):
            return jsonify({'error': 'scenario_path missing or not found'}), 400

        with open(scenario_path) as f:
            scen = json.load(f)

        client, server = load_policy(scen.get('client', {})), load_policy(scen.get('server', {}))
        sim = TLSSimulator(client, server)
        result = sim.run_handshake(attack=ATTACKS.get(attack_name, noop))

        # Persist transcript and basic run metadata back into scenario file so UI picks it up
        try:
            with open(scenario_path, 'r') as sf:
                sjson = json.load(sf)
        except Exception:
            sjson = {}

        sjson['transcript'] = getattr(result, 'transcript', '')
        sjson['last_run'] = datetime.now().isoformat()
        sjson['alerts'] = getattr(result, 'alerts', [])
        sjson['selected_kem'] = getattr(result, 'selected_kem', None)
        sjson['selected_sig'] = getattr(result, 'selected_sig', None)
        try:
            with open(scenario_path, 'w') as sf:
                json.dump(sjson, sf, indent=2)
        except Exception:
            pass

        # Run anomaly detection on transcript and persist anomaly if found
        anomaly = None
        try:
            anomaly = detect_anomalies(sjson.get('transcript', ''))
            if anomaly and isinstance(anomaly, dict):
                try:
                    with open(scenario_path, 'r') as sf:
                        sjson = json.load(sf)
                except Exception:
                    sjson = {}
                sjson['anomaly'] = anomaly
                try:
                    with open(scenario_path, 'w') as sf:
                        json.dump(sjson, sf, indent=2)
                except Exception:
                    pass
        except Exception:
            anomaly = None

        # Add event to blockchain for centralized logging (non-fatal)
        try:
            add_event_to_blockchain({
                'timestamp': datetime.now().isoformat(),
                'scenario': os.path.basename(scenario_path),
                'result': {
                    'selected_kem': sjson.get('selected_kem'),
                    'selected_sig': sjson.get('selected_sig'),
                    'alerts': sjson.get('alerts', []),
                    'transcript': sjson.get('transcript', ''),
                    'anomaly': anomaly,
                },
            })
        except Exception:
            pass

        return jsonify(
            selected_kem=sjson.get('selected_kem'),
            selected_sig=sjson.get('selected_sig'),
            alerts=sjson.get('alerts', []),
            transcript=sjson.get('transcript', ''),
            anomaly=anomaly,
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- remaining imports and helper wiring ---
from ai_anomaly.detect import detect_anomalies

# Add parent directory and blockchain to Python path to make imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
blockchain_dir = os.path.join(parent_dir, 'blockchain')
sys.path.extend([parent_dir, blockchain_dir])

blockchain_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../blockchain/fabric_client.py'))
spec = importlib.util.spec_from_file_location('fabric_client', blockchain_path)
fabric_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fabric_client)
query_events_from_blockchain = getattr(fabric_client, 'query_events_from_blockchain', lambda: [])
add_event_to_blockchain = getattr(fabric_client, 'add_event_to_blockchain', lambda *_: None)

# Custom template filters
@app.template_filter('format_timestamp')
def format_timestamp(timestamp):
    """Format ISO timestamp to a human-readable string"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime('%B %d, %Y %H:%M:%S')
    except Exception:
        return str(timestamp)


@app.template_filter('split')
def split_filter(value, delimiter=','):
    """Split a string by delimiter"""
    try:
        return value.split(delimiter)
    except Exception:
        return [value]


@app.template_filter('format_json')
def format_json(value):
    """Format JSON string to pretty print"""
    if isinstance(value, str):
        try:
            return json.dumps(json.loads(value), indent=2)
        except Exception:
            return value
    try:
        return json.dumps(value, indent=2)
    except Exception:
        return str(value)


def get_sample_logs(min_count=50):
    """Load real-time logs from scenarios directory. If there are fewer than min_count
    scenarios, synthesize additional placeholder entries so the UI shows many cards.
    This avoids mutating scenario files while providing the large-card view requested.
    """
    logs = []
    scenarios_dir = os.path.join(os.path.dirname(__file__), '../scenarios')
    real_logs = []
    if os.path.exists(scenarios_dir):
        for filename in sorted(os.listdir(scenarios_dir)):
            if filename.endswith('.json'):
                scenario_path = os.path.join(scenarios_dir, filename)
                try:
                    with open(scenario_path) as f:
                        data = json.load(f)
                        log = {
                            'id': filename,
                            'title': data.get('title', filename.replace('_', ' ').replace('.json', '').title()),
                            'details': data.get('description', ''),
                            'protocol': data.get('protocol', ''),
                            'status': data.get('status', 'success'),
                            'timestamp': data.get('last_run', data.get('timestamp', datetime.now().isoformat())),
                            'cipher_suite': data.get('cipher_suite', ''),
                            'transcript': data.get('transcript', ''),
                        }
                        real_logs.append(log)
                except Exception:
                    continue

    # If there are no real logs, create a few helpful placeholders
    if not real_logs:
        for i in range(1, min(8, min_count + 1)):
            real_logs.append({
                'id': f'placeholder-{i}.json',
                'title': f'Placeholder Scenario {i}',
                'details': 'No description available',
                'protocol': 'TLS1.3',
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'cipher_suite': '',
                'transcript': '',
            })

    # Synthesize duplicates to reach min_count (do not write to disk)
    idx = 0
    while len(logs) < min_count:
        base = real_logs[idx % len(real_logs)] if real_logs else {
            'id': f'auto-{idx}.json',
            'title': f'Auto Scenario {idx}',
            'details': '',
            'protocol': '',
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'cipher_suite': '',
            'transcript': '',
        }
        copy = dict(base)
        # make id unique
        copy['id'] = f"{base['id'].replace('.json','')}-{idx}.json"
        # stagger timestamps
        copy['timestamp'] = datetime.now().isoformat()
        logs.append(copy)
        idx += 1

    return logs


def get_sample_anomalies():
    """Load real-time anomalies from scenarios directory"""
    anomalies = []
    scenarios_dir = os.path.join(os.path.dirname(__file__), '../scenarios')
    if os.path.exists(scenarios_dir):
        for filename in sorted(os.listdir(scenarios_dir)):
            if filename.endswith('.json'):
                scenario_path = os.path.join(scenarios_dir, filename)
                try:
                    with open(scenario_path) as f:
                        data = json.load(f)
                        if 'anomaly' in data and data['anomaly']:
                            anomaly = data['anomaly']
                            # Normalize anomaly into a dict
                            anomaly = anomaly if isinstance(anomaly, dict) else {'detail': anomaly}
                            anomaly.setdefault('id', filename)
                            anomaly.setdefault('scenario', data.get('title', filename))
                            anomaly.setdefault('timestamp', anomaly.get('timestamp', datetime.now().isoformat()))
                            # Derive a numeric risk_score if not present from severity or findings
                            if 'risk_score' not in anomaly:
                                score = 0
                                sev = (anomaly.get('severity') or '').lower()
                                if sev == 'critical':
                                    score = 90
                                elif sev == 'high':
                                    score = 70
                                elif sev == 'medium':
                                    score = 45
                                elif sev == 'low':
                                    score = 20
                                else:
                                    # If findings exist, estimate score from count/severity
                                    findings = anomaly.get('findings') or []
                                    for f in findings:
                                        fsev = (f.get('severity') or '').lower()
                                        if fsev == 'critical':
                                            score += 30
                                        elif fsev == 'high':
                                            score += 20
                                        elif fsev == 'medium':
                                            score += 10
                                        else:
                                            score += 5
                                    # clamp
                                    score = min(95, score if score else 10)
                                anomaly['risk_score'] = int(score)
                            anomalies.append(anomaly)
                except Exception:
                    continue

    return anomalies

@app.route('/')
def index():
    """Dashboard homepage"""
    try:
        logs = get_sample_logs()
        anomalies = get_sample_anomalies()
        total_scenarios = len(logs)
        active_tests = sum(1 for log in logs if log.get('status', '') == 'success')
        anomalies_today = sum(1 for anomaly in anomalies if anomaly.get('timestamp', '').startswith(datetime.now().date().isoformat()))
        success_rate = int((active_tests / total_scenarios) * 100) if total_scenarios else 0
        stats = {
            'total_scenarios': total_scenarios,
            'active_tests': active_tests,
            'anomalies_today': anomalies_today,
            'success_rate': success_rate
        }
        recent_events = [
            {
                'title': log['title'],
                'description': log['details'],
                'timestamp': log['timestamp'],
                'status': log['status']
            } for log in logs[-10:]
        ]
        return render_template('index.html', stats=stats, recent_events=recent_events)
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return render_template('index.html', stats={}, recent_events=[])


@app.route('/logs')
def logs():
    """Handshake logs page"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 50
        all_logs = get_sample_logs()
        # Show up to 50 logs per page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        logs = all_logs[start_idx:end_idx]
        total_pages = (len(all_logs) + per_page - 1) // per_page
        # Ensure transcript is always present
        for log in logs:
            if not log.get('transcript'):
                log['transcript'] = log.get('details', '')
        return render_template('logs.html', logs=logs, current_page=page, total_pages=total_pages)
    except Exception as e:
        flash(f"Error loading logs: {str(e)}", "danger")
        return render_template('logs.html', logs=[], current_page=1, total_pages=1)

# previous helper view removed to avoid route collision; anomalies() below is the active view

@app.route('/anomalies')
def anomalies():
    """Anomaly detection page"""
    try:
        anomalies = get_sample_anomalies()
        stats = {
            'total_anomalies': len(anomalies),
            'critical': sum(1 for a in anomalies if a.get('severity', '').lower() == 'critical'),
            'high': sum(1 for a in anomalies if a.get('severity', '').lower() == 'high'),
            'medium': sum(1 for a in anomalies if a.get('severity', '').lower() == 'medium'),
            'low': sum(1 for a in anomalies if a.get('severity', '').lower() == 'low'),
            'blocked': sum(1 for a in anomalies if a.get('status', '') == 'blocked')
        }
        return render_template('anomalies.html', anomalies=anomalies, stats=stats)
    except Exception as e:
        flash(f"Error loading anomalies: {str(e)}", "danger")
        return render_template('anomalies.html', anomalies=[], stats={})

@app.route("/report")
def report():
    """Security reports page"""
    try:
        logs = get_sample_logs()
        anomalies = get_sample_anomalies()
        pq_ready = sum(1 for log in logs if 'KYBER' in log.get('cipher_suite', ''))
        vulnerabilities = []
        risk_levels = ['Low', 'Medium', 'High', 'Critical']
        for i, log in enumerate(logs):
            status = (log.get('status') or '').lower()
            if status in ['error', 'failed']:
                rl = 'Critical'
            elif status == 'warning':
                rl = 'High'
            elif status == 'success':
                rl = 'Low'
            else:
                rl = 'Medium'
            vulnerabilities.append({
                'component': log.get('title', ''),
                'status': log.get('status', ''),
                'risk_level': rl,
                'action': 'Review scenario' if status in ['warning', 'error', 'failed'] else 'No action required'
            })
        stats = {
            'pq_readiness': int((pq_ready / len(logs)) * 100) if logs else 0,
            'vulnerabilities': sum(1 for log in logs if log.get('status', '') == 'warning'),
            'attacks_blocked': sum(1 for log in logs if log.get('status', '') == 'success'),
            'compliance_score': 100 if pq_ready == len(logs) and logs else int((pq_ready / len(logs)) * 100) if logs else 0
        }
        # Analytics: count risk levels from vulnerabilities
        analytics = {level: sum(1 for v in vulnerabilities if v['risk_level'] == level) for level in risk_levels}

        # If empty, try to populate analytics from anomalies and blockchain events
        if sum(analytics.values()) == 0:
            # From anomalies severity
            for lvl in risk_levels:
                analytics.setdefault(lvl, 0)
            for a in anomalies:
                sev = a.get('severity', '').lower()
                if sev == 'critical':
                    analytics['Critical'] += 1
                elif sev == 'high':
                    analytics['High'] += 1
                elif sev == 'medium':
                    analytics['Medium'] += 1
                elif sev == 'low':
                    analytics['Low'] += 1

            # From blockchain events risk_assessment if available
            try:
                events = query_events_from_blockchain()
                for e in events:
                    level = e.get('risk_assessment', {}).get('level', '').title()
                    if level in analytics:
                        analytics[level] += 1
            except Exception:
                pass

        return render_template('report.html', stats=stats, vulnerabilities=vulnerabilities, analytics=analytics)
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
                scenario_path = os.path.join(scenario_dir, filename)
                try:
                    with open(scenario_path) as sf:
                        sdata = json.load(sf)
                except Exception:
                    sdata = {}
                scenario_name = sdata.get('title', os.path.splitext(filename)[0].replace('_', ' ').title())
                scenarios.append({
                    'id': filename,
                    'name': scenario_name,
                    'file': filename,
                    'path': scenario_path,
                    'description': sdata.get('description', ''),
                    'duration': sdata.get('duration', ''),
                    'complexity': sdata.get('complexity', 'Low')
                })
                
    return render_template("tests.html", scenarios=scenarios)


@app.route('/upload_scenario', methods=['POST'])
def upload_scenario():
    """Accept a scenario JSON upload and save it to scenarios directory."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'no file provided'}), 400
        f = request.files['file']
        filename = f.filename
        if not filename.endswith('.json'):
            return jsonify({'error': 'only .json files allowed'}), 400
        scenarios_dir = os.path.join(parent_dir, 'scenarios')
        os.makedirs(scenarios_dir, exist_ok=True)
        path = os.path.join(scenarios_dir, filename)
        f.save(path)
        return jsonify({'ok': True, 'path': path}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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


@app.route('/scenario_details/<scenario_id>')
def scenario_details(scenario_id):
    """Return JSON contents of a scenario file for the UI details modal."""
    try:
        safe_filename = os.path.basename(scenario_id)
        scenario_path = os.path.join(parent_dir, 'scenarios', safe_filename)
        if not os.path.exists(scenario_path):
            return jsonify({'error': 'scenario not found'}), 404
        with open(scenario_path) as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/blockchain_log')
def blockchain_log():
    """Return a small HTML fragment of recent blockchain events for UI refresh."""
    try:
        events = []
        try:
            events = query_events_from_blockchain() or []
        except Exception:
            events = []
        # Render a compact HTML list
        html = '<ul class="space-y-2 text-sm">\n'
        for e in (events or [])[:10]:
            ts = e.get('timestamp', '')
            title = e.get('scenario', e.get('result', {}).get('scenario', 'event'))
            html += f"<li><strong>{title}</strong> - {ts}</li>"
        html += '</ul>'
        return html
    except Exception:
        return ''


if __name__ == '__main__':
    # Run with 0.0.0.0 for container/local access, debug off by default
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
