FROM python:3.10-slim
WORKDIR /app
COPY pq_tls_server.py .
COPY pq_tls_client.py .
COPY server.crt .
COPY server.key .
CMD ["python", "pq_tls_server.py"]
