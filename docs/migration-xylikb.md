## Миграция из дампа `xylikb_20260220_1429.sql.migration`

Этот документ описывает **первоначальную миграцию** существующих данных Wiki.js в Coskb из дампа:

- `data/backups/xylikb_20260220_1429.sql.migration`

Дамп:

- создан с помощью `pg_dump` версии 15.x
- содержит схему и данные Wiki.js
- использует владельца объектов **`xylikb`**

Цель — развернуть новый стек Coskb и восстановить в нём эти данные.

---

## 1. Предварительные условия

- Установлены **Docker** и **Docker Compose** на целевом сервере (Ubuntu).
- Репозиторий `coskb` уже склонирован на сервер:

```bash
cd /home/user
git clone https://github.com/kretmax-creator/coskb.git coskb
cd coskb
```

Или репозиторий был обновлён:

```bash
cd /home/user/coskb
git pull origin master
```

- В репозитории уже присутствует файл:

```text
data/backups/xylikb_20260220_1429.sql.migration
```

*(если нет — скопируйте его из другого источника в эту директорию).* 

---

## 2. Настройка `.env` под дамп `xylikb`

Создайте `.env`, если он ещё не создан:

```bash
cd /home/user/coskb
cp .env.example .env
nano .env
```

Для корректного восстановления из дампа **обязательно**:

- **`POSTGRES_USER`** должен быть `xylikb`  
  Это владелец всех объектов в дампе (`OWNER TO xylikb`), поэтому пользователь с таким именем должен существовать.
- **`POSTGRES_DB`** — имя базы, в которую будут загружены данные (например, `wikijs`).  
  Это имя не зашито в дампе, но должно совпадать с настройками Wiki.js.

Соответственно, для Wiki.js:

- `DB_USER` = `POSTGRES_USER`
- `DB_PASS` = `POSTGRES_PASSWORD`
- `DB_NAME` = `POSTGRES_DB`

Пример структуры (без реальных значений паролей):

```bash
POSTGRES_USER=xylikb
POSTGRES_PASSWORD=<сложный_пароль>
POSTGRES_DB=wikijs

DB_USER=${POSTGRES_USER}
DB_PASS=${POSTGRES_PASSWORD}
DB_NAME=${POSTGRES_DB}
```

Пароль выбирается администратором и **не должен попадать в git**.

---

## 3. Подготовка каталога данных PostgreSQL

На целевом сервере:

```bash
sudo mkdir -p /var/lib/coskb-data
sudo chown root:root /var/lib/coskb-data
```

Этот путь используется как volume для контейнера Postgres в `docker-compose.yml`.

---

## 4. Загрузка Docker‑образов (при необходимости)

Если сервер имеет доступ к интернету, можно пропустить этот шаг — образы будут подтянуты автоматически при первом запуске.

Если используется **offline‑сценарий**:

1. На машине с интернетом выполнить:

   ```bash
   cd /path/to/coskb
   bash scripts/build.sh
   ```

   В `data/backups/images/` появятся `*.tar` файлы образов.

2. Перенести `data/backups/images/*.tar` на целевой сервер (в ту же директорию).

3. На целевом сервере:

   ```bash
   cd /home/user/coskb
   bash scripts/load.sh
   ```

После этого все необходимые образы будут загружены в локальный Docker.

---

## 5. Первый запуск стека Coskb

Из корня проекта:

```bash
cd /home/user/coskb
bash scripts/deploy.sh
```

Скрипт поднимет контейнеры через `docker compose up -d`.

Проверьте статус:

```bash
bash scripts/status.sh
```

Ожидается, что:

- `coskb-postgres` — `Up`
- `coskb-wikijs` — `Up`
- `coskb-nginx` — `Up`

Если `coskb-postgres` в состоянии `Restarting`, нужно сначала исправить причину (обычно неверный `.env` или отсутствие volume).

---

## 6. Восстановление дампа `xylikb_20260220_1429.sql.migration`

**Важно:** операция перезапишет данные в базе `POSTGRES_DB`, указанной в `.env`.

1. Убедитесь, что стек запущен и контейнер `coskb-postgres` в статусе `Up`:

   ```bash
   cd /home/user/coskb
   bash scripts/status.sh
   ```

2. Запустите восстановление:

   ```bash
   cd /home/user/coskb
   bash scripts/restore_db.sh data/backups/xylikb_20260220_1429.sql.migration
   ```

   Скрипт:

   - проверит наличие файла дампа
   - загрузит `.env` и прочитает `POSTGRES_USER` / `POSTGRES_DB`
   - потребует подтверждения (`Type YES to continue`)
   - скопирует дамп внутрь контейнера `coskb-postgres`
   - выполнит `psql -U $POSTGRES_USER -d $POSTGRES_DB -f /tmp/coskb_restore.sql`

3. Дождитесь завершения без ошибок.

---

## 7. Проверка после миграции

1. Ещё раз проверьте контейнеры:

   ```bash
   cd /home/user/coskb
   bash scripts/status.sh
   ```

   Все три контейнера должны быть в статусе `Up`.

2. Откройте Wiki.js в браузере:

   ```text
   http://<ip_сервера>:8890
   ```

3. Проверьте:

- наличие ожидаемых страниц и структуры разделов
- пользователей и их роли
- настройки (логотип, локаль, параметры авторизации и т.п.)

При необходимости можно дополнительно создать свежий бэкап уже с нового стенда:

```bash
cd /home/user/coskb
bash scripts/backup_db.sh
```

---

## 8. Резюме

Краткий чек‑лист миграции:

1. Клонировать репозиторий `coskb` и убедиться, что`xylikb_20260220_1429.sql.migration` находится в `data/backups/`.
2. Создать `.env` c `POSTGRES_USER=xylikb` и согласованными `POSTGRES_DB` / `DB_*`.
3. Подготовить `/var/lib/coskb-data`.
4. При необходимости загрузить Docker‑образы (`build.sh` → перенос → `load.sh`).
5. Запустить стек: `bash scripts/deploy.sh`.
6. Восстановить дамп: `bash scripts/restore_db.sh data/backups/xylikb_20260220_1429.sql.migration`.
7. Проверить Wiki.js по `http://<ip_сервера>:8890`.

После выполнения этих шагов новый стенд Coskb должен содержать все данные из исходной базы `xylikb`.

