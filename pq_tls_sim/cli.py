import argparse
import json
import click
from .handshake.simulator import TLSSimulator, Policy
from .handshake.downgrade import strip_pq_groups, strip_pq_sigs, force_tls12, strip_hybrid_only, noop

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
    with open(scenario_path) as f:
        scen = json.load(f)
    client, server = load_policy(scen['client']), load_policy(scen['server'])
    sim = TLSSimulator(client, server)
    result = sim.run_handshake(attack=ATTACKS[attack_name])
    # Write logs to file for dashboard and AI
    with open("/data/handshake.log", "w") as logf:
        logf.write(f"KEM: {result.selected_kem}, SIG: {result.selected_sig}\n")
        logf.write("ALERTS:\n")
        logf.write("\n".join(result.alerts) + "\n")
        logf.write("TRANSCRIPT:\n")
        logf.write(result.transcript + "\n")
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