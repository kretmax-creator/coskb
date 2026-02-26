# Architecture Diagram

## System Components

```mermaid
graph TB
    subgraph Host["Ubuntu Server VM"]
        subgraph Docker["Docker Compose (network: coskb)"]
            nginx["Nginx<br/>nginx:1.25"]
            wikijs["Wiki.js<br/>requarks/wiki:2"]
            postgres["PostgreSQL + pgvector<br/>pgvector/pgvector:pg15"]
            searchapi["search-api<br/>Python 3.11 / FastAPI"]
            tgbot["tg-bot<br/>Python 3.11"]
        end
        volume[("/var/lib/coskb-data<br/>(host volume)")]
    end

    user["User<br/>(corporate VPN)"]
    telegram["Telegram API<br/>api.telegram.org"]
    tguser["Telegram User<br/>(chat)"]

    user -- "HTTP :8890" --> nginx
    nginx -- "proxy :3000" --> wikijs
    wikijs -- "SQL" --> postgres
    searchapi -- "SQL + pgvector" --> postgres
    tgbot -- "HTTP" --> searchapi
    tgbot -- "HTTPS (long polling)" --> telegram
    tguser -- "message" --> telegram
    postgres --- volume
```

## Network & Ports

```mermaid
graph LR
    subgraph External
        user["User :8890"]
    end
    subgraph Docker Network: coskb
        nginx[":80 → wikijs:3000"]
        wikijs[":3000"]
        postgres[":5432"]
        searchapi[":8000"]
        tgbot["(no port)"]
    end
    subgraph Internet
        telegram["api.telegram.org:443"]
    end

    user --> nginx
    tgbot -.-> telegram
```

| Container | Image | Exposed Port | Internal Port |
|-----------|-------|-------------|---------------|
| nginx | nginx:1.25 | 8890 (host) | 80 |
| wikijs | requarks/wiki:2 | — | 3000 |
| postgres | pgvector/pgvector:pg15 | — | 5432 |
| search-api | custom (Dockerfile) | — | 8000 |
| tg-bot | custom (Dockerfile) | — | — |
