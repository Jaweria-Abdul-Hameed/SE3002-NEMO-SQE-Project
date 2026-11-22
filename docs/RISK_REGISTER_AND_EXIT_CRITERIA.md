# 5x5 Risk Register & Measurable Exit Criteria

**Project:** SE3002 Software Quality Engineering Final Project (Fall 2026)  
**Module:** NEMO Temporary Physical Access Requests

---

## 1. Risk Scoring Matrix (5x5: Likelihood x Impact)

- **Likelihood (L):** `1` Rare, `2` Unlikely, `3` Possible, `4` Likely, `5` Almost Certain
- **Impact (I):** `1` Negligible, `2` Minor, `3` Moderate, `4` Major, `5` Critical / Severe
- **Risk Bands:**
  - **Critical (15–25):** Exhaustive white-box + MCC/MC-DC + mutation + automated API/E2E + security/recovery verification; blocks release.
  - **High (10–14):** Targeted decision-table, state-transition, BVA, and cross-workflow automated verification.
  - **Medium (5–9):** Automated EP/usability/accessibility/load checks and static quality monitoring.
  - **Low (1–4):** Smoke checks and periodic monitoring.

---

## 2. Product Risks (>= 8 Required; 10 Logged)

| Risk ID | Risk Description & Module Location | L | I | Score | Level | Mapped Test Technique & Depth | Linked Exit Criterion |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **PR-01** | **DRF API bypasses form validation & approval side-effects:** `TemporaryPhysicalAccessRequestViewSet` (`NEMO/views/api.py:978`) exposes `ModelViewSet` directly without enforcing `access_requests_minimum_users`, future `start_time`, state-transition guards, or `create_temporary_access()` grant creation. | 5 | 5 | **25** | **Critical** | Automated API EP + 3-point BVA + state-transition tests + cross-workflow persistence readbacks (`tests/team/api/`), plus logged defect/RCA. | EC-01, EC-02 |
| **PR-02** | **Broken authorization / privilege escalation on edit, approve, or delete:** Unauthorized user edits/approves another user's request (`access_requests.py:111, 133`) or accesses/deletes requests across roles. | 3 | 5 | **15** | **Critical** | Complete MCC/MC-DC unit tests on `create_access_request` & `delete_access_request`; >= 4 Playwright role checks (`tests/team/security/`); OWASP ZAP passive scan. | EC-01, EC-02 |
| **PR-03** | **Invalid state transitions & post-decision mutation:** Editing or deleting `APPROVED`, `DENIED`, `EXPIRED`, or already `deleted=True` requests (note `delete_access_request` omits `deleted` check at `access_requests.py:171`). | 4 | 4 | **16** | **Critical** | State-transition unit & API tests covering every allowed + >= 1 disallowed transition from every state; Playwright exception-flow E2E checks. | EC-01 |
| **PR-04** | **Stale grant data or partial write during approval:** `create_temporary_access(access_request)` (`access_requests.py:138, 180`) creates `TemporaryPhysicalAccess` rows *before* `form.save()` commits edited fields, and lacks atomic rollback / idempotency protection on failure. | 3 | 5 | **15** | **Critical** | Controlled failure-and-recovery integration test (`tests/team/recovery/`) simulating DB/service fault; API idempotency & duplicate-grant readback assertions. | EC-01, EC-03 |
| **PR-05** | **CSRF / non-idempotent GET on state-changing delete endpoint:** `delete_access_request` (`access_requests.py:165`) is decorated with `@require_GET`, allowing state mutation via GET requests. | 4 | 3 | **12** | **High** | Security control review (`tests/team/security/`) + ZAP passive scan + Playwright role/delete verification; logged as security finding. | EC-02 |
| **PR-06** | **Buddy-count and time-window boundary defects:** Off-by-one errors in `other_users < minimum_total_users - 1` (`NEMO/forms.py:543`), `end_time <= start_time` (`NEMO/models.py:658`), or `start_time < timezone.now()` (`access_requests.py:126`). | 3 | 4 | **12** | **High** | 3-point BVA (`min-1, min, min+1`) in both unit tests and OpenAPI-driven API tests; custom business-rule mutation operators (`mutmut`). | EC-01 |
| **PR-07** | **Missing or delayed auto-expiration of past-due PENDING requests:** `mark_requests_expired()` (`access_requests.py:190`) only runs on `GET /access_requests/`, leaving stale `PENDING` requests open to API/direct-URL edits until list view loads. | 3 | 3 | **9** | **Medium** | Unit & API state-transition tests for expired boundaries; cross-workflow readback verification. | EC-01 |
| **PR-08** | **Accessibility & keyboard barriers on access request screens:** `access_request.html` / `access_requests.html` may lack ARIA/label associations, focus indicators, sufficient contrast, or keyboard-only submission on buddy autocomplete (`typeahead`). | 4 | 2 | **8** | **Medium** | Playwright keyboard-navigation & error-guidance tests (`tests/team/usability/`); Lighthouse + `@axe-core/playwright` audit before/after 1-screen fix. | EC-04 |
| **PR-09** | **Response latency degradation under concurrent request listing/creation:** Prefetch/N+1 queries in `access_requests()` (`access_requests.py:50-68` loops in Python calling `creator_and_other_users()` & `reviewers()` per row) may spike `p95` under concurrent VUs. | 3 | 3 | **9** | **Medium** | Grafana k6 OSS load benchmarks (1 VU & >= 5 VUs, 2x60s runs) comparing `p95` against 500 ms limit. | EC-03 |
| **PR-10** | **Vulnerable third-party Python dependencies:** Outdated Django, DRF, Pillow, or cryptography packages introducing known CVEs. | 2 | 4 | **8** | **Medium** | `pip-audit` automated dependency vulnerability scan over `venv/` packages with component/impact/remediation report. | EC-02 |

