#!/usr/bin/env bash
set -euo pipefail

# Install Flux controllers into flux-system namespace
if ! kubectl get ns flux-system >/dev/null 2>&1; then
  kubectl create ns flux-system
fi

flux check --pre || true
flux install

# Create base namespaces
kubectl create ns platform --dry-run=client -o yaml | kubectl apply -f -
kubectl create ns monitoring --dry-run=client -o yaml | kubectl apply -f -
