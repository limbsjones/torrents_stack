#!/usr/bin/env python3
"""Quick health check of all ArrStack services."""
import sys, json
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# 1. All containers up?
print("=== DOCKER PS ===")
ps = run('lxc-attach -n 101 -- docker ps --format "table {{.Names}}\\t{{.Status}}"')
print(ps)

# 2. Deluge socat proxy alive?
print("=== SOCAT ===")
socat = run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>/dev/null | grep socat')
if socat:
    print("  ✅ socat proxy: running")
else:
    # Socat might have died - check and restart
    socat_check = run('lxc-attach -n 101 -- docker exec deluge pgrep socat 2>&1')
    print(f"  {'✅ socat running' if socat_check.strip().isdigit() else '❌ SOCAT DOWN!'}")

# 3. *Arr download clients still configured?
print("\n=== DOWNLOAD CLIENTS ===")
for name, port, apikey, ver in [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121", "v3"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14", "v3"),
    ("lidarr", 8686, "f5efa3b451a74385a880c2189e692b40", "v1"),
]:
    result = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/{ver}/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    if 'Deluge' in result:
        import re
        h = re.search(r'"host"\s*:\s*"([^"]+)"', result)
        p = re.search(r'"port"\s*:\s*(\d+)', result)
        print(f"  [{name}] ✅ host={h.group(1) if h else '?'}, port={p.group(1) if p else '?'}")
    else:
        print(f"  [{name}] ❌ {result[:100]}")

# 4. Prowlarr apps
print("\n=== PROWLARR APPS ===")
prowlarr_key = "db4098a3fe9b47a28da32b5f874fd91d"
apps = run(f'lxc-attach -n 101 -- curl -s "http://localhost:9696/api/v1/applications" -H "X-Api-Key: {prowlarr_key}" --max-time 5 2>&1')
try:
    for a in json.loads(apps):
        print(f"  [{a.get('name')}] syncLevel={a.get('syncLevel')}, enable={a.get('enable')}")
except:
    print(f"  {apps[:200]}")

# 5. Bazarr status
print("\n=== BAZARR HEALTH ===")
result = run('lxc-attach -n 101 -- curl -s "http://localhost:6767/api/system/status" --max-time 5 2>&1')
try:
    s = json.loads(result)
    print(f"  ✅ Bazarr v{s.get('version', '?')}")
except:
    print(f"  {result[:100]}")

# 6. NPM status
print("\n=== NPM ===")
npm = run('lxc-attach -n 101 -- curl -s -o /dev/null -w "%{http_code}" http://localhost:81 2>&1')
print(f"  NPM admin UI: HTTP {npm}")

# 7. Root folders still there?
print("\n=== ROOT FOLDERS ===")
for name, port, apikey, ver in [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121", "v3"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14", "v3"),
    ("lidarr", 8686, "f5efa3b451a74385a880c2189e692b40", "v1"),
]:
    result = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/{ver}/rootfolder" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    try:
        rfs = json.loads(result)
        for rf in rfs:
            print(f"  [{name}] {rf.get('path')} (id={rf.get('id')})")
    except:
        print(f"  [{name}] {result[:100]}")

ssh.close()
