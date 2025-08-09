#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="$ROOT_DIR/benchmarks"
mkdir -p "$BENCH_DIR"

# Ensure Node/npm (for npx autocannon)
if ! command -v npx >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y && sudo apt-get install -y nodejs npm
  else
    echo "npm/npx not found and no apt-get; please install Node.js." >&2
    exit 1
  fi
fi

# Seed a portfolio (id=1), ignore if already exists
seed() {
  curl -s -X POST localhost:8001/portfolios \
    -H 'content-type: application/json' -d '{"owner_name":"Alya"}' >/dev/null || true
}

run_autocannon() {
  local outfile="$1"
  npx autocannon -c 20 -d 20 \
    -m POST \
    -H "Content-Type: application/json" \
    -b '{"portfolio_id":1,"amount":1,"type":"deposit"}' \
    --json \
    http://localhost:8001/transactions > "$outfile"
}

extract_p95() {
  python - "$1" <<'PY'
import json,sys
data=json.load(open(sys.argv[1]))
# autocannon JSON has latency percentiles under 'latency'
lat=data.get("latency") or {}
p95=lat.get("p95")
print(p95 if p95 is not None else "NaN")
PY
}

echo "== Starting services in SYNC (baseline) mode =="
"$ROOT_DIR/scripts/dev.sh" start sync
sleep 2
seed
run_autocannon "$BENCH_DIR/baseline.json"

echo "== Restarting portfolio in OFFLOAD mode =="
"$ROOT_DIR/scripts/dev.sh" restart_portfolio offload
sleep 2
run_autocannon "$BENCH_DIR/offloaded.json"

B_P95="$(extract_p95 "$BENCH_DIR/baseline.json")"
O_P95="$(extract_p95 "$BENCH_DIR/offloaded.json")"

python - <<PY
b=float("$B_P95")
o=float("$O_P95")
impr=(b-o)/b*100.0
print("\\nRESULTS")
print("--------")
print(f"Baseline p95:   {b:.2f} ms")
print(f"Offloaded p95:  {o:.2f} ms")
print(f"Improvement:    {impr:.1f}%")
PY
