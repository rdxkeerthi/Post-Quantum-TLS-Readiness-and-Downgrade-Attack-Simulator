class PQKEM:
    """Simulated post-quantum KEM for TLS."""
    def encapsulate(self, public_key: str) -> tuple[str, str]:
        return "pq_ciphertext", "pq_shared_secret"

    def decapsulate(self, ciphertext: str, private_key: str) -> str:
        if ciphertext == "pq_ciphertext":
            return "pq_shared_secret"
        raise ValueError("Invalid ciphertext")
