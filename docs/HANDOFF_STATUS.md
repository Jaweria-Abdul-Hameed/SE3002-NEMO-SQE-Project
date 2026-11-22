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

*(Next chat MUST start directly at **Phase 5** and execute **Phases 5 & 6** — Area 3, committed under `m-aun-005 <muhammadaoun1786@gmail.com>`.)*

---

## 2. Exact Paths Created / Modified

### Local Configuration, Seed & Test Harness
- `sqe_local/__init__.py`, `sqe_local/auth_backend.py`, `sqe_local/settings.py` (added `TEST.NAME = sqe_nemo_pytest.db` for fast `--reuse-db`)
- `scripts/seed_synthetic_data.py`, `scripts/reset_local_db.py`, `scripts/fetch_sonar_metrics.py`
- `pytest.ini` (`testpaths = tests/team`, `addopts = -v --nomigrations`)
- `.coveragerc`, `sonar-project.properties`, `.gitignore`

### Phase 3 (Area 1 — White-Box Unit, MCC/MC-DC & Cosmic Ray Mutation)
- `tests/team/unit/conftest.py` — Fixtures (`access_env`, `make_form_post_data`, `make_access_request`, `set_min_users`)
- `tests/team/unit/test_baseline_smoke.py` — 2 smoke tests
- `tests/team/unit/test_access_requests_whitebox.py` — 27 white-box unit tests (all 9 view functions, form BVA, model helpers, state transitions, roles, email, CSV)
- `tests/team/unit/test_mcdc_decisions.py` — 36 tests covering complete MCC truth tables & derived MC/DC independence pairs (`D1`, `D2`, `D3`, `D4a`, `D4b`, `D5`)
- `tests/team/unit/test_mutation_killers.py` — 9 tests (`MK-01`..`MK-09`) killing all 32 killable baseline surviving mutants
- `sqe_mutators/` — Editable Python package registering 4 custom Cosmic Ray business-rule operators under `nemo_br/*` (`FlipApprovalStatusOperator`, `SkipGrantCreationOperator`, `BypassReviewerCheckOperator`, `RelaxBuddyMinimumOperator`)
- `cosmic-ray.toml`, `cosmic-ray-forms.toml`, `scripts/run_cosmic_ray_parallel.py`, `scripts/run_custom_forms_mutation.py`
- `docs/PHASE3_WHITEBOX_MCC_MCDC.md`, `docs/PHASE3_MUTATION_ANALYSIS.md`
- Raw Evidence: `docs/evidence/phase3_unit_coverage.txt`, `docs/evidence/phase3_unit_coverage.json`, `docs/evidence/cr_baseline.sqlite`, `docs/evidence/cr_baseline_report.txt`, `docs/evidence/cr_final.sqlite`, `docs/evidence/cr_final_report.txt`, `docs/evidence/cr_forms_custom.sqlite`, `docs/evidence/cr_forms_custom_report.txt`

### Phase 4 (Area 2 — OpenAPI Spec, EP/3-Point BVA Generator & API/Integration)
- `openapi/temporary_physical_access_requests.yaml` — OpenAPI 3.0.3 contract
- `openapi/temporary_physical_access_requests_two_constraints_demo.yaml` — Two-constraint mutated demo spec (`other_users.minItems: 1->2`, `description.maxLength: 500->200`)
- `scripts/generate_api_test_data.py` — Spec-driven OpenAPI EP & 3-point BVA generator (`--spec`, `--output`)
- `scripts/demo_openapi_regeneration.py` — Automated 2-constraint regeneration & diff generator
- `tests/team/api/generated_test_data.json` — Generated dataset (46 body EP, 52 body 3-point BVA, 85 query/path cases, 7 state transitions)
- `tests/team/api/conftest.py` — Fast session-scoped `api_server` (`LiveServer`) + placeholder resolver
- `tests/team/api/test_api_ep_bva_generated.py` — 141 spec-driven EP, 3-point BVA & parameter tests
- `tests/team/api/test_api_integration_and_cross_workflow.py` — 13 RBAC, CRUD idempotency, state-transition, cross-workflow readback & regeneration tests
- `docs/PHASE4_OPENAPI_AND_API_TESTING.md` — API coverage summary & 9 documented endpoint weaknesses (`W-API-01`..`W-API-09`) linked to Risk Register
- Raw Evidence: `docs/evidence/phase4_api_pytest_output.txt`, `docs/evidence/phase3_4_combined_pytest_output.txt`, `docs/evidence/openapi_regeneration_demo/`

