# Project Completion & Handoff Status (All Phases 1–8 Complete)

**Last Updated:** 2026-11-22  
**Project:** SE3002 Software Quality Engineering Final Project (Fall 2026) — Section A  
**Public Team GitHub Repo:** `https://github.com/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project`  
**Target MIS:** NEMO v8.2.1 (`https://github.com/usnistgov/NEMO`, NIST Public Domain, Commit `aa5ac6e20e4e35e6f67ab7d2133b8188679ae746`)  
**Module Under Test:** Temporary Physical Access Requests  
**Group (Trio — 3 Members):**
- **Jaweria Abdul Hameed (`24I-3025`)** — Git: `Jaweria-Abdul-Hameed <jaweriahameed06@gmail.com>` — **Area 1 & Shared Lead**
- **Mohsin Khan (`24I-3135`)** — Git: `mohsinkhandevs <mohsinkhan.devs@gmail.com>` — **Area 2 Lead**
- **Muhammad Aun (`24P-3099`)** — Git: `m-aun-005 <muhammadaoun1786@gmail.com>` — **Area 3 Lead**

---

## 1. Project Phase Completion Summary

| Phase | Description | Ownership | Checklist Status | Key Evidence & Deliverables |
| :---: | :--- | :---: | :---: | :--- |
| **Phase 1** | MIS Selection, Baseline & Test Environment Setup | Trio | **COMPLETED** (`4/4 [x]`) | Baseline commit `aa5ac6e2`, `sqe_local/` settings, deterministic seed/reset scripts, 2 workflows, 10 FRs, 4 business rules (`docs/PHASE1_BASELINE_AND_SCOPE.md`). |
| **Phase 2** | Static Analysis, Living Test Plan, 5x5 Risk Register & GQM | Jaweria & Trio | **COMPLETED** (`4/4 [x]`) | SonarQube 9.9.8 scan (51 CC), hand CFG $N=37, E=54, V(G)=19$, Test Plan v1.2, 5x5 Risk Register (10 risks), 3 Exit Criteria, Week 1 GQM. |
| **Phase 3** | White-Box Unit Testing, Complete MCC/MC-DC & Mutation Analysis | Jaweria (Area 1) | **COMPLETED** (`4/4 [x]`) | 74 unit tests, 100% statement (212/212) & branch (60/60) coverage, complete MCC/MC-DC on D1–D5, Cosmic Ray (162 mutants, 100% equiv-adj), 4 custom operators (14/14 killed). |
| **Phase 4** | OpenAPI 3.0.3 Spec, Automated EP/BVA Generator & API Tests | Mohsin (Area 2) | **COMPLETED** (`4/4 [x]`) | OpenAPI 3.0.3 YAML, custom Python EP/3-point BVA generator (141 boundaries), 2-constraint dynamic regeneration demo, 155 API tests, 9 API weaknesses. |
| **Phase 5** | Use Cases, Playwright Chromium E2E, Usability & A11y Fix | Aun (Area 3) & Trio | **COMPLETED** (`4/4 [x]`) | 6 Use Cases (2/member), 30 Playwright E2E flows (UI + SQLite DB assertions), 2 usability/keyboard tests, axe-core/Lighthouse audits, 1-screen fix in `access_request.html` (violations 4&rarr;1, score 86&rarr;91). |
| **Phase 6** | Defensive Security, OWASP ZAP, k6 Performance & Recovery | Aun (Area 3) | **COMPLETED** (`4/4 [x]`) | Access matrix & 8 Playwright role checks, OWASP ZAP passive scan (113 alerts), pip-audit (82 packages, 0 CVEs), 4x65s k6 runs ($p95=227\text{ms} < 500\text{ms}$), fault-recovery test (0 duplicate grants). |
| **Phase 7** | Strict CI Quality Gate, Fix/Blocked PRs, Defects & Completion | Jaweria & Trio | **COMPLETED** (`4/4 [x]`) | Strict GitHub Actions CI gate (zero escape hatches), merged Fix PR #1, blocked PR #2, 22 GitHub Issues synced, 2 Major RCAs (5 Whys + Fishbone), Pareto chart, PERT effort comparison (+4.15% variance), Conditional Release decision. |
| **Phase 8** | Final Packaging, Integrity Audit & Viva Readiness | Trio (All) | **COMPLETED** (`4/4 [x]`) | Audit of all 3 member commits, complete 12-section PDF report `Project_24I-3025_24I-3135_24P-3099_A.pdf` (367 KB), repository zip `Project_24I-3025_24I-3135_24P-3099_A.zip` (195 MB, preserving `.git`), and Viva Defense guide (`docs/VIVA_DEFENSE_REHEARSAL_AND_LIVE_TASK.md`). |

