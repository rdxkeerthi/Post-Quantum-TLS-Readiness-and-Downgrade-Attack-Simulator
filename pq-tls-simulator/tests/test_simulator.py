from pq_tls_sim.handshake.simulator import TLSSimulator, Policy
from pq_tls_sim.handshake.downgrade import strip_pq_from_clienthello
import json

def pol(o): return Policy(o["kem_offers"], o["sig_offers"], o.get("require_pq",False), o.get("pq_allowed",True), o.get("grease",True))

def test_default_pq_selected():
    scen = {"client":{"kem_offers":["hybrid_x25519_kyber768","x25519"],"sig_offers":["hybrid_ecdsa_dilithium3","ecdsa_secp256r1_sha256"]},
            "server":{"kem_offers":["hybrid_x25519_kyber768","x25519"],"sig_offers":["hybrid_ecdsa_dilithium3","ecdsa_secp256r1_sha256"]}}
    r = TLSSimulator(pol(scen["client"]), pol(scen["server"])).run_handshake()
    assert r.selected_kem.startswith("hybrid_")
    assert r.selected_sig.startswith("hybrid_")

def test_mitm_downgrade_detected():
    scen = {"client":{"kem_offers":["kyber768","x25519"],"sig_offers":["dilithium3","ecdsa_secp256r1_sha256"],"grease":True},
            "server":{"kem_offers":["kyber768","x25519"],"sig_offers":["dilithium3","ecdsa_secp256r1_sha256"]}}
    r = TLSSimulator(pol(scen["client"]), pol(scen["server"])).run_handshake(attack=strip_pq_from_clienthello)
    assert any("mismatch" in a for a in r.alerts)

def test_default_scenario():
    scenario = {
        "name": "Test Default",
        "client": {"pq_supported": True},
        "server": {"pq_supported": True},
        "mitm": {"enabled": False}
    }
    sim = TLSSimulator(scenario)
    sim.run()

def test_mitm_downgrade():
    scenario = {
        "name": "Test MITM Downgrade",
        "client": {"pq_supported": True},
        "server": {"pq_supported": True},
        "mitm": {"enabled": True, "strip_pq": True}
    }
    sim = TLSSimulator(scenario)
    sim.run()
