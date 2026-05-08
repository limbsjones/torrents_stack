#!/usr/bin/env python3
"""Finish remaining config: Lidarr root folder, Prowlarr apps, Bazarr."""
import sys, json, base64, time
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# ── 1. LIDARR: Fix root folder permissions ──
print("=== LIDARR ROOT FOLDER ===")
# Check if Lidarr has a root folder already
result = run('lxc-attach -n 101 -- curl -s "http://localhost:8686/api/v1/rootfolder" -H "X-Api-Key: f5efa3b451a74385a880c2189e692b40" --max-time 5 2>&1')
print(f"  Current: {result[:200]}")

# The issue is that user 'abc' can't write to /mnt/media/Music
# We already fixed permissions on the host (chown 101000:101000)
# But the issue is inside the Docker container, user 'abc' runs as PUID 1000
# Inside the LXC, PUID 1000 maps to host UID 101000 → we need to check the actual UID mapping

# Let me check the container user mapping
print(run('lxc-attach -n 101 -- docker exec lidarr id abc 2>&1'))

# The issue is that /mnt/media/Music is owned by 1000:1000 inside the LXC
# But the lidarr container's PUID=1000 might map to a different UID inside Docker-in-LXC
# Let's check by creating a test file
print(run('lxc-attach -n 101 -- docker exec lidarr touch /music/.test_write 2>&1'))
print(run('lxc-attach -n 101 -- docker exec lidarr ls -la /music/ 2>&1 | head -5'))

# ── 2. PROWLARR: Add apps ──
print("\n=== PROWLARR APPS ===")
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
    p_b64 = base64.b64encode(payload.encode()).decode()
    
    # Delete existing first
    run(f'lxc-attach -n 101 -- curl -s "http://localhost:9696/api/v1/applications" --max-time 5 2>&1 | python3 -c "import sys,json; [print(a[\'id\']) for a in json.load(sys.stdin) if a.get(\'name\')==\'{app_name}\']" 2>/dev/null | while read id; do curl -s -X DELETE "http://localhost:9696/api/v1/applications/$id" --max-time 5; done')
    
    # Create
    result = run(f'lxc-attach -n 101 -- bash -c "echo {p_b64} | base64 -d | curl -s -w \' HTTP:%{{http_code}}\' -X POST http://localhost:9696/api/v1/applications -H \'Content-Type: application/json\' -d @- --max-time 10" 2>&1')
    if app_name in result:
        print(f"  [{app_name}] ✅")
    else:
        print(f"  [{app_name}] {result[:200]}")

# ── 3. BAZARR: Connect Sonarr and Radarr ──
print("\n=== BAZARR CONNECTION ===")
# Bazarr uses different API endpoints
# Check swagger/docs
print(run('lxc-attach -n 101 -- curl -s "http://localhost:6767/api/swagger.json" --max-time 5 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); [print(p) for p in d.get(\'paths\',{}).keys() if \'settings\' in p or \'sonarr\' in p or \'radarr\' in p]" 2>&1 | head -20'))

# Try different endpoints
for endpoint, payload in [
    ("/api/settings/sonarr", {"api_key": "f8fc219f6076435eb5ef6d0bc4093121", "full_update": True, "host": "sonarr", "port": 8989, "ssl": False, "base_url": ""}),
    ("/api/settings/radarr", {"api_key": "1bb778a4366d47d89c7a4b07756dfc14", "full_update": True, "host": "radarr", "port": 7878, "ssl": False, "base_url": ""}),
]:
    p_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
    
    # Try POST, PUT, PATCH
    for method in ["POST", "PUT", "PATCH"]:
        result = run(f'lxc-attach -n 101 -- bash -c "echo {p_b64} | base64 -d | curl -s -X {method} {endpoint} -H \'Content-Type: application/json\' -d @- --max-time 5" 2>&1')
        if "error" not in result.lower() and "method not allowed" not in result.lower() and result.strip():
            print(f"  [{endpoint}] {method} -> {result[:200]}")
            break
    else:
        print(f"  [{endpoint}] All methods failed")

ssh.close()
