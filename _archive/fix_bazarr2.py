#!/usr/bin/env python3
"""Write bazarr config.yaml directly."""
import sys, base64
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
print("=== CURRENT ===")
print(current[:500])

# The Bazarr config.yaml might use specific keys for sonarr/radarr
# Let me append the correct config
new_config = current.rstrip() + """
sonarr:
  apikey: f8fc219f6076435eb5ef6d0bc4093121
  base_url: ''
  full_update: false
  host: sonarr
  port: 8989
  ssl: false

radarr:
  apikey: 1bb778a4366d47d89c7a4b07756dfc14
  base_url: ''
  full_update: false
  host: radarr
  port: 7878
  ssl: false
"""

new_b64 = base64.b64encode(new_config.encode()).decode()
result = run(f'echo {new_b64} | base64 -d > {config_path}')
print(f"\n=== WRITE: {result if result else 'OK'} ===")

# Verify
result = run(f'cat {config_path}')
print("\n=== RESULT ===")
print(result)

# Restart
print("\n=== RESTART BAZARR ===")
run('lxc-attach -n 101 -- docker restart bazarr')
import time
time.sleep(5)
print(run('lxc-attach -n 101 -- docker ps --filter name=bazarr --format "table {{.Names}}\\t{{.Status}}"'))

ssh.close()
