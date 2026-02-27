import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, filters, MessageHandler

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, HEALTHCHECK_INTERVAL
from app.handlers import start_handler, help_handler, search_handler, read_handler, similar_handler
from app.healthcheck import run_healthcheck

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("tg-bot")

chat_filter = filters.Chat(chat_id=TELEGRAM_CHAT_ID)


def main():
    logger.info("Starting Coskb Telegram Bot (chat_id=%d)", TELEGRAM_CHAT_ID)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler, filters=chat_filter))
    app.add_handler(CommandHandler("help", help_handler, filters=chat_filter))
    app.add_handler(CommandHandler("search", search_handler, filters=chat_filter))
    app.add_handler(CommandHandler("read", read_handler, filters=chat_filter))
    app.add_handler(CommandHandler("similar", similar_handler, filters=chat_filter))

    if HEALTHCHECK_INTERVAL > 0:
        app.job_queue.run_repeating(
            run_healthcheck,
            interval=HEALTHCHECK_INTERVAL,
            first=30,
        )
        logger.info("Healthcheck scheduled every %d seconds", HEALTHCHECK_INTERVAL)

    logger.info("Bot is polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
