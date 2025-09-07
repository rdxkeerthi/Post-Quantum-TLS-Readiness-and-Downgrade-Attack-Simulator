#!/bin/bash

# Add parent directory to Python path
export PYTHONPATH=/home/sec/mini_project/pq-tls/pq-tls-simulator:/home/sec/mini_project/pq-tls:$PYTHONPATH
export FLASK_APP=/home/sec/mini_project/pq-tls/pq-tls-simulator/dashboard/app.py
export PQ_TLS_ROOT=/home/sec/mini_project/pq-tls/pq-tls-simulator

# Create required directories
mkdir -p data/logs
mkdir -p data/anomalies
mkdir -p data/history
mkdir -p blockchain/data

# Clean up old data files
rm -f data/logs/*.json
rm -f data/anomalies/*.json
rm -f data/history/*.json

# Install required dependencies
pip install flask click pytest requests
pip install fabric-sdk-py cryptography

# Run all scenarios to generate events
echo "Running CVE scenarios..."

scenarios=(
    "quantum_logjam_2025.json:strip_pq_groups"
    "quantum_poodle_2025.json:force_tls12"
    "quantum_heartbleed_2025.json:strip_pq_sigs"
    "quantum_robot_2025.json:strip_hybrid_only"
    "quantum_renegotiation_2025.json:none"
)

for scenario in "${scenarios[@]}"; do
    IFS=':' read -r file attack <<< "$scenario"
    echo "Running scenario: $file with attack: $attack"
    python3 -m pq_tls_sim.cli --scenario "scenarios/$file" --attack "$attack"
    if [ $? -ne 0 ]; then
        echo "Failed to run scenario $file"
        exit 1
    fi
done

# Start the dashboard in debug mode for better error reporting
echo "Starting dashboard..."
cd dashboard
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
python3 -m flask run --host=0.0.0.0
