#!/usr/bin/env python3
"""Fix remaining: Lidarr root folder + Prowlarr apps."""
import sys, json, base64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# ── 1. LIDARR: Root folder WITH name ──
print("=== LIDARR: Root folder ===")
result = run('lxc-attach -n 101 -- curl -s -X POST "http://localhost:8686/api/v1/rootfolder" -H "Content-Type: application/json" -H "X-Api-Key: f5efa3b451a74385a880c2189e692b40" --max-time 5 -d \'{"path":"/music","name":"Music"}\' 2>&1')
print(f"  {result[:300]}")
# Need to also get quality profile IDs - Lidarr might need them
# Let me check what profiles exist
profiles = run('lxc-attach -n 101 -- curl -s "http://localhost:8686/api/v1/qualityprofile" -H "X-Api-Key: f5efa3b451a74385a880c2189e692b40" --max-time 5 2>&1')
print(f"  Profiles: {profiles[:200]}")
metadata = run('lxc-attach -n 101 -- curl -s "http://localhost:8686/api/v1/metadataprofile" -H "X-Api-Key: f5efa3b451a74385a880c2189e692b40" --max-time 5 2>&1')
print(f"  Metadata: {metadata[:200]}")

# ── 2. PROWLARR: Apps with correct API key ──
print("\n=== PROWLARR: Apps ===")
prowlarr_key = "db4098a3fe9b47a28da32b5f874fd91d"
for app_name, app_url, app_key, cats in [
    ("Sonarr", "http://sonarr:8989", "f8fc219f6076435eb5ef6d0bc4093121", [5000,5010,5020,5030,5040]),
    ("Radarr", "http://radarr:7878", "1bb778a4366d47d89c7a4b07756dfc14", [2000,2010,2020,2030,2040]),
]:
    payload = json.dumps({
        "name": app_name,
        "implementation": app_name,
        "configContract": f"{app_name}Settings",
        "fields": [
            {"name": "prowlarrUrl", "value": "http://prowlarr:9696"},
            {"name": "baseUrl", "value": app_url},
            {"name": "apiKey", "value": app_key},
            {"name": "syncCategories", "value": cats}
        ],
        "syncLevel": "fullSync"
    })
    payload_b64 = base64.b64encode(payload.encode()).decode()
    result = run(f'lxc-attach -n 101 -- bash -c "echo {payload_b64} | base64 -d | curl -s -w \' HTTP:%{{http_code}}\' -X POST http://localhost:9696/api/v1/applications -H \'Content-Type: application/json\' -H \'X-Api-Key: {prowlarr_key}\' -d @- --max-time 10" 2>&1')
    print(f"  [{app_name}] {result[:250]}")

# ── 3. PROWLARR: Verify ──
print("\n=== PROWLARR: Verify apps ===")
result = run(f'lxc-attach -n 101 -- curl -s "http://localhost:9696/api/v1/applications" -H "X-Api-Key: {prowlarr_key}" --max-time 5 2>&1')
try:
    apps = json.loads(result)
    for a in apps:
        print(f"  {a.get('name')}: enabled={a.get('enabled')}, syncLevel={a.get('syncLevel')}")
except:
    print(f"  {result[:200]}")

# ── 4. BAZARR: Config file approach ──
print("\n=== BAZARR: Config check ===")
print(run('cat /var/lib/lxc/101/rootfs/opt/arrstack/bazarr/config/config.yaml 2>&1 | head -30'))

ssh.close()
