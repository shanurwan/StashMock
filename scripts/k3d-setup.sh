#!/usr/bin/env bash
set -euo pipefail

CLUSTER=${1:-stashmock}

if ! command -v k3d >/dev/null; then
  echo "Please install k3d: https://k3d.io/"
  exit 1
fi

k3d cluster create "$CLUSTER" --agents 2 --wait || true

kubectl create namespace demo || true

# Install KEDA
kubectl apply -f https://github.com/kedacore/keda/releases/download/v2.14.0/keda-2.14.0.yaml

echo "Cluster '$CLUSTER' ready."
