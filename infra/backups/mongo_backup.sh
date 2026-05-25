#!/usr/bin/env bash
# MongoDB backup script — requires mongodump in PATH
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups/mongo}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MONGO_URI="${MONGO_URI:?Set MONGO_URI}"

mkdir -p "$BACKUP_DIR"
OUT="$BACKUP_DIR/career_os_$TIMESTAMP"

echo "Backing up to $OUT"
mongodump --uri="$MONGO_URI" --out="$OUT"
tar -czf "${OUT}.tar.gz" -C "$BACKUP_DIR" "$(basename "$OUT")"
rm -rf "$OUT"
echo "Backup complete: ${OUT}.tar.gz"
