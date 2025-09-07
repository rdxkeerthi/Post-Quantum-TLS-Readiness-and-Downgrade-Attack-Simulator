# Dockerfile for Dashboard (placeholder)
FROM python:3.10-slim
WORKDIR /dashboard
COPY . /dashboard
COPY ../blockchain /dashboard/blockchain
RUN pip install flask
CMD ["flask", "run", "--host=0.0.0.0"]
