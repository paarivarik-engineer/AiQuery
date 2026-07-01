#!/usr/bin/env bash
# Quick connectivity test for AWS RDS PostgreSQL.
# Requires AWS_DB_* env vars or DATABASE_URL to be set.

set -euo pipefail

if [[ -n "${DATABASE_URL:-}" ]]; then
  exec psql "$DATABASE_URL" -c "SELECT version();"
fi

: "${AWS_DB_HOST:?Set AWS_DB_HOST or DATABASE_URL}"
: "${AWS_DB_NAME:?Set AWS_DB_NAME}"
: "${AWS_DB_USER:?Set AWS_DB_USER}"
: "${AWS_DB_PASSWORD:?Set AWS_DB_PASSWORD}"

export PGPASSWORD="$AWS_DB_PASSWORD"
PGSSLMODE="${AWS_DB_SSLMODE:-require}"

psql \
  "host=${AWS_DB_HOST} port=${AWS_DB_PORT:-5432} dbname=${AWS_DB_NAME} user=${AWS_DB_USER} sslmode=${PGSSLMODE}" \
  -c "SELECT version();"
