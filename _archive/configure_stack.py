#!/usr/bin/env python3
"""Configure all ArrStack services via their REST APIs."""
import sys, json, time
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def lxc(cmd):
    """Run a command inside CT101 and return output."""
    stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- {cmd}')
    return stdout.read().decode().strip()

def api(method, service, endpoint, data=None):
    """Call a service API inside CT101 via curl."""
    port_map = {'sonarr': 8989, 'radarr': 7878, 'lidarr': 8686, 'prowlarr': 9696, 'bazarr': 6767}
    api_keys = {'sonarr': 'f8fc219f6076435eb5ef6d0bc4093121',
                'radarr': '1bb778a4366d47d89c7a4b07756dfc14',
                'lidarr': 'f5efa3b451a74385a880c2189e692b40',
                'prowlarr': None,
                'bazarr': None}
    
    port = port_map[service]
    key = api_keys[service]
    
    url = f"http://localhost:{port}/api/v3/{endpoint}"
    if service == 'prowlarr':
        url = f"http://localhost:{port}/api/v1/{endpoint}"
    elif service == 'bazarr':
        url = f"http://localhost:{port}/api/{endpoint}"
    
    headers = f"X-Api-Key: {key}" if key else ""
    
    if data:
        cmd = f'''curl -s -X {method} "{url}" \\
          -H "Content-Type: application/json" \\
          -H "{headers}" \\
          -d '{json.dumps(data)}' 2>&1'''
    else:
        cmd = f'curl -s -X {method} "{url}" -H "{headers}" 2>&1'
    
    stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- {cmd}')
    out = stdout.read().decode().strip()
    return out

def check_status(service, endpoint=""):
    """Quick health check."""
    r = api("GET", service, endpoint)
    return r[:200] if r else "EMPTY"

print("=" * 60)
print("ARRSTACK AUTO-CONFIGURATION")
print("=" * 60)

# ── 1. SONARR: Root folder + download client ──
print("\n[1/8] Sonarr: root folder /tv...")
r = api("POST", "sonarr", "rootfolder", {
    "path": "/tv",
    "name": "TV Shows"
})
print(f"  Result: {r[:150]}")

print("\n[2/8] Sonarr: Deluge download client...")
r = api("POST", "sonarr", "downloadclient", {
    "enable": True,
    "name": "Deluge",
    "fields": [
        {"name": "Host", "value": "deluge"},
        {"name": "Port", "value": 58846},
        {"name": "UseSSL", "value": False},
        {"name": "UrlBase", "value": ""},
        {"name": "Password", "value": ""}
    ],
    "implementationName": "Deluge",
    "implementation": "Deluge",
    "configContract": "DelugeSettings",
    "protocol": "torrent"
})
print(f"  Result: {r[:150] if r else 'OK (existing?)'}")

# ── 2. RADARR: Root folder + download client ──
print("\n[3/8] Radarr: root folder /Movies...")
r = api("POST", "radarr", "rootfolder", {
    "path": "/Movies",
    "name": "Movies"
})
print(f"  Result: {r[:150]}")

print("\n[4/8] Radarr: Deluge download client...")
r = api("POST", "radarr", "downloadclient", {
    "enable": True,
    "name": "Deluge",
    "fields": [
        {"name": "Host", "value": "deluge"},
        {"name": "Port", "value": 58846},
        {"name": "UseSSL", "value": False},
        {"name": "UrlBase", "value": ""},
        {"name": "Password", "value": ""}
    ],
    "implementationName": "Deluge",
    "implementation": "Deluge",
    "configContract": "DelugeSettings",
    "protocol": "torrent"
})
print(f"  Result: {r[:150] if r else 'OK (existing?)'}")

# ── 3. LIDARR: Root folder + download client ──
print("\n[5/8] Lidarr: root folder /music...")
r = api("POST", "lidarr", "rootfolder", {
    "path": "/music",
    "name": "Music"
})
print(f"  Result: {r[:150]}")

print("\n[6/8] Lidarr: Deluge download client...")
r = api("POST", "lidarr", "downloadclient", {
    "enable": True,
    "name": "Deluge",
    "fields": [
        {"name": "Host", "value": "deluge"},
        {"name": "Port", "value": 58846},
        {"name": "UseSSL", "value": False},
        {"name": "UrlBase", "value": ""},
        {"name": "Password", "value": ""}
    ],
    "implementationName": "Deluge",
    "implementation": "Deluge",
    "configContract": "DelugeSettings",
    "protocol": "torrent"
})
print(f"  Result: {r[:150] if r else 'OK (existing?)'}")

# ── 4. PROWLARR: Connect Sonarr + Radarr as apps ──
print("\n[7/8] Prowlarr: Connect Sonarr + Radarr...")
# First check existing apps
existing = api("GET", "prowlarr", "applications")
print(f"  Existing apps: {existing[:200]}")

# Add Sonarr app
r = api("POST", "prowlarr", "applications", {
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
print(f"  Sonarr app: {r[:200]}")

# Add Radarr app
r = api("POST", "prowlarr", "applications", {
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
print(f"  Radarr app: {r[:200]}")

# ── 5. BAZARR: Connect Sonarr + Radarr ──
print("\n[8/8] Bazarr: Connect Sonarr + Radarr...")
# Bazarr uses a different auth system - auth token from config file
bazarr_auth = lxc('grep -oP \'(?<="auth_token": ").*?(?=")\' /opt/arrstack/bazarr/config/config/config.ini 2>/dev/null')
print(f"  Bazarr auth token: {bazarr_auth[:30] if bazarr_auth else 'not found'}")

# Bazarr API for Sonarr settings
cmd = '''curl -s -X PATCH "http://localhost:6767/api/settings/sonarr" \\
  -H "Content-Type: application/json" \\
  -d '{"api_key":"f8fc219f6076435eb5ef6d0bc4093121","full_update":true,"host":"sonarr","port":8989,"ssl":false,"base_url":""}' 2>&1'''
stdin, stdout, stderr = ssh.exec_command(f'lxc-attach -n 101 -- {cmd}')
print(f"  Bazarr Sonarr: {stdout.read().decode()[:200]}")

cmd2 = '''curl -s -X PATCH "http://localhost:6767/api/settings/radarr" \\
  -H "Content-Type: application/json" \\
  -d '{"api_key":"1bb778a4366d47d89c7a4b07756dfc14","full_update":true,"host":"radarr","port":7878,"ssl":false,"base_url":""}' 2>&1'''
stdin2, stdout2, stderr2 = ssh.exec_command(f'lxc-attach -n 101 -- {cmd2}')
print(f"  Bazarr Radarr: {stdout2.read().decode()[:200]}")

print("\n" + "=" * 60)
print("CONFIGURATION TERMINÉE")
print("=" * 60)
print("\nAccès rapides :")
print("  NPM Admin  → http://10.0.0.70:81  (login: admin@example.com / changeme)")
print("  Sonarr     → http://10.0.0.70:8989")
print("  Radarr     → http://10.0.0.70:7878")
print("  Lidarr     → http://10.0.0.70:8686")
print("  Deluge     → http://10.0.0.70:8112  (pw: deluge)")
print("  Prowlarr   → http://10.0.0.70:9696")
print("  Bazarr     → http://10.0.0.70:6767")
print("  Heimdall   → http://10.0.0.70:8080")

ssh.close()
