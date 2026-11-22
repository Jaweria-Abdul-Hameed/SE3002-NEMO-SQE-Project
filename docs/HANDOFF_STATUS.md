# Project Handoff Status (Multi-Chat Resume)

**Last Updated:** 2026-11-22  
**Project:** SE3002 Software Quality Engineering Final Project (Fall 2026) — Section A  
**Public Team GitHub Repo:** `https://github.com/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project`  
**Group (Trio — 3 Members):**
- **Jaweria Abdul Hameed (`24I-3025`)** — Git: `Jaweria-Abdul-Hameed <jaweriahameed06@gmail.com>` — **Area 1** (Static analysis, white-box unit testing, MCC/MC-DC, mutation analysis, CI quality gate)
- **Mohsin Khan (`24I-3135`)** — Git: `mohsinkhandevs <mohsinkhan.devs@gmail.com>` — **Area 2** (OpenAPI spec, automated EP/3-point BVA generator, API & integration testing)
- **Muhammad Aun (`24P-3099`)** — Git: `m-aun-005 <muhammadaoun1786@gmail.com>` — **Area 3** (Use cases 6 total = 2/member, Playwright E2E, usability & accessibility, defensive security, k6 performance & failure recovery)
- **Shared:** Baseline, Living Test Plan, 5x5 Risk Register, Exit Criteria, Traceability Matrix, GitHub Issues & RCAs, Weekly GQM, Completion Report, AI-Use Log

---

## 1. Completed Phases
- **Phase 1: MIS Selection, Registration & Reproducible Baseline** — **COMPLETED** (`4/4 [x]`)
- **Phase 2: Static Analysis, Test Plan, Risk Register & Exit Criteria** — **COMPLETED** (`4/4 [x]`)
- **Phase 3: White-Box Unit Testing, MCC/MC-DC & Mutation Analysis** — **COMPLETED** (`4/4 [x]`, committed under `Jaweria-Abdul-Hameed`)
- **Phase 4: OpenAPI Spec, Data Generation & API/Integration Testing** — **COMPLETED** (`4/4 [x]`, committed under `mohsinkhandevs`)
- **Phase 5: Use Cases, Playwright E2E, Usability & Accessibility** — **COMPLETED** (`4/4 [x]`, committed under `m-aun-005`)
- **Phase 6: Defensive Security, Performance & Failure Recovery** — **COMPLETED** (`4/4 [x]`, committed under `m-aun-005`)

*(Next chat MUST start directly at **Phase 7** and execute **Phases 7 & 8** — Final Batch: CI Quality Gate, Fix/Blocked PRs, GitHub Issues + 2 Major RCAs + Pareto, Test Completion Report, Final PDF `Project_24I-3025_24I-3135_24P-3099_A.pdf`, and Repo Zip `Project_24I-3025_24I-3135_24P-3099_A.zip` preserving `.git`.)*

---

## 2. Exact Paths Created / Modified (All Phases 1–6)

### Local Configuration, Seed, Playwright & Test Harness
- `sqe_local/__init__.py`, `sqe_local/auth_backend.py`, `sqe_local/settings.py`
- `scripts/seed_synthetic_data.py`, `scripts/reset_local_db.py`, `scripts/fetch_sonar_metrics.py`, `scripts/e2e_db_helper.py`
- `pytest.ini`, `.coveragerc`, `sonar-project.properties`, `.gitignore`
- `package.json`, `package-lock.json`, `playwright.config.mjs`

### Phase 3 (Area 1 — White-Box Unit, MCC/MC-DC & Cosmic Ray Mutation)
- `tests/team/unit/{conftest.py, test_baseline_smoke.py, test_access_requests_whitebox.py, test_mcdc_decisions.py, test_mutation_killers.py}` (74 tests)
- `sqe_mutators/`, `cosmic-ray.toml`, `cosmic-ray-forms.toml`, `scripts/run_cosmic_ray_parallel.py`, `scripts/run_custom_forms_mutation.py`
- `docs/PHASE3_WHITEBOX_MCC_MCDC.md`, `docs/PHASE3_MUTATION_ANALYSIS.md`
- Raw Evidence: `docs/evidence/phase3_unit_coverage.*`, `docs/evidence/cr_{baseline,final,forms_custom}.*`

