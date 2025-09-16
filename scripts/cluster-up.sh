#!/usr/bin/env bash
set -euo pipefail
CLUSTER_NAME=${1:-stashmock}
REG_PORT=${2:-5001}

if k3d cluster list | grep -q "^${CLUSTER_NAME}\b"; then
  echo "Cluster ${CLUSTER_NAME} already exists. Skipping create."
  exit 0
fi

# Create cluster with an integrated registry (host port -> 0.0.0.0:REG_PORT)
k3d cluster create "${CLUSTER_NAME}" \
  --api-port 6550 \
  -p "8080:80@loadbalancer" \
  --agents 1 --servers 1 \
  --registry-create "stashmock-registry:0.0.0.0:${REG_PORT}"

echo "Cluster ${CLUSTER_NAME} is ready. Local registry available at localhost:${REG_PORT}"
