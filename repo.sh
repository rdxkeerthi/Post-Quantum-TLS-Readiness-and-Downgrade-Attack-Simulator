pq-tls-simulator/
├── README.md
├── pyproject.toml
├── pq_tls_sim/
│   ├── __init__.py
│   ├── cli.py
│   ├── crypto/
│   │   ├── __init__.py
│   │   ├── classical.py
│   │   ├── kem.py
│   │   └── sig.py
│   ├── handshake/
│   │   ├── __init__.py
│   │   ├── messages.py
│   │   ├── simulator.py
│   │   └── downgrade.py
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       └── tls13_ciphersuites.py
├── scenarios/
│   ├── default.json
│   ├── pq_both.json
│   ├── classical_only_server.json
│   └── mitm_strip_pq.json
├── tests/
│   └── test_simulator.py
└── .github/
    └── workflows/
        └── lint.yml
