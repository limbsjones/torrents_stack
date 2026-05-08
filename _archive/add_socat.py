#!/usr/bin/env python3
"""Add socat to proxy deluge daemon port."""
import sys, base64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# Step 1: Install socat in the deluge container
print("=== INSTALL SOCAT ===")
result = run('lxc-attach -n 101 -- docker exec deluge apt-get update -qq 2>&1 | tail -3')
print(result)
result = run('lxc-attach -n 101 -- docker exec deluge apt-get install -y -qq socat 2>&1 | tail -3')
print(result)

# Step 2: Create an s6 service for socat
socat_run = """#!/usr/bin/with-contenv bash
exec s6-setuidgid abc socat TCP-LISTEN:68846,fork,reuseaddr TCP:127.0.0.1:58846
"""
b64_socat = base64.b64encode(socat_run.encode()).decode()

# Step 3: Write the socat service directory
commands = f"""
lxc-attach -n 101 -- bash -c "mkdir -p /tmp/svc-socat && echo {b64_socat} | base64 -d > /tmp/svc-socat/run && chmod +x /tmp/svc-socat/run" 2>&1
echo "WRITE: $?"
lxc-attach -n 101 -- docker cp /tmp/svc-socat deluge:/etc/s6-overlay/s6-rc.d/svc-socat/ 2>&1
echo "CP: $?"
lxc-attach -n 101 -- docker exec deluge chmod +x /etc/s6-overlay/s6-rc.d/svc-socat/run 2>&1
echo "CHMOD: $?"
"""
result = run(f"bash -c '{commands}'")
print("=== SERVICE CREATED ===")
print(result)

# Step 4: Create a type file for the service (needed by s6-rc)
commands2 = """
lxc-attach -n 101 -- bash -c 'echo "oneshot" > /tmp/svc-socat-type && docker cp /tmp/svc-socat-type deluge:/etc/s6-overlay/s6-rc.d/svc-socat/type' 2>&1
echo "TYPE: $?"
"""
result2 = run(f"bash -c '{commands2}'")
print(result2)

# Step 5: Start the socat service
print("\n=== START SOCAT ===")
run('lxc-attach -n 101 -- docker exec deluge s6-svc -u /run/service/svc-socat 2>&1')
time.sleep(2)

# Step 6: Check
print("=== SOCAT CHECK ===")
result = run('lxc-attach -n 101 -- docker exec deluge netstat -tlnp 2>&1 | grep 68846')
print(result)

# Step 7: Test from sonarr on port 68846
print("\n=== SONARR -> DELUGE 68846 ===")
print(run('lxc-attach -n 101 -- docker exec sonarr timeout 5 bash -c "echo > /dev/tcp/deluge/68846 2>&1 && echo OPEN || echo CLOSED"'))

ssh.close()
