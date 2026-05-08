#!/usr/bin/env python3
"""Deploy custom init + updated compose + reconfigure *arrs."""
import sys, base64, json, time
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# ── 1. Read local compose + custom-init, push to host ──
with open("/home/limbsjones/git/torrents_stack/compose.yaml") as f:
    compose = f.read()
with open("/home/limbsjones/git/torrents_stack/custom-init.sh") as f:
    init_script = f.read()

compose_b64 = base64.b64encode(compose.encode()).decode()
init_b64 = base64.b64encode(init_script.encode()).decode()

print("=== PUSH FILES TO HOST ===")
run(f'echo {compose_b64} | base64 -d > /opt/arrstack/compose.yaml')
run(f'mkdir -p /opt/arrstack/deluge/custom-init')
run(f'echo {init_b64} | base64 -d > /opt/arrstack/deluge/custom-init/socat.sh')
run('chmod +x /opt/arrstack/deluge/custom-init/socat.sh')
print("Files pushed")

# ── 2. Copy into LXC 101 ──
print("=== COPY INTO LXC ===")
run(f'lxc-attach -n 101 -- bash -c "echo {compose_b64} | base64 -d > /opt/arrstack/compose.yaml"')
run(f'lxc-attach -n 101 -- mkdir -p /opt/arrstack/deluge/custom-init')
run(f'lxc-attach -n 101 -- bash -c "echo {init_b64} | base64 -d > /opt/arrstack/deluge/custom-init/socat.sh"')
run('lxc-attach -n 101 -- chmod +x /opt/arrstack/deluge/custom-init/socat.sh')
run('lxc-attach -n 101 -- chown -R 101000:101000 /opt/arrstack/deluge/custom-init')
print("LXC files ready")

# Verify
print("\n=== VERIFY FILES ===")
print(run('ls -la /opt/arrstack/deluge/custom-init/'))
print(run('head -5 /opt/arrstack/deluge/custom-init/socat.sh'))

# ── 3. Docker compose up -d deluge (restart with new volume mount) ──
print("\n=== DEPLOY ===")
print(run('lxc-attach -n 101 -- docker compose -f /opt/arrstack/compose.yaml up -d deluge 2>&1'))
time.sleep(10)

# ── 4. Check socat ──
print("\n=== VERIFY SOCAT ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep -E "48846|socat"'))

# ── 5. Configure *arrs with port 48846 ──
print("\n=== CONFIGURE *ARRs ===")
configs = [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121", "v3"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14", "v3"),
    ("lidarr", 8686, "f5efa3b451a74385a880c2189e692b40", "v1"),
]

for name, port, apikey, ver in configs:
    # Get existing to find ID and delete
    existing = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/{ver}/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    try:
        dlcs = json.loads(existing)
        for dlc in dlcs:
            if 'Deluge' in dlc.get('name', ''):
                did = dlc['id']
                run(f'lxc-attach -n 101 -- curl -s -X DELETE "http://localhost:{port}/api/{ver}/downloadclient/{did}" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
                print(f"  {name}: deleted old client (id={did})")
    except:
        print(f"  {name}: no existing client or empty")

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
    p_b64 = base64.b64encode(payload.encode()).decode()
    result = run(f'lxc-attach -n 101 -- bash -c "echo {p_b64} | base64 -d | curl -s -X POST http://localhost:{port}/api/{ver}/downloadclient -H \'Content-Type: application/json\' -H \'X-Api-Key: {apikey}\' -d @- --max-time 10" 2>&1')
    if "Deluge" in result or "enable" in result:
        print(f"  {name}: ✅ configured (port 48846)")
    else:
        print(f"  {name}: ⚠️ {result[:150]}")

# ── 6. Verify all ──
print("\n=== FINAL VERIFY ===")
print(run('lxc-attach -n 101 -- docker ps --format "table {{.Names}}\\t{{.Status}}" 2>&1'))

print("\n=== DOWNLOAD CLIENTS VERIFY ===")
for name, port, apikey, ver in configs:
    cl = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/{ver}/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    if 'Deluge' in cl:
        print(f"  {name}: ✅ Deluge client active")
    else:
        print(f"  {name}: ⚠️ {cl[:100]}")

ssh.close()
print("\n✅ DONE")
