#!/usr/bin/env python3
"""Inject Deluge client into all *arr DBs directly."""
import sys, json
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

settings = {
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
}

for app, db in [
    ("Sonarr", "/var/lib/lxc/101/rootfs/opt/arrstack/sonarr/config/sonarr.db"),
    ("Radarr", "/var/lib/lxc/101/rootfs/opt/arrstack/radarr/config/radarr.db"),
    ("Lidarr", "/var/lib/lxc/101/rootfs/opt/arrstack/lidarr/config/lidarr.db"),
]:
    settings_json = json.dumps(settings).replace("'", "''")
    
    # Delete existing Deluge clients
    run(f'sqlite3 "{db}" "DELETE FROM DownloadClients WHERE Implementation='\''Deluge'\''" 2>&1')
    
    # Insert fresh
    sql = f"""INSERT INTO DownloadClients (Enable, Name, Implementation, Settings, ConfigContract, Priority, RemoveCompletedDownloads, RemoveFailedDownloads, Tags)
VALUES (1, 'Deluge', 'Deluge', '{settings_json}', 'DelugeSettings', 10, 1, 1, '[]');"""
    
    # Double-check quoting
    sql = sql.replace('"', '""')
    result = run(f'sqlite3 "{db}" "{sql}" 2>&1')
    print(f"[{app}] insert: {result[:100] if result else 'OK'}")
    
    # Verify
    result = run(f'sqlite3 "{db}" "SELECT Id, Name, Implementation, Settings FROM DownloadClients" 2>&1')
    print(f"  Data: {result[:300]}")

# Now restart all *arr containers to pick up the changes
print("\n=== RESTART *ARRs ===")
for srv in ["sonarr", "radarr", "lidarr"]:
    print(f"  Restarting {srv}...")
    run(f'lxc-attach -n 101 -- docker restart {srv} 2>&1')

import time
time.sleep(8)

# Verify API now returns the clients
print("\n=== VERIFY API ===")
for name, port, apikey in [
    ("sonarr", 8989, "f8fc219f6076435eb5ef6d0bc4093121"),
    ("radarr", 7878, "1bb778a4366d47d89c7a4b07756dfc14"),
]:
    result = run(f'lxc-attach -n 101 -- curl -s "http://localhost:{port}/api/v3/downloadclient" -H "X-Api-Key: {apikey}" --max-time 5 2>&1')
    if 'Deluge' in result:
        import re
        host_m = re.search(r'"host"\s*:\s*"([^"]+)"', result)
        port_m = re.search(r'"port"\s*:\s*(\d+)', result)
        h = host_m.group(1) if host_m else '?'
        p = port_m.group(1) if port_m else '?'
        print(f"  [{name}] ✅ Deluge active (host={h}, port={p})")
    else:
        print(f"  [{name}] ❌ {result[:200]}")

ssh.close()
