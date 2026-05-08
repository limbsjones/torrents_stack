#!/usr/bin/env python3
"""Fix Deluge properly - check auth, stop daemon, edit config, restart."""
import sys, json, time
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip()

# Check all relevant files
print("=== DELUGE CONFIG PATH VERIFICATION ===")
print(run('ls -la /var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/ 2>&1 | head -20'))

print("\n=== AUTH FILE ===")
print(run('cat /var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/auth 2>&1'))

print("\n=== DOCKER VOLUME MOUNT ===")
# Check the docker inspect for the actual volume mount path
print(run('lxc-attach -n 101 -- docker inspect deluge --format "{{json .Mounts}}" 2>&1 | python3 -c "import sys,json; [print(m[\'Source\'],\'->\',m[\'Destination\']) for m in json.load(sys.stdin)]" 2>/dev/null'))

ssh.close()
