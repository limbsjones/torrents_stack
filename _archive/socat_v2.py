#!/usr/bin/env python3
"""Start socat on diff port and verify."""
import sys
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode() + stderr.read().decode()

# Start socat on port 48846 (proxy to 127.0.0.1:58846)
print("=== START SOCAT ON 48846 ===")
# Use bash -c to keep socat in background
result = run('lxc-attach -n 101 -- docker exec deluge bash -c "socat TCP-LISTEN:48846,reuseaddr,fork TCP:127.0.0.1:58846 &" 2>&1')
print(result)
time.sleep(2)

# Check
print("=== LISTENING ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep -E "48846|58846|socat"'))

# Test from sonarr
print("\n=== TEST FROM SONARR ===")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 5 bash -c "echo > /dev/tcp/deluge/48846 2>&1 && echo OPEN || echo CLOSED"'))

# Also test from radarr
print(run('lxc-attach -n 101 -- docker exec radarr timeout 5 bash -c "echo > /dev/tcp/deluge/48846 2>&1 && echo OPEN || echo CLOSED"'))

# Test from LXC directly (CT101's localhost)
print("\n=== FROM LXC ===")
print(run('lxc-attach -n 101 -- timeout 3 bash -c "echo > /dev/tcp/10.0.0.70/48846 2>&1 && echo OPEN || echo CLOSED"'))
print(run('lxc-attach -n 101 -- curl -s -o /dev/null -w "%{http_code}" http://10.0.0.70:8112 2>&1'))

ssh.close()
