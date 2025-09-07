# POODLE attack logic stub
# Add logic to force TLS 1.0 and enable CBC padding oracle if scenario requests it

def modify_clienthello_for_poodle(clienthello, scenario):
    if scenario.get("mitm", {}).get("actions"):
        for action in scenario["mitm"]["actions"]:
            if action["type"] == "force_version" and action["version"] == "TLS1.0":
                clienthello["version"] = "TLS1.0"
            if action["type"] == "enable_padding_oracle":
                clienthello["cbc_padding_oracle"] = True
    return clienthello

# In your MITM proxy, call this function when scenario matches
