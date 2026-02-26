# Vision

## 1. Назначение документа
Vision описывает целевую техническую архитектуру Coskb, принципы проектирования и границы MVP. Документ предназначен для архитектурного и технического ревью перед реализацией.

**Название проекта:** Coskb (рабочее название)

**Репозиторий:** https://github.com/kretmax-creator/coskb

## 2. Обзор системы
Coskb — монолитное wiki-приложение (Wiki.js), развёрнутое на Ubuntu Server VM с использованием Docker Compose. PostgreSQL — основное хранилище данных. Nginx — reverse proxy. 
Данные будут мигрированы из прототипа, развернутого на Kubernetes-кластере через pg_dump/restore.

## 3. Технологический стек

### MVP
*   **Wiki Engine:** Wiki.js 2.x (официальный Docker-образ `requarks/wiki:2`).
*   **Database:** PostgreSQL 15 с pgvector (Docker-образ `pgvector/pgvector:pg15`).
*   **Reverse Proxy:** Nginx 1.25 (официальный Docker-образ `nginx:1.25`).
*   **Orchestration:** Docker Compose.
*   **Container Runtime:** Docker Engine.
*   **Host OS:** Ubuntu Server.

### Поиск и AI
*   **Embedding Model:** `intfloat/multilingual-e5-small` (CPU, ~130MB).
*   **Vector Storage:** pgvector (расширение PostgreSQL, схема `ai`).
*   **Search API:** Python 3.11+, FastAPI, sentence-transformers. Docker-образ собирается из Dockerfile.

### Telegram-бот
*   **Runtime:** Python 3.11+, python-telegram-bot. Docker-образ собирается из Dockerfile.
*   **Режим:** long polling (не требует входящих соединений).

## 4. Архитектурные принципы

### 4.1 Принципы MVP
- **Простота важнее гибкости.**
- **Явность вместо магии.**
- **Ручные операции допустимы.**

### 4.2 Осознанные архитектурные компромиссы
- Docker Compose вместо оркестраторов (K8s, Swarm).
- Ручное управление секретами (`.env` файл).
- Совместное использование одной БД для контента и будущих векторных данных.
- Ассеты (картинки) хранятся в БД.
- Offline-режим: на первом этапе без обновлений wikijs из интернета.

Все перечисленные решения применимы только для MVP и подлежат пересмотру при росте нагрузки или числа пользователей.

## 5. Структура проекта

### Repository layout
```text
/
├── docs/                # Документация
│   ├── vision.md        # Технический проект
│   ├── tasklist.md      # План разработки
│   ├── ci-cd.md         # CI/CD процесс
│   ├── network-research.md
│   ├── diagrams/        # Mermaid-диаграммы
│   └── adr/             # Architecture Decision Records
├── nginx/               # Конфигурация Nginx
│   └── default.conf     # Reverse proxy config
├── scripts/             # Скрипты автоматизации
│   ├── build.sh         # Скачивание образов (offline)
│   ├── load.sh          # Загрузка образов в Docker (offline)
│   ├── deploy.sh        # docker compose up
│   ├── stop.sh          # docker compose down
│   ├── backup_db.sh     # pg_dump
│   ├── restore_db.sh    # Восстановление дампа
│   ├── status.sh        # Состояние контейнеров
│   └── update.sh        # git pull + rebuild + restart
├── services/            # Кастомные сервисы
│   ├── search-api/      # Семантический поиск (Python, FastAPI)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   └── tg-bot/          # Telegram-бот (Python)
│       ├── Dockerfile
│       ├── requirements.txt
│       └── app/
├── data/                # Бэкапы и данные
│   └── backups/         # Дампы БД
├── docker-compose.yml   # Описание стека
├── config.yml           # Wiki.js config (offline: true)
├── .env.example         # Шаблон переменных окружения
├── .gitignore
└── README.md            # Инструкция по запуску
```

### Runtime layout (Docker)
- Контейнеры: postgres, wikijs, nginx, search-api, tg-bot.
- Сеть: внутренняя Docker bridge network `coskb`.
- Данные PostgreSQL: host volume `/var/lib/coskb-data`.
- Nginx: порт 8890 → wikijs:3000.
- search-api и tg-bot: только внутренняя сеть, без внешних портов.

## 6. Архитектура системы

### Компоненты (MVP)
1.  **Nginx**
    *   Reverse proxy. Единственная внешняя точка входа.
    *   Порт: 8890 на хосте → wikijs:3000 внутри сети.
