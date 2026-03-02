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

FTS_WEIGHT = float(os.environ.get("FTS_WEIGHT", "0.4"))
VECTOR_WEIGHT = float(os.environ.get("VECTOR_WEIGHT", "0.6"))
FTS_LANGUAGE = os.environ.get("FTS_LANGUAGE", "russian")

MIN_SCORE_HYBRID = float(os.environ.get("MIN_SCORE_HYBRID", "0.35"))
MIN_SCORE_VECTOR = float(os.environ.get("MIN_SCORE_VECTOR", "0.55"))
MIN_SCORE_FTS = float(os.environ.get("MIN_SCORE_FTS", "0.001"))
