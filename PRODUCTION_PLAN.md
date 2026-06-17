# Evira — Production Plan & Roadmap

**Target product:** `evira` (Version B — the web/FastAPI codebase)
**Owner:** Engineering team (Dev · QA · Quality/Compliance · Production/DevOps · OT)
**Date:** 2026-06-15
**Companion:** [`AUDIT.md`](./AUDIT.md) (decision record & gap analysis)

> **Scope:** Take Version B from "demo runs locally" to **enterprise production launch**.
> Estimated **6–10 weeks** depending on team size. Each phase has an explicit **exit gate** — do not advance until the gate is green.

---

## 0. Guiding Principles (the "definition of done")

A feature is **done** only when it is: (1) implemented against **real data** (no random/mock), (2) **secured** (authz + secrets handled), (3) **tested** (automated), (4) **observable** (logged/monitored), and (5) **documented**. Anything less is "demo-ware" — which is exactly what stalled both previous attempts.

---

## Phase 0 — Stabilize & Baseline  *(Week 1)*  · Owner: Eng + DevOps

**Goal:** one reproducible, version-controlled, end-to-end-runnable baseline.

- [ ] `git init` the `studio` project; first commit; push to a private remote (GitHub/GitLab/Azure DevOps).
- [ ] Add `.gitignore`: `node_modules/`, `.next/`, `__pycache__/`, `*.pyc`, `*.db`, `.env`, `backend/.env`, `*.log`, `test.pdf`.
- [ ] **Remove committed secrets** from history; rotate any real credentials in `backend/.env`.
- [ ] Pin **all** backend deps to exact versions in `backend/requirements.txt`; record the Python version (e.g. 3.13). Commit `package-lock.json` (already present).
- [ ] Write a one-command local bring-up: `npm run dev:all` (frontend + backend via `concurrently`, already configured).
- [ ] Stand up a **test SQL Server** + a **WinCC OPC UA simulator** (use `asyncua`'s example server) and walk the entire `USER_GUIDE.md` flow once.

**🚦 Exit gate 0:** `npm run build` ✅, `tsc --noEmit` ✅, `uvicorn app.main:app` starts clean ✅, one report generates against real (simulated) data ✅, repo is under git ✅.

---

## Phase 1 — Security & Auth Hardening  *(Weeks 2–3)*  · Owner: Security/Quality + Eng

**Goal:** close every 🔴 High gap from the audit. (Refs: B-G1, B-G2, B-G3.)

- [ ] Replace "SQL-login-as-auth" with proper **JWT issuance + refresh tokens**; port `argon2`/`PyJWT` password hashing from Version A.
- [ ] Implement **RBAC** (Operator / Engineer / Admin) and enforce per-route on the backend.
- [ ] Remove the `MOCK_AUTH` bypass from any production path (gate behind a test-only flag).
- [ ] Restrict CORS in `backend/app/main.py` to known origins (env-driven allowlist).
- [ ] Move secrets out of committed files → environment injection / secrets manager; **encrypt stored DB/SMTP/OPC credentials at rest** (`cryptography`/`keyring`).
- [ ] Replace `admin@example.com` placeholder (`db_pool.py`) with config.
- [ ] **Audit logging** of every login, report generation, and config change (foundation for 21 CFR Part 11 / IEC 62443 if regulated).

**🚦 Exit gate 1:** `/security-review` passes; no `allow_origins=["*"]`, no `MOCK_AUTH` in prod path, no plaintext secrets in repo, RBAC enforced.

---

## Phase 2 — Data & Domain Correctness  *(Weeks 3–5)*  · Owner: Eng + OT + DBA

**Goal:** real, correct, repeatable data. (Refs: B-G4, B-G5, B-G6, B-G11.)

- [ ] Introduce a **migration framework** (Alembic). Consolidate `db_init.py` / `db_init_new.py` / raw `.sql` into versioned migrations.
- [ ] Remove `random`-seeded values from production init; provide a clearly-labeled **demo-seed** mode only.
- [ ] **Port mature domain logic from Version A**: report-data extraction, shift definitions, template validation, WinCC activity tracking. (This is the payoff for keeping A as reference.)
- [ ] Make OPC UA **tag→machine mapping config-driven** (replace hardcoded "Extruder→M001" rules).
- [ ] Harden OPC UA client: reconnection with backoff, graceful PLC-offline handling, bounded subscription buffers.
- [ ] Reconcile the **3-step vs 5-step** report wizard (fix UI or docs so they match — B-G8).

**🚦 Exit gate 2:** Production/Quality/Downtime reports generate against real historian data; values **verified correct by an OT engineer**; no random data in any prod path; migrations run clean on an empty DB.

---

## Phase 3 — QA & Reliability  *(Weeks 5–7)*  · Owner: QA Lead

**Goal:** an automated safety net so the product can change without regressing. (Refs: B-G7.)

- [ ] Backend `pytest`: every router + service (auth, report-gen, scheduler, OPC mapping, email). Target **≥70%** coverage on core services.
- [ ] Frontend: component tests + **2–3 Playwright E2E** flows:
  - login → select scope → generate → download PDF
  - create scheduled task → verify email dispatch
  - settings → connect systems → tags auto-discover
- [ ] Load/soak test: WebSocket telemetry stream under sustained tag churn; scheduler under many concurrent jobs.
- [ ] Negative tests: DB down, PLC offline, SMTP rejects, bad template → graceful, logged failures (not crashes).
- [ ] Wire **CI** to run lint + typecheck + tests on every push.

**🚦 Exit gate 3:** CI green; E2E PDF sanity-checked; failure modes degrade gracefully.

---

## Phase 4 — Productionize & Deploy  *(Weeks 7–9)*  · Owner: Production/DevOps + OT

**Goal:** deployable, observable, recoverable — for **both** deployment models (see `AUDIT.md` §6).

- [ ] **Packaging (decide per customer):**
  - *Central web:* Docker Compose — frontend + backend + reverse proxy (TLS).
  - *Air-gapped/restricted:* package backend as a **Windows service**; frontend served locally; everything on `localhost`.
- [ ] Implement health/readiness endpoints (resolve the "report engine status" TODO in `db.py`).
- [ ] Structured logging via `loguru` (already a dep) → central log store; metrics + alerting on the 4 subsystems (DB, WinCC, Email, Report compiler) the dashboard already tracks.
- [ ] Backups for SQL + templates; documented + tested **disaster recovery**.
- [ ] CI/CD with staged rollout: dev → factory staging → 1 production line → fleet.
- [ ] Write the **runbook** (start/stop, common failures, escalation).

**🚦 Exit gate 4:** Monitoring live; rollback tested; runbook complete; deploys succeed in both web and local-service modes.

---

## Phase 5 — Launch & Handover  *(Week 10)*  · Owner: Production + QA

- [ ] **UAT** with real plant operators against a staging line; sign-off checklist.
- [ ] Operator training (train-the-trainer) + updated `USER_GUIDE.md`.
- [ ] Tag release `v1.0.0`; release notes; defined support/maintenance process.
- [ ] Post-launch monitoring window (2 weeks) with on-call.

**🚦 Exit gate 5:** UAT signed off; launch approved; support process active.

---

## Cross-Cutting: Version A Retirement

- [ ] Confirm feature parity in Version B before retiring A.
- [ ] Port remaining domain logic (Phase 2).
- [ ] Freeze `D:\AutoRepTool` **read-only**; archive a tagged snapshot; do **not** delete until post-UAT.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Effort splits across A and B again | Med | High | Freeze A; single backlog on B (R1 fix) |
| OPC UA behaves differently vs real PLC than simulator | Med | High | Phase 2 testing on a real/staging WinCC server with OT engineer |
| Regulated-customer compliance scope discovered late | Med | High | Confirm GxP/IEC 62443 needs in Phase 1 |
| Report values subtly wrong | Med | High | OT-engineer verification gate in Phase 2 |
| Credential leakage | Low | High | Phase 1 secrets removal + rotation + encryption |

---

## Immediate Next 3 Actions

1. **Baseline Version B** under git and run it end-to-end (Phase 0) → produce a concrete, prioritized defect list.
2. **Confirm regulatory/security scope** per target customer (drives Phase 1 depth).
3. **Start Phase 1** (auth/JWT/CORS/secrets) — the highest-risk gaps.

---

## Progress Tracker

| Phase | Status | Exit gate met? | Date |
|-------|--------|----------------|------|
| 0 — Stabilize & Baseline | ✅ Done | git baseline; backend imports; frontend builds; **live e2e 10/10** | 2026-06-15 |
| 1 — Security & Auth | ✅ Substantially done | JWT auth on all data routers, CORS allowlist, SSRF allowlist, path-traversal guards, no leaked errors; secrets gitignored | 2026-06-15 |
| 2 — Data & Domain | ◑ In progress | DB auto-bootstrap (D45) + demo-seed gated; **report gen validated PDF+CSV**. Remaining: Alembic migrations (D42) + port A's domain logic | — |
| 3 — QA & Reliability | ◑ Started | `e2e_smoke.py` + `e2e_report.py` green. Remaining: pytest unit suite + CI + Playwright | — |
| 4 — Productionize & Deploy | ◑ In progress | **Docker Compose stack (db+backend+frontend) builds & runs; full stack verified live** (login, dashboard, reports, frontend). Remaining: TLS/reverse-proxy, backups, CI/CD | 2026-06-15 |
| 5 — Launch & Handover | ⬜ Not started | — | — |

**Defects:** 24 fixed (all HIGH + key MED), 3 open (D24 template escaping, D31 minor contract gaps, D42 full Alembic). See `DEFECTS.md`.
