import logging
import time
from contextlib import asynccontextmanager

import psycopg2
from fastapi import FastAPI, Query, HTTPException
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

from app.config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME,
    MODEL_NAME, EMBEDDING_DIM, TOP_K, SNIPPET_LENGTH,
    FTS_WEIGHT, VECTOR_WEIGHT, FTS_LANGUAGE,
)

logger = logging.getLogger("search-api")
logging.basicConfig(level=logging.INFO)

model: SentenceTransformer | None = None


def get_raw_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME,
    )


def get_connection():
    conn = get_raw_connection()
    register_vector(conn)
    return conn


def wait_for_db(retries: int = 30, delay: float = 2.0):
    for attempt in range(1, retries + 1):
        try:
            conn = get_raw_connection()
            conn.close()
            logger.info("Database connection established")
            return
        except psycopg2.OperationalError:
            logger.warning("DB not ready (attempt %d/%d), retrying...", attempt, retries)
            time.sleep(delay)
    raise RuntimeError("Could not connect to database")


def init_db():
    conn = get_raw_connection()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS ai;")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS ai.embeddings (
            id SERIAL PRIMARY KEY,
            page_id INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL,
            path TEXT,
            content_preview TEXT,
            embedding vector({EMBEDDING_DIM}) NOT NULL,
            fts tsvector,
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cur.execute("""
        ALTER TABLE ai.embeddings ADD COLUMN IF NOT EXISTS fts tsvector;
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_embeddings_fts
        ON ai.embeddings USING gin(fts);
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Database schema initialized (ai.embeddings)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    logger.info("Loading model: %s", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)
    logger.info("Model loaded")

    wait_for_db()
    init_db()

    yield


app = FastAPI(title="Coskb Search API", lifespan=lifespan)


def encode_query(text: str):
    return model.encode(f"query: {text}", normalize_embeddings=True)


def encode_passage(text: str):
    return model.encode(f"passage: {text}", normalize_embeddings=True)


@app.get("/health")
def health():
    try:
        conn = get_raw_connection()
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "model_loaded": model is not None,
        "db_connected": db_ok,
    }


@app.post("/index")
def index_pages():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, path, content
        FROM pages
        WHERE "isPublished" = true
    """)
    pages = cur.fetchall()

    if not pages:
        cur.close()
        conn.close()
        return {"indexed": 0, "message": "No published pages found"}

    texts = [f"{row[1]}\n{row[3] or ''}" for row in pages]
    embeddings = model.encode(
        [f"passage: {t}" for t in texts],
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    for (page_id, title, path, content), embedding in zip(pages, embeddings):
        preview = (content or "")[:SNIPPET_LENGTH]
        fts_text = f"{title} {content or ''}"
        cur.execute("""
            INSERT INTO ai.embeddings (page_id, title, path, content_preview, embedding, fts, updated_at)
            VALUES (%s, %s, %s, %s, %s, to_tsvector(%s, %s), NOW())
            ON CONFLICT (page_id) DO UPDATE SET
                title = EXCLUDED.title,
                path = EXCLUDED.path,
                content_preview = EXCLUDED.content_preview,
                embedding = EXCLUDED.embedding,
                fts = EXCLUDED.fts,
                updated_at = NOW()
        """, (page_id, title, path, preview, embedding.tolist(), FTS_LANGUAGE, fts_text))

    conn.commit()
    count = len(pages)
    cur.close()
    conn.close()

    logger.info("Indexed %d pages", count)
    return {"indexed": count}


@app.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(default=TOP_K, ge=1, le=20),
    mode: str = Query(default="hybrid", description="Search mode: hybrid, vector, fts"),
):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    conn = get_connection()
    cur = conn.cursor()

    if mode == "fts":
        cur.execute("""
            SELECT page_id, title, path, content_preview,
                   ts_rank(fts, plainto_tsquery(%s, %s)) AS score
            FROM ai.embeddings
            WHERE fts @@ plainto_tsquery(%s, %s)
            ORDER BY score DESC
            LIMIT %s
        """, (FTS_LANGUAGE, q, FTS_LANGUAGE, q, top_k))

    elif mode == "vector":
        query_vec = encode_query(q)
        cur.execute("""
            SELECT page_id, title, path, content_preview,
                   1 - (embedding <=> %s::vector) AS score
            FROM ai.embeddings
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_vec.tolist(), query_vec.tolist(), top_k))

    else:
        query_vec = encode_query(q)
        cur.execute("""
            WITH vec AS (
                SELECT page_id,
                       1 - (embedding <=> %s::vector) AS vec_score
                FROM ai.embeddings
            ),
            fts AS (
                SELECT page_id,
                       ts_rank(fts, plainto_tsquery(%s, %s)) AS fts_score
                FROM ai.embeddings
            )
            SELECT e.page_id, e.title, e.path, e.content_preview,
                   (%s * COALESCE(fts.fts_score, 0) + %s * vec.vec_score) AS score
            FROM ai.embeddings e
            JOIN vec ON vec.page_id = e.page_id
            JOIN fts ON fts.page_id = e.page_id
            ORDER BY score DESC
            LIMIT %s
        """, (query_vec.tolist(), FTS_LANGUAGE, q,
              FTS_WEIGHT, VECTOR_WEIGHT, top_k))

    results = []
    for row in cur.fetchall():
        results.append({
            "page_id": row[0],
            "title": row[1],
            "path": row[2],
            "snippet": (row[3] or "")[:200],
            "score": round(float(row[4]), 4),
        })

    cur.close()
    conn.close()

    return {"query": q, "mode": mode, "results": results}


@app.get("/stats")
def stats():
    conn = get_raw_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM ai.embeddings")
    count = cur.fetchone()[0]

    cur.execute("SELECT MAX(updated_at) FROM ai.embeddings")
    last_update = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "indexed_pages": count,
        "last_indexed_at": str(last_update) if last_update else None,
    }
