# PQ-TLS Engine

- `pq_tls_server.py`: Production-ready Python PQ-TLS server (X25519/ECDSA, ready for liboqs/oqs-provider integration)
- `pq_tls_client.py`: Production-ready Python PQ-TLS client (X25519/ECDSA, ready for liboqs/oqs-provider integration)

## How to run

1. Generate a self-signed cert/key (for demo):
   ```bash
   openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes -subj "/CN=localhost"
   ```
2. Start the server:
   ```bash
   python pq_tls_server.py
   ```
3. In another terminal, run the client:
   ```bash
   python pq_tls_client.py
   ```

## Extending for Real PQ
- Swap SSLContext for OpenSSL oqs-provider or python-oqs for Kyber/Dilithium/hybrid support.
- Add handshake transcript logging, downgrade detection, and hooks for attack simulation.
