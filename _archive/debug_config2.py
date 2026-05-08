#!/usr/bin/env python3
"""Debug config files via paramiko."""
import sys
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# Read core.conf via host filesystem
print("=== CORE.CONF (raw) ===")
print(run("xxd /var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/core.conf | head -60"))

print("\n=== AUTH (raw) ===")
print(run("xxd /var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/auth"))

ssh.close()
