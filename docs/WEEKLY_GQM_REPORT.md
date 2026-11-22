# Weekly Progress & GQM Metrics Report

**Project:** SE3002 Software Quality Engineering Final Project (Fall 2026)  
**Target MIS:** NEMO v8.2.1 (`aa5ac6e20e4e35e6f67ab7d2133b8188679ae746`)

---

## 1. GQM (Goal-Question-Metric) Definitions

| Goal | Questions | Metric & Formula | Interpretation Context |
| :--- | :--- | :--- | :--- |
| **G1: Code & Defect Quality** | How defect-prone is the in-scope module relative to its size? | **Defect Density** = `Confirmed Defects / In-Scope KLOC` | Evaluated against baseline static inspection + test-discovered bugs; higher early defect density during testing indicates effective fault discovery before release, whereas unfixed high-severity density blocks release. |
| **G2: Verification Completeness** | What proportion of specified functional requirements have passing automated tests? | **Requirements Coverage (%)** = `(FRs with >=1 Passing Automated Test / Total FRs) * 100` | Must reach `100%` across `FR-01..FR-10` by Phase 6 before release sign-off. |
| **G3: Fix Stability** | Are defect fixes holding without regressions or failed re-tests? | **Reopen Rate (%)** = `(Reopened Defects / Total Closed Defects) * 100` | Target `<= 10%`; a spike indicates incomplete root-cause fixes or weak regression assertions. |

---

## 2. Weekly Tracking Log

### Week 1 Report (Phases 1–2 Initialization — 2026-11-21)
- **Planned Milestones:** Complete Phase 1 (MIS baseline, reproducible setup/seed/reset, 2 workflows, >= 8 FRs, 4 business rules, test basis) and Phase 2 (Test Plan, 3-point estimates, 5x5 Risk Register, Exit Criteria, Traceability Matrix, SonarQube + CFG CC baseline).
- **Actual Progress:**
  - Phase 1 technical setup completed and verified: baseline cloned at `aa5ac6e20e4e35e6f67ab7d2133b8188679ae746`, `venv/` + NEMO 8.2.1/Django 5.2.18 installed, `sqe_local/` non-invasive config + `scripts/reset_local_db.py` + `scripts/seed_synthetic_data.py` verified, `pytest tests/team` smoke tests `2/2 PASSED`.
  - Section `A` registration confirmed for 3-member group (`24I-3025`, `24I-3135`, `24P-3099`).
  - Phase 2 test management artifacts authored (`TEST_PLAN.md`, `RISK_REGISTER_AND_EXIT_CRITERIA.md`, `TRACEABILITY_MATRIX.md`, `WEEKLY_GQM_REPORT.md`, `AI_USAGE_LOG.md`).
  - Real SonarQube 9.9.8 scan executed via Docker (`nemo-sqe-access-requests`): `access_requests.py` has `249` NCLOC, Cyclomatic Complexity `51`, Cognitive Complexity `85` (`create_access_request` = `50`), `6` code smells, `1` CSRF security hotspot (`S3752`), `0` bugs/vulnerabilities, `16.7%` combined coverage (`22.3%` line, `0.0%` branch). Hand-calculated CFG for `create_access_request`: `N=37, E=54, V(G)=19` (`24` with atomic boolean expansion).
- **Schedule Variance:** On track — Phases 1 and 2 completed.
- **GQM Snapshot (Week 1 Baseline):**
  - **Defect Density:** `0.00` logged GitHub Issues so far (3 baseline candidate weaknesses + 6 SonarQube code smells + 1 security hotspot identified in `0.249` KLOC of `access_requests.py` to be logged in GitHub Issues once public remote repo is created).
  - **Requirements Coverage:** `20.0%` (`2 / 10` FRs partially covered by Phase 1 smoke tests `FR-01`, `FR-10`; full suites planned in Phases 3–5).
  - **Reopen Rate:** `N/A (0 / 0 closed defects)`.
