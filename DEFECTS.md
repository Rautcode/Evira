# SCADA Reports Studio — Defect Register (Version B)

**Source:** end-to-end audit + backend import run + multi-file code review (2026-06-15).
**Legend:** 🔴 High · 🟠 Medium · 🟡 Low · ✅ Fixed · ⬜ Open
**Companion:** [`AUDIT.md`](./AUDIT.md) · [`PRODUCTION_PLAN.md`](./PRODUCTION_PLAN.md)

---

## A. Blocking / startup (fixed this session)

| ID | Sev | Status | File(s) | Issue → Fix |
|----|-----|--------|---------|-------------|
| D01 | 🔴 | ✅ | `routers/*.py` | **Whole API mounted at root.** Every router lacked a URL prefix, so routes resolved to `/login`, `/send`… instead of `/auth/login`, `/email/send`… (broke the frontend contract) and crashed FastAPI on empty-prefix routes. → Added prefixes to dashboard, auth, charts, email, logger, report, scheduler, template, websocket. |
| D02 | 🟠 | ✅ | `routers/dashboard.py` | `/scada/tags` aborted whole response on a non-numeric tag value (`float()`), didn't close cursor on error, leaked raw DB errors, unbounded `limit`. → Guarded `float()`, `finally: cursor.close()`, generic error + server log, `Query(..., ge=1, le=100)`. |

## B. Security — authentication & authorization

| ID | Sev | Status | File(s) | Issue → Fix |
|----|-----|--------|---------|-------------|
| D10 | 🔴 | ✅ | all routers | **No endpoint enforced auth** despite JWT machinery in `auth.py`. → Added `app/core/security.py` (`get_current_user`); applied `dependencies=[Depends(get_current_user)]` centrally in `main.py` to all data routers (36 routes now require a Bearer token). Auth + websocket stay public. |
| D11 | 🔴 | ✅ | `routers/email.py` | `POST /email/send` arbitrary `attachment_path` → exfiltration. → Now auth-required (D10) + attachments restricted to allowed output dirs (`reports`/`charts`/`outputs`) via `is_within_any`; recipients validated with `email_validator`. |
| D12 | 🔴 | ✅ | `routers/charts.py` | `GET /charts/download/{file_name}` path traversal. → `resolve_within(CHARTS_DIR, file_name)` rejects `..`/absolute escapes (new `app/utils/safe_paths.py`). |
| D13 | 🔴 | ✅ | `routers/logger.py` | `POST /logger/log` arbitrary write. → Auth-required (D10) + 16 KB entry cap, per-line JSON guard, `limit` clamped `1..1000`, OSError handled. |
| D14 | 🟠 | ✅ | `services/auth_service.py` | `validate_sql_login` connected to any caller-supplied `server` → SSRF. → `MSSQL_ALLOWED_SERVERS` allowlist (falls back to `MSSQL_SERVER`; `*` opt-out) + reject ODBC connection-string injection chars (`;{}\n\r`) in server/db/user/pass. |
| D15 | 🟠 | ✅ | `routers/websocket.py` + `useWebSocket.ts` | WS endpoints had no auth + client targeted the wrong host. → Backend validates `?token=` (`verify_ws_token`, closes 1008); frontend `useWebSocket` now builds the URL from `NEXT_PUBLIC_API_BASE_URL` (http→ws) and appends the stored `auth_token`. |
| D16 | 🟠 | ✅ | `main.py` | `CORS allow_origins=["*"]`. → Env-driven allowlist via `CORS_ALLOW_ORIGINS` (default `http://localhost:3000`). |

## C. Correctness bugs