---

## 3. Project Risks (>= 2 Required; 3 Logged)

| Risk ID | Risk Description | L | I | Score | Level | Mitigation & Contingency Plan |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **PJ-01** | **External tool / environment setup delays (Docker SonarQube, ZAP, k6, Playwright):** Local Windows tool incompatibilities or daemon startup failures could block scheduled static, security, or load runs. | 3 | 4 | **12** | **High** | Pin reproducible versions in `venv/`, validate Docker images early in Phase 2, keep deterministic scripts in `scripts/`, and verify Linux CI parity in GitHub Actions. |
| **PJ-02** | **CI threshold miscalibration or test flakiness on PR gate:** Time-dependent (`timezone.now()`) assertions or overly strict initial thresholds could cause flaky PR blocks. | 3 | 3 | **9** | **Medium** | Freeze/offset test timestamps relative to `timezone.now() + timedelta(...)`, justify coverage & mutation thresholds from Phase 3 evidence, and ban `continue-on-error`/`|| true`. |
| **PJ-03** | **Uneven Git history or viva readiness gap among trio members:** One member committing all files or failing to rehearse shared artifacts risks viva deductions. | 2 | 5 | **10** | **High** | Enforce per-area Git authorship (Jaweria: Area 1; Mohsin: Area 2; Muhammad Aun: Area 3; all 3: shared), maintain `docs/HANDOFF_STATUS.md` & `docs/AI_USAGE_LOG.md`, and run Phase 8 mock viva drill. |

---

## 4. Measurable Exit / Release Criteria (>= 3 Required; >= 2 Tied to Highest Risks)

| Criterion ID | Category | Measurable Target | Linked Top Risks | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **EC-01** | Functional, Structural & Fault Detection | **100%** statement & branch coverage on `NEMO/views/access_requests.py` & `TemporaryPhysicalAccessRequestForm`; **100%** MC/DC pair coverage on critical decisions; **>= 85%** mutation score on business-rule module with **0** unaddressed killable mutants; **100%** of FR-01..FR-10 covered across unit, API, and E2E suites. | **PR-01 (25), PR-03 (16), PR-04 (15), PR-06 (12)** | `coverage.py` XML/HTML report, MCC/MC-DC truth tables, `mutmut` surviving-mutant log, Traceability Matrix, GitHub Actions CI run. |
| **EC-02** | Security & Authorization | **100%** pass on **>= 4** automated Playwright RBAC checks (`allowed` + `denied` across both roles); **0** unmitigated Critical/High OWASP ZAP passive or `pip-audit` findings lacking documented fix/control/risk acceptance; **0** CI escape hatches (`continue-on-error` / `|| true`). | **PR-01 (25), PR-02 (15), PR-05 (12), PR-10 (8)** | `tests/team/security/` Playwright output, OWASP ZAP passive report, `pip-audit` JSON/text report, `.github/workflows/*.yml`. |
| **EC-03** | Performance & Failure Recovery | Grafana k6 `p95 <= 500 ms` and unexpected failure rate `< 1.0%` across both `1 VU` and `>= 5 VUs` (2x60s runs each); controlled failure-and-recovery test leaves **0** partial/duplicate `TemporaryPhysicalAccess` or request records upon fault + retry. | **PR-04 (15), PR-09 (9)** | Raw k6 summary outputs (4 runs), `tests/team/recovery/` pytest output. |
| **EC-04** | Usability & Accessibility | **100%** pass on Playwright task-completion, error-guidance, and keyboard-only navigation tests; **0** Critical/Serious `@axe-core/playwright` violations on the remediated screen and measurable Lighthouse Accessibility score improvement (`After >= Before`). | **PR-08 (8)** | `tests/team/usability/` Playwright report, before/after Lighthouse & axe-core reports. |
