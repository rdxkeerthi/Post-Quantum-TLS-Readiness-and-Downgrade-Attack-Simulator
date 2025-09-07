
from pq_tls_sim.handshake.simulator import TLSSimulator, Policy
from pq_tls_sim.handshake.downgrade import strip_pq_groups, strip_pq_sigs, force_tls12, strip_hybrid_only, noop

def pol(o):
    return Policy(
        kem_offers=o.get("kem_offers", []),
        sig_offers=o.get("sig_offers", []),
        require_pq=o.get("require_pq", False),
        require_hybrid=o.get("require_hybrid", False),
        pq_allowed=o.get("pq_allowed", True),
        grease=o.get("grease", True),
        cert_sigalg=o.get("cert_sigalg", None),
        impl=o.get("impl", None)
    )


import logging
import os

# Setup Docker-aware logging
def get_docker_logger():
    logger = logging.getLogger("pq_tls_test")
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

docker_logger = get_docker_logger()

test_results = []

def log_test_result(name, passed, transcript=None):
    msg = f"Test: {name} | {'PASS' if passed else 'FAIL'}"
    if transcript:
        msg += f"\nTranscript:\n{transcript}"
    docker_logger.info(msg)
    test_results.append((name, passed, transcript))
    # Write individual test log to application log file
    log_dir = os.path.join(os.path.dirname(__file__), '../logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'test_results_individual.log')
    with open(log_path, 'a') as f:
        f.write(msg + '\n' + ('-'*60) + '\n')

def pytest_runtest_makereport(item, call):
    # This hook is auto-discovered by pytest
    if call.when == 'call':
        passed = call.excinfo is None
        log_test_result(item.name, passed)

def test_default_pq_selected():
    scen = {
        "client": {
            "kem_offers": ["HYBRID_X25519_KYBER1024", "X25519"],
            "sig_offers": ["hybrid_ecdsa_falcon1024", "ecdsa_secp256r1_sha256"]
        },
        "server": {
            "kem_offers": ["HYBRID_X25519_KYBER1024", "X25519"],
            "sig_offers": ["hybrid_ecdsa_falcon1024", "ecdsa_secp256r1_sha256"]
        }
    }
    r = TLSSimulator(pol(scen["client"]), pol(scen["server"])).run_handshake()
    try:
        assert r.selected_kem.lower().startswith("hybrid")
        assert r.selected_sig.lower().startswith("hybrid")
        log_test_result("test_default_pq_selected", True, r.transcript)
    except AssertionError:
        log_test_result("test_default_pq_selected", False, r.transcript)
        raise

def test_mitm_downgrade_detected():
    scen = {
        "client": {
            "kem_offers": ["KYBER768", "X25519"],
            "sig_offers": ["dilithium3", "ecdsa_secp256r1_sha256"],
            "grease": True
        },
        "server": {
            "kem_offers": ["KYBER768", "X25519"],
            "sig_offers": ["dilithium3", "ecdsa_secp256r1_sha256"]
        }
    }
    r = TLSSimulator(pol(scen["client"]), pol(scen["server"])).run_handshake(attack=strip_pq_groups)
    try:
        assert any("downgrade" in a.lower() or "mismatch" in a.lower() for a in r.alerts)
        log_test_result("test_mitm_downgrade_detected", True, r.transcript)
    except AssertionError:
        log_test_result("test_mitm_downgrade_detected", False, r.transcript)
        raise

def test_default_scenario():
    client = {
        "kem_offers": ["X25519", "KYBER768", "KYBER1024", "HYBRID_X25519_KYBER1024"],
        "sig_offers": ["ecdsa_secp256r1_sha256", "dilithium3", "falcon-1024", "hybrid_ecdsa_falcon1024"],
        "require_pq": True,
        "require_hybrid": True,
        "pq_allowed": True,
        "grease": True,
        "cert_sigalg": "dilithium3",
        "impl": "OpenSSL"
    }
    server = {
        "kem_offers": ["X25519", "KYBER768", "KYBER1024", "HYBRID_X25519_KYBER1024"],
        "sig_offers": ["ecdsa_secp256r1_sha256", "dilithium3", "falcon-1024", "hybrid_ecdsa_falcon1024"],
        "require_pq": True,
        "require_hybrid": True,
        "pq_allowed": True,
        "grease": True,
        "cert_sigalg": "dilithium3",
        "impl": "BoringSSL"
    }
    sim = TLSSimulator(pol(client), pol(server))
    result = sim.run_handshake()
    try:
        assert result.selected_kem in client["kem_offers"]
        log_test_result("test_default_scenario", True, result.transcript)
    except AssertionError:
        log_test_result("test_default_scenario", False, result.transcript)
        raise

def test_mitm_downgrade():
    client = {
        "kem_offers": ["X25519", "KYBER768", "KYBER1024", "HYBRID_X25519_KYBER1024"],
        "sig_offers": ["ecdsa_secp256r1_sha256", "dilithium3", "falcon-1024", "hybrid_ecdsa_falcon1024"],
        "require_pq": True,
        "require_hybrid": True,
        "pq_allowed": True,
        "grease": True,
        "cert_sigalg": "dilithium3",
        "impl": "OpenSSL"
    }
    server = {
        "kem_offers": ["X25519", "KYBER768", "KYBER1024", "HYBRID_X25519_KYBER1024"],
        "sig_offers": ["ecdsa_secp256r1_sha256", "dilithium3", "falcon-1024", "hybrid_ecdsa_falcon1024"],
        "require_pq": True,
        "require_hybrid": True,
        "pq_allowed": True,
        "grease": True,
        "cert_sigalg": "dilithium3",
        "impl": "BoringSSL"
    }
    sim = TLSSimulator(pol(client), pol(server))
    result = sim.run_handshake(attack=strip_pq_groups)
    try:
        assert any("downgrade" in a.lower() or "mismatch" in a.lower() for a in result.alerts)
        log_test_result("test_mitm_downgrade", True, result.transcript)
    except AssertionError:
        log_test_result("test_mitm_downgrade", False, result.transcript)
        raise


# Additional test cases for broader coverage
def test_classical_only():
    client = {"kem_offers": ["X25519"], "sig_offers": ["ecdsa_secp256r1_sha256"]}
    server = {"kem_offers": ["X25519"], "sig_offers": ["ecdsa_secp256r1_sha256"]}
    r = TLSSimulator(pol(client), pol(server)).run_handshake()
    try:
        assert r.selected_kem == "X25519"
        assert r.selected_sig == "ecdsa_secp256r1_sha256"
        log_test_result("test_classical_only", True, r.transcript)
    except AssertionError:
        log_test_result("test_classical_only", False, r.transcript)
        raise

def test_pq_only_success():
    client = {"kem_offers": ["KYBER1024"], "sig_offers": ["falcon-1024"]}
    server = {"kem_offers": ["KYBER1024"], "sig_offers": ["falcon-1024"]}
    r = TLSSimulator(pol(client), pol(server)).run_handshake()
    try:
        assert r.selected_kem == "KYBER1024"
        assert r.selected_sig == "falcon-1024"
        log_test_result("test_pq_only_success", True, r.transcript)
    except AssertionError:
        log_test_result("test_pq_only_success", False, r.transcript)
        raise

def test_hybrid_vs_classical():
    client = {"kem_offers": ["HYBRID_X25519_KYBER1024"], "sig_offers": ["hybrid_ecdsa_falcon1024"]}
    server = {"kem_offers": ["X25519"], "sig_offers": ["ecdsa_secp256r1_sha256"]}
    r = TLSSimulator(pol(client), pol(server)).run_handshake()
    try:
        assert r.selected_kem == "none" or r.selected_sig == "none"
        log_test_result("test_hybrid_vs_classical", True, r.transcript)
    except AssertionError:
        log_test_result("test_hybrid_vs_classical", False, r.transcript)
        raise

def test_force_tls12_attack():
    client = {"kem_offers": ["KYBER1024", "X25519"], "sig_offers": ["falcon-1024", "ecdsa_secp256r1_sha256"]}
    server = {"kem_offers": ["KYBER1024", "X25519"], "sig_offers": ["falcon-1024", "ecdsa_secp256r1_sha256"]}
    r = TLSSimulator(pol(client), pol(server)).run_handshake(attack=force_tls12)
    try:
        assert "TLS Version: TLS1.2" in r.transcript
        log_test_result("test_force_tls12_attack", True, r.transcript)
    except AssertionError:
        log_test_result("test_force_tls12_attack", False, r.transcript)
        raise

def test_strip_hybrid_only_attack():
    client = {"kem_offers": ["HYBRID_X25519_KYBER1024", "KYBER1024"], "sig_offers": ["hybrid_ecdsa_falcon1024", "falcon-1024"]}
    server = {"kem_offers": ["HYBRID_X25519_KYBER1024", "KYBER1024"], "sig_offers": ["hybrid_ecdsa_falcon1024", "falcon-1024"]}
    r = TLSSimulator(pol(client), pol(server)).run_handshake(attack=strip_hybrid_only)
    try:
        assert "hybrid" not in r.selected_kem.lower() and "hybrid" not in r.selected_sig.lower()
        log_test_result("test_strip_hybrid_only_attack", True, r.transcript)
    except AssertionError:
        log_test_result("test_strip_hybrid_only_attack", False, r.transcript)
        raise

def test_no_mutual_kem():
    client = {"kem_offers": ["KYBER1024"], "sig_offers": ["falcon-1024"]}
    server = {"kem_offers": ["X25519"], "sig_offers": ["ecdsa_secp256r1_sha256"]}
    r = TLSSimulator(pol(client), pol(server)).run_handshake()
    try:
        assert r.selected_kem == "none"
        assert r.selected_sig == "none"
        log_test_result("test_no_mutual_kem", True, r.transcript)
    except AssertionError:
        log_test_result("test_no_mutual_kem", False, r.transcript)
        raise

# Group test report at the end
def pytest_sessionfinish(session, exitstatus):
    total = len(test_results)
    passed = sum(1 for _, ok, _ in test_results if ok)
    failed = total - passed
    docker_logger.info(f"GROUP TEST REPORT: {passed}/{total} passed, {failed} failed.")
    for name, ok, transcript in test_results:
        docker_logger.info(f"  {name}: {'PASS' if ok else 'FAIL'}")
