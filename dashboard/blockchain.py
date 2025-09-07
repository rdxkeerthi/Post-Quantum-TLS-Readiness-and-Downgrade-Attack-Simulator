import json
import os
from datetime import datetime

class BlockchainLogger:
    def __init__(self):
        self.events_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'blockchain_events.json')
        self._initialize_events_file()

    def _initialize_events_file(self):
        if not os.path.exists(os.path.dirname(self.events_file)):
            os.makedirs(os.path.dirname(self.events_file))
        if not os.path.exists(self.events_file):
            with open(self.events_file, 'w') as f:
                json.dump([], f)

    def log_event(self, scenario, scenario_id, result, event_type='pq_tls_simulation'):
        event = {
            'timestamp': datetime.now().isoformat(),
            'scenario': scenario,
            'scenario_id': scenario_id,
            'type': event_type,
            'result': result,
            'version': '2025.1'
        }
        
        try:
            with open(self.events_file, 'r') as f:
                events = json.load(f)
            events.append(event)
            with open(self.events_file, 'w') as f:
                json.dump(events, f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to log blockchain event: {e}")
            return False

    def get_events(self, limit=None):
        try:
            with open(self.events_file, 'r') as f:
                events = json.load(f)
            if limit:
                return events[-limit:]
            return events
        except Exception as e:
            print(f"[ERROR] Failed to read blockchain events: {e}")
            return []

blockchain = BlockchainLogger()
