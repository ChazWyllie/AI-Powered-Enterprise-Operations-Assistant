#!/usr/bin/env bash
# Production smoke test for AI Enterprise Operations Assistant.
# Usage: ./scripts/smoke-test.sh [BASE_URL]
#
# Defaults to http://localhost:8000 if no argument provided.

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0

green() { printf "\033[32m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*"; }
bold()  { printf "\033[1m%s\033[0m\n" "$*"; }

check() {
  local desc="$1" expected_status="$2" actual_status="$3"
  if [ "$actual_status" -eq "$expected_status" ]; then
    green "  ✓ $desc (HTTP $actual_status)"
    PASS=$((PASS + 1))
  else
    red "  ✗ $desc (expected $expected_status, got $actual_status)"
    FAIL=$((FAIL + 1))
  fi
}

bold "Smoke Testing: $BASE_URL"
echo "================================================"

# 1. Health check
bold "1. GET /health"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
check "Health endpoint returns 200" 200 "$STATUS"

# 2. Chat — plan_only
bold "2. POST /chat (plan_only)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "show system status", "mode": "plan_only"}')
check "Chat plan_only returns 200" 200 "$STATUS"

# 3. Chat response structure
bold "3. Response structure validation"
BODY=$(curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "check logs", "mode": "plan_only"}')

# Check required fields exist
for field in answer plan actions_taken audit; do
  if echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert '$field' in d" 2>/dev/null; then
    green "  ✓ Response contains '$field'"
    PASS=$((PASS + 1))
  else
    red "  ✗ Response missing '$field'"
    FAIL=$((FAIL + 1))
  fi
done

# 4. Invalid request
bold "4. POST /chat (invalid mode → 422)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "mode": "invalid"}')
check "Invalid mode returns 422" 422 "$STATUS"

# 5. Empty message
bold "5. POST /chat (empty message → 422)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "", "mode": "plan_only"}')
check "Empty message returns 422" 422 "$STATUS"

echo ""
echo "================================================"
bold "Results: $PASS passed, $FAIL failed"

if [ "$FAIL" -gt 0 ]; then
  red "SMOKE TEST FAILED"
  exit 1
else
  green "SMOKE TEST PASSED"
  exit 0
fi
