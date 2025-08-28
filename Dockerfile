# Dockerfile for PQ-TLS Simulator

# Dockerfile for PQ-TLS Simulator (fixed for editable install and pyproject.toml)
FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip && \
    pip install --no-cache-dir .[dev] || pip install --no-cache-dir -e .
CMD ["python", "-m", "pq_tls_sim.cli", "--scenario", "scenarios/default.json"]
