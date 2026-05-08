#!/usr/bin/env python3
"""Check exact sonarr/radarr sections in Bazarr config."""
import sys
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

config_path = "/var/lib/lxc/101/rootfs/opt/arrstack/bazarr/config/config/config.yaml"
lines = run(f'cat {config_path}').split('\n')
sonarr_lines = []
radarr_lines = []
in_sonarr = in_radarr = False

for i, line in enumerate(lines):
    if line.strip() == 'sonarr:' and not in_sonarr:
        in_sonarr = True
        in_radarr = False
        sonarr_lines.append(f"Line {i}: {line}")
    elif line.strip() == 'radarr:' and not in_radarr:
        in_radarr = True
        in_sonarr = False
        radarr_lines.append(f"Line {i}: {line}")
    elif in_sonarr and line.startswith('  '):
        sonarr_lines.append(f"Line {i}: {line}")
    elif in_radarr and line.startswith('  '):
        radarr_lines.append(f"Line {i}: {line}")
    else:
        in_sonarr = in_radarr = False

print("=== SONARR CONFIG ===")
for l in sonarr_lines:
    print(l)
print("\n=== RADARR CONFIG ===")
for l in radarr_lines:
    print(l)

# Also check general section for use_sonarr/use_radarr
print("\n=== GENERAL SECTION ===")
for i, line in enumerate(lines):
    if 'use_sonarr' in line or 'use_radarr' in line:
        print(f"Line {i}: {line}")

ssh.close()
