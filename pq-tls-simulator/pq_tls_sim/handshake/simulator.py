from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from .messages import ClientHello, ServerHello, hash_offers
from ..utils.logging import Logger
from ..utils.tls13_ciphersuites import KEM_GROUPS, SIG_ALGS, is_pq_kem, is_pq_sig
from pq_tls_sim.crypto.classical import ClassicalCrypto
from pq_tls_sim.crypto.kem import PQKEM
from pq_tls_sim.crypto.sig import PQSignature
from pq_tls_sim.utils.logging import log

@dataclass
class Policy:
    kem_offers: List[str]
    sig_offers: List[str]
    require_pq: bool = False
    require_hybrid: bool = False
    pq_allowed: bool = True
    grease: bool = True
    cert_sigalg: Optional[str] = None
    impl: Optional[str] = None

@dataclass
class Result:
    selected_kem: str
    selected_sig: str
    alerts: List[str]
    transcript: str

class TLSSimulator:
    def __init__(self, client: Policy, server: Policy, logger: Optional[Logger]=None, scenario=None):
        self.client, self.server = client, server
        self.log = logger or Logger()
        self.scenario = scenario
        # Remove scenario-dependent logic for now
        # self.client_pq = scenario["client"].get("pq_supported", False) if scenario else False
        # self.server_pq = scenario["server"].get("pq_supported", False) if scenario else False
        # self.mitm = scenario.get("mitm", {}).get("enabled", False) if scenario else False
        # self.strip_pq = scenario.get("mitm", {}).get("strip_pq", False) if scenario else False

    def build_client_hello(self) -> ClientHello:
        kem_offers = [g for g in self.client.kem_offers if g in KEM_GROUPS]
        sig_offers = [s for s in self.client.sig_offers if s in SIG_ALGS]
        ex = {"pq_negotiation_context": hash_offers(kem_offers, sig_offers)}
        if self.client.grease and kem_offers:
            ex["grease_echo"] = kem_offers[0]
        ch = ClientHello(offered_kem_groups=kem_offers, offered_sig_algs=sig_offers,
                         grease_kem=kem_offers[0] if self.client.grease and kem_offers else None, extensions=ex)
        self.log.add("client", f"ClientHello kem={kem_offers}, sigs={sig_offers}")
        return ch

    def server_select(self, ch: ClientHello) -> ServerHello:
        ex = {}
        if "grease_echo" in ch.extensions: ex["grease_echo"] = ch.extensions["grease_echo"]
        kem = next((g for g in self.server.kem_offers if g in ch.offered_kem_groups), None)
        sig = next((s for s in self.server.sig_offers if s in ch.offered_sig_algs), None)
        if not kem or not sig:
            self.log.error("server", "No mutual KEM/SIG")
            return ServerHello("none", "none", ex)
        ex["pq_negotiation_context"] = ch.extensions.get("pq_negotiation_context","")
        self.log.add("server", f"ServerHello selects kem={kem}, sig={sig}")
        return ServerHello(kem, sig, ex)

    def detect_downgrade(self, ch: ClientHello, sh: ServerHello) -> List[str]:
        alerts = []
        client_pq = any(is_pq_kem(g) for g in ch.offered_kem_groups) or any(is_pq_sig(s) for s in ch.offered_sig_algs)
        server_pq = any(is_pq_kem(g) for g in self.server.kem_offers) or any(is_pq_sig(s) for s in self.server.sig_offers)
        if client_pq and server_pq and not (is_pq_kem(sh.selected_kem_group) or is_pq_sig(sh.selected_sig_alg)):
            alerts.append("Possible downgrade: PQ supported but classical negotiated.")
        if ch.extensions.get("grease_echo") != sh.extensions.get("grease_echo"):
            alerts.append("GREASE echo mismatch: possible MITM.")
        if ch.extensions.get("pq_negotiation_context") != sh.extensions.get("pq_negotiation_context"):
            alerts.append("Negotiation context mismatch.")
        return alerts

    def run_handshake(self, attack: Optional[Callable[[ClientHello], ClientHello]]=None) -> Result:
        ch = self.build_client_hello()
        ch_obs = attack(ch) if attack else ch
        if ch_obs is not ch: self.log.warn("network", "ClientHello modified by MITM")
        sh = self.server_select(ch_obs)
        alerts = self.detect_downgrade(ch, sh)
        for a in alerts: self.log.warn("detector", a)
        # Determine TLS version
        tls_version = ch_obs.extensions.get("forced_version", "TLS1.3")
        # Determine if PQ KEM or PQ Sig was negotiated
        pq_kem = is_pq_kem(sh.selected_kem_group) if sh.selected_kem_group else False
        pq_sig = is_pq_sig(sh.selected_sig_alg) if sh.selected_sig_alg else False
        pq_status = []
        if pq_kem:
            pq_status.append("PQ KEM")
        if pq_sig:
            pq_status.append("PQ Signature")
        pq_status_str = ", ".join(pq_status) if pq_status else "Classical Only"
        # Add to transcript
        self.log.add("report", f"TLS Version: {tls_version}, PQ: {pq_status_str}")
        return Result(sh.selected_kem_group, sh.selected_sig_alg, alerts, self.log.dump())
