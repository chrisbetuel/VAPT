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

RESTORE_FILE="${1:-}"

usage() {
    echo "Usage: $0 [backup_file]"
    echo ""
    echo "If backup_file is not provided, the latest backup from S3 will be restored."
    exit 1
}

export PGPASSWORD="${DB_PASSWORD}"

if [[ -z "${RESTORE_FILE}" ]]; then
    echo "No backup file specified. Fetching latest backup from S3..."

    LATEST=$(aws s3 ls "s3://${S3_BUCKET}/" --endpoint-url "${S3_ENDPOINT}" \
        | sort -t_ -k2 -r \
        | head -1 \
        | awk '{print $4}')

    if [[ -z "${LATEST}" ]]; then
        echo "Error: No backups found in S3 bucket ${S3_BUCKET}"
        exit 1
    fi

    echo "Latest backup found: ${LATEST}"

    mkdir -p "${BACKUP_DIR}"
    RESTORE_FILE="${BACKUP_DIR}/${LATEST}"

    aws s3 cp "s3://${S3_BUCKET}/${LATEST}" "${RESTORE_FILE}" \
        --endpoint-url "${S3_ENDPOINT}" \
        --only-show-errors

    echo "Downloaded backup to ${RESTORE_FILE}"
fi

if [[ ! -f "${RESTORE_FILE}" ]]; then
    echo "Error: Backup file not found: ${RESTORE_FILE}"
    usage
fi

echo "WARNING: This will overwrite the current database '${DB_NAME}'!"
read -p "Are you sure you want to proceed? [y/N]: " CONFIRM

if [[ "${CONFIRM}" != "y" && "${CONFIRM}" != "Y" ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo "Starting restore of ${DB_NAME} from ${RESTORE_FILE}..."

TERMINATE_SQL="SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();"
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "${TERMINATE_SQL}" 2>/dev/null || true

psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
    -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true

psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
    -c "CREATE DATABASE ${DB_NAME};"

gunzip -c "${RESTORE_FILE}" \
    | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}"

echo "Restore completed successfully from: ${RESTORE_FILE}"
