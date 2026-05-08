#!/usr/bin/env python3
"""Fix Lidarr root, Prowlarr auth, Bazarr settings."""
import sys, json, base64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# ── 1. LIDARR: Add root folder ──
print("=== LIDARR: Add root folder ===")
result = run('lxc-attach -n 101 -- curl -s -X POST "http://localhost:8686/api/v1/rootfolder" -H "Content-Type: application/json" -H "X-Api-Key: f5efa3b451a74385a880c2189e692b40" --max-time 5 -d \'{"path":"/music"}\' 2>&1')
if 'path' in result and 'error' not in result.lower():
    print(f"  ✅ Root folder: {result[:200]}")
else:
    print(f"  ⚠️ {result[:200]}")

# ── 2. PROWLARR: Check auth requirements ──
print("\n=== PROWLARR: Check API ===")
# Prowlarr uses X-Api-Key too?
result = run('lxc-attach -n 101 -- curl -s "http://localhost:9696/api/v1/status" --max-time 5 2>&1')
print(f"  Status (no key): {result[:100]}")
result = run('lxc-attach -n 101 -- curl -s "http://localhost:9696/api/v1/status" -H "X-Api-Key: f8fc219f6076435eb5ef6d0bc4093121" --max-time 5 2>&1')
print(f"  Status (sonarr key): {result[:100]}")

# Check Prowlarr config for API key
print("\n=== PROWLARR CONFIG ===")
print(run('grep -i "apikey\|ApiKey" /var/lib/lxc/101/rootfs/opt/arrstack/prowlarr/config/config.xml 2>&1 | head -5'))

# Get prowlarr API key from config
prowlarr_key = run('grep ApiKey /var/lib/lxc/101/rootfs/opt/arrstack/prowlarr/config/config.xml 2>&1')
if '<ApiKey>' in prowlarr_key:
    key = prowlarr_key.split('<ApiKey>')[1].split('</ApiKey>')[0].strip()
    print(f"  Prowlarr API key: {key}")
else:
    print(f"  Raw: {prowlarr_key}")

# ── 4. BAZARR: Check Bazarr API docs ──
print("\n=== BAZARR: API Docs ===")
result = run('lxc-attach -n 101 -- curl -s "http://localhost:6767/api/swagger.json" --max-time 5 2>&1')
try:
    swagger = json.loads(result)
    # Print all paths
    for path, methods in swagger.get('paths', {}).items():
        print(f"  {path}: {list(methods.keys())}")
except:
    print(f"  Raw: {result[:300]}")

ssh.close()
