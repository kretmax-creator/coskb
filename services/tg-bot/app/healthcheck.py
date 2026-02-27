import logging

import httpx
import psycopg2
from telegram.ext import ContextTypes

from app.config import (
    TELEGRAM_CHAT_ID,
    DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME,
)

logger = logging.getLogger("tg-bot.healthcheck")


async def run_healthcheck(context: ContextTypes.DEFAULT_TYPE):
    issues: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://wikijs:3000")
            if r.status_code >= 500:
                issues.append(f"Wiki.js вернул HTTP {r.status_code}")
    except Exception:
        issues.append("Wiki.js недоступен")

    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASS, dbname=DB_NAME,
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
    except Exception:
        issues.append("PostgreSQL недоступен")

    if issues:
        text = "⚠️ Healthcheck — проблемы:\n" + "\n".join(f"• {i}" for i in issues)
        logger.warning("Healthcheck issues: %s", issues)
        await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
    else:
        logger.info("Healthcheck OK")
