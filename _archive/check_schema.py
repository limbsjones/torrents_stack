#!/usr/bin/env python3
"""Check what fields the *arr API expects for Deluge."""
import sys, json, base64
sys.path.insert(0, "/usr/lib/python3.14/site-packages")
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.0.0.252", username="root", password="vlpovcfq2477")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode()

# Check a working download client or the schema
print("=== SONARR: All download clients (verbose) ===")
# Get schema for Deluge implementation
result = run('lxc-attach -n 101 -- curl -s "http://localhost:8989/api/v3/downloadclient/schema" -H "X-Api-Key: f8fc219f6076435eb5ef6d0bc4093121" --max-time 10 2>&1')
try:
    schema = json.loads(result)
    for impl in schema:
        if 'Deluge' in impl.get('implementation', ''):
            print(f"\nImplementation: {impl['implementation']}")
            print(f"Config contract: {impl.get('configContract')}")
            print("Fields:")
            for f in impl.get('fields', []):
                print(f"  {f.get('name')} = {f.get('value')} (type: {f.get('type')}, order: {f.get('order')})")
except:
    print(f"Schema response (first 500): {result[:500]}")

# Also try to see if there are any fields I can inspect
print("\n=== TEST: Get actual field format from a known working schema ===")
# Check the actual field names by looking at the spec
result2 = run("lxc-attach -n 101 -- curl -s 'http://localhost:8989/api/v3/downloadclient' -H 'X-Api-Key: f8fc219f6076435eb5ef6d0bc4093121' --max-time 5 2>&1")
print(f"All clients: {result2[:500]}")

ssh.close()
