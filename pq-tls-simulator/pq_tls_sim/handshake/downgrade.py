from .messages import ClientHello
from pq_tls_sim.utils.logging import log

def strip_pq_from_clienthello(ch: ClientHello) -> ClientHello:
    def is_pq(x): return "kyber" in x or "dilithium" in x or "falcon" in x or "hybrid_" in x
    return ClientHello(
        offered_kem_groups=[g for g in ch.offered_kem_groups if not is_pq(g)],
        offered_sig_algs=[s for s in ch.offered_sig_algs if not is_pq(s)],
        grease_kem=None,
        extensions={k:v for k,v in ch.extensions.items() if k not in ("pq_negotiation_context","grease_echo")}
    )

def strip_pq_groups(ch: ClientHello) -> ClientHello:
    def is_pq(x): return "kyber" in x.lower() or "frodokem" in x.lower() or "hybrid_" in x.lower()
    return ClientHello(
        offered_kem_groups=[g for g in ch.offered_kem_groups if not is_pq(g)],
        offered_sig_algs=ch.offered_sig_algs,
        grease_kem=None,
        extensions={k:v for k,v in ch.extensions.items() if k != "pq_negotiation_context"}
    )

def strip_hybrid_only(ch: ClientHello) -> ClientHello:
    def is_hybrid(x): return "hybrid" in x.lower()
    return ClientHello(
        offered_kem_groups=[g for g in ch.offered_kem_groups if not is_hybrid(g)],
        offered_sig_algs=[s for s in ch.offered_sig_algs if not is_hybrid(s)],
        grease_kem=ch.grease_kem,
        extensions=ch.extensions.copy()
    )

def strip_pq_sigs(ch: ClientHello) -> ClientHello:
    def is_pq(x): return "dilithium" in x.lower() or "falcon" in x.lower()
    return ClientHello(
        offered_kem_groups=ch.offered_kem_groups,
        offered_sig_algs=[s for s in ch.offered_sig_algs if not is_pq(s)],
        grease_kem=ch.grease_kem,
        extensions={k:v for k,v in ch.extensions.items() if k != "pq_negotiation_context"}
    )

def force_tls12(ch: ClientHello) -> ClientHello:
    log("[MITM] Downgrade attack: Forcing TLS 1.2!")
    ch.extensions["forced_version"] = "TLS1.2"
    return ch

def noop(ch: ClientHello) -> ClientHello: return ch

class DowngradeAttack:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def perform(self, client_hello):
        if self.enabled:
            log("[MITM] Downgrade attack: Stripping PQ support from ClientHello!")
            client_hello.pq_supported = False
        return client_hello