### Phase 4 (Area 2 — OpenAPI Spec, EP/3-Point BVA Generator & API/Integration)
- `openapi/temporary_physical_access_requests.yaml`, `openapi/temporary_physical_access_requests_two_constraints_demo.yaml`
- `scripts/generate_api_test_data.py`, `scripts/demo_openapi_regeneration.py`
- `tests/team/api/{conftest.py, generated_test_data.json, test_api_ep_bva_generated.py, test_api_integration_and_cross_workflow.py}` (154 tests)
- `docs/PHASE4_OPENAPI_AND_API_TESTING.md`
- Raw Evidence: `docs/evidence/phase4_api_pytest_output.txt`, `docs/evidence/openapi_regeneration_demo/`

### Phase 5 (Area 3 — Use Cases, Playwright E2E, Usability & Accessibility)
- `docs/PHASE5_USE_CASES.md` — 6 complete use cases (`UC-01..02` Jaweria, `UC-03..04` Mohsin, `UC-05..06` Muhammad Aun; each with preconditions, main, >=2 alt, >=2 exception, postconditions)
- `tests/team/e2e/{helpers.mjs, use_cases.spec.mjs}` — 30 Playwright Chromium tests covering every UC flow with UI + SQLite postcondition assertions
- `tests/team/usability/usability_and_keyboard.spec.mjs` — 2 workflow usability tests (`USA-WF1-ERR-KBD` error-guidance + recovery + keyboard-only navigation/submit; `USA-WF2-TASK`)
- `scripts/run_accessibility_audits.mjs` — Automated `@axe-core/playwright` + Google Lighthouse runner on authenticated screens
- `NEMO/templates/requests/access_requests/access_request.html` — 1-screen accessibility fix (Serious `link-name` buddy-remove button + `<main>` landmark + `aria-live="polite"` + valid `maxlength` guard)
- `docs/PHASE5_USABILITY_AND_ACCESSIBILITY.md`
- Raw Evidence: `docs/evidence/phase5/playwright_report.json`, `docs/evidence/phase5/playwright-html-report/`, `docs/evidence/phase5/before/`, `docs/evidence/phase5/after/`

### Phase 6 (Area 3 — Defensive Security, Performance & Failure Recovery)
- `tests/team/security/role_checks.spec.mjs` — 8 Playwright role access checks (`SEC-RBAC-01`..`SEC-RBAC-08`)
- `scripts/run_zap_passive_scan.py` — Docker OWASP ZAP (`ghcr.io/zaproxy/zaproxy:stable`) passive scan orchestrator
- `tests/team/performance/access_requests_load.js` & `scripts/run_k6_benchmarks.py` — Grafana `k6 v2.4.0` load test (`GET /access_requests/`, 1 VU x 2 & 5 VUs x 2, 65s each)
- `tests/team/recovery/test_failure_and_recovery.py` — Controlled `OperationalError` fault-injection + recovery test (`0` duplicate grants)
- `docs/PHASE6_SECURITY_PERFORMANCE_RECOVERY.md`
- Raw Evidence: `docs/evidence/phase6/{rbac_checks_evidence.json, zap_passive_alerts.json, zap_passive_summary.json, zap_passive_report.html, pip_audit_report.json, pip_audit_report.txt, k6_1vu_run1*, k6_1vu_run2*, k6_5vu_run1*, k6_5vu_run2*, k6_environment_and_summary.json}`
- Combined Pytest Run (`Unit + API + Recovery = 229 passed`): `docs/evidence/phase5_6_combined_pytest_output.txt`

### Updated Living Project Docs (Shared)
- `docs/TEST_PLAN.md` (v1.1 — updated Phases 1–6 status & tracked effort)
- `docs/TRACEABILITY_MATRIX.md` (10/10 FRs mapped across Unit + API + E2E/Usability/Security/Recovery)
- `docs/WEEKLY_GQM_REPORT.md` (added Week 3 snapshot)
- `docs/AI_USAGE_LOG.md` (added `AI-06` and `AI-07` + saved prompts)

---

## 3. Exact Verified Metrics & Commands

