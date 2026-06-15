# SCADA Report Generator — Deep Technical Audit & Production Decision

**Audited by:** Cross-functional review (Principal Engineer · QA Lead · Quality/Compliance · Production/DevOps · OT/Industrial-Automation Specialist)
**Date:** 2026-06-15
**Status:** Decision record — recommendation approved for planning
**Related document:** [`PRODUCTION_PLAN.md`](./PRODUCTION_PLAN.md)

---

## 1. Executive Summary

Two codebases were found, both left incomplete:

| | **Version A — `AutoRepTool`** | **Version B — `scada-reports-studio`** ⭐ |
|---|---|---|
| Path | `D:\AutoRepTool` | `D:\New folder (2)\studio\studio` |
| Type | Monolithic **desktop** app (CustomTkinter, PyInstaller `.exe`) | **Web client–server** (Next.js 14 + FastAPI) |
| Age | Older (~May 2025) | Newer (~Jun 2025) |
| Size | ~24,500 LOC Python across 91 files | Next.js frontend + ~50 backend modules |
| OT integration | SQL Server only (pyodbc) | **Live OPC UA (`asyncua`) + SQL Server + WebSocket streaming** |
| Deployment | Per-machine `.exe` install | Browser + central API, **or** local Windows service |

**These are not two different products — they are two generations of the same product.** Version B is a deliberate re-architecture of Version A. The effort was split across both, so neither shipped.

### Recommendation

> **Build the production application on Version B (`scada-reports-studio`).**
> Use Version A as a **reference specification** to port mature domain logic, then **freeze it read-only**.

Version B is the more modern, more complete, more secure-capable, and more deployable codebase. Critically, it can be deployed **either** as a central web app **or** as a fully-local Windows service — which directly answers the open question of "some customers forbid external/server tools, some allow them" (see §6, Deployment Decision Matrix).

---

## 2. Audit Methodology

- Full file-tree enumeration of both projects.
- Line counts, dependency manifests, and entry-point review.
- Static scan for incompleteness markers (`TODO`, `FIXME`, `mock`, `stub`, `random`, `NotImplemented`, `.bak`, `.new`).
- Read-through of critical modules: app entry points, auth, DB connectors, report generation, OPC UA/WinCC integration, the frontend↔backend API contract.
- Build/version-control/operational-hygiene checks.

---

## 3. Version A — `AutoRepTool` (Desktop) — Findings

### 3.1 What it is
A Windows desktop application (CustomTkinter UI, packaged with PyInstaller + Inno Setup) that connects to a SQL Server historian and generates industrial reports. It has a broad feature surface: auth, dashboard, charts, templates, scheduler, error/activity viewers, WinCC activity tracking, PDF/Excel export.

### 3.2 Strengths
- Large, mature **domain logic** accumulated over time (report extraction, template validation, shift handling, WinCC activity tracking).
- Real security primitives present in deps: `argon2-cffi`, `PyJWT`, `cryptography`, `keyring`.
- Rich export stack: `reportlab`, `fpdf`, `openpyxl`, `matplotlib`, `seaborn`.

### 3.3 Critical problems (root-cause level)
| ID | Problem | Evidence |
|----|---------|----------|
| A1 | **Abandoned mid-refactor.** Entry point was gutted. | `main.py` = 10 KB but `main.py.bak` = 56 KB; leftover `chart.py.new`, `custom_widgets.py.new`, `chart_container.py.new`, `test_data_fetcher.py.bak`. |
| A2 | **No single source of truth.** Same modules duplicated across layers. | `dashboard.py`, `scheduler.py`, `template_manager.py`, `activity_metrics_viewer.py`, `error_viewer.py`, `performance_dashboard.py`, `resource_manager.py`, `theme_utils.py` exist in 2–3 of `app/core`, `app/ui`, `app/utils`. |
| A3 | **Chronically unstable database layer.** Ships six scripts whose only purpose is to fix a DB that keeps breaking. | `rebuild_database.py`, `repair_database.py`, `create_missing_tables.py`, `check_db.py`, `check_db_tables.py`, `init_test_db.py`. |
| A4 | **Crashes suppressed rather than fixed.** | `main.py` monkey-patches `tkinter.Widget.focus_set` globally to swallow `TclError` ("bad window path name") — a UI lifecycle/threading bug masked, not solved. |
| A5 | **No version control.** | Not a git repository. |
| A6 | **Poor operational hygiene.** | 5 log files and build artifacts committed in the project root. |
| A7 | **Architectural ceiling.** | Desktop = per-machine install + per-machine credentials, no central control/patching, single-user, no real-time multi-viewer. Hard to scale to "enterprise." |

---

## 4. Version B — `scada-reports-studio` (Web) — Findings

### 4.1 What it is
A web application: **Next.js 14 / React 18** frontend (Radix UI, Tailwind, Recharts, framer-motion) talking to a **FastAPI** Python backend. Same domain as Version A, plus **live telemetry**. 11 authenticated pages (dashboard, report-generator, scheduler, templates, email-sender, wincc-activity-logger, logs-errors, settings, report-history, help).

### 4.2 Strengths
| ID | Strength | Evidence |
|----|----------|----------|
| B1 | **Clean layered architecture.** | `backend/app/{routers,services,models,utils,core}` with pydantic schemas; frontend `src/{app,components,lib,hooks}`. |
| B2 | **Genuinely implemented, not mocked.** Only ~5 stub markers in the entire backend. | Real `asyncua` (OPC UA), `pyodbc` (SQL Server), `reportlab`+`matplotlib`+`jinja2` (PDF/charts), `apscheduler`, `websockets`. |
| B3 | **Live OT telemetry + tag auto-discovery.** | `wincc_service.py` (358 lines): real OPC UA subscriptions, data-change callbacks, tag→machine mapping. Capability Version A never had. |
| B4 | **Complete, coherent API contract.** | `src/lib/api.ts` maps every frontend call to a backend router (auth, report, template, email, scheduler, logger, charts, dashboard, system-settings). |
| B5 | **It builds and is documented.** | `.next` production build present; complete `USER_GUIDE.md`. |
| B6 | **Deployment flexibility.** | Can run as central web app or local Windows service — fits both permissive and security-restricted customers. |

