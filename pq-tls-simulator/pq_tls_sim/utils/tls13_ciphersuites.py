KEM_GROUPS = [
    "X25519",
    "secp256r1",
    "KYBER768",
    "KYBER1024",
    "FRODOKEM-1344",
    "HYBRID_X25519_KYBER768",
    "HYBRID_X25519_KYBER1024"
]

SIG_ALGS = [
    "ecdsa_secp256r1_sha256",
    "rsa_pss_rsae_sha256",
    "dilithium3",
    "falcon-512",
    "falcon-1024",
    "hybrid_ecdsa_dilithium3",
    "hybrid_ecdsa_falcon1024"
]

def is_pq_kem(name: str) -> bool:
    return any(x in name.upper() for x in ["KYBER", "FRODOKEM", "HYBRID"])

def is_pq_sig(name: str) -> bool:
    return any(x in name.lower() for x in ["dilithium", "falcon", "hybrid"])

TLS13_CIPHERSUITES = [
    "TLS_AES_128_GCM_SHA256",
    "TLS_AES_256_GCM_SHA384",
    "TLS_CHACHA20_POLY1305_SHA256",
    "TLS_PQ_KEMTLS_WITH_AES_128_GCM_SHA256",
    "TLS_HYBRID_KEMTLS_WITH_AES_128_GCM_SHA256"
]

TLS14_CIPHERSUITES = [
    "TLS_AES_128_GCM_SHA256",
    "TLS_AES_256_GCM_SHA384",
    "TLS_CHACHA20_POLY1305_SHA256",
    "TLS_PQ_KEMTLS_WITH_AES_256_GCM_SHA384",
    "TLS_HYBRID_KEMTLS_WITH_AES_256_GCM_SHA384"
]