### Key Verified Metrics Through Phase 6
- **Total Automated Team Tests:** **`269 / 269` passed** (`229` pytest [`74` unit + `154` API + `1` recovery] + `40` Playwright Chromium [`30` E2E UC flows + `2` usability/keyboard + `8` RBAC security checks]).
- **Unit Coverage & Mutation (Area 1):** `212/212` stmts (`100.0%`), `60/60` branches (`100.0%`); Cosmic Ray `151/162` (`93.21%` raw / `100.0%` equiv-adjusted), `14/14` (`100%`) custom `nemo_br/*` business-rule mutants killed.
- **Usability & Accessibility Before vs. After 1-Screen Fix (`access_request.html`):**
  - `create_access_request`: `@axe-core/playwright` **`4 -> 1`** violations (`0` Serious/Critical); Lighthouse Accessibility **`90 -> 91`**.
  - `review_access_request`: `@axe-core/playwright` **`4 -> 1`** violations (`0` Serious/Critical); Lighthouse Accessibility **`86 -> 91`**.
- **Security & Dependencies:** `8/8` Playwright RBAC checks passed; OWASP ZAP passive scan (`1` High `moment.min.js v2.29.3`, `15` Medium JS/CSP, `58` Low, `39` Info; `sessionid` `HttpOnly` & `SameSite=Lax` verified); `pip-audit` `82` entries checked, **`0` known Python CVEs**.
- **Grafana k6 OSS (`GET /access_requests/`, pre-set limits `p95 <= 500 ms`, `< 1%` failures):**
  - `1vu_run1`: `p95=38.421ms`, `7.892 RPS`, `0.00%` failures (`514` reqs)
  - `1vu_run2`: `p95=136.413ms`, `5.758 RPS`, `0.00%` failures (`375` reqs)
  - `5vu_run1`: `p95=225.470ms`, `23.146 RPS`, `0.00%` failures (`1514` reqs)
  - `5vu_run2`: `p95=227.656ms`, `28.616 RPS`, `0.00%` failures (`1866` reqs)

### Exact Commands
```powershell
# Reset & Seed Local DB
.\venv\Scripts\python.exe scripts\reset_local_db.py

# Start Local NEMO Server
$env:DJANGO_SETTINGS_MODULE = "sqe_local.settings"
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload

# Run All Pytest Suites (229 tests: Unit + API + Recovery)
.\venv\Scripts\python.exe -m pytest tests/team --reuse-db

# Run All Playwright Chromium Suites (40 tests: E2E + Usability + Security)
node node_modules/@playwright/test/cli.js test

# Re-run Accessibility Audits (Before/After)
node scripts\run_accessibility_audits.mjs --phase after

# Re-run OWASP ZAP Passive Scan (requires Docker)
.\venv\Scripts\python.exe scripts\run_zap_passive_scan.py

# Re-run Grafana k6 OSS Benchmarks (4 x 65s runs)
.\venv\Scripts\python.exe scripts\run_k6_benchmarks.py
```

---

## 4. Open GitHub / Tool Actions for Phase 7
1. **GitHub Actions CI Quality Gate (`.github/workflows/`):** Must run SonarQube (note: SonarCloud or Docker/service SonarQube reachable in CI — ask user if SonarCloud token/project or self-hosted runner is needed, or configure strict SonarQube + pytest + coverage + Cosmic Ray + Playwright on PRs with zero `continue-on-error` / `|| true`).
2. **Required PRs:** Guide user to create: (a) **1 documented Fix PR** (fails before fix, passes after fix, e.g. fixing one of our confirmed defects such as `W-API-01` or `W-API-06` or `PR-05` `@require_POST` on delete), and (b) **1 pipeline-blocked PR** (demonstrating merge blocked by threshold/test failure).
3. **GitHub Issues & RCAs:** Log defects on GitHub Issues with severity/priority/status/triage (`gh` CLI or web UI), write >= 2 major RCAs (`5 Whys` + `Fishbone`), Pareto analysis, and Test Completion Report (`Release or Hold` decision).

---

## 5. Exact Next Phase to Start
- **Start at Phase 7** (and execute **Phases 7 & 8** in the next chat — Final Batch):
  1. **Phase 7:** Enforce strict GitHub Actions PR gate (zero escape hatches), create & verify 1 Fix PR + 1 Blocked PR, log GitHub Issues + >= 2 major RCAs (`5 Whys` + `Fishbone`) + Pareto, finalize Weekly GQM + Actual Effort vs PERT + Test Completion Report.
  2. **Phase 8:** Audit repository contents, tool versions, and per-member Git commit history; compile complete PDF report `Project_24I-3025_24I-3135_24P-3099_A.pdf` and `.zip` archive `Project_24I-3025_24I-3135_24P-3099_A.zip` (including `.git`); prepare viva Q&A and live business-rule / OpenAPI mutation rehearsal sheet.