- **Control Actions:**
  1. Create public GitHub repo (recommended name `SE3002-NEMO-SQE-Project`) under `Jaweria-Abdul-Hameed`, add `mohsinkhandevs` and `m-aun-005` as collaborators, and push `main`.
  2. Begin Phase 3 white-box unit testing targeting 100% statement/branch coverage, MCC/MC-DC pairs on `create_access_request`, and `mutmut` + 2 custom business-rule operators.

---

### Week 2 Report (Phases 3–4 Execution — 2026-11-22)
- **Planned Milestones:** Complete Phase 3 (Area 1 — 100% statement/branch unit coverage, complete MCC/MC-DC pairs, Cosmic Ray + >= 2 custom operators, >= 15 surviving-mutant analysis & remediation) and Phase 4 (Area 2 — OpenAPI 3.0.3 spec, EP & 3-point BVA generator, 2-constraint regeneration demo, `pytest` + `requests` API/integration suite & weakness report).
- **Actual Progress:**
  - **Phase 3 (Area 1 — Jaweria):**
    - Authored 74 isolated unit tests in `tests/team/unit/` achieving **100.0% statement (212/212) and 100.0% branch (60/60) coverage** across `NEMO/views/access_requests.py` (`148/148` stmts, `50/50` branches), `TemporaryPhysicalAccessRequestForm` (`13/13` stmts, `4/4` branches), and `TemporaryPhysicalAccess` / `TemporaryPhysicalAccessRequest` (`51/51` stmts, `6/6` branches).
    - Enumerated complete MCC truth tables and automated every MC/DC independence pair across all 5 compound decisions (`D1`–`D5`) in `docs/PHASE3_WHITEBOX_MCC_MCDC.md`.
    - Built and registered 4 custom Cosmic Ray business-rule operators (`sqe_mutators/`: `FlipApprovalStatusOperator`, `SkipGrantCreationOperator`, `BypassReviewerCheckOperator`, `RelaxBuddyMinimumOperator`).
    - Executed real 162-mutant Cosmic Ray baseline (`119/162` = **73.46%**, 43 surviving), classified all 43 surviving mutants (`10` missing tests, `22` weak assertions, `11` mathematically equivalent), added `test_mutation_killers.py` (`MK-01`..`MK-09`), and re-executed Cosmic Ray achieving **`151/162` = `93.21%` raw mutation score (`100.0%` equivalent-adjusted; `14/14` = `100%` custom business-rule mutants killed)**.
  - **Phase 4 (Area 2 — Mohsin):**
    - Authored OpenAPI 3.0.3 spec (`openapi/temporary_physical_access_requests.yaml`) and spec-driven generator (`scripts/generate_api_test_data.py`) producing 46 body EP cases, 52 body 3-point BVA cases, 85 query/path cases, and 7 state-transition cases.
    - Executed two-constraint regeneration demo (`other_users.minItems: 1->2`, `description.maxLength: 500->200`) and verified live API test consumption (`6/6 passed`).
    - Executed **154/154 passing `pytest` + `requests` API & integration tests** in 21.29s against local live NEMO server, discovering and documenting **9 genuine API endpoint weaknesses (`W-API-01`..`W-API-09`)** linked to `PR-01`, `PR-02`, `PR-03`, `PR-04`, `PR-06`.
- **Schedule Variance:** On track — Phases 1 through 4 completed (`16/32` total checklist items `[x]`).
- **GQM Snapshot (Week 2):**
  - **Defect Density (Confirmed Test Findings):** `9` confirmed API/endpoint weaknesses + `6` SonarQube code smells + `1` CSRF security hotspot across `0.249` KLOC of `access_requests.py` (and DRF API layer) — `9` actionable product defects queued for GitHub Issues & Phase 7 RCAs (`W-API-01`..`W-API-09`, including 3 Critical: `W-API-03`, `W-API-04`, `W-API-05`). *Interpretation:* High early defect discovery in the REST API confirms our risk register's top risk (`PR-01`, score 25) and shows strong fault-detection effectiveness of spec-driven EP/BVA + cross-workflow readbacks.
  - **Requirements Coverage:** **`100.0%` (`10 / 10` FRs)** covered by passing automated tests at both Unit and API/Integration levels (`228 / 228` tests passing).
  - **Reopen Rate:** `N/A (0 / 0 closed defects yet; fix PR scheduled in Phase 7)`.
