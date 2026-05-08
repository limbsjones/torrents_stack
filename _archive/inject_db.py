#!/usr/bin/env python3
"""Inject Deluge download client into *arr databases directly."""
import sys, json, base64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# Check DownloadClients table schema for each *arr
print("=== SONARR: DownloadClients schema ===")
print(run('sqlite3 /var/lib/lxc/101/rootfs/opt/arrstack/sonarr/config/sonarr.db ".schema DownloadClients" 2>&1'))

print("\n=== SONARR: existing clients ===")
print(run('sqlite3 /var/lib/lxc/101/rootfs/opt/arrstack/sonarr/config/sonarr.db "SELECT * FROM DownloadClients" 2>&1'))

print("\n=== RADARR: DownloadClients schema ===")
print(run('sqlite3 /var/lib/lxc/101/rootfs/opt/arrstack/radarr/config/radarr.db ".schema DownloadClients" 2>&1'))

print("\n=== LIDARR: find download clients table ===")
print(run('sqlite3 /var/lib/lxc/101/rootfs/opt/arrstack/lidarr/config/lidarr.db ".tables" 2>&1 | tr " " "\\n" | grep -i download'))

ssh.close()
