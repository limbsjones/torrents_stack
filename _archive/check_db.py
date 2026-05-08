#!/usr/bin/env python3
"""Check if *arr stores config in SQLite or XML."""
import sys, json
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode() + stderr.read().decode()

# Check config files
print("=== SONARR CONFIG FILES ===")
print(run('ls -la /var/lib/lxc/101/rootfs/opt/arrstack/sonarr/config/ 2>&1'))
print(run('ls -la /var/lib/lxc/101/rootfs/opt/arrstack/radarr/config/ 2>&1'))

# Check for SQLite DB
print("\n=== SQLITE DBS ===")
print(run('find /var/lib/lxc/101/rootfs/opt/arrstack/sonarr/config/ -name "*.db" 2>&1'))
print(run('find /var/lib/lxc/101/rootfs/opt/arrstack/radarr/config/ -name "*.db" 2>&1'))
print(run('find /var/lib/lxc/101/rootfs/opt/arrstack/lidarr/config/ -name "*.db" 2>&1'))

# Check config.xml  
print("\n=== CONFIG XML ===")
print(run('cat /var/lib/lxc/101/rootfs/opt/arrstack/sonarr/config/config.xml 2>&1 | head -20'))

# Try accessing SQLite
print("\n=== SONARR DB TABLES ===")
sonarr_db = '/var/lib/lxc/101/rootfs/opt/arrstack/sonarr/config/sonarr.db'
if sonarr_db:
    result = run(f'sqlite3 {sonarr_db} ".tables" 2>&1 | head -20')
    if "no such" not in result:
        print(result)
    else:
        # Try finding the correct DB name
        result = run('ls /var/lib/lxc/101/rootfs/opt/arrstack/sonarr/config/*.db 2>&1')
        print(result)

ssh.close()
