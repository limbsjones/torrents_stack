#!/usr/bin/env python3
"""ArrStack Health Monitor — Surveillance des services avec email"""

import os, sys, json, time
import urllib.request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# === Configuration ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
BACKUP_DIR = os.path.join(PARENT_DIR, "backups")
STATE_FILE = os.path.join(BACKUP_DIR, ".health_state")
LOG_FILE = os.path.join(BACKUP_DIR, "health_monitor.log")
os.makedirs(BACKUP_DIR, exist_ok=True)
GMAIL_USER = "martin.langlois@gmail.com"

# Try to find Gmail credentials (tried on local machine, ~/.hermes, CT101 files)
GMAIL_APP_PASSWORD = ""
cred_paths = [
    os.path.expanduser("~/.hermes/scripts/send_email_summary.py"),
    os.path.join(SCRIPT_DIR, ".gmail_creds.py"),
    os.path.join(os.path.expanduser("~"), ".gmail_creds.py"),
]
for cp in cred_paths:
    if os.path.exists(cp):
        import re
        with open(cp) as f:
            content = f.read()
        m = re.search(r'GMAIL_APP_PASSWORD\s*=\s*"([^"]+)"', content)
        if m:
            GMAIL_APP_PASSWORD = m.group(1)
            break
FROM_EMAIL = GMAIL_USER
TO_EMAIL = GMAIL_USER

SERVICES = [
    ("Sonarr", "http://localhost:8989"),
    ("Radarr", "http://localhost:7878"),
    ("Prowlarr", "http://localhost:9696"),
    ("Lidarr", "http://localhost:8686"),
    ("Bazarr", "http://localhost:6767"),
    ("Deluge", "http://localhost:8112"),
    ("Heimdall", "http://localhost:80"),
]

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def check_service(name, url):
    """Check if a service responds. Returns (name, status_emoji, http_code)."""
    req = urllib.request.Request(url, method="GET")
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        code = resp.getcode()
        if 200 <= code < 400:
            return (name, "✅", str(code))
        else:
            return (name, "⚠️", str(code))
    except urllib.error.URLError as e:
        return (name, "❌", f"Connection failed: {str(e)[:50]}")
    except Exception as e:
        return (name, "❌", str(e)[:50])

def send_email(subject, html_body):
    """Send email via Gmail SMTP."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        log("✅ Email sent successfully")
        return True
    except Exception as e:
        log(f"❌ Failed to send email: {e}")
        # Save to file as fallback
        fallback_path = os.path.join(BACKUP_DIR, "last_alert.html")
        with open(fallback_path, "w") as f:
            f.write(html_body)
        log(f"💾 Alert saved to {fallback_path}")
        return False

def build_html(results, all_ok):
    """Build HTML email body."""
    now = datetime.now()
    date_str = now.strftime("%A %d %B %Y")
    time_str = now.strftime("%H:%M:%S")
    
    html = f"""<html><body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>🔍 Rapport de santé ArrStack</h2>
<p><em>{date_str} à {time_str}</em></p>
<table border="0" cellpadding="8" style="font-family:monospace;width:100%;border-collapse:collapse;">
<tr style="background:#f0f0f0;"><th style="text-align:left;">Service</th><th style="text-align:left;">Statut</th></tr>
"""
    for name, emoji, detail in results:
        color = "#e8f5e9" if "✅" in emoji else "#ffebee"
        html += f'<tr style="background:{color};"><td>{name}</td><td>{emoji} {detail}</td></tr>\n'
    
    html += "</table>\n"
    
    if all_ok:
        html += '<p style="color:green;font-weight:bold;">✅ Tous les services sont en ligne !</p>'
    else:
        html += '<p style="color:red;font-weight:bold;">⚠️ Un ou plusieurs services sont indisponibles !</p>'
        html += '<p>Vérifiez : <code>docker ps</code> sur CT101</p>'
    
    html += '<hr><p style="color:#888;font-size:small;">ArrStack Health Monitor</p>'
    html += "</body></html>"
    return html

def main():
    log("🔍 Démarrage de la vérification de santé...")
    
    results = []
    down_count = 0
    
    for name, url in SERVICES:
        try:
            result = check_service(name, url)
            results.append(result)
            _, status, detail = result
            log(f"  {status} {name}: {detail}")
            if status in ("❌", "⚠️"):
                down_count += 1
        except Exception as e:
            results.append((name, "❌", str(e)[:50]))
            down_count += 1
    
    # Load previous state
    prev_down = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                prev_down = int(f.read().strip())
        except:
            pass
    
    with open(STATE_FILE, "w") as f:
        f.write(str(down_count))
    
    all_ok = (down_count == 0)
    
    # Send email if there's a change or if services are down
    if down_count != prev_down or not all_ok:
        if all_ok:
            subject = "✅ ArrStack — Tous les services rétablis !"
        else:
            subject = f"⚠️ ArrStack — {down_count} service(s) indisponible(s)"
        
        html = build_html(results, all_ok)
        send_email(subject, html)
    
    log(f"✅ Vérification terminée. Services en panne: {down_count}")
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
