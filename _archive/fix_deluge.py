#!/usr/bin/env python3
"""Fix Deluge daemon to listen on 0.0.0.0:58846."""
import sys, json, time
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip()

# 1. Check the file we wrote
print("=== CORE.CONF allow_remote ===")
print(run('grep -E "allow_remote|daemon_port|listen_interface" /var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/core.conf'))

# 2. The config has a weird format: {"file":1,"format":1}{...config...}
# We need the config part between the two.
# Actually, I'll just write a completely new config using Python on the host

print("\n=== FIXING WITH PYTHON ON HOST ===")
python_fix = '''
import json
with open("/var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/core.conf", "r") as f:
    raw = f.read()
# Find the second JSON object
idx = raw.index("}{") + 1
config = json.loads(raw[idx:])
config["allow_remote"] = True
config["listen_interface"] = "0.0.0.0"
# Also ensure daemon_port is correct
config["daemon_port"] = 58846
# Rebuild with the header first
header = json.loads(raw[:idx])
with open("/var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/core.conf", "w") as f:
    f.write(json.dumps(header))
    f.write(json.dumps(config, indent=4))
print("OK: allow_remote=", config["allow_remote"], "listen_interface=", config["listen_interface"])
'''
encoded = __import__('base64').b64encode(python_fix.encode()).decode()
result = run(f'echo {encoded} | base64 -d | python3')
print(result)

# 3. Verify
print("\n=== VERIFY FILE ===")
print(run('grep -E "allow_remote|daemon_port|listen_interface" /var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/core.conf'))

# 4. Restart Deluge
print("\n=== RESTART ===")
print(run('lxc-attach -n 101 -- docker restart deluge'))
time.sleep(3)

# 5. Check daemon listening
print("\n=== DAEMON LISTENING ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep 58846'))

# 6. Test connectivity from Sonarr
print("\n=== SONARR -> DELUGE 58846 ===")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 3 bash -c "echo > /dev/tcp/deluge/58846 && echo OPEN || echo CLOSED" 2>&1'))

ssh.close()
