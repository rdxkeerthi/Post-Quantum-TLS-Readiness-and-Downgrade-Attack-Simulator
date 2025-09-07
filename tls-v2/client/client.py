import socket, ssl
import logging

logging.basicConfig(filename='client_handshake.log', level=logging.INFO)

context = ssl.create_default_context()
# For real PQ: integrate with python-oqs or hybrid OpenSSL build
context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2  # Only allow TLS 1.3/1.4

server_addr = ('localhost', 8443)
with socket.create_connection(server_addr) as sock:
    with context.wrap_socket(sock, server_hostname='localhost') as ssock:
        logging.info('Handshake with server')
        print('Server says:', ssock.recv(1024).decode())
