#!/usr/bin/env python3
"""v2 - Corrected ArrStack API configuration."""
import sys, json, time
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def lxc(cmd):
    stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- sh -c \'{cmd}\'')
    return stdout.read().decode().strip()

# ── 1. FIX Sonarr Deluge (add password + check daemon) ──
print("[1] Sonarr: Fix Deluge client with password...")
# First delete any existing Deluge client
lxc('curl -s -X GET "http://localhost:8989/api/v3/downloadclient" -H "X-Api-Key: f8fc219f6076435eb5ef6d0bc4093121"')
# Create with correct fields
sonarr_deluge = json.dumps({
    "enable": True,
    "name": "Deluge",
    "fields": [
        {"name": "Host", "value": "deluge"},
        {"name": "Port", "value": 58846},
        {"name": "UseSSL", "value": False},
        {"name": "UrlBase", "value": ""},
        {"name": "Password", "value": "deluge"}
    ],
    "implementationName": "Deluge",
    "implementation": "Deluge",
    "configContract": "DelugeSettings",
    "protocol": "torrent",
    "priority": 10
})
cmd = f'''curl -s -X POST "http://localhost:8989/api/v3/downloadclient" \\
  -H "Content-Type: application/json" \\
  -H "X-Api-Key: f8fc219f6076435eb5ef6d0bc4093121" \\
  -d '{sonarr_deluge}' --max-time 10 2>&1'''
stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- sh -c \'{cmd}\'')
out = stdout.read().decode().strip()[:300]
print(f"  Result: {out}")

# ── 2. FIX Radarr Deluge (add priority + password) ──
print("\n[2] Radarr: Fix Deluge client...")
radarr_deluge = json.dumps({
    "enable": True,
    "name": "Deluge",
    "fields": [
        {"name": "Host", "value": "deluge"},
        {"name": "Port", "value": 58846},
        {"name": "UseSSL", "value": False},
        {"name": "UrlBase", "value": ""},
        {"name": "Password", "value": "deluge"}
    ],
    "implementationName": "Deluge",
    "implementation": "Deluge",
    "configContract": "DelugeSettings",
    "protocol": "torrent",
    "priority": 10
})
cmd = f'''curl -s -X POST "http://localhost:7878/api/v3/downloadclient" \\
  -H "Content-Type: application/json" \\
  -H "X-Api-Key: 1bb778a4366d47d89c7a4b07756dfc14" \\
  -d '{radarr_deluge}' --max-time 10 2>&1'''
stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- sh -c \'{cmd}\'')
out = stdout.read().decode().strip()[:300]
print(f"  Result: {out}")

# ── 3. LIDARR root folder ──  
print("\n[3] Lidarr: root folder /music...")
lidarr_rf = json.dumps({"path": "/music"})
cmd = f'''curl -s -X POST "http://localhost:8686/api/v1/rootfolder" \\
  -H "Content-Type: application/json" \\
  -H "X-Api-Key: f5efa3b451a74385a880c2189e692b40" \\
  -d '{lidarr_rf}' --max-time 10 2>&1'''
stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- sh -c \'{cmd}\'')
out = stdout.read().decode().strip()[:300]
print(f"  Result: {out}")

# ── 4. LIDARR Deluge ──
print("\n[4] Lidarr: Deluge client...")
lidarr_deluge = json.dumps({
    "enable": True,
    "name": "Deluge",
    "fields": [
        {"name": "Host", "value": "deluge"},
        {"name": "Port", "value": 58846},
        {"name": "UseSSL", "value": False},
        {"name": "UrlBase", "value": ""},
        {"name": "Password", "value": "deluge"}
    ],
    "implementationName": "Deluge",
    "implementation": "Deluge",
    "configContract": "DelugeSettings",
    "protocol": "torrent",
    "priority": 10
})
cmd = f'''curl -s -X POST "http://localhost:8686/api/v1/downloadclient" \\
  -H "Content-Type: application/json" \\
  -H "X-Api-Key: f5efa3b451a74385a880c2189e692b40" \\
  -d '{lidarr_deluge}' --max-time 10 2>&1'''
stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- sh -c \'{cmd}\'')
out = stdout.read().decode().strip()[:300]
print(f"  Result: {out}")

# ── 5. PROWLARR: Connect apps ──
print("\n[5] Prowlarr: Add Sonarr app...")
prowl_sonarr = json.dumps({
    "name": "Sonarr",
    "implementation": "Sonarr",
    "configContract": "SonarrSettings",
    "fields": [
        {"name": "prowlarrUrl", "value": "http://prowlarr:9696"},
        {"name": "baseUrl", "value": "http://sonarr:8989"},
        {"name": "apiKey", "value": "f8fc219f6076435eb5ef6d0bc4093121"},
        {"name": "syncCategories", "value": [5000, 5010, 5020, 5030, 5040]}
    ],
    "syncLevel": "fullSync"
})
cmd = f'''curl -s -X POST "http://localhost:9696/api/v1/applications" \\
  -H "Content-Type: application/json" \\
  -d '{prowl_sonarr}' --max-time 10 2>&1'''
stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- sh -c \'{cmd}\'')
out = stdout.read().decode().strip()[:300]
print(f"  Sonarr app: {out}")

print("\n[6] Prowlarr: Add Radarr app...")
prowl_radarr = json.dumps({
    "name": "Radarr",
    "implementation": "Radarr",
    "configContract": "RadarrSettings",
    "fields": [
        {"name": "prowlarrUrl", "value": "http://prowlarr:9696"},
        {"name": "baseUrl", "value": "http://radarr:7878"},
        {"name": "apiKey", "value": "1bb778a4366d47d89c7a4b07756dfc14"},
        {"name": "syncCategories", "value": [2000, 2010, 2020, 2030, 2040]}
    ],
    "syncLevel": "fullSync"
})
cmd = f'''curl -s -X POST "http://localhost:9696/api/v1/applications" \\
  -H "Content-Type: application/json" \\
  -d '{prowl_radarr}' --max-time 10 2>&1'''
stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- sh -c \'{cmd}\'')
out = stdout.read().decode().strip()[:300]
print(f"  Radarr app: {out}")

# ── 6. BAZARR ──
print("\n[7] Bazarr: Connect Sonarr...")
# Bazarr uses PUT not PATCH
bazarr_sonarr = json.dumps({
    "api_key": "f8fc219f6076435eb5ef6d0bc4093121",
    "full_update": True,
    "host": "sonarr",
    "port": 8989,
    "ssl": False,
    "base_url": ""
})
cmd = f'''curl -s -X PUT "http://localhost:6767/api/settings/sonarr" \\
  -H "Content-Type: application/json" \\
  -d '{bazarr_sonarr}' --max-time 10 2>&1'''
stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- sh -c \'{cmd}\'')
out = stdout.read().decode().strip()[:200]
print(f"  Sonarr: {out}")

print("\n[8] Bazarr: Connect Radarr...")
bazarr_radarr = json.dumps({
    "api_key": "1bb778a4366d47d89c7a4b07756dfc14",
    "full_update": True,
    "host": "radarr",
    "port": 7878,
    "ssl": False,
    "base_url": ""
})
cmd = f'''curl -s -X PUT "http://localhost:6767/api/settings/radarr" \\
  -H "Content-Type: application/json" \\
  -d '{bazarr_radarr}' --max-time 10 2>&1'''
stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- sh -c \'{cmd}\'')
out = stdout.read().decode().strip()[:200]
print(f"  Radarr: {out}")

# ── 7. Final verification ──
print("\n" + "=" * 60)
print("VÉRIFICATION FINALE")
time.sleep(3)

checks = [
    ("Sonarr Deluge", "curl -s 'http://localhost:8989/api/v3/downloadclient' -H 'X-Api-Key: f8fc219f6076435eb5ef6d0bc4093121' | python3 -c 'import sys,json; d=json.load(sys.stdin); print([x[\"name\"] for x in d] if d else \"empty\")'"),
    ("Radarr Deluge", "curl -s 'http://localhost:7878/api/v3/downloadclient' -H 'X-Api-Key: 1bb778a4366d47d89c7a4b07756dfc14' | python3 -c 'import sys,json; d=json.load(sys.stdin); print([x[\"name\"] for x in d] if d else \"empty\")'"),
    ("Sonarr Root", "curl -s 'http://localhost:8989/api/v3/rootfolder' -H 'X-Api-Key: f8fc219f6076435eb5ef6d0bc4093121' | python3 -c 'import sys,json; d=json.load(sys.stdin); print([x[\"path\"] for x in d] if d else \"empty\")'"),
    ("Radarr Root", "curl -s 'http://localhost:7878/api/v3/rootfolder' -H 'X-Api-Key: 1bb778a4366d47d89c7a4b07756dfc14' | python3 -c 'import sys,json; d=json.load(sys.stdin); print([x[\"path\"] for x in d] if d else \"empty\")'"),
    ("Prowlarr Apps", "curl -s 'http://localhost:9696/api/v1/applications' | python3 -c 'import sys,json; d=json.load(sys.stdin); print([x[\"name\"] for x in d] if d else \"empty\")'"),
]

for name, check in checks:
    cmd = f'lxc-attach -n 101 -- sh -c \'{check}\''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    print(f"  [{name}] {out}")

ssh.close()
print("\n✅ Configuration terminée !")
