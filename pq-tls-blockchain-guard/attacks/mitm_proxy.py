import socket, threading

# MITM Proxy for TLS handshake interception (toy, extend for real PQ)
LISTEN_PORT = 9444
TARGET_HOST = 'localhost'
TARGET_PORT = 9443

class MITMProxy:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', LISTEN_PORT))
        self.sock.listen(5)
        print(f"[MITM] Listening on 0.0.0.0:{LISTEN_PORT}")

    def handle(self, client_sock):
        server_sock = socket.create_connection((TARGET_HOST, TARGET_PORT))
        threading.Thread(target=self.pipe, args=(client_sock, server_sock)).start()
        threading.Thread(target=self.pipe, args=(server_sock, client_sock)).start()

    def pipe(self, src, dst):
        while True:
            data = src.recv(4096)
            if not data:
                break
            # Here you can modify ClientHello/ServerHello for downgrade attacks
            dst.sendall(data)
        src.close()
        dst.close()

    def serve_forever(self):
        while True:
            client_sock, _ = self.sock.accept()
            threading.Thread(target=self.handle, args=(client_sock,)).start()

if __name__ == "__main__":
    MITMProxy().serve_forever()
