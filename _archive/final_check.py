#!/usr/bin/env python3
"""Final verification of all services."""
import sys, json
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

print("=== DOWNLOAD CLIENTS ===")
for name, port, apikey, ver in [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121", "v3"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14", "v3"),
    ("lidarr", 8686, "f5efa3b451a74385a880c2189e692b40", "v1"),
]:
    result = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/{ver}/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    try:
        data = json.loads(result)
        if data:
            for d in data:
                print(f"  [{name}] {d.get('name')}, port={d.get('port')}, host={d.get('host')}")
                for f in d.get('fields', []):
                    if f.get('name') in ('Host', 'Port', 'Password'):
                        print(f"    {f['name']}: {f['value']}")
        else:
            # Retry POST with verbose output
            payload = json.dumps({
                "enable": True, "name": "Deluge",
                "fields": [
                    {"name": "Host", "value": "deluge"},
                    {"name": "Port", "value": 48846},
                    {"name": "UseSSL", "value": False},
                    {"name": "UrlBase", "value": ""},
                    {"name": "Password", "value": "deluge"}
                ],
                "implementationName": "Deluge", "implementation": "Deluge",
                "configContract": "DelugeSettings", "protocol": "torrent", "priority": 10
            })
            p_b64 = __import__('base64').b64encode(payload.encode()).decode()
            result2 = run(f'lxc-attach -n 101 -- bash -c "echo {p_b64} | base64 -d | curl -s -w \'\\nHTTPCODE:%{{http_code}}\' -X POST http://localhost:{port}/api/{ver}/downloadclient -H \'Content-Type: application/json\' -H \'X-Api-Key: {apikey}\' -d @- --max-time 10" 2>&1')
            print(f"  [{name}] POST: {result2[:300]}")
    except json.JSONDecodeError:
        print(f"  [{name}] JSON parse error: {result[:200]}")

print("\n=== PORTS & CONNECTIVITY ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep socat'))
print("\n=== SONARR -> DELUGE ===")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 5 bash -c "echo > /dev/tcp/deluge/48846 2>&1 && echo OPEN:48846 || echo CLOSED:48846"'))

ssh.close()
