# Living Test Plan & Three-Point Effort Estimates

**Project:** SE3002 Software Quality Engineering Final Project (Fall 2026)  
**Target MIS:** NEMO v8.2.1 (`https://github.com/usnistgov/NEMO`, Commit `aa5ac6e20e4e35e6f67ab7d2133b8188679ae746`)  
**Module Under Test:** Temporary Physical Access Requests  
**Version:** 1.1 (Updated After Phases 1–6 Execution)

---

## 1. Scope

### In Scope
1. **Server-Side Business Logic (Unit & Mutation Target):**
   - `NEMO/views/access_requests.py` (`access_requests`, `create_access_request`, `delete_access_request`, `create_temporary_access`, `mark_requests_expired`, `send_request_received_email`, `csv_export`, `access_csv_export`, `is_user_a_reviewer`)
   - `NEMO/forms.py` (`TemporaryPhysicalAccessRequestForm`)
   - `NEMO/models.py` (`RequestStatus`, `TemporaryPhysicalAccessRequest`, `TemporaryPhysicalAccess`)
2. **HTTP REST API & Serialization (API & Data Generation Target):**
   - `NEMO/views/api.py` (`TemporaryPhysicalAccessRequestViewSet`)
   - `NEMO/serializers.py` (`TemporaryPhysicalAccessRequestSerializer`)
   - `NEMO/permissions.py` (`DjangoModelPermissions`)
   - Endpoint `/api/temporary_physical_access_requests/` and `/api/temporary_physical_access_requests/<id>/`
3. **Browser UI & User Journeys (E2E, Usability, Accessibility, Security, Performance Target):**
   - `/login/`, `/user_requests/access/`, `/access_requests/`, `/create_access_request/`, `/edit_access_request/<id>/`, `/delete_access_request/<id>/`, `/export_access_requests/`
   - Templates: `NEMO/templates/requests/access_requests/access_requests.html`, `access_request.html`, `access_requests_table.html`

### Out of Scope
- Upstream NEMO test suite (`NEMO/tests/`) — excluded from team test counts, coverage, and traceability (earns 0 marks).
- Unrelated NEMO modules (Tool Reservations, Billing/Accounting, Consumables, Kiosk/Area Access hardware tablets, Interlocks, Adjustment Requests, Buddy Requests, Staff Assistance Requests).

---

## 2. Test Approach by Risk Level

| Risk Tier | Score Range (5x5) | Required Techniques & Depth |
| :--- | :---: | :--- |
| **Critical** | 15–25 | 100% statement & branch coverage; complete MCC truth tables + MC/DC independence pairs; custom business-rule mutation operators; full EP + 3-point BVA API checks + cross-workflow persistence readbacks; Playwright RBAC & E2E state verification; OWASP ZAP passive scan + source control audit; controlled failure-recovery verification; strict CI merge blocking. |
| **High** | 10–14 | State-transition & decision-table testing across all allowed + >=1 disallowed transition per state; repeated/idempotency API checks; Playwright E2E alternative & exception flows; `pip-audit` dependency check; k6 p95 latency benchmarks (1 VU & >=5 VUs, 2x60s runs). |
| **Medium** | 5–9 | Equivalence partitioning on optional fields & filters; Lighthouse (Accessibility, Best Practices, SEO) + `@axe-core/playwright` scans with 1-screen remediation; keyboard-only navigation & error-guidance tests; SonarQube maintainability/duplication review. |
| **Low** | 1–4 | Smoke checks, static lint/complexity monitoring, and documented baseline verification. |

---

## 3. Roles & Area Ownership

| Team Member | Roll No. | Owned Areas |
| :--- | :--- | :--- |
| **Jaweria Abdul Hameed** | `24I-3025` | **Area 1:** SonarQube static analysis, CFG/CC calculation, 100% stmt/branch unit suite, MCC/MC-DC, `mutmut` + custom operators, GitHub Actions CI gate. |
| **Mohsin Khan** | `24I-3135` | **Area 2:** OpenAPI spec, EP/3-point BVA generator, 2-constraint regeneration demo, `pytest` + `Requests` API/integration tests & weakness report. |
| **Muhammad Aun** | `24P-3099` | **Area 3:** Use case specs (6 total = 2/member), Playwright E2E automation, task/keyboard tests, Lighthouse + axe-core & 1-screen fix, attack surface & access matrix, Playwright >=4 role checks, OWASP ZAP passive scan + 2 controls, `pip-audit`, k6 benchmarks, failure-recovery test. |
| **Shared (Trio)** | All 3 | Baseline setup, Living Test Plan, 5x5 Risk Register, Exit Criteria, Traceability Matrix, GitHub Issues & RCAs, Weekly GQM reports, Test Completion Report, AI-Use Log, Final PDF/ZIP. |

---

## 4. Test Environment & Synthetic Data

- **Runtime:** Python 3.12.0, Django 5.2.18, DRF 3.18.3, SQLite (`sqe_nemo.db`), Windows 11 local host + Ubuntu GitHub Actions runners.
- **Settings Isolation:** `sqe_local/settings.py` + `sqe_local/auth_backend.py` (`LocalSyntheticAuthBackend` using `locmem` email backend so zero real emails leave the test machine).
- **Synthetic Data Reset:** `.\venv\Scripts\python.exe scripts\reset_local_db.py` restores clean seeded users (`lab_user`, `buddy_user`, `buddy_user_2`, `other_requester`, `facility_reviewer`, `area_only_reviewer`, `inactive_user`), areas (`Cleanroom Bay A`, `Cryo Vault B`), levels, customizations (`access_requests_minimum_users=2`), and sample requests.
- **Open-Source Test Tooling:** `pytest`, `coverage.py`, `SonarQube`, `mutmut` / `Cosmic Ray`, custom Python OpenAPI EP/BVA generator, `Requests`, `Playwright` (Chromium), `Google Lighthouse`, `@axe-core/playwright`, `OWASP ZAP` (passive), `pip-audit`, `Grafana k6 OSS`, `GitHub Actions`.

