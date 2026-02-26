# CI/CD Process

## 1. Branching Model

```
master          ─────●─────●─────●─────●─────
                     ↑           ↑
feature/search  ────●──●──●────/
feature/tg-bot       ────●──●─/
```

- **`master`** — стабильная ветка, всегда готова к деплою на VM.
- **`feature/<name>`** — ветка на каждую задачу/фичу. Создаётся от `master`.

### Правила

- Один PR — одна задача/фича.
- PR содержит описание: что изменено и зачем.
- Merge в `master` через PR на GitHub.
- Коммиты на английском.
- Не пушить напрямую в `master` (кроме hotfix при необходимости).

---

## 2. Рабочий цикл разработки

1. Создать ветку:
   ```bash
   git checkout master
   git pull origin master
   git checkout -b feature/<name>
   ```

2. Внести изменения, закоммитить:
   ```bash
   git add <files>
   git commit -m "Description of changes"
   ```

3. Запушить ветку:
   ```bash
   git push -u origin feature/<name>
   ```

4. Создать PR на GitHub → описание → review → merge.

5. Задеплоить на VM (см. раздел 3).

6. Удалить ветку после merge:
   ```bash
   git branch -d feature/<name>
   git push origin --delete feature/<name>
   ```

---

## 3. Деплой на VM

### Обновление production (master)

На VM из корня проекта:

```bash
bash scripts/update.sh
```

Скрипт выполняет:
1. `git pull origin master`
2. `docker compose build` (пересборка кастомных образов, если изменились)
3. `docker compose up -d` (рестарт изменённых сервисов)

### Preview-деплой feature-ветки

Для тестирования feature-ветки на VM **без влияния на production**.
Применимо только для фич, **не изменяющих схему БД**.

```bash
bash scripts/update.sh feature/<name> --preview
```

Скрипт в preview-режиме:
1. Переключается на указанную ветку.
2. Запускает стек с альтернативным портом (8891) и суффиксом `preview` для контейнеров.
3. Production-стек на порту 8890 продолжает работать.

Остановка preview:
```bash
bash scripts/update.sh --preview-stop
```

---

## 4. Структура коммитов

Формат: краткое описание на английском (imperative mood).

```
Add semantic search API endpoint
Fix hybrid search scoring weights
Update Telegram bot /read command
```

Для многострочных коммитов — первая строка заголовок, затем пустая строка и тело:

```
Add hybrid search combining FTS and vector similarity

Implement weighted scoring: α * fts_rank + β * cosine_similarity.
Default weights: α=0.4, β=0.6. Configurable via environment variables.
```

---

## 5. Будущее

- **GitHub Actions:** линтинг, проверка `docker compose config`, автотесты.
- **Автоматический деплой:** webhook или scheduled pull на VM.
