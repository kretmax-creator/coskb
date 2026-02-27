#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi
DB_USER="${POSTGRES_USER:-coskb}"
DB_NAME="${POSTGRES_DB:-coskb}"

PASS=0
FAIL=0
TOTAL=0

check() {
    local name="$1"
    local result="$2"
    TOTAL=$((TOTAL + 1))
    if [ "$result" -eq 0 ]; then
        PASS=$((PASS + 1))
        echo "  [PASS] $name"
    else
        FAIL=$((FAIL + 1))
        echo "  [FAIL] $name"
    fi
}

py_get() {
    local container="$1"
    local url="$2"
    docker exec "$container" python -c "
import urllib.request, sys
try:
    r = urllib.request.urlopen('$url', timeout=10)
    sys.stdout.write(r.read().decode())
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
" 2>/dev/null
}

py_http_code() {
    local container="$1"
    local url="$2"
    docker exec "$container" python -c "
import urllib.request, sys
try:
    r = urllib.request.urlopen('$url', timeout=5)
    print(r.getcode())
except urllib.error.HTTPError as e:
    print(e.code)
except Exception:
    print('000')
" 2>/dev/null
}

echo "=== Coskb E2E Tests ==="
echo ""

# --- 1. Containers ---
echo "1. Containers running"

for c in coskb-postgres coskb-wikijs coskb-nginx coskb-search-api coskb-tg-bot; do
    status=$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo "missing")
    if [ "$status" = "running" ]; then
        check "$c is running" 0
    else
        check "$c is running (status: $status)" 1
    fi
done

echo ""

# --- 2. PostgreSQL ---
echo "2. PostgreSQL"

if docker exec coskb-postgres pg_isready -U "$DB_USER" -q 2>/dev/null; then
    check "pg_isready" 0
else
    check "pg_isready" 1
fi

row_count=$(docker exec coskb-postgres psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT COUNT(*) FROM pages WHERE \"isPublished\" = true" 2>/dev/null | tr -cd '0-9')
if [ -n "$row_count" ] && [ "$row_count" -gt 0 ] 2>/dev/null; then
    check "Published pages exist ($row_count)" 0
else
    check "Published pages exist (${row_count:-0})" 1
fi

embed_count=$(docker exec coskb-postgres psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT COUNT(*) FROM ai.embeddings" 2>/dev/null | tr -cd '0-9')
if [ -n "$embed_count" ] && [ "$embed_count" -gt 0 ] 2>/dev/null; then
    check "Embeddings indexed ($embed_count)" 0
else
    check "Embeddings indexed (${embed_count:-0})" 1
fi

echo ""

# --- 3. Wiki.js via Nginx ---
echo "3. Wiki.js via Nginx"

http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8890 2>/dev/null || echo "000")
if [ "$http_code" = "200" ] || [ "$http_code" = "302" ]; then
    check "Nginx -> Wiki.js (HTTP $http_code)" 0
else
    check "Nginx -> Wiki.js (HTTP $http_code)" 1
fi

echo ""

# --- 4. search-api ---
echo "4. search-api"

health=$(py_get coskb-search-api http://localhost:8000/health || echo "{}")
if echo "$health" | grep -q '"status"'; then
    status_val=$(echo "$health" | grep -o '"status":"[^"]*"' | head -1)
    check "/health -> $status_val" 0
else
    check "/health" 1
fi

stats=$(py_get coskb-search-api http://localhost:8000/stats || echo "{}")
if echo "$stats" | grep -q '"indexed_pages"'; then
    check "/stats responds" 0
else
    check "/stats responds" 1
fi

search_result=$(py_get coskb-search-api "http://localhost:8000/search?q=vpn&mode=hybrid&top_k=3" || echo "{}")
if echo "$search_result" | grep -q '"results"'; then
    result_count=$(echo "$search_result" | grep -o '"page_id"' | wc -l | tr -cd '0-9')
    check "/search?q=vpn hybrid ($result_count results)" 0
else
    check "/search?q=vpn hybrid" 1
fi

search_fts=$(py_get coskb-search-api "http://localhost:8000/search?q=vpn&mode=fts&top_k=3" || echo "{}")
if echo "$search_fts" | grep -q '"results"'; then
    check "/search mode=fts" 0
else
    check "/search mode=fts" 1
fi

search_vec=$(py_get coskb-search-api "http://localhost:8000/search?q=vpn&mode=vector&top_k=3" || echo "{}")
if echo "$search_vec" | grep -q '"results"'; then
    check "/search mode=vector" 0
else
    check "/search mode=vector" 1
fi

echo ""

# --- 5. tg-bot ---
echo "5. tg-bot"

bot_log_file=$(mktemp)
docker logs coskb-tg-bot >"$bot_log_file" 2>&1 || true

if grep -q "Application started" "$bot_log_file"; then
    check "Bot started" 0
else
    check "Bot started" 1
fi

if grep -q "Scheduler started" "$bot_log_file"; then
    check "Healthcheck scheduler running" 0
else
    check "Healthcheck scheduler running" 1
fi

error_count=$(tail -50 "$bot_log_file" | grep -ci "traceback\|attributeerror\|runtimeerror\|importerror" || true)
if [ "$error_count" -eq 0 ]; then
    check "No errors in recent logs" 0
else
    check "No errors in recent logs ($error_count found)" 1
fi

rm -f "$bot_log_file"

echo ""

# --- 6. Telegram API connectivity ---
echo "6. Telegram API"

tg_code=$(py_http_code coskb-tg-bot https://api.telegram.org || echo "000")
tg_code=$(echo "$tg_code" | tr -cd '0-9')
if [ "$tg_code" = "200" ] || [ "$tg_code" = "302" ]; then
    check "Outbound to api.telegram.org (HTTP $tg_code)" 0
else
    check "Outbound to api.telegram.org (HTTP ${tg_code:-000})" 1
fi

echo ""

# --- Summary ---
echo "=== Results: $PASS/$TOTAL passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
