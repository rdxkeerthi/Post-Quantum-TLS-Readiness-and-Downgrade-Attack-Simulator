import socket, ssl
import logging

logging.basicConfig(filename='server_handshake.log', level=logging.INFO)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile='server.crt', keyfile='server.key')
# For real PQ: integrate with python-oqs or hybrid OpenSSL build
context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2  # Only allow TLS 1.3/1.4

bind_addr = ('0.0.0.0', 8443)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.bind(bind_addr)
sock.listen(5)
print('Server listening on', bind_addr)

with context.wrap_socket(sock, server_side=True) as ssock:
    while True:
        conn, addr = ssock.accept()
        logging.info(f'Handshake from {addr}')
        print('Connection from', addr)
        conn.send(b'Hello from TLS 1.4 PQ Server!')
        conn.close()
