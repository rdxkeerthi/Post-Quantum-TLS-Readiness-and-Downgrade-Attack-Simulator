# Downgrade attack logic stub
# Add logic to strip PQ/hybrid ciphers and force TLS 1.2 if scenario requests it

def modify_clienthello_for_downgrade(clienthello, scenario):
    if scenario.get("mitm", {}).get("actions"):
        for action in scenario["mitm"]["actions"]:
            if action["type"] == "strip_pq_ciphers":
                clienthello["kem"] = [k for k in clienthello.get("kem", []) if not k.startswith("KYBER") and not k.startswith("HYBRID")]
                clienthello["sig"] = [s for s in clienthello.get("sig", []) if not s.startswith("falcon") and not s.startswith("hybrid")]
            if action["type"] == "force_version" and action["version"] == "TLS1.2":
                clienthello["version"] = "TLS1.2"
    return clienthello

# In your MITM proxy, call this function when scenario matches
