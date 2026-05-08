#!/usr/bin/env python3
"""Test Deluge RPC from Sonarr with correct hostname."""
import sys
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode() + stderr.read().decode()

rpc_test = r'''
import socket, json, struct, zlib

def test_rpc(host, port, password="deluge"):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((host, port))
        print(f"TCP to {host}:{port} - OK")
        
        # Login request
        login_msg = json.dumps({
            "method": "daemon.login",
            "params": [password],
            "id": 1
        })
        
        compressed = zlib.compress(login_msg.encode())
        header = struct.pack("!i", len(compressed))
        s.sendall(header + compressed)
        
        # Read response
        resp_header = s.recv(4)
        if len(resp_header) < 4:
            return f"Incomplete header: {len(resp_header)}"
        resp_len = struct.unpack("!i", resp_header)[0]
        resp_data = b""
        while len(resp_data) < resp_len:
            chunk = s.recv(resp_len - len(resp_data))
            if not chunk:
                break
            resp_data += chunk
        
        decompressed = zlib.decompress(resp_data)
        s.close()
        return f"RPC OK: {decompressed.decode()[:200]}"
    except Exception as e:
        return f"ERROR: {e}"

# Test via socat proxy (deluge:48846)
print("=== VIA SOCAT (deluge:48846) ===")
print(test_rpc("deluge", 48846))

# Test directly (deluge:58846) - should fail since daemon is localhost-only
print("\n=== DIRECT DAEMON (deluge:58846) ===")
print(test_rpc("deluge", 58846))

# Test via Web API (deluge:8112)
print("\n=== WEB UI (deluge:8112) ===")
print(test_rpc("deluge", 8112))
'''

b64 = __import__('base64').b64encode(rpc_test.encode()).decode()
result = run(f'lxc-attach -n 101 -- bash -c "echo {b64} | base64 -d | docker exec -i sonarr python3" 2>&1')
print(result)

ssh.close()
