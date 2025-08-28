class ClassicalCrypto:
    """Simulated classical cryptography for TLS."""
    def encrypt(self, plaintext: str) -> str:
        return f"encrypted(classical):{plaintext}"

    def decrypt(self, ciphertext: str) -> str:
        if ciphertext.startswith("encrypted(classical):"):
            return ciphertext[len("encrypted(classical):"):]
        raise ValueError("Invalid ciphertext")
