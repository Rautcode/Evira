#!/usr/bin/env bash
# Quick liveness check for all four Evira services.
# Returns exit code 0 (all healthy) or 1 (at least one failed).
# Suitable as a cron watchdog or pre-deploy gate.
#
# Usage:
#   bash scripts/healthcheck.sh
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
FRONTEND_BASE="${FRONTEND_BASE:-http://localhost:3000}"
OPCUA_HOST="${OPCUA_HOST:-localhost}"
OPCUA_PORT="${OPCUA_PORT:-4840}"

FAILED=0

check_http() {
  local name="$1" url="$2" expect="${3:-200}"
  local code
  code=$(curl -sk -o /dev/null -w "%{http_code}" "$url" || echo "000")
  if [[ "$code" == "$expect" ]]; then
    echo "  OK   $name ($url) → $code"
  else
    echo "  FAIL $name ($url) → $code (expected $expect)"
    FAILED=1
  fi
}

check_tcp() {
  local name="$1" host="$2" port="$3"
  if timeout 3 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null; then
    echo "  OK   $name ($host:$port)"
  else
    echo "  FAIL $name ($host:$port) — TCP connect failed"
    FAILED=1
  fi
}

echo "=== Evira Health Check — $(date -u +"%Y-%m-%dT%H:%M:%SZ") ==="

check_http "Backend /health"    "$API_BASE/health"
check_http "Backend /docs"      "$API_BASE/docs"
check_http "Frontend"           "$FRONTEND_BASE"
check_tcp  "OPC UA Simulator"   "$OPCUA_HOST" "$OPCUA_PORT"

if [[ $FAILED -eq 0 ]]; then
  echo "=== ALL HEALTHY ==="
else
  echo "=== DEGRADED — $FAILED check(s) failed ==="
fi

exit $FAILED
