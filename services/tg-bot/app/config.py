import os

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])

SEARCH_API_URL = os.environ.get("SEARCH_API_URL", "http://search-api:8000")
WIKI_BASE_URL = os.environ.get("WIKI_BASE_URL", "http://172.24.120.131:8890")

DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_USER = os.environ.get("DB_USER", "coskb")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "coskb")

HEALTHCHECK_INTERVAL = int(os.environ.get("HEALTHCHECK_INTERVAL", "300"))
