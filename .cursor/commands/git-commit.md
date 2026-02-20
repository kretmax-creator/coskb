# git-commit — Commit after successful iteration

**Context:** `docs/vision.md`, `.cursor/rules/workflow.mdc`, `.cursor/rules/conventions.mdc`, `.cursor/rules/security.mdc`

**When:** Workflow step 5 — only after:
1. Implementation is done
2. User confirmed the changes
3. `docs/tasklist.md` updated (`[ ]` → `[x]`, ⬜ → ✅)

---

## Pre-commit check (security.mdc)

Before staging, verify:
- No passwords, tokens, keys, DSN in staged files
- No secrets in docker-compose.yml, YAML, examples, comments
- No hardcoded credentials or temporary test data

If any found → **STOP**, fix, then commit.

---

## Steps

1. **Stage changes**
   ```bash
   git add -A
   ```
   Or selective: `git add <paths>`

2. **Commit** — message **in English** (workflow requirement)
   ```bash
   git commit -m "<message>"
   ```

3. **Push**
   ```bash
   git push
   ```

---

## Commit message format

- **Imperative mood:** `Add X`, `Fix Y`, `Update Z`
- **Optional prefix:** `Iteration N: <summary>`
- **Examples:**
  - `Iteration 1: Add docker-compose with PostgreSQL, Wiki.js, Nginx`
  - `Fix Nginx reverse proxy config`
  - `Update README with migration instructions`

---

## One-liner (after pre-check)

```bash
git add -A && git commit -m "Iteration N: <summary>" && git push
```

Replace `N` and `<summary>` with actual iteration number and short description.