### Updated Living Project Docs (Shared)
- `docs/TRACEABILITY_MATRIX.md` — Updated to 10/10 FRs (100%) verified across Unit (74 tests) + API/Integration (154 tests) = 228 passing tests
- `docs/WEEKLY_GQM_REPORT.md` — Added Week 2 progress & GQM snapshot
- `docs/AI_USAGE_LOG.md` — Added `AI-04` and `AI-05` + saved prompts

---

## 3. Exact Verified Metrics & Commands

### Key Verified Metrics So Far
- **Unit Coverage (Server-Side Business Logic):** `212 / 212` statements (**100.0%**), `60 / 60` branches (**100.0%**) across `NEMO/views/access_requests.py` (`148/148`, `50/50`), `TemporaryPhysicalAccessRequestForm` (`13/13`, `4/4`), and `TemporaryPhysicalAccess`/`TemporaryPhysicalAccessRequest` (`51/51`, `6/6`).
- **Cosmic Ray Mutation Score (`NEMO/views/access_requests.py`):** Baseline `119/162` (`73.46%`, 43 surviving) -> Final **`151/162` (`93.21%` raw; `100.0%` equivalent-adjusted across 11 proven equivalent mutants)**; **14 / 14 (`100%`) custom `nemo_br/*` business-rule mutants killed** across `access_requests.py` (12) + `forms.py` (2).
- **API & Integration Suite:** **`154 / 154` passed**, **228 / 228 combined (`tests/team`) passed**.

### Commands
```powershell
# Reset & Seed Local DB
.\venv\Scripts\python.exe scripts\reset_local_db.py

# Start Local NEMO Server (for Playwright / Lighthouse / ZAP / k6 in Phases 5-6)
$env:DJANGO_SETTINGS_MODULE = "sqe_local.settings"
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

# Run All Team Tests (Unit + API = 228 tests)
.\venv\Scripts\python.exe -m pytest tests/team --reuse-db

# Regenerate API EP/3-Point BVA Data from OpenAPI Spec
.\venv\Scripts\python.exe scripts\generate_api_test_data.py --spec openapi\temporary_physical_access_requests.yaml --output tests\team\api\generated_test_data.json

# Re-run Cosmic Ray Parallel Mutation Suite
.\venv\Scripts\python.exe scripts\run_cosmic_ray_parallel.py --workers 6 --fresh --session docs\evidence\cr_final.sqlite --report docs\evidence\cr_final_report.txt
```

---

## 4. Open GitHub / Tool Actions
1. **Collaborator Invitations:** Ensure `mohsinkhandevs` and `m-aun-005` accept their repository invitations on `https://github.com/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project`.
2. **Phase 5–6 Tool Installs (next chat):** Install Playwright + Chromium (`playwright` / `@playwright/test` + `@axe-core/playwright` + `lighthouse`), `pip-audit`, `OWASP ZAP` (Docker `ghcr.io/zaproxy/zaproxy:stable`), and `Grafana k6 OSS` (Docker `grafana/k6` or native Windows binary).

---

## 5. Exact Next Phase to Start
- **Start at Phase 5** (and execute **Phases 5 & 6** in the next chat — **Area 3, Muhammad Aun `24P-3099`**, commit as `m-aun-005 <muhammadaoun1786@gmail.com>`):
  1. **Phase 5:** Write 6 complete use case specs (2/member, preconditions, main, >=2 alt, >=2 exception, postconditions); automate EVERY flow in Playwright (Chromium) asserting UI + DB postconditions; automate 2 workflow task tests (with business-rule error guidance + recovery, and keyboard-only navigation/submission); run Lighthouse + `@axe-core/playwright` on each key screen, fix 1 screen, re-verify before/after, and archive all reports.
  2. **Phase 6:** Map attack surface & 2-role access matrix; automate >= 4 Playwright role checks; run OWASP ZAP passive scan during Playwright execution + review >= 2 controls corroborated by source/config; run `pip-audit`; set p95 & failure targets BEFORE load testing and run Grafana k6 OSS (`1 VU` & `>= 5 VUs`, 2 runs each × >= 60s = 4 runs); automate 1 controlled failure-and-recovery state-change test in `tests/team/recovery/`.
