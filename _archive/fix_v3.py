#!/usr/bin/env python3
"""Fix Lidarr root with profile IDs + Bazarr config."""
import sys, json, base64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# 1. Lidarr: Get proper profile IDs
print("=== LIDARR: Profiles ===")
profiles = json.loads(run('lxc-attach -n 101 -- curl -s "http://localhost:8686/api/v1/qualityprofile" -H "X-Api-Key: f5efa3b451a74385a880c2189e692b40" --max-time 5 2>&1'))
qpid = profiles[0]['id'] if profiles else 1
print(f"  QualityProfile ID: {qpid} ({profiles[0]['name'] if profiles else 'default'})")

meta = json.loads(run('lxc-attach -n 101 -- curl -s "http://localhost:8686/api/v1/metadataprofile" -H "X-Api-Key: f5efa3b451a74385a880c2189e692b40" --max-time 5 2>&1'))
mpid = meta[0]['id'] if meta else 1
print(f"  MetadataProfile ID: {mpid} ({meta[0]['name'] if meta else 'default'})")

# Create root folder with proper profiles
result = run(f'lxc-attach -n 101 -- curl -s -X POST "http://localhost:8686/api/v1/rootfolder" -H "Content-Type: application/json" -H "X-Api-Key: f5efa3b451a74385a880c2189e692b40" --max-time 5 -d \'{{"path":"/music","name":"Music","defaultQualityProfileId":{qpid},"defaultMetadataProfileId":{mpid}}}\' 2>&1')
if 'id' in result and 'error' not in result.lower():
    print(f"  ✅ Root folder created: {result[:200]}")
else:
    print(f"  ⚠️ {result[:300]}")

# 2. Bazarr: Check for config file
print("\n=== BAZARR: Config files ===")
print(run('ls -la /var/lib/lxc/101/rootfs/opt/arrstack/bazarr/config/ 2>&1 | head -20'))

# Check bazarr config in SQLite or other format
print("\n=== BAZARR: DB check ===")
print(run('find /var/lib/lxc/101/rootfs/opt/arrstack/bazarr/ -name "*.db" -o -name "*.ini" -o -name "*.cfg" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" 2>&1'))

# 3. Final check: All services status
print("\n=== FINAL STATUS ===")
print(run('lxc-attach -n 101 -- docker ps --format "table {{.Names}}\\t{{.Status}}" 2>&1'))

ssh.close()