---

## 5. Schedule (8 Phases)

| Phase | Target Window | Key Deliverables | Status |
| :--- | :--- | :--- | :--- |
| Phase 1 | Week 1 (Days 1–5) | MIS selection, baseline commit `aa5ac6e2...`, seed/reset scripts, FRs, 4 business rules, test basis | Completed |
| Phase 2 | Week 1–2 | SonarQube baseline & CFG CC, Living Test Plan, 5x5 Risk Register, Exit Criteria, Traceability, GQM #1 | Completed |
| Phase 3 | Week 2 | 100% stmt/branch unit tests, MCC/MC-DC pairs, `Cosmic Ray` + 4 custom operators, 43 surviving mutants | Completed |
| Phase 4 | Week 2–3 | OpenAPI spec, EP/3-point BVA generator, 2-constraint demo, API/integration suite & 9 weaknesses | Completed |
| Phase 5 | Week 3 | 6 Use cases (2/member), 30 Playwright E2E flows, keyboard/error-guidance tests, Lighthouse + axe-core + 1 fix | Completed |
| Phase 6 | Week 3–4 | Attack surface, access matrix, 8 Playwright role checks, ZAP passive, `pip-audit`, k6 (4x65s), recovery | Completed |
| Phase 7 | Week 4 | Strict GitHub Actions gate, Fix PR + Blocked PR, GitHub Issues + 2 RCAs + Pareto, Completion Report | Planned |
| Phase 8 | Week 4–5 | Integrity audit, final PDF & `.zip` (with `.git`), viva rehearsal & live mutation drill | Planned |

---

## 6. Entry, Exit, Suspension & Resumption Criteria

### Entry Criteria
- Baseline repository checked out at `aa5ac6e20e4e35e6f67ab7d2133b8188679ae746` with clean `venv/` install.
- `scripts/reset_local_db.py` executes cleanly and `pytest tests/team/unit/test_baseline_smoke.py` passes 100%.
- All synthetic accounts, tokens, and `PhysicalAccessLevel` records verified present.

### Exit Criteria (Summary — Full Metrics in `RISK_REGISTER_AND_EXIT_CRITERIA.md`)
1. **EC-01 (Structural & Fault Detection):** 100% statement & branch coverage on `NEMO/views/access_requests.py` and `TemporaryPhysicalAccessRequestForm`, complete MCC/MC-DC on critical decisions, >= 85% mutation score with 0 unaddressed killable mutants, and 100% FR traceability across unit/API/E2E.
2. **EC-02 (Authorization & Security Gate):** 100% pass on >= 4 Playwright role-based access decisions, 0 High/Critical unmitigated OWASP ZAP or `pip-audit` vulnerabilities without documented risk acceptance, and strict CI PR gate active with 0 escape hatches.
3. **EC-03 (Performance, Recovery & Accessibility):** k6 `p95 <= 500 ms` and `< 1%` unexpected failures across 1-VU and 5-VU (2x60s) runs; controlled failure-recovery leaves 0 duplicate `TemporaryPhysicalAccess` or `TemporaryPhysicalAccessRequest` rows; 0 Critical/Serious axe-core violations on the remediated screen.

### Suspension & Resumption Criteria
- **Suspend testing if:** (a) local SQLite migrations or seed scripts fail to initialize; (b) the Django test server crashes on startup or returns 5xx on `/login/`; or (c) a blocking dependency (Chromium/SonarQube/ZAP/k6) is unreachable.
- **Resume testing when:** Root cause is logged, environment/script fix is verified via `scripts/reset_local_db.py`, and baseline smoke tests pass.

---

## 7. Three-Point Effort Estimates (PERT)

Using $E = \frac{O + 4M + P}{6}$ and $\sigma = \frac{P - O}{6}$ (person-hours):

| Testing Area | Owner | Optimistic ($O$) | Most Likely ($M$) | Pessimistic ($P$) | Expected ($E$) | Std Dev ($\sigma$) | Actual Effort (hrs) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Baseline, Test Management & Reporting | Shared | 6.0 | 9.0 | 14.0 | **9.33** | 1.33 | *In Progress (7.0 hrs through Wk 3)* |
| Area 1: Static Analysis, White-Box Unit, MCC/MC-DC, Mutation & CI Gate | Jaweria | 10.0 | 14.0 | 20.0 | **14.33** | 1.67 | *In Progress (11.5 hrs; CI Gate in Ph 7)* |
| Area 2: OpenAPI Spec, EP/BVA Generator & API/Integration Suite | Mohsin | 8.0 | 12.0 | 18.0 | **12.33** | 1.67 | **12.0** |
| Area 3A: Use Cases (6), Playwright E2E, Usability & Accessibility | Muhammad Aun | 8.0 | 12.0 | 18.0 | **12.33** | 1.67 | **11.5** |
| Area 3B: Security Assessment, k6 Performance & Failure Recovery | Muhammad Aun | 7.0 | 10.0 | 16.0 | **10.50** | 1.50 | **10.0** |
| **Total Project Effort** | **Trio** | **39.0** | **57.0** | **86.0** | **58.83** | **3.52*** | *52.0 hrs logged through Wk 3* |

*\*Total $\sigma = \sqrt{\sum \sigma_i^2} = 3.52$ hrs.*