---

## 2. Final Submission Deliverables

1. **Official PDF Report:**
   - **File Path:** `Project_24I-3025_24I-3135_24P-3099_A.pdf` (Workspace root)
   - **Size:** 367.2 KB (14-page publication-quality A4 PDF with vector diagrams and tables)
   - **Source HTML:** `docs/FINAL_PROJECT_REPORT.html`
2. **Official Repository ZIP Archive:**
   - **File Path:** `Project_24I-3025_24I-3135_24P-3099_A.zip` (Workspace root)
   - **Size:** 195.54 MB
   - **Git History Preserved:** Strictly includes complete `.git` directory (312 git files, verified commit history for Jaweria, Mohsin, and Aun).
3. **Public GitHub Repository:**
   - URL: `https://github.com/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project`
   - **Documented Fix PR #1 (Merged):** `https://github.com/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project/pull/1`
   - **Pipeline-Blocked PR #2 (Open for Viva Inspection):** `https://github.com/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project/pull/2`
   - **Defect Issues Catalog:** Issues #3 through #24 (`https://github.com/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project/issues`)

---

## 3. Overall Verified Quality Metrics

- **Total Automated Team Tests:** **`270 / 270` passed (100% pass rate)**
  - Pytest Suites (`tests/team/`): **230 tests** (74 White-box Unit + 155 REST API/Integration + 1 Fault Recovery)
  - Playwright Chromium Suites (`tests/team/`): **40 tests** (30 Use Case E2E flows + 2 Usability/Keyboard + 8 Security Role Checks)
  - Upstream tests: Strictly 0 counted (all isolated in `tests/team/`).
- **Code Coverage:** **100.0% Statement (212/212)** and **100.0% Branch (60/60)** on all in-scope access request logic.
- **Mutation Testing:** **100.0% Equivalent-Adjusted Mutation Score** (151/151 killable mutants killed; 11 proven equivalent); **14 / 14 Custom Business-Rule Mutants Killed (100%)**.
- **Performance:** 4x65s k6 steady-state benchmark runs: peak $p95 = 227.6\text{ ms} \ll 500\text{ ms}$ threshold; 0.00% HTTP failure rate.
- **Defensive Security & CVEs:** 8/8 Playwright role checks passed; OWASP ZAP passive scan completed; **0 known CVEs** across all 82 dependencies via `pip-audit`.
- **Accessibility:** 1-screen fix in `access_request.html` dropped axe-core violations from 4 to 1 (0 Serious) and improved Google Lighthouse score from 86 to 91.
- **Project Effort Variance:** PERT Expected $T_e = 152.66\text{ hrs}$ vs. Actual $159.0\text{ hrs}$ ($+4.15\%$ variance, well within $\sigma = 10.34\text{ hrs}$).
- **Release Decision:** **CONDITIONAL RELEASE (v8.2.1-sqe)** (All 3 Exit Criteria PASSED).

---

## 4. Reproducible Commands Reference

```powershell
# 1. Reset and Seed Synthetic Database
.\venv\Scripts\python.exe scripts\reset_local_db.py

# 2. Run All Pytest Suites (230 tests: Unit, API, Recovery)
.\venv\Scripts\python.exe -m pytest tests/team --reuse-db

# 3. Run Pytest with Statement and Branch Coverage
.\venv\Scripts\python.exe -m pytest tests/team/unit/ --cov=NEMO/views/access_requests.py --cov=NEMO/forms.py --cov-branch --cov-report=term-missing

# 4. Start Local NEMO Server (for Browser Tests)
$env:DJANGO_SETTINGS_MODULE = "sqe_local.settings"
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload

# 5. Run Playwright Chromium Suites (40 tests: E2E, Usability, Security)
npx.cmd playwright test tests/team/

# 6. Run OpenAPI Specification 2-Constraint Regeneration Demo
.\venv\Scripts\python.exe scripts\demo_openapi_regeneration.py

# 7. Run Cosmic Ray Custom Business-Rule Mutation Operators
.\venv\Scripts\python.exe scripts\run_custom_forms_mutation.py

# 8. Re-compile PDF Report and Package Submission Zip
.\venv\Scripts\python.exe scripts\generate_final_report_html.py
node scripts\compile_submission_pdf.mjs
.\venv\Scripts\python.exe scripts\package_submission_zip.py
```

---

## 5. Viva Defense Readiness
Refer to `docs/VIVA_DEFENSE_REHEARSAL_AND_LIVE_TASK.md` for complete rehearsal questions, per-member Q&A guidelines, and step-by-step instructions for executing the live business-rule mutation drill during the viva.