- **Control Actions:**
  1. Proceed to Phase 5 (Area 3 — Muhammad Aun): author 6 use cases (2/member), automate all main/alt/exception flows in Playwright (Chromium), run task/error-guidance/keyboard tests, and run Lighthouse + `@axe-core/playwright` audits with 1-screen remediation.
  2. Proceed to Phase 6 (Area 3): execute Playwright >= 4 role checks, OWASP ZAP passive scan + 2 control reviews, `pip-audit`, Grafana k6 OSS benchmarks (1 & >= 5 VUs x 2 x 60s), and failure-and-recovery integration test.

---

### Week 3 Report (Phases 5–6 Execution — 2026-11-22)
- **Planned Milestones:** Complete Phase 5 (Area 3A — 6 use cases = 2/member, full Playwright E2E suite, task/error-guidance/keyboard navigation tests, Lighthouse + `@axe-core/playwright` before/after 1-screen remediation) and Phase 6 (Area 3B — Attack surface & access matrix, >= 4 Playwright role checks, OWASP ZAP passive scan + >= 2 security control reviews, `pip-audit`, 4 comparable >= 60s Grafana k6 OSS runs, controlled failure-and-recovery integration test).
- **Actual Progress:**
  - **Phase 5 (Area 3A — Muhammad Aun):**
    - Documented 6 complete Use Case specifications (`UC-01`..`UC-06`, 2 per member, each with preconditions, main flow, >= 2 alternative flows, >= 2 exception flows, and postconditions) in `docs/PHASE5_USE_CASES.md`.
    - Automated all 30 executable Use Case flows in Playwright Chromium (`tests/team/e2e/use_cases.spec.mjs`) asserting both UI rendering and SQLite postconditions via `scripts/e2e_db_helper.py`.
    - Automated 2 workflow usability tests (`USA-WF1-ERR-KBD`, `USA-WF2-TASK`) verifying business-rule error guidance, recovery, keyboard-only `Tab`/`ArrowDown`/`Enter` navigation & submission, and approval task completion.
    - Ran `@axe-core/playwright` and Google Lighthouse across 4 key screens (`/login/`, `/user_requests/access/`, `/create_access_request/`, `/edit_access_request/<id>/`), prioritizing 7 unique findings (`UA-01`..`UA-07`), remediated `NEMO/templates/requests/access_requests/access_request.html` (fixing Serious `link-name` + Moderate `landmark-one-main`/`region`), and verified before/after improvement (`axe`: `4 -> 1` on Create/Review with `0` Serious/Critical; Lighthouse Accessibility: `90 -> 91` Create, `86 -> 91` Review).
  - **Phase 6 (Area 3B — Muhammad Aun):**
    - Mapped attack surface & 2-role access matrix and passed **8 / 8 Playwright role checks** (`SEC-RBAC-01`..`SEC-RBAC-08`).
    - Executed OWASP ZAP (`ghcr.io/zaproxy/zaproxy:stable`) passive scan across 10 live Playwright workflow/security tests (`1` High `moment.js`, `15` Medium JS/CSP, `58` Low, `39` Informational; verified `sessionid` `HttpOnly` & `SameSite=Lax` + server-side role guards), and ran `pip-audit` across `82` Python distributions (`0` known CVEs).
    - Executed 4 comparable `65s` Grafana k6 OSS runs (`1vu_run1`: `p95=38.421ms`, `1vu_run2`: `p95=136.413ms`, `5vu_run1`: `p95=225.470ms`, `5vu_run2`: `p95=227.656ms`, all `0.00%` failures vs `<= 500ms` & `< 1%` targets).
    - Passed controlled `OperationalError` failure-and-recovery integration test (`tests/team/recovery/test_failure_and_recovery.py`) leaving `0` duplicate grant/request rows.
