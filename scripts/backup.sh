#!/bin/bash
set -euo pipefail

DB_NAME="${DB_NAME:-vapt}"
DB_USER="${DB_USER:-vapt}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_PASSWORD="${DB_PASSWORD:-vapt-secret-password}"

BACKUP_DIR="${BACKUP_DIR:-/tmp/vapt-backups}"
S3_BUCKET="${S3_BUCKET:-vapt-backups}"
S3_ENDPOINT="${S3_ENDPOINT:-http://minio:9000}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-vapt-minio-access}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-vapt-minio-secret}"

RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/vapt_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

export PGPASSWORD="${DB_PASSWORD}"

echo "Starting backup of database ${DB_NAME}..."
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --no-owner --no-acl \
    | gzip > "${BACKUP_FILE}"

BACKUP_SIZE=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || echo 0)
echo "Backup completed: ${BACKUP_FILE} (${BACKUP_SIZE} bytes)"

echo "Uploading to S3-compatible storage at ${S3_ENDPOINT}..."
aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/" \
    --endpoint-url "${S3_ENDPOINT}" \
    --only-show-errors

echo "Upload completed."

echo "Rotating backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "vapt_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

aws s3 ls "s3://${S3_BUCKET}/" --endpoint-url "${S3_ENDPOINT}" \
    | while read -r line; do
        key=$(echo "$line" | awk '{print $4}')
        if [[ -n "$key" ]]; then
            date_str=$(echo "$key" | grep -oP '\d{8}_\d{6}')
            if [[ -n "$date_str" ]]; then
                file_ts=$(date -d "${date_str:0:8} ${date_str:9:2}:${date_str:11:2}:${date_str:13:2}" +%s 2>/dev/null || echo 0)
                cutoff=$(date -d "-${RETENTION_DAYS} days" +%s)
                if [[ "$file_ts" -lt "$cutoff" ]]; then
                    aws s3 rm "s3://${S3_BUCKET}/${key}" --endpoint-url "${S3_ENDPOINT}" --only-show-errors
                    echo "Removed old backup: ${key}"
                fi
            fi
        fi
    done

echo "Backup rotation completed."
echo "Backup process finished successfully."
