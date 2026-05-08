#!/usr/bin/env python3
"""Check full API response for download clients."""
import sys, json
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

for name, port, apikey, ver in [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121", "v3"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14", "v3"),
    ("lidarr", 8686, "f5efa3b451a74385a880c2189e692b40", "v1"),
]:
    result = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/{ver}/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    try:
        dlcs = json.loads(result)
        for d in dlcs:
            settings = d.get('settings', {})
            if not settings:
                settings = d  # Sometimes settings is at top level
            print(f"[{name}]")
            print(f"  Name: {d.get('name')}")
            print(f"  Implementation: {d.get('implementation')}")
            print(f"  ConfigContract: {d.get('configContract')}")
            print(f"  Enable: {d.get('enable')}")
            # Get fields from settings
            if 'fields' in settings:
                for f in settings.get('fields', []):
                    if f.get('name') in ('host', 'port', 'password'):
                        print(f"  {f['name']}: {f.get('value')}")
            else:
                print(f"  Settings keys: {list(settings.keys())[:8]}")
                print(f"  host: {settings.get('host', 'N/A')}")
                print(f"  port: {settings.get('port', 'N/A')}")
    except Exception as e:
        print(f"[{name}] Error: {e}")
        print(f"  Raw: {result[:200]}")

ssh.close()
