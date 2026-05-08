#!/usr/bin/env python3
"""Make socat permanent + configure *arrs with port 48846."""
import sys, base64, json
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode() + stderr.read().decode()

# ── STEP 1: Patch s6 deluged service to start socat before deluged ──
new_run = b"""#!/usr/bin/with-contenv bash
# shellcheck shell=bash

DELUGE_LOGLEVEL=${DELUGE_LOGLEVEL:-info}

if [[ -f /config/core.conf ]]; then
    DELUGED_PORT=$(grep '"daemon_port"' /config/core.conf | tr -cd "[:digit:]")
fi

# Start socat proxy for daemon port (binds to 0.0.0.0:48846 -> 127.0.0.1:58846)
socat TCP-LISTEN:48846,reuseaddr,fork TCP:127.0.0.1:${DELUGED_PORT:-58846} &
SOCAT_PID=$!
echo "socat started on port 48846 (PID: $SOCAT_PID)"

if [[ -z ${LSIO_NON_ROOT_USER} ]]; then
    exec \\
        s6-notifyoncheck -d -n 300 -w 1000 -c "nc -z 127.0.0.1 ${DELUGED_PORT:-58846}" \\
            s6-setuidgid abc /lsiopy/bin/deluged -c /config -d --loglevel="${DELUGE_LOGLEVEL}"
else
    exec \\
        s6-notifyoncheck -d -n 300 -w 1000 -c "nc -z 127.0.0.1 ${DELUGED_PORT:-58846}" \\
            /lsiopy/bin/deluged -c /config -d --loglevel="${DELUGE_LOGLEVEL}"
fi
"""
b64_new = base64.b64encode(new_run).decode()

print("=== PATCH S6 SERVICE FILE ===")
result = run(f'lxc-attach -n 101 -- bash -c "echo {b64_new} | base64 -d > /tmp/svc-deluged-run2" 2>&1')
print(result)
result = run('lxc-attach -n 101 -- docker cp /tmp/svc-deluged-run2 deluge:/etc/s6-overlay/s6-rc.d/svc-deluged/run 2>&1')
print(result)
result = run('lxc-attach -n 101 -- docker exec deluge chmod +x /etc/s6-overlay/s6-rc.d/svc-deluged/run 2>&1')
print(result)

# Restart the container to apply
print("\n=== RESTART DELUGE CONTAINER ===")
result = run('lxc-attach -n 101 -- docker restart deluge 2>&1')
print(result)
time.sleep(5)

# Verify socat started
print("\n=== VERIFY ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep -E "48846|socat"'))
print("\n---")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 5 bash -c "echo > /dev/tcp/deluge/48846 2>&1 && echo OPEN || echo CLOSED"'))

# ── STEP 2: Configure *arrs with correct port 48846 ──
# First delete existing Deluge clients
print("\n\n=== DELETE OLD DELUGE CLIENTS ===")
for srv, port, apikey in [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14"),
    ("lidarr", 8686, "f5efa3b451a74385a880c2189e692b40"),
]:
    # List clients
    clients = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/v3/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    if 'Deluge' in clients or '"name"' in clients:
        import json as j
        try:
            dlcs = j.loads(clients)
            for dlc in dlcs:
                if 'Deluge' in dlc.get('name',''):
                    did = dlc['id']
                    r2 = run(f'lxc-attach -n 101 -- curl -s -X DELETE "http://localhost:{port}/api/v3/downloadclient/{did}" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
                    print(f"  Deleted {srv} client id {did}: {r2[:100]}")
        except:
            print(f"  {srv}: no existing Deluge client to delete")
    
    # Lidarr uses /api/v1
    if srv == "lidarr":
        clients = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/v1/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')

# Now add with port 48846
print("\n=== ADD DELUGE WITH PORT 48846 ===")
for srv, port, apikey, version in [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121", "v3"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14", "v3"),
    ("lidarr", 8686, "f5efa3b451a74385a880c2189e692b40", "v1"),
]:
    payload = base64.b64encode(json.dumps({
        "enable": True,
        "name": "Deluge",
        "fields": [
            {"name": "Host", "value": "deluge"},
            {"name": "Port", "value": 48846},
            {"name": "UseSSL", "value": False},
            {"name": "UrlBase", "value": ""},
            {"name": "Password", "value": "deluge"}
        ],
        "implementationName": "Deluge",
        "implementation": "Deluge",
        "configContract": "DelugeSettings",
        "protocol": "torrent",
        "priority": 10
    }).encode()).decode()
    
    result = run(f'lxc-attach -n 101 -- bash -c "echo {payload} | base64 -d | curl -s -X POST http://localhost:{port}/api/{version}/downloadclient -H \"Content-Type: application/json\" -H \"X-Api-Key: {apikey}\" -d @- --max-time 10" 2>&1')
    print(f"  [{srv}] {result[:200]}")

# ── STEP 3: Verify ──
print("\n=== VERIFY DOWNLOAD CLIENTS ===")
for srv, port, apikey in [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14"),
]:
    result = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/v3/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    print(f"  [{srv}] {result[:200]}")

# ── STEP 4: Final status ──
print("\n=== FINAL STATUS ===")
print(run('lxc-attach -n 101 -- docker ps --format "table {{.Names}}\\t{{.Status}}" 2>&1'))

ssh.close()
