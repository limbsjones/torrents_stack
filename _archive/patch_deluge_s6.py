#!/usr/bin/env python3
"""Patch deluged service file to add -i 0.0.0.0 flag."""
import sys, base64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# New service file with -i 0.0.0.0 added
new_run_content = """#!/usr/bin/with-contenv bash
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

b64_content = base64.b64encode(new_run_content.encode()).decode()

# Write the modified file into the deluge container
commands = f"""
echo {b64_content} | base64 -d > /tmp/svc-deluged-run
lxc-attach -n 101 -- docker cp /tmp/svc-deluged-run deluge:/etc/s6-overlay/s6-rc.d/svc-deluged/run 2>&1
echo "COPY: $?"
# Verify
lxc-attach -n 101 -- docker exec deluge head -10 /etc/s6-overlay/s6-rc.d/svc-deluged/run 2>&1
# Remove temp file
rm -f /tmp/svc-deluged-run
"""
result = run(f'''bash -c '{commands}' ''')
print("=== FILE PATCH ===")
print(result)

# Restart deluged service
print("\n=== RESTARTING DELUGED ===")
# First stop
run('lxc-attach -n 101 -- docker exec deluge s6-svc -d /run/service/svc-deluged 2>&1')
time.sleep(2)
# Start again
run('lxc-attach -n 101 -- docker exec deluge s6-svc -u /run/service/svc-deluged 2>&1')
time.sleep(5)

# Check daemon binding
print("\n=== DAEMON BINDING ===")
print(run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep 58846'))

# Test from sonarr
print("\n=== SONARR -> DELUGE TEST ===")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 3 bash -c "echo > /dev/tcp/deluge/58846 && echo OPEN || echo CLOSED" 2>&1'))

ssh.close()
