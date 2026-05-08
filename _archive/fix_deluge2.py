#!/usr/bin/env python3
"""Force Deluge remote access via deluge-console."""
import sys, json, time
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip()

# 1. Try setting via deluge-console inside the container
print("=== VIA DELUGE-CONSOLE ===")
cmd = 'lxc-attach -n 101 -- docker exec deluge deluge-console "config -s allow_remote true" 2>&1'
print(run(cmd))

# 2. Also set listen_interfaces
cmd2 = 'lxc-attach -n 101 -- docker exec deluge deluge-console "config -s listen_interface 0.0.0.0" 2>&1'
print(run(cmd2))

# 3. Verify config was read/set
cmd3 = 'lxc-attach -n 101 -- docker exec deluge deluge-console "config allow_remote" 2>&1'
print("allow_remote setting:", run(cmd3))

# 4. Check core.conf again to see if deluge-console changed it
time.sleep(2)
print("\n=== CORE.CONF AFTER deluge-console ===")
print(run('lxc-attach -n 101 -- grep -E "allow_remote|listen_interface" /opt/arrstack/deluge/config/core.conf'))

# 5. Now re-check daemon binding
print("\n=== DAEMON BINDING ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep 58846'))

# 6. Test from sonarr
print("\n=== SONARR -> DELUGE TEST ===")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 3 bash -c "echo > /dev/tcp/deluge/58846 && echo OPEN || echo CLOSED" 2>&1'))

ssh.close()
