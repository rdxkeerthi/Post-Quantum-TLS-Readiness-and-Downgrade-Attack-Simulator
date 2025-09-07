# Hyperledger Fabric client stub for PQ-TLS logging
import os
import json
from datetime import datetime

BLOCKCHAIN_FILE = os.path.join(os.path.dirname(__file__), 'data', 'events.json')

def load_events():
    if os.path.exists(BLOCKCHAIN_FILE):
        try:
            with open(BLOCKCHAIN_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_events(events):
    os.makedirs(os.path.dirname(BLOCKCHAIN_FILE), exist_ok=True)
    with open(BLOCKCHAIN_FILE, 'w') as f:
        json.dump(events, f, indent=2)

def log_event_to_blockchain(event):
    """Log event to file-based blockchain stub."""
    events = load_events()
    event['timestamp'] = datetime.now().isoformat()
    events.append(event)
    save_events(events)
    print(f"[BLOCKCHAIN] Logged event: {event}")
    return True

def add_event_to_blockchain(event_data):
    """Add a PQ-TLS simulation result to blockchain."""
    if not isinstance(event_data, dict):
        raise ValueError("Event data must be a dictionary")
    
    # Add metadata
    event_data['type'] = 'pq_tls_simulation'
    event_data['version'] = '2025.1'
    
    return log_event_to_blockchain(event_data)

def query_events_from_blockchain(filter_type=None):
    """Query events from the blockchain"""
    events = load_events()
    
    print(f"[BLOCKCHAIN] Loading events from {BLOCKCHAIN_FILE}")
    if filter_type:
        events = [e for e in events if e.get('type') == filter_type]
        print(f"[BLOCKCHAIN] Found {len(events)} events of type {filter_type}")
    else:
        print(f"[BLOCKCHAIN] Found {len(events)} total events")
    return events

def verify_event_integrity(event):
    """Verify event integrity (stub, always returns True)."""
    print(f"[BLOCKCHAIN] Verifying event: {event}")
    # TODO: Implement real hash/signature check
    return True