### 4.3 Gaps to close before production
| ID | Gap | Evidence | Severity |
|----|-----|----------|----------|
| B-G1 | **Auth is not production-grade.** Login validates SQL credentials and returns a token, but JWT issuance/refresh/RBAC and password hashing need to be confirmed/hardened. A `MOCK_AUTH` bypass exists. | `auth_service.py`, `MOCK_AUTH` env flag | 🔴 High |
| B-G2 | **CORS wide open.** | `main.py`: `allow_origins=["*"]  # TODO: Restrict in production` | 🔴 High |
| B-G3 | **Secrets on disk / placeholders.** | `backend/.env` committed; `admin@example.com` TODO in `db_pool.py` | 🔴 High |
| B-G4 | **Fake/random seed data in DB init.** | `db_init_new.py` uses `random.uniform(...)` to populate values | 🟠 Medium |
| B-G5 | **No migration framework.** | Raw `.sql` files (`init_db.sql`, `update_db_tables.sql`); duplicate `db_init.py`/`db_init_new.py` | 🟠 Medium |
| B-G6 | **Thin report engine.** | `report_generator.py` is only 84 lines; needs A's mature extraction logic | 🟠 Medium |
| B-G7 | **Almost no automated tests.** | Only `app/tests/test_realtime.py` on backend; none on frontend | 🟠 Medium |
| B-G8 | **Doc/code drift.** | `USER_GUIDE.md` says "3-step wizard"; code has 5 steps (`step1`–`step5`) | 🟡 Low |
| B-G9 | **No version control / CI.** | Not a git repository | 🟠 Medium |
| B-G10 | **Unpinned backend dependencies.** | `backend/requirements.txt` mostly unpinned (`fastapi`, `jinja2`, `pandas`, …) | 🟡 Low |
| B-G11 | **Hardcoded OT mapping rules.** | Tag→machine rules ("Extruder"→M001) are hardcoded, not config-driven | 🟠 Medium |

**Net:** Version B's gaps are *finishing work on a sound foundation*. Version A's problems are *structural decay*.

---

## 5. Why Both Projects Stalled — Root Causes

| # | Root cause | Evidence | Owning discipline |
|---|-----------|----------|-------------------|
| R1 | **Rewrite started before the original was finished** → effort split, neither shipped | A mid-refactor; B a parallel rewrite | Engineering leadership |
| R2 | **No source control / CI** | Neither folder is a git repo | DevOps |
| R3 | **Data layer never stabilized** | 6 repair scripts (A); random-seeded data + no migrations (B) | QA / DBA |
| R4 | **No automated test safety net** | A: scattered tests; B: one test file | QA |
| R5 | **Security deferred to "later"** | `CORS *`, `MOCK_AUTH`, secrets in `.env`, placeholder admin email | Security / Quality |
| R6 | **Documentation drifted from code** | 3-step vs 5-step wizard | Quality |
| R7 | **No "definition of done" / production gate** | Both abandoned at "demo works on my machine" | Production |

**The meta-lesson:** the single most important governance fix is to **commit to ONE codebase (Version B), put it under git + CI, and define explicit production exit gates** (see `PRODUCTION_PLAN.md`).

---

## 6. Deployment Decision Matrix (answers the open question)

You noted: *some companies forbid external/server-hosted tools for security; others allow them.* Version B supports **both** without code forks. Use this matrix per customer:

| Customer constraint | Recommended deployment of Version B | Notes |
|---------------------|-------------------------------------|-------|
| Permissive IT, multi-user, central control wanted | **Central web server** (Docker: frontend + backend + reverse proxy) | Easiest updates, single source, multi-user dashboards |
| Strict OT / air-gapped factory network, no server allowed | **Local Windows service** on the engineering PC next to WinCC | FastAPI runs on `localhost`; browser points to `localhost`; no external exposure |
| Customer mandates a single installable `.exe` per machine | **Bundle B** (FastAPI + a packaged browser/Electron shell, or PyInstaller the backend + local Next.js export) | Still B; only the packaging changes. This is the *only* scenario where A's model was ever justified — and B covers it too. |
| Regulated (pharma/food — 21 CFR Part 11, GxP) or IEC 62443 OT security | Either, **plus** audit logging, e-signatures, RBAC, encrypted credentials | Drives Phase 1 hardening scope |

**Conclusion:** deployment uncertainty is *not* a reason to keep the desktop app. Version B's single codebase serves all four scenarios. Decide packaging per-deal, not per-codebase.

---

## 7. Disposition of Version A

1. **Mine it first** — port mature domain logic into Version B (report extraction, shift/template validation, WinCC activity tracking, argon2 auth). This is where A's 24k LOC pays off.
2. **Then freeze it read-only** — to prevent the split-effort trap (R1) from recurring.
3. **Do not delete** until Version B reaches feature parity and UAT sign-off.

---

## 8. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-15 | Productionize **Version B**; archive Version A as reference | B is more modern, more complete, genuinely implemented, deployment-flexible; A is structurally decayed and mid-refactor |
| 2026-06-15 | Support both web-server and local-service deployment from one codebase | Resolves customer-by-customer security constraints without a code fork |

---

*Next: see [`PRODUCTION_PLAN.md`](./PRODUCTION_PLAN.md) for the phased roadmap, exit gates, and checklists.*
