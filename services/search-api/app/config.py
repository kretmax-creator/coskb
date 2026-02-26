import os

DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_USER = os.environ.get("DB_USER", "coskb")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "coskb")

MODEL_NAME = "intfloat/multilingual-e5-small"
EMBEDDING_DIM = 384
TOP_K = 5
SNIPPET_LENGTH = 300
