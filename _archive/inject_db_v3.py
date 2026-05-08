#!/usr/bin/env python3
"""Inject Deluge client into all *arr DBs directly. Simpler approach."""
import sys, json, base64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

settings_json = json.dumps({
    "host": "deluge",
    "port": 48846,
    "useSsl": False,
    "urlBase": "",
    "password": "deluge",
    "addPaused": False,
    "downloadDirectory": None,
    "completedDirectory": None,
    "recentTvPriority": 0,
    "olderTvPriority": 0
})

# Write SQL script to a temp file
sql_script = f"""
DELETE FROM DownloadClients WHERE Implementation = 'Deluge';
INSERT INTO DownloadClients
  (Enable, Name, Implementation, Settings, ConfigContract, Priority, RemoveCompletedDownloads, RemoveFailedDownloads, Tags)
VALUES
  (1, 'Deluge', 'Deluge', '{settings_json}', 'DelugeSettings', 10, 1, 1, '[]');
"""

dbs = [
    "/var/lib/lxc/101/rootfs/opt/arrstack/sonarr/config/sonarr.db",
    "/var/lib/lxc/101/rootfs/opt/arrstack/radarr/config/radarr.db",
    "/var/lib/lxc/101/rootfs/opt/arrstack/lidarr/config/lidarr.db",
]

names = ["Sonarr", "Radarr", "Lidarr"]

for name, db in zip(names, dbs):
    sql_b64 = base64.b64encode(sql_script.encode()).decode()
    result = run(f'bash -c "echo {sql_b64} | base64 -d | sqlite3 {db} 2>&1"')
    print(f"[{name}] {result if result else '✅ Injected'}")

    # Verify
    result = run(f'sqlite3 "{db}" "SELECT Id, Name, Settings FROM DownloadClients" 2>&1')
    if 'Deluge' in result:
        print(f"  Data: {result[:200]}")
    else:
        print(f"  ⚠️ No data: {result[:200]}")

# Restart
print("\n=== RESTART *ARRs ===")
for srv in ["sonarr", "radarr", "lidarr"]:
    run(f'lxc-attach -n 101 -- docker restart {srv} 2>&1')
    print(f"  {srv} restarted")
time.sleep(8)

# Verify API
print("\n=== API VERIFY ===")
for name, port, apikey in [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14"),
    ("lidarr", 8686, "f5efa3b451a74385a880c2189e692b40"),
]:
    ver = "v3" if name != "lidarr" else "v1"
    result = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/{ver}/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    if 'Deluge' in result:
        import re
        h = re.search(r'"host"\s*:\s*"([^"]+)"', result)
        p = re.search(r'"port"\s*:\s*(\d+)', result)
        print(f"  [{name}] ✅ host={h.group(1) if h else '?'}, port={p.group(1) if p else '?'}")
    else:
        print(f"  [{name}] ❌ {result[:200]}")

ssh.close()
