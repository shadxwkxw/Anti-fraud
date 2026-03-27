#!/bin/bash
set -euo pipefail

if [ "${AIRFLOW_DB_USER}" = "${POSTGRES_USER}" ] && [ "${AIRFLOW_DB_NAME}" = "${POSTGRES_DB}" ]; then
  exit 0
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<EOSQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${AIRFLOW_DB_USER}') THEN
        EXECUTE format(
            'CREATE ROLE %I LOGIN PASSWORD %L',
            '${AIRFLOW_DB_USER}',
            '${AIRFLOW_DB_PASSWORD}'
        );
    END IF;
END
\$\$;

SELECT format('CREATE DATABASE %I OWNER %I', '${AIRFLOW_DB_NAME}', '${AIRFLOW_DB_USER}')
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = '${AIRFLOW_DB_NAME}'
)\gexec
EOSQL