| ID | Sev | Status | File(s) | Issue → Fix |
|----|-----|--------|---------|-------------|
| D20 | 🟠 | ✅ | `routers/template.py` + service | `delete_template` wrote `{}` instead of deleting; `template_id` flowed into file paths (traversal). → Added `TemplateService.delete_template` (real `os.remove`) + `_path_for` id validation (`^[A-Za-z0-9_-]{1,128}$`) used by all ops; router maps `ValueError`→400, `FileNotFoundError`→404; enabled Jinja autoescape. |
| D21 | 🟠 | ✅ | `routers/charts.py` | `d[x_field]`/`d[y_field]` → `KeyError`/500 on missing field; blank chart on empty data. → Validate non-empty + required fields present, return 400; figure closed in `finally`; switched to headless `Agg` backend. |
| D22 | 🟠 | ✅ | `routers/report.py` | Returned `str(e)` to clients (preview/list/machines) — leaked DB schema. → Generic messages + `logger.exception`; reformatted the mashed `for ...: machines.append(` loop for clarity. |
| D23 | 🟠 | ✅ | `routers/scheduler.py` | Bad cron string → unhandled 500; `remove_job` returned error with HTTP 200. → `from_crontab` wrapped → 400; `remove_job` → 404 when missing, 500 on failure, 200 only on success. |
| D24 | 🟡 | ⬜ | `services/template_service.py` | Template preview renders via `env.from_string()`, so `select_autoescape` doesn't apply — preview output is unescaped. → If preview is shown as HTML, render with explicit `autoescape=True` (or sanitize); if output target is PDF/markdown, document that escaping is intentionally off. |

## D. Frontend ↔ backend contract mismatches

| ID | Sev | Status | Issue → Fix |
|----|-----|--------|-------------|
| D30 | 🟠 | ✅ | Frontend calls `GET /auth/me` + `POST /auth/logout`; backend had `/auth/verify` and no logout. → Added `/auth/me` + stateless `/auth/logout`; `verify` now reuses shared `decode_token`. |
| D31 | 🟡 | ⬜ | Frontend `GET /logger/{id}` and `GET /charts/` have no matching backend routes (backend has `/logger/download`,`/activity`; `/charts/generate`). → Reconcile. |

## F. Deployment / bootstrap

| ID | Sev | Status | Issue → Fix |
|----|-----|--------|-------------|
| D45 | 🟠 | ✅ | App could not bootstrap a fresh SQL Server: `initialize_database()` connected straight to `scada_reports`, which doesn't exist on a new server. → Added `ensure_database_exists()` (connects to `master`, creates the DB if missing, with a safe-identifier guard) called at the start of init. Found while attempting the live end-to-end run. |
| D46 | 🔴 | ✅ | **Startup/shutdown events never ran.** `add_event_handler("startup", lambda: startup_event(app))` registered a *sync* lambda returning a coroutine that Starlette never awaited → DB init, seeding, and scheduler start silently never happened (`RuntimeWarning: coroutine was never awaited`). → Registered proper `async` `@app.on_event` handlers. Caught by the live smoke test. |
| D47 | 🟠 | ✅ | `MSSQL_ALLOWED_SERVERS` (D14) split on comma, but SQL Server addresses use `host,port` (`localhost,1433`) → a comma-port server never matched its own allowlist. → Split on `;`/newline instead. |

## E. Architecture / performance / hygiene

| ID | Sev | Status | Issue → Fix |
|----|-----|--------|-------------|
| D40 | 🟠 | ✅ | Blocking sync DB I/O inside `async def` handlers blocked the event loop. → Converted dashboard (`get_dashboard`, `_stats`, `_activity_feed`, `_scada_tags`) + `report.get_machines` to plain `def` (FastAPI runs them in a threadpool). `system_settings.update` stays `async` (legit `await reconnect()`); other routers were already sync. |
| D41 | 🟠 | ✅ | `scheduler.py` started `BackgroundScheduler` at import. → Now started/stopped in app lifespan (`core/events.py`), not at import. (Multi-worker note documented: run scheduler in a single worker or external runner.) |
| D42 | 🟠 | ◑ | `db_init_new.py` seeds tables with `random.uniform(...)`. → **Partial:** startup seed now gated behind `SEED_DEMO_DATA=1` (no auto-random-seed in prod). **Still open:** replace raw SQL init with Alembic migrations. |
| D43 | 🟡 | ✅ | Unpinned backend deps; PyJWT + SQLAlchemy were missing entirely. → Pinned all to verified installed versions; added the two missing deps. |
| D44 | 🟡 | ✅ | Conflicting `basicConfig` calls in scheduler.py + logger.py. → Removed both; central logging owned by `app.main`; modules use `getLogger(__name__)`. |

---

## Fix order (recommended)
1. **B — auth/authz (D10–D16)** — highest risk reduction.
2. **C — correctness (D20–D23)** + **D30** contract fixes.
3. **E40/E41** — async/scheduler architecture.
4. **E42/E43** — data migrations + dependency pinning (Phase 2/0 of plan).