2.  **Wiki.js**
    *   Stateless приложение. Хранит контент и ассеты через PostgreSQL.
    *   Режим: offline (`offline: true` в config.yml).
3.  **PostgreSQL**
    *   Stateful компонент. Единственный источник данных системы.
    *   Расширение pgvector для векторного поиска.
    *   **Физическое хранение:** host volume `/var/lib/coskb-data`.

### Компоненты (поиск и интеграции)
4.  **search-api**
    *   Python-сервис (FastAPI). Семантический и гибридный поиск.
    *   Модель: `intfloat/multilingual-e5-small` (CPU).
    *   Читает статьи из Wiki.js таблиц, хранит эмбеддинги в схеме `ai` (pgvector).
    *   API: индексация, поиск, похожие статьи, обнаружение дубликатов.
    *   Только внутренняя сеть (без внешних портов).
5.  **tg-bot**
    *   Python-сервис (python-telegram-bot). Long polling.
    *   Команды: `/search` (поиск статей), `/read` (полный текст), `/similar` (похожие).
    *   Healthcheck сервисов с алертами в Telegram-чат.
    *   Работает в одном указанном чате (`TELEGRAM_CHAT_ID`).
    *   Только внутренняя сеть + outbound к `api.telegram.org`.

## 7. Модель данных
*   **Wiki.js** — управляет своей схемой `public` (страницы, пользователи, ассеты). Не проектируем таблицы вручную.
*   **pgvector** — схема `ai`, таблица эмбеддингов статей. Управляется сервисом `search-api`.

## 8. Сценарии работы

### Первичная установка (миграция)
1.  Создать `.env` по шаблону `.env.example`.
2.  Подготовить директорию для данных БД (`/var/lib/coskb-data`).
3.  Загрузить Docker-образы (offline: `build.sh` → `load.sh`).
4.  Запустить стек: `deploy.sh`.
5.  Восстановить дамп: `restore_db.sh`.
6.  Wiki.js подхватывает существующие данные.

### Деплой (чистая установка)
1.  Создать `.env`.
2.  Запустить `deploy.sh` → Wiki.js открывает Setup Wizard.
3.  Пройти Setup Wizard, создать администратора.

### Нормальная работа (MVP)
1.  Пользователь заходит на `http://<host>:8890` → логинится → создаёт/редактирует статью → сохраняет.
2.  Поиск: полнотекстовый поиск через Wiki.js.

## 9. Конфигурирование
**Подход:** Все настройки передаются через переменные окружения (`.env` файл).

**Секреты:** Не хранятся в git. `.env` файл в `.gitignore`. Шаблон `.env.example` содержит только имена переменных.

## 10. Логгирование
**MVP-подход:** Приложения пишут в stdout/stderr. Логи доступны через `docker compose logs`.

**Формат:** Plain text.

## 11. CI/CD

*   **Ветвление:** `master` (стабильная) + `feature/<name>` → PR → merge.
*   **Деплой:** `scripts/update.sh` — git pull → docker compose build → restart.
*   **Preview:** возможность запуска feature-ветки по отдельному порту (для фич без изменения схемы БД).
*   **Коммиты:** на английском языке.
*   Подробное описание: `docs/ci-cd.md`.

## 12. Технический план (Roadmap)

### Этап 1 — MVP (Infrastructure + Migration) ✅
- Развёртывание Wiki.js, PostgreSQL, Nginx на Docker.
- Миграция данных.
- Документированная процедура деплоя.

**Definition of Done:** Развёртывание по инструкции выполнено; данные восстановлены; Wiki.js работает; README содержит полную процедуру.

### Этап 2 — Поиск и интеграции
- Семантический поиск (pgvector + multilingual-e5-small).
- Гибридный поиск (FTS + vector).
- Telegram-бот (поиск, чтение статей, healthcheck).
- Похожие статьи и обнаружение дубликатов.

**Definition of Done:** Поиск по смыслу работает; бот отвечает на команды в Telegram; API похожих статей возвращает релевантные результаты.

### Этап 3 — Контент (Future)
- Импорт новых данных.
- Формирование структуры базы знаний.

### Этап 4 — Расширения (Future)
- Поисковый виджет в Wiki.js UI.
- GitHub Actions.
- Автобэкапы с ротацией.
- Аналитика поиска, RAG.
