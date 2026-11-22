# AI Usage & Verification Log

**Course:** SE3002 — Software Quality Engineering (Fall 2026) — Section A  
**Group (Trio):** Jaweria Abdul Hameed (`24I-3025`), Mohsin Khan (`24I-3135`), Muhammad Aun (`24P-3099`)  

> Every generative AI interaction used during this project is disclosed below with tool, purpose, generated output summary, human verification/edits performed, and exact saved prompts.

---

## Log Entries

| ID | Date | Phase | Tool / Model | Purpose | Output Summary | Human Verification & Edits Applied |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AI-01** | 2026-11-21 | Phase 1 | Antigravity AI Assistant | Initialize NEMO baseline (`aa5ac6e20e4e35e6f67ab7d2133b8188679ae746`), create non-invasive SQLite local settings (`sqe_local/`), deterministic seed/reset scripts (`scripts/`), and isolated `tests/team/` structure. | Generated `sqe_local/settings.py`, `sqe_local/auth_backend.py`, `scripts/seed_synthetic_data.py`, `scripts/reset_local_db.py`, `pytest.ini`, `tests/team/unit/test_baseline_smoke.py`, and `docs/PHASE1_BASELINE_AND_SCOPE.md`. | Verified exact baseline commit via `git rev-parse HEAD`, reviewed `NEMO/views/access_requests.py`, `NEMO/forms.py`, `NEMO/models.py`, `NEMO/views/api.py`, and `NEMO/permissions.py` line-by-line, executed `scripts/reset_local_db.py` against SQLite, and verified smoke tests pass under `pytest tests/team`. |
| **AI-02** | 2026-11-21 | Phase 2 | Antigravity AI Assistant | Draft Phase 2 Living Test Plan with PERT three-point estimates, 5x5 Risk Register & Exit Criteria, Requirements Traceability Matrix, and Week 1 GQM Progress Report. | Generated `docs/TEST_PLAN.md`, `docs/RISK_REGISTER_AND_EXIT_CRITERIA.md`, `docs/TRACEABILITY_MATRIX.md`, and `docs/WEEKLY_GQM_REPORT.md`. | Cross-checked all risk IDs, line numbers, FRs, and business rules against NEMO source code; updated ownership/estimates for 3-member group (`24I-3025`, `24I-3135`, `24P-3099`) and Section A. |
| **AI-03** | 2026-11-22 | Phase 2 | Antigravity AI Assistant | Configure SonarQube 9.9.8 scan (`sonar-project.properties`, `.coveragerc`), fetch live metrics via `scripts/fetch_sonar_metrics.py`, and derive exact CFG + McCabe Cyclomatic Complexity for `create_access_request`. | Generated `sonar-project.properties`, `.coveragerc`, `scripts/fetch_sonar_metrics.py`, `docs/evidence/sonarqube_baseline_metrics.json`, and `docs/PHASE2_STATIC_ANALYSIS_AND_CFG.md`. | Executed real `coverage.py` + `sonar-scanner-cli` against `http://localhost:9090`, fixed Cobertura `<source>` path resolution, verified CFG node/edge/predicate math (`N=37, E=54, V(G)=19`) programmatically in Python, and compared against SonarQube (`complexity=51`, `cognitive_complexity=85`/`50`). |

---

## Saved Prompts Archive

### AI-01 Prompt (Phase 1 Setup)
```text
Execute the SE3002 Software Quality Engineering Final Project (Fall 2026, 120 marks) in c:\Users\Jaweria\Projects\SQE_Project on NEMO baseline commit aa5ac6e20e4e35e6f67ab7d2133b8188679ae746, completing Phases 1-2 in this session, keeping all team tests isolated in tests/team/, and logging genuine tool outputs and AI usage.
```
