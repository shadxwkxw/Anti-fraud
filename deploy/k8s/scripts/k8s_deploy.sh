#!/usr/bin/env bash
set -euo pipefail

# Usage: k8s_deploy.sh <online_tag> <batch_tag> <airflow_tag>
# Environment variables required:
#   GHCR_USERNAME, GHCR_PASSWORD         — GHCR pull credentials
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#   MINIO_ROOT_USER, MINIO_ROOT_PASSWORD
#   AIRFLOW_FERNET_KEY, AIRFLOW_ADMIN_USERNAME, AIRFLOW_ADMIN_PASSWORD

ONLINE_TAG="${1:?Usage: k8s_deploy.sh <online_tag> <batch_tag> <airflow_tag>}"
BATCH_TAG="${2:?Missing batch_tag}"
AIRFLOW_TAG="${3:?Missing airflow_tag}"

NAMESPACE="antifraud-system"
REGISTRY="ghcr.io/shadxwkxw"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$SCRIPT_DIR/../base"

echo "=== Deploying Anti-fraud system ==="
echo "  online:  ${REGISTRY}/antifraud-online:${ONLINE_TAG}"
echo "  batch:   ${REGISTRY}/antifraud-batch:${BATCH_TAG}"
echo "  airflow: ${REGISTRY}/antifraud-airflow:${AIRFLOW_TAG}"

# 1. Ensure namespace exists
kubectl apply -f "${BASE_DIR}/namespace.yaml"

# 2. Create/update GHCR pull secret
kubectl create secret docker-registry ghcr-pull-secret \
  --namespace="${NAMESPACE}" \
  --docker-server=ghcr.io \
  --docker-username="${GHCR_USERNAME}" \
  --docker-password="${GHCR_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Create/update application secrets
kubectl create secret generic antifraud-secrets \
  --namespace="${NAMESPACE}" \
  --from-literal=POSTGRES_HOST="${POSTGRES_HOST}" \
  --from-literal=POSTGRES_PORT="${POSTGRES_PORT}" \
  --from-literal=POSTGRES_DB="${POSTGRES_DB}" \
  --from-literal=POSTGRES_USER="${POSTGRES_USER}" \
  --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
  --from-literal=AWS_ACCESS_KEY_ID="${MINIO_ROOT_USER}" \
  --from-literal=AWS_SECRET_ACCESS_KEY="${MINIO_ROOT_PASSWORD}" \
  --from-literal=MINIO_ROOT_USER="${MINIO_ROOT_USER}" \
  --from-literal=MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Create/update Airflow secrets
kubectl create secret generic airflow-secrets \
  --namespace="${NAMESPACE}" \
  --from-literal=AIRFLOW__CORE__FERNET_KEY="${AIRFLOW_FERNET_KEY}" \
  --from-literal=AIRFLOW_ADMIN_USERNAME="${AIRFLOW_ADMIN_USERNAME}" \
  --from-literal=AIRFLOW_ADMIN_PASSWORD="${AIRFLOW_ADMIN_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. Apply manifests with kustomize, overriding image tags
cd "${BASE_DIR}"
kustomize edit set image \
  "antifraud-online=${REGISTRY}/antifraud-online:${ONLINE_TAG}" \
  "antifraud-batch=${REGISTRY}/antifraud-batch:${BATCH_TAG}" \
  "antifraud-airflow=${REGISTRY}/antifraud-airflow:${AIRFLOW_TAG}"

kustomize build . | kubectl apply -f -

# 6. Wait for rollouts
echo "=== Waiting for MinIO ==="
kubectl rollout status deployment/minio -n "${NAMESPACE}" --timeout=120s

echo "=== Waiting for Airflow DB ==="
kubectl rollout status statefulset/airflow-db -n "${NAMESPACE}" --timeout=120s

echo "=== Waiting for Airflow Webserver ==="
kubectl rollout status deployment/airflow-webserver -n "${NAMESPACE}" --timeout=180s

echo "=== Waiting for Airflow Scheduler ==="
kubectl rollout status deployment/airflow-scheduler -n "${NAMESPACE}" --timeout=120s

echo "=== Waiting for Online Service ==="
kubectl rollout status deployment/antifraud-online -n "${NAMESPACE}" --timeout=120s

echo "=== Deployment complete ==="
kubectl get pods -n "${NAMESPACE}"
