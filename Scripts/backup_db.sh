#!/usr/bin/env bash
# Backup the Evira SQL Server database to a dated .bak file.
#
# Usage (run from the project root):
#   bash scripts/backup_db.sh
#
# Environment variables (override via .env or shell export):
#   MSSQL_SERVER    — host[:port] of SQL Server  (default: localhost,14333)
#   MSSQL_DATABASE  — database name              (default: scada_reports)
#   MSSQL_USERNAME  — SQL login                  (default: sa)
#   MSSQL_PASSWORD  — SQL password               (required; no default)
#   BACKUP_DIR      — host directory for backups  (default: ./backups)
#
# Cron example (daily at 02:00):
#   0 2 * * * cd /opt/evira && bash scripts/backup_db.sh >> logs/backup.log 2>&1
set -euo pipefail

SERVER="${MSSQL_SERVER:-localhost,14333}"
DATABASE="${MSSQL_DATABASE:-scada_reports}"
USERNAME="${MSSQL_USERNAME:-sa}"
PASSWORD="${MSSQL_PASSWORD:?MSSQL_PASSWORD must be set}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETAIN_DAYS="${RETAIN_DAYS:-30}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${DATABASE}_${TIMESTAMP}.bak"

mkdir -p "$BACKUP_DIR"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting backup of ${DATABASE} on ${SERVER}"

# sqlcmd must be on PATH (mssql-tools or mssql-tools18 on Linux)
SQLCMD=$(command -v sqlcmd 2>/dev/null || command -v /opt/mssql-tools18/bin/sqlcmd 2>/dev/null || true)
if [[ -z "$SQLCMD" ]]; then
  echo "ERROR: sqlcmd not found on PATH. Install mssql-tools or mssql-tools18." >&2
  exit 1
fi

"$SQLCMD" -S "$SERVER" -U "$USERNAME" -P "$PASSWORD" -C -No -Q \
  "BACKUP DATABASE [$DATABASE] TO DISK = N'/var/opt/mssql/backup/${BACKUP_FILE}' WITH COMPRESSION, STATS = 10"

# Copy the .bak out of the container (assumes the service is named 'db')
if command -v docker &>/dev/null && docker ps --filter "name=evira-db" --format "{{.Names}}" | grep -q evira-db; then
  docker cp "evira-db:/var/opt/mssql/backup/${BACKUP_FILE}" "${BACKUP_DIR}/${BACKUP_FILE}"
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Backup copied to ${BACKUP_DIR}/${BACKUP_FILE}"
else
  echo "WARNING: evira-db container not found; .bak is inside the container only."
fi

# Prune old backups beyond RETAIN_DAYS
find "$BACKUP_DIR" -name "${DATABASE}_*.bak" -mtime +"$RETAIN_DAYS" -delete && \
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Old backups pruned (>${RETAIN_DAYS}d)"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Backup complete."
