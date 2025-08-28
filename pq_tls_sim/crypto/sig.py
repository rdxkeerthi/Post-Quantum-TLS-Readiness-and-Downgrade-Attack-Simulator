class PQSignature:
    """Simulated post-quantum signature for TLS."""
    def sign(self, message: str, private_key: str) -> str:
        return f"pq_signature({message})"

    def verify(self, message: str, signature: str, public_key: str) -> bool:
        return signature == f"pq_signature({message})"
