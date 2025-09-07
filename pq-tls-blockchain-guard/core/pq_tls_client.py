import socket, ssl, logging
from datetime import datetime

# --- PQ-TLS Client (X25519/ECDSA, ready for liboqs/oqs-provider integration) ---
# For real PQ: swap context for OpenSSL oqs-provider or python-oqs

logging.basicConfig(filename='handshake_client.log', level=logging.INFO)

class PQTLSClient:
    def __init__(self, host='localhost', port=9443):
        self.host = host
        self.port = port
        self.context = ssl.create_default_context()

    def connect(self):
        with socket.create_connection((self.host, self.port)) as sock:
            with self.context.wrap_socket(sock, server_hostname=self.host) as ssock:
                logging.info(f"{datetime.now()} Handshake with {self.host}:{self.port}")
                print('[PQ-TLS] Server says:', ssock.recv(1024).decode())

if __name__ == "__main__":
    PQTLSClient().connect()
