# SafeVoice — Deployment Guide

Single-container deployment. The Dockerfile builds the React frontend, copies `dist/` into the Python backend's `static/` directory, and serves both from one FastAPI process on `$PORT`. Alembic migrations run at container start.

> This guide assumes Railway. The same image runs anywhere that accepts a Dockerfile (Fly, Render, GCP Cloud Run, plain VPS with Docker).

---

## 1. Required environment variables

### Backend (runtime)

| Variable | Required | Example | Notes |
|---|---|---|---|
| `DATABASE_URL` | yes (prod) | `postgresql://user:pass@host:5432/safevoice` | SQLAlchemy URL. Railway sets this automatically when you attach a Postgres plugin. `postgres://` is auto-rewritten to `postgresql://`. Defaults to SQLite in dev. |
| `OPENAI_API_KEY` | yes | `sk-proj-…` | Without it, `/analyze/*` endpoints return **503** (by design — see TUTOR_PREP §5). |
| `CORS_ORIGINS` | yes | `https://safevoice.app,https://www.safevoice.app` | Comma-separated. Must include the public frontend origin. |
| `RATE_LIMIT_RPM` | no | `120` | Requests per minute per IP. Defaults to 120. |
| `ANTHROPIC_API_KEY` | no | `sk-ant-…` | Optional — used by the legal-AI RAG analysis endpoint. |
| `PORT` | no | `8000` | Set by Railway automatically. |

### Frontend (build-time — baked into the static bundle)

The React frontend is compiled at image-build time. Vite inlines `VITE_*` variables into the bundle; changing them later requires a **rebuild**, not a restart.

| Variable | Required | Example |
|---|---|---|
| `VITE_OPERATOR_NAME` | **yes** (§5 TMG) | `Mikel Ninh` |
| `VITE_OPERATOR_STREET` | **yes** | `Beispielstraße 1` |
| `VITE_OPERATOR_CITY` | **yes** | `10115 Berlin` |
| `VITE_OPERATOR_COUNTRY` | no (defaults `Deutschland`) | `Deutschland` |
| `VITE_OPERATOR_EMAIL` | **yes** | `kontakt@safevoice.app` |
| `VITE_OPERATOR_PHONE` | no | `+49 30 …` |

⚠️ **Missing any of the four required VITE_OPERATOR_\* values will render a yellow warning on `/impressum` and `/datenschutz`, which is legally non-compliant for a public deployment.** Set these before making the app public.

---

## 2. Railway deployment — first-time setup

### 2.1 Create the project

```bash
railway login
railway init                 # creates a project + links the repo
railway add --plugin postgres  # provisions Postgres; DATABASE_URL is injected automatically
```

### 2.2 Set the runtime env vars

```bash
railway variables set OPENAI_API_KEY=sk-proj-…
railway variables set CORS_ORIGINS=https://<your-railway-domain>
railway variables set RATE_LIMIT_RPM=120
# optional
railway variables set ANTHROPIC_API_KEY=sk-ant-…
```

### 2.3 Set the build-time (VITE_\*) vars

Railway passes build-arg env vars into the Dockerfile build. Set them **before the first deploy**:

```bash
railway variables set VITE_OPERATOR_NAME="Mikel Ninh"
railway variables set VITE_OPERATOR_STREET="Beispielstraße 1"
railway variables set VITE_OPERATOR_CITY="10115 Berlin"
railway variables set VITE_OPERATOR_COUNTRY="Deutschland"
railway variables set VITE_OPERATOR_EMAIL="kontakt@safevoice.app"
# optional
railway variables set VITE_OPERATOR_PHONE="+49 30 …"
```

If you change any `VITE_*` later, you must **redeploy** so Vite rebuilds the bundle. A plain restart is not enough.

### 2.4 Deploy

```bash
railway up
```

First boot will:
1. Build the Docker image (frontend compile → backend install)
2. Start the container; `CMD` in the Dockerfile runs:
   - `Base.metadata.create_all()` — ensure base tables exist
   - `alembic stamp head` — mark the baseline (no-op on subsequent deploys)
   - `alembic upgrade head` — apply any pending migrations
   - `seed_categories_and_laws()` — insert/update reference data
   - `uvicorn app.main:app`
3. Railway probes `GET /health`. The service is marked healthy when it returns 200.

### 2.5 Custom domain + HTTPS

Add your domain in the Railway dashboard → Settings → Domains. Railway provisions a certificate via Let's Encrypt automatically. **After adding the domain, update `CORS_ORIGINS`** to include the new origin and redeploy.

---

## 3. Local parity — docker-compose

For a Postgres-backed local stack that mirrors production:

```bash
cp .env.example .env          # fill in OPENAI_API_KEY, VITE_OPERATOR_*
docker-compose up --build     # → http://localhost:8000
```

`docker-compose.yml` spins up Postgres 16 on `:5432` and the app on `:8000`. Data persists in the named volume `pgdata`.

---

## 4. Migration strategy

Alembic is the source of truth for schema. **Do not** edit `database.py` tables directly on a running deployment — create a migration instead:

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "add some_column to cases"
# review the generated file in alembic/versions/
alembic upgrade head                # apply locally
git commit -m "feat(db): add some_column to cases"
railway up                          # applies on deploy (see Dockerfile CMD)
```

Existing prod databases get the baseline marker from `alembic stamp head` on first boot, so new migrations are applied incrementally after that.

---

## 5. Post-deploy checklist

- [ ] Public URL returns 200 on `/` and `/health`
- [ ] `/impressum` shows real operator details (no yellow warning)
- [ ] `/datenschutz` shows matching operator details
- [ ] `POST /analyze/text` with `{"text":"..."}` returns a classification (OpenAI key set)
- [ ] `GET /docs` shows Swagger UI
- [ ] Magic-link email delivers (check spam folder — configure a real SMTP provider once you have one)
- [ ] `CORS_ORIGINS` includes the public domain
- [ ] Custom domain has a valid TLS certificate

---

## 6. Rollback

Railway keeps previous deployments. Rollback via dashboard → Deployments → `…` → Rollback. Migrations are **not** auto-reversed — if a migration is destructive, write a down-migration first and deploy that separately.

---

## 7. Known deploy-time pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Impressum shows `— nicht konfiguriert —` | `VITE_OPERATOR_*` not set at **build** time | Set them, then `railway up` (rebuild — not just restart) |
| `/analyze/text` returns 503 | `OPENAI_API_KEY` missing or invalid | Set the key, restart |
| CORS errors in browser console | Public domain not in `CORS_ORIGINS` | Add it, restart |
| Migrations fail on first deploy | Prod Postgres wasn't empty before `alembic stamp head` | Create a fresh DB, or manually reconcile the `alembic_version` table |
| Healthcheck flaps | App takes >120s to boot (seeding, first OpenAI call) | Increase `healthcheckTimeout` in `railway.json` |
