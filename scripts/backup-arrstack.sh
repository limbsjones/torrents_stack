#!/bin/bash
# =============================================================
# ArrStack — Backup des configurations
# =============================================================
# Sauvegarde toutes les configs des services *arr dans
# /opt/arrstack/backups/ et nettoie les backups de +7 jours.
#
# Usage: ./backup-arrstack.sh                    # backup local
#        ./backup-arrstack.sh --to /mnt/backups  # backup ailleurs
#        ./backup-arrstack.sh --restore backups/arrstack-2026-05-08.tar.gz
# =============================================================
set -euo pipefail

BACKUP_DIR="${2:-/opt/arrstack/backups}"
SRC_DIR="/opt/arrstack"
RETENTION_DAYS=14
DATE_STAMP=$(date +%Y-%m-%d_%H%M%S)
BACKUP_FILE="arrstack-configs-${DATE_STAMP}.tar.gz"

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1"; }

usage() {
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo "  --to DIR     Répertoire de destination (défaut: /opt/arrstack/backups)"
    echo "  --restore FICHIER  Restaurer depuis un fichier de backup"
    echo "  --help       Affiche cette aide"
    exit 0
}

restore_backup() {
    local FILE="$1"
    if [ ! -f "$FILE" ]; then
        err "Fichier de backup introuvable : $FILE"
        exit 1
    fi
    warn "Restauration depuis : $FILE"
    warn "Les configurations actuelles seront écrasées !"
    echo "Appuyez sur Ctrl+C dans 5s pour annuler..."
    sleep 5

    info "Extraction de $FILE vers $SRC_DIR..."
    tar -xzf "$FILE" -C "$SRC_DIR"
    info "Restauration terminée ! Redémarrez les conteneurs : docker compose restart"
    exit 0
}

# Parse arguments
case "${1:-}" in
    --to) shift 2;;
    --restore) restore_backup "$2";;
    --help|-h) usage;;
esac

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Build list of directories to backup
DIRS=()
for service in sonarr radarr lidarr prowlarr bazarr deluge heimdall npm; do
    if [ -d "$SRC_DIR/$service/config" ]; then
        DIRS+=("$service/config")
        info "Ajout : $service/config"
    elif [ "$service" = "npm" ] && [ -d "$SRC_DIR/npm/data" ]; then
        DIRS+=("npm/data")
        info "Ajout : npm/data"
    fi
done

# Backup compose.yaml and .env too
if [ -f "$SRC_DIR/compose.yaml" ]; then
    cp "$SRC_DIR/compose.yaml" /tmp/arrstack-compose-backup.yaml
    info "Ajout : compose.yaml"
fi
if [ -f "$SRC_DIR/.env" ]; then
    cp "$SRC_DIR/.env" /tmp/arrstack-env-backup
    info "Ajout : .env"
fi

# Create archive
cd "$SRC_DIR"
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    "${DIRS[@]}" \
    /tmp/arrstack-compose-backup.yaml 2>/dev/null || true
cd /tmp
tar -czf "$BACKUP_DIR/$BACKUP_FILE" arrstack-compose-backup.yaml arrstack-env-backup 2>/dev/null || true
rm -f /tmp/arrstack-compose-backup.yaml /tmp/arrstack-env-backup

# Combine into single archive if we had separate files
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    info "Backup créé : $BACKUP_DIR/$BACKUP_FILE"
else
    # Re-do as one archive
    cd "$SRC_DIR"
    tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
        sonarr/config radarr/config lidarr/config prowlarr/config \
        bazarr/config deluge/config heimdall/config \
        npm/data npm/letsencrypt \
        compose.yaml .env 2>/dev/null && \
    info "Backup créé : $BACKUP_DIR/$BACKUP_FILE" || \
    err "Échec de la création du backup"
fi

# Show size
SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
info "Taille : $SIZE"

# Cleanup old backups
OLD=$(find "$BACKUP_DIR" -name "arrstack-configs-*.tar.gz" -mtime +$RETENTION_DAYS -type f)
if [ -n "$OLD" ]; then
    echo "$OLD" | while read -r f; do
        rm -f "$f"
        warn "Supprimé (ancien) : $(basename "$f")"
    done
fi

# Summary
COUNT=$(find "$BACKUP_DIR" -name "arrstack-configs-*.tar.gz" -type f | wc -l)
info "Backups disponibles : $COUNT (rétention ${RETENTION_DAYS} jours)"
info "Terminé !"
