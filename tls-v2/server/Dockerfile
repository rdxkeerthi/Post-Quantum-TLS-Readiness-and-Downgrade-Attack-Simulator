FROM python:3.10-slim
WORKDIR /app
COPY server.py .
COPY server.crt .
COPY server.key .
CMD ["python", "server.py"]
