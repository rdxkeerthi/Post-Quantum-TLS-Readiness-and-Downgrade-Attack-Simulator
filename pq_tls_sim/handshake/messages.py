import hashlib

class ClientHello:
    def __init__(self, offered_kem_groups=None, offered_sig_algs=None, grease_kem=None, extensions=None, pq_supported=None):
        self.offered_kem_groups = offered_kem_groups or []
        self.offered_sig_algs = offered_sig_algs or []
        self.grease_kem = grease_kem
        self.extensions = extensions or {}
        self.pq_supported = pq_supported

class ServerHello:
    def __init__(self, selected_kem_group=None, selected_sig_alg=None, extensions=None, pq_selected=None):
        self.selected_kem_group = selected_kem_group
        self.selected_sig_alg = selected_sig_alg
        self.extensions = extensions or {}
        self.pq_selected = pq_selected

def hash_offers(kem_offers, sig_offers):
    """Hash the KEM and signature offers for negotiation context."""
    m = hashlib.sha256()
    m.update(",".join(kem_offers).encode())
    m.update(",".join(sig_offers).encode())
    return m.hexdigest()
