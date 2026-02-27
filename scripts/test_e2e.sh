#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

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

if docker exec coskb-postgres pg_isready -U coskb -q 2>/dev/null; then
    check "pg_isready" 0
else
    check "pg_isready" 1
fi

row_count=$(docker exec coskb-postgres psql -U coskb -d coskb -tAc "SELECT COUNT(*) FROM pages WHERE \"isPublished\" = true" 2>/dev/null || echo "0")
row_count=$(echo "$row_count" | tr -d '[:space:]')
if [ "$row_count" -gt 0 ] 2>/dev/null; then
    check "Published pages exist ($row_count)" 0
else
    check "Published pages exist" 1
fi

embed_count=$(docker exec coskb-postgres psql -U coskb -d coskb -tAc "SELECT COUNT(*) FROM ai.embeddings" 2>/dev/null || echo "0")
embed_count=$(echo "$embed_count" | tr -d '[:space:]')
if [ "$embed_count" -gt 0 ] 2>/dev/null; then
    check "Embeddings indexed ($embed_count)" 0
else
    check "Embeddings indexed" 1
fi

echo ""

# --- 3. Wiki.js via Nginx ---
echo "3. Wiki.js via Nginx"

http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8890 2>/dev/null || echo "000")
if [ "$http_code" = "200" ] || [ "$http_code" = "302" ]; then
    check "Nginx → Wiki.js (HTTP $http_code)" 0
else
    check "Nginx → Wiki.js (HTTP $http_code)" 1
fi

echo ""

# --- 4. search-api ---
echo "4. search-api"

health=$(docker exec coskb-tg-bot curl -s --connect-timeout 5 http://search-api:8000/health 2>/dev/null || echo "{}")
if echo "$health" | grep -q '"status":"ok"'; then
    check "/health → ok" 0
else
    check "/health → $health" 1
fi

stats=$(docker exec coskb-tg-bot curl -s --connect-timeout 5 http://search-api:8000/stats 2>/dev/null || echo "{}")
if echo "$stats" | grep -q '"indexed_pages"'; then
    check "/stats responds" 0
else
    check "/stats responds" 1
fi

search_result=$(docker exec coskb-tg-bot curl -s --connect-timeout 10 "http://search-api:8000/search?q=vpn&mode=hybrid&top_k=3" 2>/dev/null || echo "{}")
if echo "$search_result" | grep -q '"results"'; then
    result_count=$(echo "$search_result" | grep -o '"page_id"' | wc -l)
    check "/search?q=vpn returns results ($result_count)" 0
else
    check "/search?q=vpn" 1
fi

search_fts=$(docker exec coskb-tg-bot curl -s --connect-timeout 10 "http://search-api:8000/search?q=vpn&mode=fts&top_k=3" 2>/dev/null || echo "{}")
if echo "$search_fts" | grep -q '"results"'; then
    check "/search mode=fts" 0
else
    check "/search mode=fts" 1
fi

search_vec=$(docker exec coskb-tg-bot curl -s --connect-timeout 10 "http://search-api:8000/search?q=vpn&mode=vector&top_k=3" 2>/dev/null || echo "{}")
if echo "$search_vec" | grep -q '"results"'; then
    check "/search mode=vector" 0
else
    check "/search mode=vector" 1
fi

echo ""

# --- 5. tg-bot ---
echo "5. tg-bot"

bot_log=$(docker compose logs tg-bot --tail 30 2>/dev/null || echo "")
if echo "$bot_log" | grep -q "Application started"; then
    check "Bot started" 0
else
    check "Bot started" 1
fi

if echo "$bot_log" | grep -q "Scheduler started"; then
    check "Healthcheck scheduler running" 0
else
    check "Healthcheck scheduler running" 1
fi

error_count=$(echo "$bot_log" | grep -ci "error\|traceback\|exception" || true)
if [ "$error_count" -eq 0 ]; then
    check "No errors in recent logs" 0
else
    check "No errors in recent logs ($error_count found)" 1
fi

echo ""

# --- 6. Telegram API connectivity ---
echo "6. Telegram API"

tg_code=$(docker exec coskb-tg-bot curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://api.telegram.org 2>/dev/null || echo "000")
if [ "$tg_code" = "200" ] || [ "$tg_code" = "302" ]; then
    check "Outbound to api.telegram.org (HTTP $tg_code)" 0
else
    check "Outbound to api.telegram.org (HTTP $tg_code)" 1
fi

echo ""

# --- Summary ---
echo "=== Results: $PASS/$TOTAL passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
