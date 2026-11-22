# Requirements Traceability Matrix

**Project:** SE3002 Software Quality Engineering Final Project (Fall 2026)  
**Module:** NEMO Temporary Physical Access Requests  
**Rule:** Team-written tests live exclusively in `tests/team/`. Upstream `NEMO/tests/` are excluded. Each executable case is counted once per test level.

---

## 1. Functional Requirements & Business Rules Traceability

| Req / Rule ID | Summary | Risk Link | Unit (`tests/team/unit/`) | API / Integration (`tests/team/api/`) | Browser E2E & Area 3 (`tests/team/e2e\|usability\|security\|recovery/`) | Current Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FR-01** | Lab User submits new access request in `PENDING` state | PR-01, PR-06 | `UT-AR-01..03` (Planned Phase 3) | `API-AR-01..04` (Planned Phase 4) | `E2E-UC1-01`, `USA-WF1-01` (Planned Phase 5); `test_access_requests_ui_and_api_baseline` (Smoke) | Baseline Smoke Verified |
| **FR-02** | Reject invalid buddy count, `end <= start`, or past `start_time` | PR-01, PR-06 | `UT-BR1-01..09` (Planned Phase 3) | `API-BVA-01..12` (Planned Phase 4) | `E2E-UC1-EXC-01..02`, `USA-ERR-01` (Planned Phase 5) | Planned |
| **FR-03** | Lab User sees only own/buddy non-deleted requests | PR-02 | `UT-VIS-01..04` (Planned Phase 3) | `API-FLT-01..03` (Planned Phase 4) | `E2E-UC1-ALT-01`, `SEC-RBAC-01..04` (Planned Phase 5–6) | Planned |
| **FR-04** | Creator edits own `PENDING` request | PR-02, PR-03 | `UT-EDIT-01..05` (Planned Phase 3) | `API-PUT-01..04` (Planned Phase 4) | `E2E-UC2-01` (Planned Phase 5) | Planned |
| **FR-05** | Creator soft-deletes own `PENDING` request (`deleted=True`) | PR-03, PR-05 | `UT-DEL-01..04` (Planned Phase 3) | `API-DEL-01..03` (Planned Phase 4) | `E2E-UC2-ALT-01`, `SEC-CTL-01` (Planned Phase 5–6) | Planned |
| **FR-06** | Reviewers see all `PENDING` requests for reviewed areas | PR-02 | `UT-REV-01..04` (Planned Phase 3) | `API-REV-01..02` (Planned Phase 4) | `E2E-UC3-01`, `SEC-RBAC-02` (Planned Phase 5–6) | Planned |
| **FR-07** | Reviewer approves `PENDING -> APPROVED` & creates `TemporaryPhysicalAccess` | PR-04 | `UT-APP-01..04` (Planned Phase 3) | `API-XW-01..03` (Planned Phase 4) | `E2E-UC3-01`, `REC-01` (Planned Phase 5–6) | Planned |
| **FR-08** | Reviewer denies `PENDING -> DENIED` with 0 grants created | PR-03, PR-04 | `UT-DEN-01..03` (Planned Phase 3) | `API-XW-04..05` (Planned Phase 4) | `E2E-UC4-01` (Planned Phase 5) | Planned |
| **FR-09** | Reject edits/deletions on `APPROVED`/`DENIED`/`EXPIRED`/`deleted` requests | PR-03 | `UT-ST-01..08` (Planned Phase 3) | `API-ST-01..06` (Planned Phase 4) | `E2E-UC4-EXC-01..02` (Planned Phase 5) | Planned |
| **FR-10** | Auto-expire past-due `PENDING` requests; DRF API permissions | PR-01, PR-07 | `UT-EXP-01..03` (Planned Phase 3) | `API-RBAC-01..05` (Planned Phase 4) | `SEC-RBAC-01..04`, `PERF-K6-01..04` (Planned Phase 6) | Baseline Smoke Verified |
| **BR-1** | Boundary/limit rules (buddy min, `end > start`, `start >= now`) | PR-06 | Phase 3 Unit + Custom Mutants | Phase 4 EP/3-Point BVA | Phase 5 Error Guidance E2E | Planned |
| **BR-2** | Multi-condition Boolean decisions (MCC + MC/DC) | PR-02 | Phase 3 MCC + MC/DC Pairs | Phase 4 Decision Table API | Phase 5–6 Role & Flow Checks | Planned |
| **BR-3** | State-transition rules (`PENDING -> APPROVED/DENIED/EXPIRED/deleted`) | PR-03 | Phase 3 State Transition Suite | Phase 4 Invalid Transition API | Phase 5 Exception Flows | Planned |
| **BR-4** | Role-based access permissions (Lab User vs Reviewer) | PR-02, PR-05 | Phase 3 Role Guard Tests | Phase 4 `DjangoModelPermissions` | Phase 6 Playwright >= 4 Role Checks | Planned |

---

## 2. Requirements Coverage Summary (Updated Per Phase)

- **Total Functional Requirements:** 10 (`FR-01` .. `FR-10`)
- **Total Business Rules:** 4 (`BR-1` .. `BR-4`)
- **Planned Phase 5 Use Cases (Trio = 2/member):** 6 use cases (`UC-01`..`UC-06`) mapped across `FR-01`..`FR-10`
- **Phase 2 Baseline Smoke Coverage:** 2/10 FRs partially exercised (`FR-01`, `FR-10`) via `tests/team/unit/test_baseline_smoke.py`; full structural, API, E2E, usability, security, performance, and recovery suites scheduled in Phases 3–6.
