#!/usr/bin/env python3
"""Patch deluged service file inside the container."""
import sys, base64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# Step 1: Write the new run file inside the LXC
new_run = """#!/usr/bin/with-contenv bash
# shellcheck shell=bash

DELUGE_LOGLEVEL=${DELUGE_LOGLEVEL:-info}

if [[ -f /config/core.conf ]]; then
    DELUGED_PORT=$(grep '"daemon_port"' /config/core.conf | tr -cd "[:digit:]")
fi

if [[ -z ${LSIO_NON_ROOT_USER} ]]; then
    exec \\
        s6-notifyoncheck -d -n 300 -w 1000 -c "nc -z 127.0.0.1 ${DELUGED_PORT:-58846}" \\
            s6-setuidgid abc /lsiopy/bin/deluged -c /config -d -i 0.0.0.0 --loglevel="${DELUGE_LOGLEVEL}"
else
    exec \\
        s6-notifyoncheck -d -n 300 -w 1000 -c "nc -z 127.0.0.1 ${DELUGED_PORT:-58846}" \\
            /lsiopy/bin/deluged -c /config -d -i 0.0.0.0 --loglevel="${DELUGE_LOGLEVEL}"
fi
"""
b64 = base64.b64encode(new_run.encode()).decode()

# Write file inside the LXC
print("=== WRITING FILE INSIDE LXC ===")
result = run(f'lxc-attach -n 101 -- bash -c "echo {b64} | base64 -d > /tmp/svc-deluged-run" 2>&1')
print(result)

# Copy into the deluge container  
print("=== COPYING INTO CONTAINER ===")
result = run('lxc-attach -n 101 -- docker cp /tmp/svc-deluged-run deluge:/etc/s6-overlay/s6-rc.d/svc-deluged/run 2>&1')
print(result)

# Verify
print("=== VERIFY ===")
result = run('lxc-attach -n 101 -- docker exec deluge head -15 /etc/s6-overlay/s6-rc.d/svc-deluged/run 2>&1')
print(result)

# Restart the service
print("\n=== RESTART DELUGED SERVICE ===")
run('lxc-attach -n 101 -- docker exec deluge s6-svc -d /run/service/svc-deluged 2>&1')
time.sleep(2)
run('lxc-attach -n 101 -- docker exec deluge s6-svc -u /run/service/svc-deluged 2>&1')
time.sleep(5)

# Check
print("=== DAEMON BINDING ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep 58846'))

print("\n=== SONARR -> DELUGE ===")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 3 bash -c "echo > /dev/tcp/deluge/58846 2>&1 && echo OPEN || echo CLOSED"'))

ssh.close()
