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
| D11 | 🔴 | ⬜ | `routers/email.py` | `POST /email/send` is unauthenticated and `attachment_path` is caller-controlled → arbitrary file exfiltration. → Require auth + validate/whitelist attachment path. |
| D12 | 🔴 | ⬜ | `routers/charts.py` | `GET /charts/download/{file_name}` has no path-traversal guard (`../../` escapes `CHARTS_DIR`). → Apply realpath/startswith check (pattern already in report.py). |
| D13 | 🔴 | ⬜ | `routers/logger.py` | `POST /logger/log` writes arbitrary client JSON to disk, no auth → log injection / disk exhaustion. → Auth + size/shape validation. |
| D14 | 🟠 | ⬜ | `routers/auth.py` | `validate_sql_login` connects to a caller-supplied `server`/`database` → SSRF / credential probing. → Restrict to a configured allowlist. |
| D15 | 🟠 | ⬜ | `routers/websocket.py` | WS endpoints have no token check on connect; also URL built from `window.location.host` (frontend), not the backend. → Add WS auth; fix client base URL. |
| D16 | 🟠 | ✅ | `main.py` | `CORS allow_origins=["*"]`. → Env-driven allowlist via `CORS_ALLOW_ORIGINS` (default `http://localhost:3000`). |

## C. Correctness bugs

| ID | Sev | Status | File(s) | Issue → Fix |
|----|-----|--------|---------|-------------|
| D20 | 🟠 | ⬜ | `routers/template.py` | `delete_template` calls `save_template(id, {})` — writes an empty template instead of deleting (tombstone). → Real delete. |
| D21 | 🟠 | ⬜ | `routers/charts.py` | `d[x_field]`/`d[y_field]` → `KeyError`/500 on missing field; blank chart on empty data. → Validate fields + non-empty, return 400. |
| D22 | 🟠 | ⬜ | `routers/report.py` | Returns `str(e)` to clients (L117/153/222) — leaks DB schema. → Generic message + server log. Verify mangled `for`/`append` lines L177/204 parse correctly. |
| D23 | 🟠 | ⬜ | `routers/scheduler.py` | Bad cron string → unhandled 500; `remove_job` returns error with HTTP 200. → try/except → 400; proper status codes. |

## D. Frontend ↔ backend contract mismatches

| ID | Sev | Status | Issue → Fix |
|----|-----|--------|-------------|
| D30 | 🟠 | ✅ | Frontend calls `GET /auth/me` + `POST /auth/logout`; backend had `/auth/verify` and no logout. → Added `/auth/me` + stateless `/auth/logout`; `verify` now reuses shared `decode_token`. |
| D31 | 🟡 | ⬜ | Frontend `GET /logger/{id}` and `GET /charts/` have no matching backend routes (backend has `/logger/download`,`/activity`; `/charts/generate`). → Reconcile. |

## E. Architecture / performance / hygiene

| ID | Sev | Status | Issue → Fix |
|----|-----|--------|-------------|
| D40 | 🟠 | ⬜ | Blocking sync DB/file/matplotlib I/O inside `async def` handlers across routers → blocks event loop. → Make routes `def` (threadpool) or async drivers. |
| D41 | 🟠 | ⬜ | `scheduler.py` starts `BackgroundScheduler` at import → duplicates under multi-worker; can't shut down cleanly. → Start in app lifespan, single worker. |
| D42 | 🟠 | ⬜ | `db_init_new.py` seeds tables with `random.uniform(...)` values. → Deterministic migrations (Alembic) + explicit demo-seed mode. |
| D43 | 🟡 | ⬜ | Unpinned backend deps (`requirements.txt`). → Pin exact versions. |
| D44 | 🟡 | ⬜ | Two `basicConfig` calls (scheduler.py, logger.py) conflict. → Central logging config. |

---

## Fix order (recommended)
1. **B — auth/authz (D10–D16)** — highest risk reduction.
2. **C — correctness (D20–D23)** + **D30** contract fixes.
3. **E40/E41** — async/scheduler architecture.
4. **E42/E43** — data migrations + dependency pinning (Phase 2/0 of plan).
