#!/usr/bin/env python3
"""
Test Runner for PQ-TLS Scenarios
"""
import os
import sys
import json
import subprocess
from datetime import datetime

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from blockchain.fabric_client import add_event_to_blockchain

def run_all_scenarios():
    """Run all quantum scenarios"""
    scenarios_dir = os.path.join(current_dir, 'scenarios')
    
    # Load scenarios dynamically from the scenarios directory
    def get_scenario_config(scenario_file):
        # Valid attack types supported by the simulator
        VALID_ATTACKS = ['none', 'strip_pq_groups', 'strip_pq_sigs', 'force_tls12', 'strip_hybrid_only']
        
        with open(os.path.join(scenarios_dir, scenario_file)) as f:
            config = json.load(f)
            
            # Map CVE-based attack types to supported attack types
            attack_type = config.get('attack_type', 'none')
            if attack_type not in VALID_ATTACKS:
                # Map attack types to closest matching supported type
                attack_map = {
                    'force_sslv3': 'force_tls12',
                    'force_weak_cipher': 'strip_pq_groups',
                    'force_weak_rsa': 'strip_pq_groups',
                    'padding_oracle': 'strip_pq_groups',
                    'cross_protocol': 'force_tls12',
                    'quantum_sike_break': 'strip_pq_groups',
                    'quantum_rainbow': 'strip_pq_sigs',
                    'ecdsa_spoof': 'strip_pq_sigs',
                    'side_channel': 'strip_pq_sigs',
                    'hybrid_downgrade': 'strip_hybrid_only',
                    'null_deref': 'none',
                    'buffer_overflow': 'none',
                    'dilithium_side_channel': 'strip_pq_sigs'
                }
                attack_type = attack_map.get(attack_type, 'none')
            return attack_type

    # Get all JSON files from scenarios directory recursively
    scenarios = []
    for root, _, files in os.walk(scenarios_dir):
        for file in files:
            if file.endswith('.json'):
                rel_path = os.path.relpath(os.path.join(root, file), scenarios_dir)
                scenarios.append(rel_path)

    # Map scenarios to their attacks
    QUANTUM_SCENARIOS = {
        scenario: get_scenario_config(scenario)
        for scenario in scenarios
    }
    
    results = []
    for scenario_file, attack_type in QUANTUM_SCENARIOS.items():
        scenario_path = os.path.join(scenarios_dir, scenario_file)
        if not os.path.exists(scenario_path):
            print(f"[ERROR] Scenario file not found: {scenario_file}")
            continue
            
        print(f"\nRunning scenario: {scenario_file} with attack: {attack_type}")
        try:
            # Run the simulation
            result = subprocess.run([
                "python3", "-m", "pq_tls_sim.cli",
                "--scenario", scenario_path,
                "--attack", attack_type
            ], capture_output=True, text=True, check=True)
            
            # Parse output
            output = result.stdout
            
            # Load scenario data
            with open(scenario_path) as f:
                scenario_data = json.load(f)
            
            # Ensure required fields exist
            if 'client' not in scenario_data or 'server' not in scenario_data:
                scenario_data['client'] = scenario_data.get('client', {})
                scenario_data['server'] = scenario_data.get('server', {})
            
            # Add default fields if missing
            for party in ['client', 'server']:
                scenario_data[party] = scenario_data.get(party, {})
                if 'kem_offers' not in scenario_data[party]:
                    scenario_data[party]['kem_offers'] = scenario_data[party].get('supported_groups', ['X25519', 'KYBER768', 'KYBER1024'])
                if 'sig_offers' not in scenario_data[party]:
                    scenario_data[party]['sig_offers'] = scenario_data[party].get('signature_algorithms', ['ecdsa_secp256r1_sha256', 'falcon-1024'])
                # Ensure other required fields exist
                if 'require_pq' not in scenario_data[party]:
                    scenario_data[party]['require_pq'] = True
                if 'require_hybrid' not in scenario_data[party]:
                    scenario_data[party]['require_hybrid'] = True
            # Parse key findings
            findings = {
                'quantum_vulnerability': 'quantum_unsafe' in output.lower(),
                'pq_algorithms_used': any(alg in output for alg in ['KYBER', 'Dilithium', 'Falcon']),
                'mitigation_success': 'mitigation successful' in output.lower(),
                'transcript': output
            }
            
            # Add to blockchain
            event_data = {
                'timestamp': datetime.now().isoformat(),
                'scenario': scenario_file,
                'scenario_id': scenario_file.replace('.json', '').upper(),
                'type': 'pq_tls_simulation',
                'result': findings,
                'client_info': scenario_data.get('client', {}),
                'server_info': scenario_data.get('server', {})
            }
            
            add_event_to_blockchain(event_data)
            results.append({
                'scenario': scenario_file,
                'success': True,
                'output': output
            })
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to run scenario {scenario_file}: {e}")
            print("Output:", e.stdout)
            print("Error:", e.stderr)
            results.append({
                'scenario': scenario_file,
                'success': False,
                'error': str(e),
                'output': e.stdout + "\n" + e.stderr
            })
    
    return results

if __name__ == "__main__":
    # Ensure proper Python path
    os.environ['PYTHONPATH'] = parent_dir + os.pathsep + os.environ.get('PYTHONPATH', '')
    
    print("Starting PQ-TLS test runner...")
    results = run_all_scenarios()
    
    # Print summary
    print("\nTest Summary:")
    success_count = sum(1 for r in results if r['success'])
    print(f"Ran {len(results)} scenarios")
    print(f"Success: {success_count}")
    print(f"Failed: {len(results) - success_count}")
    
    # Print failures if any
    failures = [r for r in results if not r['success']]
    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"- {f['scenario']}: {f['error']}")
