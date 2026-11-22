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
- **Phase 1: MIS Selection, Registration & Reproducible Baseline** — **COMPLETED** (all 4 checklist items `[x]`)
- **Phase 2: Static Analysis, Test Plan, Risk Register & Exit Criteria** — **COMPLETED** (all 4 checklist items `[x]`)

*(Next chat must start directly at **Phase 3** and execute **Phases 3 & 4**.)*

---

## 2. Exact Paths Created / Modified

### Local Configuration, Seed & Test Harness
- `sqe_local/__init__.py` — Local SQE config package marker
- `sqe_local/auth_backend.py` — `LocalSyntheticAuthBackend` (`SQE_LOCAL_TEST_PASSWORD`, default `nemo-sqe-test-2026`)
- `sqe_local/settings.py` — Reproducible SQLite + DRF Token/Session settings (`sqe_nemo.db`)
- `scripts/seed_synthetic_data.py` — Idempotent synthetic data seeder (7 users, tokens, areas, levels, customization, sample requests)
- `scripts/reset_local_db.py` — Resets `sqe_nemo.db`, runs migrations, and re-seeds synthetic data
- `scripts/fetch_sonar_metrics.py` — Queries SonarQube REST API and writes `docs/evidence/sonarqube_baseline_metrics.json`
- `pytest.ini` — Configures `testpaths = tests/team`, `DJANGO_SETTINGS_MODULE = sqe_local.settings`
- `.coveragerc` — Branch coverage config (`source = .`, `include = NEMO/*, sqe_local/*`, omitting `NEMO/migrations/*` & `NEMO/tests/*`)
- `sonar-project.properties` — SonarQube project config (`nemo-sqe-access-requests`, Python 3.12, `coverage.xml`)
- `.gitignore` — Excludes `sqe_nemo.db`, `coverage.xml`, `.coverage`, `.scannerwork/`, `email_logs/`, `staticfiles/`, and assignment PDFs

### Isolated Team Tests (`tests/team/`)
- `tests/team/__init__.py`
- `tests/team/unit/__init__.py`
- `tests/team/unit/test_baseline_smoke.py` — 2/2 smoke tests (`test_synthetic_seed_and_login_workflow`, `test_access_requests_ui_and_api_baseline`)
- `tests/team/api/__init__.py`
- `tests/team/e2e/__init__.py`
- `tests/team/usability/__init__.py`
- `tests/team/security/__init__.py`
- `tests/team/recovery/__init__.py`

### Documentation & Evidence (`docs/`)
- `docs/PHASE1_BASELINE_AND_SCOPE.md` — MIS metadata (`usnistgov/NEMO`, commit `aa5ac6e20e4e35e6f67ab7d2133b8188679ae746`, NIST Public Domain), workflows, shared persistent state matrix, FR-01..FR-10, 2 roles, BR-1..BR-4, test basis & assumptions, trio ownership
- `docs/PHASE2_STATIC_ANALYSIS_AND_CFG.md` — Real SonarQube `9.9.8.100196` metrics + interpretation, 6 code smells, 1 CSRF security hotspot (`python:S3752`), Mermaid CFG for `create_access_request` (`N=37, E=54, V(G)=19`, `24` atomic boolean paths) vs SonarQube (`complexity=51`, `cognitive_complexity=85`/`50`)
- `docs/evidence/sonarqube_baseline_metrics.json` — Raw SonarQube REST API JSON snapshot
- `docs/TEST_PLAN.md` — Living Test Plan & PERT three-point effort estimates
- `docs/RISK_REGISTER_AND_EXIT_CRITERIA.md` — 10 product risks + 3 project risks (5x5 matrix) and 4 measurable exit criteria
- `docs/TRACEABILITY_MATRIX.md` — FR-01..FR-10 and BR-1..BR-4 traceability matrix
- `docs/WEEKLY_GQM_REPORT.md` — Week 1 progress & GQM metrics
- `docs/AI_USAGE_LOG.md` — Disclosed AI usage (`AI-01`..`AI-03`) + saved prompts

---

## 3. Exact Commands to Start, Reset, Test & Scan

### Reset & Seed Synthetic Database
```powershell
.\venv\Scripts\python.exe scripts\reset_local_db.py
```

### Start Local NEMO Server
```powershell
$env:DJANGO_SETTINGS_MODULE = "sqe_local.settings"
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### Run Isolated Team Tests
```powershell
.\venv\Scripts\python.exe -m pytest tests/team
```

### Run Coverage (`coverage.xml` with Linux path mapping for Docker SonarQube)
```powershell
.\venv\Scripts\coverage.exe run -m pytest tests/team
.\venv\Scripts\coverage.exe xml -o coverage.xml
.\venv\Scripts\python.exe -c "p='coverage.xml'; txt=open(p,encoding='utf-8').read(); open(p,'w',encoding='utf-8').write(txt.replace(r'C:\Users\Jaweria\Projects\SQE_Project','/usr/src'))"
```

### SonarQube Local Container (`http://localhost:9090`)
- Running container: `sqe-sonarqube` (`sonarqube:lts-community` mapped to `9090:9000`, since port `9000` is used by `atip_minio`).
- Re-scan command (pass generated token in `$env:SONAR_TOKEN`):
  ```powershell
  docker run --rm -v "${PWD}:/usr/src" -e SONAR_HOST_URL="http://host.docker.internal:9090" -e SONAR_TOKEN="$env:SONAR_TOKEN" sonarsource/sonar-scanner-cli
  ```

---

## 4. Open GitHub / User Actions
1. **Collaborator Invitations Sent:** `mohsinkhandevs` and `m-aun-005` were invited with `push` access to `https://github.com/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project` — both should accept their GitHub repository invitations.
2. **GitHub Issues (Phase 7 / Ongoing):** Log the 3 baseline candidate weaknesses + SonarQube findings as GitHub Issues once functional/API/security verification produces concrete failing evidence.

---

## 5. Exact Next Phase to Start
- **Start at Phase 3** (and execute **Phases 3 & 4** in the next chat):
  1. **Phase 3 (Area 1 — Jaweria):** 100% statement & branch coverage unit tests on `NEMO/views/access_requests.py` and `TemporaryPhysicalAccessRequestForm`, complete MCC truth tables + MC/DC pairs on `create_access_request` / business rules, `mutmut` (or `Cosmic Ray`) + >= 2 custom business-rule mutation operators, and >= 15 surviving-mutant analysis & killing all killable mutants.
  2. **Phase 4 (Area 2 — Mohsin):** OpenAPI spec for `/api/temporary_physical_access_requests/` (and access-request endpoints), EP & 3-point BVA generator script, two-constraint regeneration demo, and `pytest` + `Requests` API/integration suite with cross-workflow readbacks & weakness report.
