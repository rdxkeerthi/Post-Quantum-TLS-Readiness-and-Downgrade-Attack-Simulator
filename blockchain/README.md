# Blockchain Integration (Hyperledger Fabric)

This directory contains a stub for logging PQ-TLS handshake and CVE events to a Hyperledger Fabric blockchain network.

- `fabric_client.py`: Python stub for logging events. Replace with real Fabric SDK logic as needed.
- Integration: The simulator (`pq_tls_sim/cli.py`) calls `log_event_to_blockchain()` after each handshake.

## How to Extend
- Replace the stub in `fabric_client.py` with real Hyperledger Fabric SDK calls.
- Deploy a Fabric network and configure credentials.
- Use blockchain logging for tamper-proof audit trails of security events.
