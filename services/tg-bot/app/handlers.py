import logging

import httpx
import psycopg2
from telegram import Update
from telegram.ext import ContextTypes

from app.config import (
    SEARCH_API_URL, WIKI_BASE_URL,
    DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME,
)

logger = logging.getLogger("tg-bot.handlers")

MAX_MESSAGE_LENGTH = 4096


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Coskb Bot — поиск по базе знаний.\n\n"
        "Команды:\n"
        "/search <запрос> — поиск статей\n"
        "/read <заголовок> — полный текст статьи\n"
        "/similar <заголовок> — похожие статьи\n"
        "/help — справка",
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>Доступные команды:</b>\n\n"
        "/search &lt;запрос&gt; — гибридный поиск по базе знаний (top-3)\n"
        "/read &lt;заголовок&gt; — полный текст статьи\n"
        "/similar &lt;заголовок&gt; — похожие статьи\n"
        "/help — эта справка",
        parse_mode="HTML",
    )


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Использование: /search <запрос>")
        return

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{SEARCH_API_URL}/search",
                params={"q": query, "mode": "hybrid", "top_k": 3},
            )
            resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.exception("search-api request failed")
        await update.message.reply_text("Ошибка при обращении к search-api.")
        return

    results = data.get("results", [])
    if not results:
        await update.message.reply_text("Ничего не найдено.")
        return

    lines = []
    for r in results:
        url = f"{WIKI_BASE_URL}/{r['path']}" if r.get("path") else ""
        snippet = (r.get("snippet") or "")[:200]
        line = f"• <b>{_escape_html(r['title'])}</b> ({r['score']})\n{_escape_html(snippet)}"
        if url:
            line += f"\n{url}"
        lines.append(line)

    text = "\n\n".join(lines)
    await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)


async def read_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = " ".join(context.args) if context.args else ""
    if not title:
        await update.message.reply_text("Использование: /read <заголовок статьи>")
        return

    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASS, dbname=DB_NAME,
        )
        cur = conn.cursor()
        cur.execute(
            'SELECT title, content FROM pages WHERE "isPublished" = true AND title ILIKE %s LIMIT 1',
            (f"%{title}%",),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
    except Exception:
        logger.exception("Database query failed")
        await update.message.reply_text("Ошибка при обращении к базе данных.")
        return

    if not row:
        await update.message.reply_text(f"Статья «{title}» не найдена.")
        return

    page_title, content = row
    content = _strip_html(content or "")
    header = f"<b>{_escape_html(page_title)}</b>\n\n"

    chunks = _split_text(header + content, MAX_MESSAGE_LENGTH)
    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="HTML", disable_web_page_preview=True)


async def similar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = " ".join(context.args) if context.args else ""
    if not title:
        await update.message.reply_text("Использование: /similar <заголовок статьи>")
        return

    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASS, dbname=DB_NAME,
        )
        cur = conn.cursor()
        cur.execute(
            'SELECT id, title FROM pages WHERE "isPublished" = true AND title ILIKE %s LIMIT 1',
            (f"%{title}%",),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
    except Exception:
        logger.exception("Database query failed")
        await update.message.reply_text("Ошибка при обращении к базе данных.")
        return

    if not row:
        await update.message.reply_text(f"Статья «{title}» не найдена.")
        return

    page_id, page_title = row

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{SEARCH_API_URL}/similar",
                params={"page_id": page_id, "top_k": 5},
            )
            resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.exception("search-api /similar request failed")
        await update.message.reply_text("Ошибка при обращении к search-api.")
        return

    items = data.get("similar", [])
    if not items:
        await update.message.reply_text(f"Похожих статей для «{page_title}» не найдено.")
        return

    lines = [f"Похожие на <b>{_escape_html(page_title)}</b>:\n"]
    for r in items:
        url = f"{WIKI_BASE_URL}/{r['path']}" if r.get("path") else ""
        line = f"• <b>{_escape_html(r['title'])}</b> ({r['score']})"
        if url:
            line += f"\n  {url}"
        lines.append(line)

    await update.message.reply_text("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _strip_html(text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", text)


def _split_text(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_pos = text.rfind("\n", 0, limit)
        if split_pos == -1:
            split_pos = limit
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n")
    return chunks
