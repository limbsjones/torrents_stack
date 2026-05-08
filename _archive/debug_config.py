#!/usr/bin/env python3
"""Debug: check the written config file verbatim."""
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# Read the config file verbatim
result = run('cat /var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/core.conf')
print("=== FULL CORE.CONF VERBATIM ===")
print(repr(result[:1000]))
print(f"\n--- Total length: {len(result)} chars ---")

# Also check auth
result2 = run('cat /var/lib/lxc/101/rootfs/opt/arrstack/deluge/config/auth')
print("\n=== AUTH VERBATIM ===")
print(repr(result2))

ssh.close()
