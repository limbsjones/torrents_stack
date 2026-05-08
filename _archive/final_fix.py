#!/usr/bin/env python3
"""Final config with correct field names (lowercase)."""
import sys, json, base64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

configs = [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121", "v3"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14", "v3"),
    ("lidarr", 8686, "f5efa3b451a74385a880c2189e692b40", "v1"),
]

for name, port, apikey, ver in configs:
    # Delete existing Deluge clients first
    existing = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/{ver}/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    try:
        dlcs = json.loads(existing) if existing.strip().startswith('[') else []
        for dlc in dlcs:
            if 'Deluge' in dlc.get('name', ''):
                did = dlc['id']
                run(f'lxc-attach -n 101 -- curl -s -X DELETE "http://localhost:{port}/api/{ver}/downloadclient/{did}" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
                print(f"  {name}: deleted id={did}")
    except:
        pass

    # Create with CORRECT lowercase field names
    payload = json.dumps({
        "enable": True,
        "name": "Deluge",
        "fields": [
            {"name": "host", "value": "deluge"},
            {"name": "port", "value": 48846},
            {"name": "useSsl", "value": False},
            {"name": "urlBase", "value": ""},
            {"name": "password", "value": "deluge"}
        ],
        "implementationName": "Deluge",
        "implementation": "Deluge",
        "configContract": "DelugeSettings",
        "protocol": "torrent",
        "priority": 10
    })
    
    p_b64 = base64.b64encode(payload.encode()).decode()
    result = run(f'lxc-attach -n 101 -- bash -c "echo {p_b64} | base64 -d | curl -s -w \'\\nHTTP:%{{http_code}}\' -X POST http://localhost:{port}/api/{ver}/downloadclient -H \'Content-Type: application/json\' -H \'X-Api-Key: {apikey}\' -d @- --max-time 10" 2>&1')
    print(f"  [{name}] {result[:300]}")

# VERIFY
print("\n=== VERIFY ===")
for name, port, apikey, ver in configs:
    result = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/{ver}/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    try:
        dlcs = json.loads(result)
        if dlcs:
            for d in dlcs:
                host_port = ""
                for f in d.get('fields', []):
                    if f['name'] in ('host', 'port'):
                        host_port += f"{f['name']}={f['value']} "
                print(f"  [{name}] ✅ {d.get('name')} - {host_port}")
        else:
            print(f"  [{name}] ❌ empty: {result[:100]}")
    except:
        print(f"  [{name}] ❌ error: {result[:100]}")

ssh.close()