- **Schedule Variance:** On track — Phases 1 through 6 completed (`24/32` total checklist items `[x]`).
- **GQM Snapshot (Week 3):**
  - **Defect Density (Confirmed Test Findings):** `9` API weaknesses (`W-API-01..09`) + `7` usability/a11y findings (`UA-01..07`, `UA-01`/`UA-02` remediated on `access_request.html`) + `5` ZAP/security findings (`SEC-ZAP-01..05`) + `6` SonarQube smells/`1` hotspot across `access_requests.py` & UI templates (`21` total unique findings logged prior to Phase 7 GitHub Issues triage & Pareto). *Interpretation:* Cross-layer verification (unit + API + E2E + a11y + passive security) exposed both API rule-parity gaps (`PR-01`) and legacy UI/JS hygiene gaps (`PR-05`, `PR-08`, `PR-10`), while confirming `0` critical runtime crashes or performance threshold breaches (`EC-03`).
  - **Requirements Coverage:** **`100.0%` (`10 / 10` FRs)** verified across Unit (`74`), API (`154`), E2E (`30`), Usability (`2`), Security (`8`), and Recovery (`1`) = **`269` automated team tests**.
  - **Reopen Rate:** **`0.0%` (`0 / 2` UI accessibility fixes `UA-01`/`UA-02` reopened after re-audit & full E2E regression)**.
- **Control Actions:**
  1. Proceed to Phase 7 (Area 1 & Shared): configure strict GitHub Actions PR quality gate (SonarQube + pytest + Playwright + Cosmic Ray, zero escape hatches), log all defects in GitHub Issues with triage, complete 2 major RCAs (`5 Whys` + `Fishbone`) & Pareto analysis, deliver 1 documented Fix PR + 1 pipeline-blocked PR, and finalize Test Completion Report (`Release or Hold`).

---

### Week 4 (Phases 7 & 8: CI Quality Gate, Defects & RCAs, Test Completion & Final Packaging)
- **Status:** **COMPLETED** (Phases 7 & 8 completed; all 32 checklist items ticked `[x]`).
- **Accomplishments:**
  - Configured strict non-bypassable GitHub Actions PR quality gate (`.github/workflows/ci.yml`) running static linting, 230 Pytest tests, 40 Playwright browser tests, mutation testing, and evidence-justified threshold verification with zero escape hatches (no `continue-on-error`, no `|| true`).
  - Delivered and merged **PR #1 (Documented Fix PR)** fixing W-API-01 (`TemporaryPhysicalAccessRequestSerializer.validate()` buddy count enforcement) after proving failure before fix (`assert 200 == 400`) and green CI pass after fix.
  - Demonstrated **PR #2 (Pipeline-Blocked PR)** proving that intentional threshold breaches correctly block pull requests from merging.
  - Synchronized all 22 test-discovered defects to **GitHub Issues** (#3 through #24) with labels, milestones, severity, priority, and triage status.
  - Completed two comprehensive Root Cause Analyses (**5 Whys + Fishbone diagrams**) for W-API-01/03 and UA-01/02 with corrective and preventive actions.
  - Conducted **Pareto Analysis** proving that API Testing (40.9%) and Usability/A11y (31.8%) account for 72.73% of all project defects (80/20 rule).
  - Evaluated three-point PERT estimation ($152.66\text{ hrs}$) vs. actual effort ($159.0\text{ hrs}$, variance $+4.15\%$).
  - Delivered Test Completion Report with residual risk assessment and evidence-based **Conditional Release** decision meeting all 3 Exit Criteria.
  - Generated final submission artifacts: PDF report `Project_24I-3025_24I-3135_24P-3099_A.pdf` and zip archive `Project_24I-3025_24I-3135_24P-3099_A.zip` (preserving `.git`).
- **Schedule Variance:** **0 days** — Completed on schedule with 100% checklist items satisfied.
- **GQM Snapshot (Final Week 4):**
  - **Defect Density:** `22` defects discovered and triaged across `0.85` KLOC in-scope code = **`25.88 defects/KLOC`**.
  - **Requirements Coverage:** **`100.0%` (`10 / 10` FRs)** covered across **`270` automated team tests** (230 pytest + 40 Playwright).
  - **Reopen Rate:** **`0.0%` (`0 / 22` defects reopened)**.
- **Final Governance Statement:** All project quality targets achieved; repository audit confirms complete per-member Git commit history and zero fabrication.
