Open a terminal and go to the simulator directory:

cd /home/sec/mini_project/pq-tls/pq-tls/pq-tls-simulator

Create and activate a virtualenv, upgrade pip, and install dependencies:

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt



Run the dashboard (backgrounded example that writes logs and PID):

. .venv/bin/activate
/absolute/path/to/pq-tls/pq-tls-simulator/.venv/bin/python dashboard/app.py > /tmp/pq_dashboard.log 2>&1 & echo $! > /tmp/pq_dashboard.pid
tail -n 80 /tmp/pq_dashboard.log



## RUN 2

. .venv/bin/activate && python dashboard/app.py

cd /home/sec/mini_project/pq-tls/pq-tls/pq-tls-simulator && /home/sec/mini_project/pq-tls/pq-tls/pq-tls-simulator/.venv/bin/python dashboard/app.py > /tmp/pq_dashboard.log 2>&1 & echo $! > /tmp/pq_dashboard.pid


tail -n 80 /tmp/pq_dashboard.log || true
