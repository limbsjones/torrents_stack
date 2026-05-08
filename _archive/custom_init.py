#!/usr/bin/env python3
"""Add custom init script to deluge container for socat persistence."""
import sys
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time, base64

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode() + stderr.read().decode()

# Check init-custom-files mechanism
print("=== INIT-CUSTOM-FILES ===")
print(run('lxc-attach -n 101 -- docker exec deluge cat /etc/s6-overlay/s6-rc.d/init-custom-files/run 2>&1'))

# Approach: write a custom script to /config/init/ inside the container
# which linuxserver checks at startup
print("\n=== CHECK CUSTOM INIT PATHS ===")
print(run('lxc-attach -n 101 -- docker exec deluge ls -la /config/ 2>&1 | head -10'))

# Actually, let me try the approach from linuxserver docs:
# Mount a script to /etc/cont-init.d/ or use the config directory
# For linuxserver/deluge, custom init scripts go into /config/init/

# Let me just add socat start script to /config/init/
init_script = """#!/usr/bin/with-contenv bash
# Start socat proxy for deluge daemon
if command -v socat &>/dev/null; then
    socat TCP-LISTEN:48846,reuseaddr,fork TCP:127.0.0.1:58846 &
    echo "[custom-init] socat started on 48846 -> 58846"
else
    echo "[custom-init] socat not found, skipping"
fi
"""
b64_init = base64.b64encode(init_script.encode()).decode()

print("\n=== WRITING CUSTOM INIT ===")
result = run(f'lxc-attach -n 101 -- bash -c "mkdir -p /config/init && echo {b64_init} | base64 -d > /config/init/socat.sh && chmod +x /config/init/socat.sh" 2>&1')
print(result)

# Verify
print(run('lxc-attach -n 101 -- ls -la /config/init/ 2>&1'))
print(run('lxc-attach -n 101 -- head -10 /config/init/socat.sh 2>&1'))

# Restart deluge
print("\n=== RESTART DELUGE ===")
print(run('lxc-attach -n 101 -- docker restart deluge 2>&1'))
time.sleep(8)

# Check
print("\n=== VERIFY ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep -E "48846|socat"'))
print("---")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 5 bash -c "echo > /dev/tcp/deluge/48846 2>&1 && echo OPEN || echo CLOSED"'))

ssh.close()
