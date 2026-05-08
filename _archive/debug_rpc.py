#!/usr/bin/env python3
"""Debug deluge RPC connectivity from Sonarr."""
import sys, json
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode() + stderr.read().decode()

# Test connectivity from Sonarr container
print("=== DNS RESOLUTION ===")
print(run('lxc-attach -n 101 -- docker exec sonarr getent hosts deluge 2>&1'))
print(run('lxc-attach -n 101 -- docker exec sonarr nslookup deluge 2>&1 | head -10'))

print("\n=== TCP CONNECTIVITY (nc -zv) ===")
print(run('lxc-attach -n 101 -- docker exec sonarr nc -zv deluge 48846 2>&1'))
print(run('lxc-attach -n 101 -- docker exec sonarr nc -zv deluge 58846 2>&1'))
print(run('lxc-attach -n 101 -- docker exec sonarr nc -zv deluge 8112 2>&1'))

print("\n=== SIMULATE DELUGE RPC ===")
# Test via python inside sonarr container
rpc_test = """
import socket, time
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
try:
    s.connect(('deluge', 48846))
    print("CONNECTED to deluge:48846")
    # Deluge RPC uses len+payload protocol
    # Send a test RPC message
    s.close()
except Exception as e:
    print(f"FAILED: {e}")
"""
b64 = __import__('base64').b64encode(rpc_test.encode()).decode()
result = run(f'lxc-attach -n 101 -- bash -c "echo {b64} | base64 -d | docker exec -i sonarr python3" 2>&1')
print(result)

print("\n=== DELUGE AUTH FILE ===")
print(run('cat /var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/auth'))

# Check if radarr can also connect
print("\n=== RADARR -> DELUGE ===")
print(run('lxc-attach -n 101 -- docker exec radarr nc -zv deluge 48846 2>&1'))

ssh.close()
