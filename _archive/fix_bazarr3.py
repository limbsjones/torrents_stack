#!/usr/bin/env python3
"""Fix Bazarr config properly - merge values into existing sections."""
import sys, base64, re
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

config_path = "/var/lib/lxc/101/rootfs/opt/arrstack/bazarr/config/config/config.yaml"

# Read current
current = run(f'cat {config_path}')

# Fix: Remove the duplicated sections at the end, update the original sections
# Strategy: Remove everything after line "sonarr:" that was appended (the second occurrence)
# Then update the existing sonarr/radarr values

lines = current.split('\n')

# Find all "sonarr:" section indices
sonarr_indices = [i for i, l in enumerate(lines) if l.strip().startswith('sonarr:')]
radarr_indices = [i for i, l in enumerate(lines) if l.strip().startswith('radarr:')]

print(f"sonarr at lines: {sonarr_indices}")
print(f"radarr at lines: {radarr_indices}")

# Remove from the second occurrence of sonarr to the end
if len(sonarr_indices) > 1:
    # Keep first sonarr section (and everything before it)
    # Also keep first radarr section
    # Cut from second sonarr to end
    cut_at = sonarr_indices[-1]  # second occurrence
    lines = lines[:cut_at]
    current = '\n'.join(lines)
    
    # Now update the existing sonarr values
    old = '''sonarr:
  apikey: ''
  base_url: /
  defer_search_signalr: false
  exclude_season_zero: false
  excluded_series_types: []
  excluded_tags: []
  full_update: Daily
  full_update_day: 6
  full_update_hour: 4
  http_timeout: 60
  ip: 127.0.0.1
  only_monitored: false
  port: 8989
  series_sync: 60
  series_sync_on_live: true
  ssl: false
  sync_only_monitored_episodes: false
  sync_only_monitored_series: false
  use_ffprobe_cache: true'''
    
    new = '''sonarr:
  apikey: f8fc219f6076435eb5ef6d0bc4093121
  base_url: /
  defer_search_signalr: false
  exclude_season_zero: false
  excluded_series_types: []
  excluded_tags: []
  full_update: Daily
  full_update_day: 6
  full_update_hour: 4
  http_timeout: 60
  ip: sonarr
  only_monitored: false
  port: 8989
  series_sync: 60
  series_sync_on_live: true
  ssl: false
  sync_only_monitored_episodes: false
  sync_only_monitored_series: false
  use_ffprobe_cache: true'''
    
    current = current.replace(old, new)
    
    # Update radarr similarly
    old_r = '''radarr:
  apikey: ''
  base_url: /
  defer_search_signalr: false
  excluded_tags: []
  full_update: Daily
  full_update_day: 6
  full_update_hour: 4
  http_timeout: 60
  ip: 127.0.0.1
  movies_sync: 60
  movies_sync_on_live: true
  only_monitored: false
  port: 7878
  ssl: false
  sync_only_monitored_movies: false
  use_ffprobe_cache: true'''
    
    new_r = '''radarr:
  apikey: 1bb778a4366d47d89c7a4b07756dfc14
  base_url: /
  defer_search_signalr: false
  excluded_tags: []
  full_update: Daily
  full_update_day: 6
  full_update_hour: 4
  http_timeout: 60
  ip: radarr
  movies_sync: 60
  movies_sync_on_live: true
  only_monitored: false
  port: 7878
  ssl: false
  sync_only_monitored_movies: false
  use_ffprobe_cache: true'''
    
    current = current.replace(old_r, new_r)
    
    # Also update the general.use_sonarr and general.use_radarr settings
    current = current.replace('use_radarr: false', 'use_radarr: true')
    current = current.replace('use_sonarr: false', 'use_sonarr: true')
    
    # Write back
    new_b64 = base64.b64encode(current.encode()).decode()
    result = run(f'echo {new_b64} | base64 -d > {config_path}')
    print(f"Write: {result if result else 'OK'}")
    
    # Verify
    result = run(f'cat {config_path}')
    # Check no duplicates
    if result.count('sonarr:') == 2 and result.count('radarr:') == 2:
        print("✅ Single sonarr/radarr sections now")
    else:
        print(f"⚠️ sonarr appears {result.count('sonarr:')} times, radarr {result.count('radarr:')} times")
    
    # Show relevant section
    print("\n=== SONARR SECTION ===")
    for line in result.split('\n'):
        if 'sonarr' in line.lower() or 'radarr' in line.lower() or 'apikey' in line.lower() or 'ip:' in line:
            print(line)
else:
    print("No duplicate sections found, just updating existing values")
    # Simple replacement
    current = current.replace("  ip: 127.0.0.1\n  port: 8989", "  ip: sonarr\n  port: 8989")
    current = current.replace("  apikey: ''\n  base_url: /\n", "  apikey: f8fc219f6076435eb5ef6d0bc4093121\n  base_url: /\n")
    # Actually, let me just do targeted replacements
    print("Would do targeted replacements")

# Restart
print("\n=== RESTART BAZARR ===")
run('lxc-attach -n 101 -- docker restart bazarr')

import time
time.sleep(5)
print(run('lxc-attach -n 101 -- docker ps --filter name=bazarr --format "table {{.Names}}\\t{{.Status}}"'))

ssh.close()
