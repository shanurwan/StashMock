#!/usr/bin/env bash
set -euo pipefail
CLUSTER_NAME=${1:-stashmock}

if k3d cluster list | grep -q "^${CLUSTER_NAME}\b"; then
  k3d cluster delete "${CLUSTER_NAME}"
else
  echo "Cluster ${CLUSTER_NAME} not found."
fi
