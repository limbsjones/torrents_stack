#!/usr/bin/env python3
"""Stop deluged, fix config+auth, restart, verify."""
import sys, json, time
import base64 as b64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip()

# ── STEP 1: Fix config files on host filesystem ──
fix_script = '''
import json, os

config_path = "/var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/core.conf"
auth_path = "/var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/auth"

# Read config
with open(config_path, "r") as f:
    raw = f.read()

# Parse the two-JSON format
idx = raw.index("}") + 1  
header = json.loads(raw[:idx])
config = json.loads(raw[idx:])

# Fix settings
config["allow_remote"] = True
config["listen_interface"] = "0.0.0.0"

# Write back
with open(config_path, "w") as f:
    f.write(json.dumps(header))
    f.write(json.dumps(config, indent=4))

# Add user to auth file  
# Format: username:password:level (10=admin)
with open(auth_path, "r") as f:
    auth_content = f.read()

if "deluge:deluge:10" not in auth_content:
    with open(auth_path, "a") as f:
        f.write("\\ndeluge:deluge:10\\n")

# Fix ownership
os.system("chown 101000:101000 " + config_path)
os.system("chown 101000:101000 " + auth_path)

print("CONFIG_FIXED")
print("allow_remote:", config["allow_remote"])
print("listen_interface:", config["listen_interface"])
print("auth_has_user:", "deluge:deluge:10" in auth_content)
'''

encoded = b64.b64encode(fix_script.encode()).decode()
result = run(f'echo {encoded} | base64 -d | python3')
print("=== CONFIG FIX ===")
print(result)

# ── STEP 2: Stop deluged process inside container, restart ──
print("\n=== KILLING DELUGED ===")
pid = run('lxc-attach -n 101 -- cat /opt/arrstack/deluge/config/deluged.pid 2>/dev/null')
print(f"deluged PID: {pid}")

# Kill and restart via the s6 supervisor
# The container uses s6-overlay, so we can signal the service
run('lxc-attach -n 101 -- s6-svc -d /run/service/svc-deluged 2>/dev/null')
time.sleep(2)
print(run('lxc-attach -n 101 -- ps aux | grep deluged 2>&1'))

# ── STEP 3: Start deluged from scratch with new config ──
print("\n=== STARTING DELUGED ===")
run('lxc-attach -n 101 -- s6-svc -u /run/service/svc-deluged 2>/dev/null')
time.sleep(3)

# Check daemon
print("\n=== DAEMON CHECK ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep 58846'))

# ── STEP 4: Test from Sonarr ──
print("\n=== SONARR -> DELUGE 58846 ===")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 3 bash -c "echo > /dev/tcp/deluge/58846 && echo OPEN || echo CLOSED" 2>&1'))

ssh.close()
