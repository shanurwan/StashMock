#!/usr/bin/env bash
set -euo pipefail

NS=${1:-preview-$GITHUB_HEAD_REF}
kubectl delete namespace "$NS" --ignore-not-found
