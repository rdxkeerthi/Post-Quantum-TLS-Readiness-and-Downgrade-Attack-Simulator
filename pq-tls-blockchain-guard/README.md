# pq-tls-blockchain-guard

A production-ready, modular PQ-TLS platform with:
- PQ-TLS server/client (liboqs/OpenSSL oqs-provider, hybrid, fallback)
- Real demo app (web/file-transfer/chat) using PQ-TLS
- Downgrade & MITM attack simulator (intercept/modify TLS handshakes, transcript logs)
- Attack alerting: on-chain (blockchain), off-chain, ML anomaly detection, Prometheus Alertmanager, webhooks
- Blockchain integration: Hyperledger Fabric (preferred) + private Ethereum, with smart contracts/chaincode for handshake/alert logs
- AI anomaly detector microservice (IsolationForest, LSTM AE)
- Admin dashboard (React/Next.js) for handshakes, alerts, chain audit, ML scores
- Full DevOps: Docker Compose, Kubernetes/Helm, GitHub Actions CI/CD, Prometheus/Grafana/Loki, docs/runbook

## Repo Structure
```
pq-tls-blockchain-guard/
├── api/                       # FastAPI REST control plane (scan, attack, reports)
├── core/                      # PQ-TLS Engine (liboqs wrapper + simulator + server/client)
├── demo_app/                  # Real demo web app (server & client integration)
├── attacks/                   # Attack simulator modules (MITM, downgrade, packet injector)
├── blockchain/                # Blockchain integration (fabric chaincode / geth contracts + deploy scripts)
├── ai-detector/               # ML microservice (train + infer)
├── dashboard/                 # React / Next.js admin UI
├── infra/
│   ├── helm/
│   ├── k8s/
│   └── terraform/ (optional)
├── observability/
│   └── prometheus-grafana-loki/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── RUNBOOK.md
│   └── demo_scripts/
├── docker-compose.yml
├── .github/workflows/ci-cd.yml
├── tests/
└── README.md
```

## Quickstart
- `docker compose up --build` to launch all services for local dev
- See `docs/ARCHITECTURE.md` and `docs/RUNBOOK.md` for details

---

This is a scaffold. Each directory contains a minimal stub or README. Extend each service as needed for your use case.
