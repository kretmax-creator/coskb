# Search Sequence Diagrams

## Indexing (POST /index)

```mermaid
sequenceDiagram
    actor Admin
    participant API as search-api
    participant Model as e5-small model
    participant PG as PostgreSQL

    Admin->>API: POST /index
    API->>PG: SELECT id, title, content FROM pages (Wiki.js)
    PG-->>API: rows[]
    loop For each page
        API->>Model: encode(title + content)
        Model-->>API: embedding vector (384 dim)
        API->>PG: UPSERT INTO ai.embeddings (page_id, vector)
    end
    PG-->>API: OK
    API-->>Admin: 200 OK (indexed N pages)
```

## Semantic Search (GET /search?q=...)

```mermaid
sequenceDiagram
    actor Client
    participant API as search-api
    participant Model as e5-small model
    participant PG as PostgreSQL

    Client->>API: GET /search?q=настройка vpn
    API->>Model: encode("настройка vpn")
    Model-->>API: query vector (384 dim)
    API->>PG: SELECT ... ORDER BY vector <=> query LIMIT 5
    PG-->>API: top-5 results (page_id, title, score)
    API-->>Client: JSON [{title, snippet, score, url}, ...]
```

## Hybrid Search (mode=hybrid, default)

```mermaid
sequenceDiagram
    actor Client
    participant API as search-api
    participant Model as e5-small model
    participant PG as PostgreSQL

    Client->>API: GET /search?q=настройка vpn&mode=hybrid
    API->>Model: encode("настройка vpn")
    Model-->>API: query vector
    API->>PG: CTE: vec_score + fts_score → α·fts + β·vector ORDER BY score
    PG-->>API: top-K results
    API-->>Client: JSON [{title, snippet, score, mode}, ...]
```

Modes: `hybrid` (default, α=0.4 β=0.6), `vector` (only embeddings), `fts` (only full-text search).
Weights configurable via `FTS_WEIGHT` / `VECTOR_WEIGHT` environment variables.
