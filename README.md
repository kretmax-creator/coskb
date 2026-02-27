## Coskb

Coskb — это инфраструктура для развёртывания приватной Wiki-системы на базе Wiki.js 2.x, PostgreSQL 15 и Nginx 1.25 с помощью Docker Compose.

Стек:

- **Wiki Engine**: `requarks/wiki:2`
- **Database**: `postgres:15`
- **Reverse Proxy**: `nginx:1.25`
- **Orchestration**: Docker Compose

Исходное видение и архитектура описаны в `docs/vision.md`.

---

## Требования

- Ubuntu Server c установленным:
  - `docker` (Docker Engine)
  - `docker compose` (compose‑plugin)
- Доступ по SSH с правами `sudo`
- Диск:
  - несколько гигабайт под Docker‑образы и контейнеры
  - каталог данных PostgreSQL: `/var/lib/coskb-data`

---

## Подготовка окружения

### 1. Клонирование репозитория

На целевом сервере:

```bash
cd /home/user
git clone https://github.com/kretmax-creator/coskb.git coskb
cd coskb
```

*(При желании можно использовать `gh repo clone kretmax-creator/coskb coskb`.)*

### 2. Создание `.env`

Файл `.env` **не хранится в git**. Создайте его по шаблону:

```bash
cd /home/user/coskb
cp .env.example .env
nano .env
```

В `.env` необходимо задать как минимум:

- `POSTGRES_USER` — имя пользователя БД
- `POSTGRES_PASSWORD` — пароль БД
- `POSTGRES_DB` — имя базы данных Wiki.js
- `DB_USER`, `DB_PASS`, `DB_NAME` — должны совпадать с вышеуказанными значениями

Пароли и реальные значения выбираются администратором и **не должны попадать в git**.

### 3. Подготовка директории для данных БД

Каталог на хосте, куда будет монтироваться PostgreSQL:

```bash
sudo mkdir -p /var/lib/coskb-data
sudo chown root:root /var/lib/coskb-data
```

Путь жёстко зашит в `docker-compose.yml` как volume для контейнера `postgres`.

---

## Управление стеком (онлайн/обычный режим)

Все команды ниже выполняются из корня проекта `/home/user/coskb`.

### Запуск стека

```bash
bash scripts/deploy.sh
```

Скрипт вызывает `docker compose up -d` и выводит текущее состояние сервисов.

### Остановка стека

```bash
bash scripts/stop.sh
```

Контейнеры будут остановлены и удалены через `docker compose down`.

### Статус контейнеров

```bash
bash scripts/status.sh
```

Это удобная обёртка над `docker compose ps`.

---

## Offline‑workflow с Docker‑образами

Проект поддерживает сценарий, когда доступ в интернет есть только на одной машине.

### 1. Подготовка образов на машине с интернетом

На машине, где есть доступ к Docker Hub:

```bash
cd /path/to/coskb
bash scripts/build.sh
```

Скрипт:

- выполняет `docker pull` для образов `postgres:15`, `requarks/wiki:2`, `nginx:1.25`
- сохраняет их в каталоге `data/backups/images/` в виде `*.tar`

Эти файлы можно перенести на оффлайн‑сервер (scp, внешняя флешка и т.п.).

### 2. Загрузка образов на оффлайн‑сервере

На целевом сервере (после копирования `*.tar` в `data/backups/images/`):

```bash
cd /home/user/coskb
bash scripts/load.sh
```

Скрипт выполнит `docker load -i` для каждого `*.tar` в `data/backups/images/`.

После этого можно запускать стек как обычно:

```bash
bash scripts/deploy.sh
```

---

## Бэкапы и восстановление БД

### Создание бэкапа

Контейнер `coskb-postgres` должен быть запущен (`bash scripts/deploy.sh`).

```bash
cd /home/user/coskb
bash scripts/backup_db.sh
```

В результате в `data/backups/` появится файл вида:

```text
data/backups/coskb_YYYYMMDD_HHMM.sql
```

Это plain‑text дамп, созданный через `pg_dump`.

### Восстановление из бэкапа

**Внимание:** операция перезаписывает данные в текущей базе Postgres.

```bash
cd /home/user/coskb
bash scripts/restore_db.sh data/backups/coskb_YYYYMMDD_HHMM.sql
```

Скрипт:

- потребует ручного подтверждения (`YES`)
- скопирует дамп внутрь контейнера `coskb-postgres`
- выполнит `psql -U $POSTGRES_USER -d $POSTGRES_DB -f /tmp/coskb_restore.sql`

Перед запуском убедитесь, что в `.env` корректно заданы `POSTGRES_USER` и `POSTGRES_DB`.

---

## Проверка работоспособности

После запуска стека:

```bash
cd /home/user/coskb
bash scripts/status.sh
```

Ожидаемый результат:

- `coskb-postgres` — `Up`
- `coskb-wikijs` — `Up`
- `coskb-nginx` — `Up`, порт `0.0.0.0:8890->80/tcp`

Далее в браузере:

- открыть `http://<ip_сервера>:8890`
- убедиться, что Wiki.js открывается и работает

Для сценария с миграцией — проверить наличие статей, пользователей и настроек, перенесённых из исходного стенда.

### Автоматические E2E-тесты

```bash
bash scripts/test_e2e.sh
```

Скрипт проверяет все компоненты: контейнеры, PostgreSQL, Wiki.js, search-api, tg-bot, доступ к Telegram API.

---

## Smoke-тест Telegram-бота

После сборки/пересборки бота (`docker compose up -d --build tg-bot`) рекомендуется выполнить ручную проверку в Telegram-чате, привязанном к боту.

### 1. Проверка запуска

Убедиться, что контейнер запущен и нет ошибок:

```bash
docker ps | grep coskb-tg-bot
docker logs coskb-tg-bot --tail 20
```

В логах должны быть строки `Application started` и `Scheduler started`.

### 2. Команды для проверки

Отправить в Telegram-чат бота:

| Команда | Ожидаемый результат |
|---------|---------------------|
| `/start` | Приветствие и список команд |
| `/help` | Справка по командам |
| `/search vpn` | Top-3 статьи с заголовком, сниппетом и ссылкой |
| `/search несуществующий_запрос_xyz` | Сообщение «Ничего не найдено.» |
| `/read Настройка VPN` | Полный текст статьи (возможно в нескольких сообщениях) |
| `/read несуществующая_статья_xyz` | Сообщение «Статья ... не найдена.» |
| `/search` (без аргумента) | Подсказка: «Использование: /search <запрос>» |
| `/read` (без аргумента) | Подсказка: «Использование: /read <заголовок статьи>» |

### 3. Проверка healthcheck

Healthcheck работает автоматически (по умолчанию каждые 5 минут). Чтобы проверить вручную — остановить Wiki.js и подождать срабатывания:

```bash
docker stop coskb-wikijs
# Подождать до 5 минут — бот отправит алерт в чат
docker start coskb-wikijs
```

### 4. Проверка ограничения по чату

Бот должен отвечать **только** в чате, указанном в `TELEGRAM_CHAT_ID`. Сообщения из других чатов игнорируются.

