# Deployment Guide — Evira

This stack ships as three containers: **db** (SQL Server 2022), **backend**
(FastAPI), and **frontend** (Next.js). It can run as a central web app *or*
fully self-hosted on an isolated OT network — see the matrix below.

---

## 1. One-command launch (central web deployment)

Prerequisites: Docker Desktop / Docker Engine + Compose v2.

```bash
cp .env.docker.example .env      # then edit JWT_SECRET + MSSQL_SA_PASSWORD
docker compose up --build
```

Then open:
- **App:** http://localhost:3000
- **API docs:** http://localhost:8000/docs

The backend waits for SQL Server to be healthy, auto-creates the `scada_reports`
database, applies Alembic migrations, and (if `SEED_DEMO_DATA=1`) seeds demo data
on first boot.

Stop / reset:
```bash
docker compose down            # stop (keeps the DB volume)
docker compose down -v         # stop AND delete the database volume
```

---

## 2. Configuration (`.env`)

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET` | **Required.** Long random string used to sign JWTs. |
| `MSSQL_SA_PASSWORD` | SA password for the bundled SQL Server (complexity rules apply). |
| `SEED_DEMO_DATA` | `1` = seed demo data on first boot; `0` = start empty (production). |
| `NEXT_PUBLIC_API_BASE_URL` | URL the **browser** uses to reach the backend. Baked into the frontend at build time — set to the public URL for a remote host. |

Backend also honors (set in `docker-compose.yml`): `MSSQL_SERVER`,
`MSSQL_DATABASE`, `MSSQL_AUTH_TYPE`, `MSSQL_USERNAME`, `MSSQL_PASSWORD`,
`MSSQL_ALLOWED_SERVERS` (anti-SSRF allowlist), `CORS_ALLOW_ORIGINS`.

---

## 3. Deployment matrix (pick per customer)

| Customer constraint | How to deploy | Notes |
|---------------------|---------------|-------|
| **Central web, multi-user** | `docker compose up` on a server; put a TLS reverse proxy in front; point `NEXT_PUBLIC_API_BASE_URL` + `CORS_ALLOW_ORIGINS` at the public domain | Easiest updates, single source of truth |
| **Existing SQL Server** (don't use bundled db) | Remove the `db` service; set backend `MSSQL_SERVER`/credentials to the existing server; add it to `MSSQL_ALLOWED_SERVERS` | Common in plants with a historian already |
| **Air-gapped / isolated OT network** | Pre-pull/`docker save` the images on a connected machine, `docker load` on the OT host, run compose there | No internet needed at runtime |
| **No container runtime allowed** | Run backend as a Windows service (`uvicorn app.main:app`) next to WinCC and `npm run start` (or a static export) for the frontend on the same PC | Everything stays on `localhost` |

---

## 4. Production hardening checklist

- [ ] Set a strong unique `JWT_SECRET`; do not commit `.env`.
- [ ] `SEED_DEMO_DATA=0` in production.
- [ ] Put TLS (HTTPS/WSS) in front of frontend + backend.
- [ ] Restrict `CORS_ALLOW_ORIGINS` to the real domain(s).
- [ ] Restrict `MSSQL_ALLOWED_SERVERS` to the real DB host(s).
- [ ] Back up the SQL Server volume / database on a schedule.
- [ ] Run the backend with a single worker (the scheduler is in-process) or move
      scheduling to an external runner if scaling out (see `DEFECTS.md` D41).

---

## 5. Verifying a deployment

```bash
# backend health + API
curl http://localhost:8000/docs

# run the end-to-end smoke test against the running stack
cd backend && MSSQL_SERVER=localhost,14333 python e2e_smoke.py
```
