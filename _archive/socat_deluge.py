#!/usr/bin/env python3
"""Install socat in Alpine-based deluge container and run proxy."""
import sys
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    return out + err

# Check what's available
print("=== CONTAINER OS CHECK ===")
print(run('lxc-attach -n 101 -- docker exec deluge cat /etc/os-release 2>&1'))
print(run('lxc-attach -n 101 -- docker exec deluge which socat nc bash 2>&1'))

# Install socat via apk
print("\n=== INSTALL SOCAT ===")
print(run('lxc-attach -n 101 -- docker exec deluge apk add socat 2>&1 | tail -5'))

# Kill existing deluged, restart with -i 0.0.0.0 via modified run file
# Actually - we already patched the run file. Let me check if the issue is 
# that s6-notifyoncheck is checking 127.0.0.1 and the socat approach.

# Quick test: just start socat in background
print("\n=== START SOCAT ===")
time.sleep(2)
result = run('lxc-attach -n 101 -- docker exec -d deluge socat TCP-LISTEN:58846,reuseaddr,fork TCP:127.0.0.1:58846 2>&1')
print(result)
time.sleep(2)

# Check
print("\n=== LISTENING PORTS ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep -E "5884|socat"'))

# Test from sonarr
print("\n=== SONARR -> DELUGE 58846 ===")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 5 bash -c "echo > /dev/tcp/deluge/58846 2>&1 && echo OPEN || echo CLOSED"'))

ssh.close()
