#!/usr/bin/env python3
"""Configure Bazarr via config.yaml."""
import sys, json, yaml
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# Read current config
config_path = "/var/lib/lxc/101/rootfs/opt/arrstack/bazarr/config/config/config.yaml"
result = run(f'cat {config_path} 2>&1')
print("=== CURRENT CONFIG ===")
print(result)

# Parse and modify
import io
config = yaml.safe_load(result)
print("\n=== PARSED ===")
print(json.dumps(config, indent=2)[:500])

# Add/modify sonarr and radarr settings
config.setdefault('sonarr', {})
config['sonarr'].update({
    'base_url': '',
    'host': 'sonarr',
    'port': 8989,
    'ssl': False,
    'apikey': 'f8fc219f6076435eb5ef6d0bc4093121'
})

config.setdefault('radarr', {})
config['radarr'].update({
    'base_url': '',
    'host': 'radarr',
    'port': 7878,
    'ssl': False,
    'apikey': '1bb778a4366d47d89c7a4b07756dfc14'
})

# Write back
new_yaml = yaml.dump(config, default_flow_style=False)
import base64 as b64
yaml_b64 = b64.b64encode(new_yaml.encode()).decode()
result = run(f'echo {yaml_b64} | base64 -d > {config_path} 2>&1')
print(f"\n=== WRITE: {result if result else 'OK'} ===")

# Verify
result = run(f'cat {config_path} | head -30')
print("\n=== VERIFY ===")
print(result)

# Restart Bazarr
print("\n=== RESTART BAZARR ===")
run('lxc-attach -n 101 -- docker restart bazarr 2>&1')

import time
time.sleep(5)

print("\n=== BAZARR STATUS ===")
print(run('lxc-attach -n 101 -- docker ps --filter name=bazarr --format "table {{.Names}}\\t{{.Status}}" 2>&1'))

ssh.close()
