import argparse
import json
import click
from pq_tls_sim.handshake.simulator import TLSSimulator, Policy
from pq_tls_sim.handshake.downgrade import strip_pq_groups, strip_pq_sigs, force_tls12, strip_hybrid_only, noop
from blockchain.fabric_client import log_event_to_blockchain

ATTACKS = {
    "none": noop,
    "strip_pq_groups": strip_pq_groups,
    "strip_pq_sigs": strip_pq_sigs,
    "force_tls12": force_tls12,
    "strip_hybrid_only": strip_hybrid_only
}

def load_policy(obj):
    return Policy(
        kem_offers=obj['kem_offers'],
        sig_offers=obj['sig_offers'],
        require_pq=obj.get('require_pq', False),
        require_hybrid=obj.get('require_hybrid', False),
        pq_allowed=obj.get('pq_allowed', True),
        grease=obj.get('grease', True),
        cert_sigalg=obj.get('cert_sigalg', None),
        impl=obj.get('impl', None)
    )

def run_simulation(scenario_path, attack_name):
    import os
    import datetime
    from ai_anomaly.detect import detect_anomalies

    with open(scenario_path) as f:
        scen = json.load(f)
    
    # Create unique log file name with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    scenario_name = os.path.splitext(os.path.basename(scenario_path))[0]
    log_file = f"{scenario_name}_{timestamp}.log"
    
    client, server = load_policy(scen['client']), load_policy(scen['server'])
    sim = TLSSimulator(client, server)
    result = sim.run_handshake(attack=ATTACKS[attack_name])
    
    # Create detailed handshake log
    log_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'scenario': scenario_name,
        'attack': attack_name,
        'handshake': {
            'selected_kem': result.selected_kem,
            'selected_sig': result.selected_sig,
            'alerts': result.alerts,
            'transcript': result.transcript,
            'success': bool(result.selected_kem and result.selected_sig)
        },
        'config': {
            'client': {
                'supported_groups': scen['client'].get('kem_offers', []),
                'signature_algorithms': scen['client'].get('sig_offers', []),
                'require_pq': scen['client'].get('require_pq', False),
                'require_hybrid': scen['client'].get('require_hybrid', False)
            },
            'server': {
                'supported_groups': scen['server'].get('kem_offers', []),
                'signature_algorithms': scen['server'].get('sig_offers', []),
                'require_pq': scen['server'].get('require_pq', False),
                'require_hybrid': scen['server'].get('require_hybrid', False)
            }
        }
    }

    # Save detailed log
    os.makedirs("data/logs", exist_ok=True)
    log_path = os.path.join("data/logs", log_file)
    with open(log_path, "w") as logf:
        json.dump(log_data, logf, indent=2)

    # Run AI anomaly detection
    anomalies = detect_anomalies(log_data)
    if anomalies:
        log_data['anomalies'] = anomalies
        # Save anomalies to a separate file
        os.makedirs("data/anomalies", exist_ok=True)
        anomaly_path = os.path.join("data/anomalies", log_file)
        with open(anomaly_path, "w") as af:
            json.dump(anomalies, af, indent=2)
    
    # Log to blockchain with extended information
    event_data = {
        'scenario': scenario_name,
        'attack': attack_name,
        'timestamp': log_data['timestamp'],
        'result': log_data['handshake'],
        'client_info': log_data['config']['client'],
        'server_info': log_data['config']['server'],
        'anomalies': anomalies if anomalies else []
    }
    log_event_to_blockchain(event_data)
    print("=== RESULT ===")
    print(f"KEM: {result.selected_kem}, SIG: {result.selected_sig}")
    print("=== ALERTS ===")
    print("\n".join(result.alerts) if result.alerts else "none")
    print("=== TRANSCRIPT ===")
    print(result.transcript)

@click.command()
@click.option('--scenario', type=click.Path(exists=True), required=True, help='Path to scenario JSON file')
@click.option('--attack', type=click.Choice(list(ATTACKS.keys())), default='none', help='MITM attack type')
def main(scenario, attack):
    """Run a TLS handshake simulation scenario."""
    run_simulation(scenario, attack)

if __name__ == "__main__":
    main()