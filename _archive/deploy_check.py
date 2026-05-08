#!/usr/bin/env python3
import sys
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode().strip()

# 1. Docker ps
print("=== DOCKER PS ===")
print(run('lxc-attach -n 101 -- docker ps --format "table {{.Names}}\\t{{.Status}}"'))

# 2. NPM port check  
time.sleep(3)
print("\n=== NPM HTTP (port 81) ===")
print(run('lxc-attach -n 101 -- curl -s -o /dev/null -w "%{http_code}" http://localhost:81'))

# 3. Files check
print("\n=== COMPOSE CHECK ===")
print(run('lxc-attach -n 101 -- head -5 /opt/arrstack/compose.yaml'))

# 4. API keys from config files  
print("\n=== SONARR API KEY ===")
apikey = run('lxc-attach -n 101 -- grep -oP "(?<=<ApiKey>).*?(?=</ApiKey>)" /opt/arrstack/sonarr/config/config.xml 2>/dev/null')
print(apikey)

print("\n=== RADARR API KEY ===")
apikey_r = run('lxc-attach -n 101 -- grep -oP "(?<=<ApiKey>).*?(?=</ApiKey>)" /opt/arrstack/radarr/config/config.xml 2>/dev/null')
print(apikey_r)

print("\n=== LIDARR API KEY ===")
apikey_l = run('lxc-attach -n 101 -- grep -oP "(?<=<ApiKey>).*?(?=</ApiKey>)" /opt/arrstack/lidarr/config/config.xml 2>/dev/null')
print(apikey_l)

ssh.close()
