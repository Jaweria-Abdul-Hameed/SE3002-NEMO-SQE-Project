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
