#!/usr/bin/env python3
"""Fix Deluge startup to bind daemon to 0.0.0.0."""
import sys
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# 1. Check the s6 service run file for deluged
print("=== S6 DELUGED SERVICE FILE ===")
print(run('lxc-attach -n 101 -- docker exec deluge cat /etc/s6-overlay/s6-rc.d/svc-deluged/run 2>&1'))

print("\n=== S6 DELUGED FINISH FILE ===")
print(run('lxc-attach -n 101 -- docker exec deluge cat /etc/s6-overlay/s6-rc.d/svc-deluged/finish 2>&1'))

# 2. Check if there's a custom-cont-init.d or similar
print("\n=== CUSTOM INIT SCRIPTS ===")
print(run('lxc-attach -n 101 -- docker exec deluge ls -la /etc/s6-overlay/s6-rc.d/ 2>&1'))
print(run('lxc-attach -n 101 -- docker exec deluge find /etc -name "*.sh" -type f 2>&1 | head -20'))

# 3. Check if there's a custom-cont-init dir for linuxserver
print("\n=== CUSTOM CONT INIT ===")
print(run('lxc-attach -n 101 -- docker exec deluge ls -la /custom-cont-init.d/ 2>&1'))
print(run('lxc-attach -n 101 -- docker exec deluge ls -la /etc/cont-init.d/ 2>&1 | head -20'))

ssh.close()
