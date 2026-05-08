#!/usr/bin/env python3
"""Test Deluge RPC auth and connection."""
import sys
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode() + stderr.read().decode()

# Test 1: Can we connect to deluged via RPC with socat proxy?
print("=== DELUGE CONSOLE VIA SOCAT ===")
# Use deluge-console from inside the deluge container to test connectivity via socat proxy
result = run('lxc-attach -n 101 -- docker exec deluge deluge-console -c /config "connect 127.0.0.1:58846 deluge deluge" 2>&1')
print(result[:500])

# Test 2: Check if deluged is actually responding properly
print("\n=== TEST: direct deluged connection ===")
result = run('lxc-attach -n 101 -- docker exec deluge timeout 5 deluge-console -c /config "info" 2>&1')
print(result[:500])

# Test 3: Try to connect from sonarr container using a tool
# Sonarr doesn't have python, but maybe we can use curl or another method
print("\n=== SONARR CONTAINER TOOLS ===")
print(run('lxc-attach -n 101 -- docker exec sonarr which curl wget nc bash ls 2>&1'))

# Test 4: Try installing python3 in sonarr container
print("\n=== INSTALL PYTHON IN SONARR ===")
result = run('lxc-attach -n 101 -- docker exec sonarr apk add python3 2>&1 | tail -5')
print(result)

# Test 5: Now test RPC from sonarr
rpc_test = r'''
import socket, json, struct, hashlib

def send_rpc(host, port, method, args, password):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((host, port))
    
    # Deluge RPC protocol: 
    # 1. Send: <msg_len:4><msg>
    # 2. Protocol uses zlib compressed JSON-RPC
    import zlib
    
    # Login request
    req_id = 1
    login_msg = json.dumps({
        "method": "daemon.login",
        "params": [password, "2.0"],
        "id": req_id
    })
    
    compressed = zlib.compress(login_msg.encode())
    header = struct.pack("!i", len(compressed))
    s.sendall(header + compressed)
    
    # Read response
    resp_header = s.recv(4)
    if len(resp_header) < 4:
        return "Incomplete response header"
    resp_len = struct.unpack("!i", resp_header)[0]
    resp_data = b""
    while len(resp_data) < resp_len:
        chunk = s.recv(resp_len - len(resp_data))
        if not chunk:
            break
        resp_data += chunk
    
    decompressed = zlib.decompress(resp_data)
    s.close()
    return decompressed.decode()

try:
    result = send_rpc("127.0.0.1", 58846, "daemon.login", ["deluge"], "deluge")
    print("RPC RESULT:", result[:300])
except Exception as e:
    print(f"RPC ERROR: {e}")

try:
    result2 = send_rpc("0.0.0.0", 48846, "daemon.login", ["deluge"], "deluge")
    print("RPC VIA SOCAT:", result2[:300])
except Exception as e:
    print(f"RPC VIA SOCAT ERROR: {e}")
'''

b64 = __import__('base64').b64encode(rpc_test.encode()).decode()
result = run(f'lxc-attach -n 101 -- bash -c "echo {b64} | base64 -d | docker exec -i sonarr python3" 2>&1')
print("\n=== RPC TEST FROM SONARR ===")
print(result[:1000])

ssh.close()
