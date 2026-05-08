#!/bin/bash
# =============================================================
# ArrStack Health Monitor — Surveillance des services
# =============================================================
# Vérifie l'état de chaque service et envoie un email si
# un service est injoignable.
# Compatible avec le système d'email du backup script.
# =============================================================

set -euo pipefail

# === Configuration ===
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PARENT_DIR}/backups"
LOG_FILE="${BACKUP_DIR}/health_monitor.log"
STATE_FILE="${BACKUP_DIR}/.health_state"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
FROM_EMAIL="martin.langlois@gmail.com"
TO_EMAIL="martin.langlois@gmail.com"

# Créer les répertoires si nécessaire
mkdir -p "$BACKUP_DIR"

# === Liste des services à vérifier (nom, URL, port) ===
SERVICES=(
    "Sonarr:http://localhost:8989"
    "Radarr:http://localhost:7878"
    "Prowlarr:http://localhost:9696"
    "Lidarr:http://localhost:8686"
    "Bazarr:http://localhost:6767"
    "Deluge:http://localhost:8112"
    "Heimdall:http://localhost:80"
)

log() {
    echo "[$TIMESTAMP] $*" | tee -a "$LOG_FILE"
}

check_service() {
    local name="$1"
    local url="$2"
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url" 2>/dev/null || echo "000")
    
    if [[ "$http_code" == "000" ]]; then
        echo "$name:❌ DOWN (connection refused/timeout)"
        return 1
    elif [[ "$http_code" =~ ^[2-3] ]]; then
        echo "$name:✅ OK (HTTP $http_code)"
        return 0
    else
        echo "$name:⚠️  WARN (HTTP $http_code)"
        return 2
    fi
}

# === Vérification ===
log "🔍 Démarrage de la vérification de santé..."
DOWN_COUNT=0
RESULTS=()

for svc in "${SERVICES[@]}"; do
    IFS=":" read -r name url <<< "$svc"
    result=$(check_service "$name" "$url" 2>&1) || true
    RESULTS+=("$result")
    if echo "$result" | grep -q "❌\|⚠️ "; then
        DOWN_COUNT=$((DOWN_COUNT + 1))
    fi
    log "$result"
done

# === État précédent ===
PREV_DOWN=0
[[ -f "$STATE_FILE" ]] && PREV_DOWN=$(cat "$STATE_FILE")
echo "$DOWN_COUNT" > "$STATE_FILE"

log "📊 Services en panne: $DOWN_COUNT (précédent: $PREV_DOWN)"

# === Envoi d'email si changement d'état ===
if [[ "$DOWN_COUNT" -ne "$PREV_DOWN" ]] || [[ "$DOWN_COUNT" -gt 0 ]]; then
    
    if [[ "$DOWN_COUNT" -eq 0 ]]; then
        SUBJECT="✅ ArrStack — Tous les services sont rétablis !"
        STATUS_HEADER="✅ Tous les services sont de nouveau en ligne."
    else
        SUBJECT="⚠️ ArrStack — $DOWN_COUNT service(s) indisponible(s)"
        STATUS_HEADER="⚠️ $DOWN_COUNT service(s) en panne !"
    fi
    
    # Construire le corps HTML
    HTML='<h2>🔍 Rapport de santé ArrStack</h2>'
    HTML+="<p><em>$TIMESTAMP</em></p>"
    HTML+='<table border="0" cellpadding="6" style="font-family:monospace;width:100%;">'
    HTML+='<tr style="background:#f0f0f0;"><th>Service</th><th>Statut</th></tr>'
    
    for result in "${RESULTS[@]}"; do
        name="${result%%:*}"
        status="${result#*:}"
        if echo "$status" | grep -q "✅"; then
            HTML+="<tr style=\"background:#e8f5e9;\"><td>$name</td><td>$status</td></tr>"
        else
            HTML+="<tr style=\"background:#ffebee;\"><td>$name</td><td>$status</td></tr>"
        fi
    done
    
    HTML+='</table>'
    
    if [[ "$DOWN_COUNT" -eq 0 ]]; then
        HTML+='<p style="color:green;">✅ Tous les services sont en ligne !</p>'
    else
        HTML+='<p style="color:red;">⚠️ Un ou plusieurs services sont indisponibles !</p>'
        HTML+='<p>Vérifiez avec : <code>docker ps</code> sur CT101</p>'
    fi
    
    # Envoyer l'email via python (sendmail pas toujours disponible)
    python3 -c "
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os, sys

msg = MIMEMultipart('alternative')
msg['Subject'] = '$SUBJECT'
msg['From'] = '$FROM_EMAIL'
msg['To'] = '$TO_EMAIL'
msg.attach(MIMEText('''$HTML''', 'html', 'utf-8'))

# Utilisation de Sendmail local (disponible dans le conteneur ou via msmtp)
try:
    s = smtplib.SMTP('localhost', 25)
    s.send_message(msg)
    s.quit()
    print('Email sent via local SMTP')
except Exception as e:
    print(f'Local SMTP failed: {e}')
    # Fallback: save to file
    with open('${BACKUP_DIR}/last_alert.html', 'w') as f:
        f.write('''$HTML''')
    print('Alert saved to file')
" 2>&1 | while read line; do log "$line"; done
    
fi

log "✅ Vérification terminée."
