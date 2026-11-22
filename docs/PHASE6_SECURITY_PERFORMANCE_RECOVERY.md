# Phase 6: Defensive Security, Performance Benchmarking & Failure Recovery

**Project:** SE3002 Software Quality Engineering Final Project (Fall 2026)  
**Target MIS:** NEMO v8.2.1 (`aa5ac6e20e4e35e6f67ab7d2133b8188679ae746`)  
**Area Owner:** Area 3 — Muhammad Aun (`24P-3099`)  
**Linked Risks:** `PR-02`, `PR-04`, `PR-05`, `PR-09`, `PR-10` | **Linked Exit Criteria:** `EC-02`, `EC-03`

---

## 1. Attack Surface Map & Two-Role Access Matrix

### In-Scope Attack Surface (Workflows 1 & 2)

| Surface / Route | HTTP Methods | Auth & Permission Guard | Persistent Records Read / Mutated |
| :--- | :--- | :--- | :--- |
| `/login/`, `/logout/` | `GET`, `POST` | Public login; POST-only logout + CSRF | Django `sessionid` cookie, `User` auth |
| `/user_requests/access/` | `GET` | `@login_required` (`NEMO/views/user_requests.py`) | Renders tab shell, triggers async `/access_requests/` |
| `/access_requests/` | `GET` | `@login_required`, `@require_GET` (`access_requests.py:43`) | Calls `mark_requests_expired()`; filters requests by role; deletes seen `Notification`s |
| `/create_access_request/` | `GET`, `POST` | `@login_required`, `@require_http_methods(["GET","POST"])` (`access_requests.py:88`) | Creates `PENDING` `TemporaryPhysicalAccessRequest`, `Notification`, email |
| `/edit_access_request/<id>/` | `GET`, `POST` | `@login_required`, POST ownership/reviewer + `PENDING`/`deleted` checks (`access_requests.py:106-112`) | Updates request; reviewer `approve_request` creates `TemporaryPhysicalAccess` grants |
| `/delete_access_request/<id>/` | `GET` *(weakness `PR-05`)* | `@login_required`, `@require_GET`, `creator == request.user`, `status == PENDING` (`access_requests.py:164-172`) | Soft-deletes (`deleted=True`), removes `Notification`s |
| `/export_access_requests/` | `GET` | `@user_office_or_manager_required`, `@require_GET` (`access_requests.py:251`) | Streams CSV of non-deleted `TemporaryPhysicalAccessRequest` rows |
| `/api/temporary_physical_access_requests/` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | DRF `SessionAuthentication` / `TokenAuthentication` + `DjangoModelPermissions` (`NEMO/views/api.py:978`) | Full CRUD on `TemporaryPhysicalAccessRequest` *(object-level & rule gaps logged in Phase 4 `W-API-01..09`)* |

### Two-Role Access Matrix

| Action / Resource | Anonymous | Lab User (`lab_user` / `other_requester`) | Facility Manager / Area Reviewer (`facility_reviewer` / `area_only_reviewer`) |
| :--- | :---: | :---: | :---: |
| Create `PENDING` access request (`/create_access_request/`) | **DENY** (302 `/login/`) | **ALLOW** | **ALLOW** |
| View own / buddy requests (`/access_requests/`) | **DENY** (302 `/login/`) | **ALLOW** (own/buddy only) | **ALLOW** (all reviewed-area + own requests) |
| Edit own `PENDING` request (`/edit_access_request/<id>/`) | **DENY** (302 `/login/`) | **ALLOW** | **ALLOW** (all reviewed-area `PENDING` requests) |
| Edit another user's `PENDING` request | **DENY** | **DENY** (`You are not allowed to edit this request.`) | **ALLOW** (if reviewer for area; else **DENY**) |
| Approve / Deny `PENDING` request (`approve_request` / `deny_request`) | **DENY** | **DENY** (decision key ignored; stays `PENDING`, 0 grants) | **ALLOW** (`PENDING -> APPROVED/DENIED`) |
| Soft-delete own `PENDING` request (`/delete_access_request/<id>/`) | **DENY** | **ALLOW** | **ALLOW** (own only) |
| Delete another user's `PENDING` request | **DENY** | **DENY** (HTTP 400) | **DENY** (HTTP 400 — `creator != request.user`) |
| Export CSV (`/export_access_requests/`) | **DENY** (302 `/login/`) | **DENY** (302 `/login/`) | **ALLOW** (Facility Manager / User Office) |

---

## 2. Automated Playwright Role Access Checks (8 Decisions — `>= 4` Required)

Executed in [`tests/team/security/role_checks.spec.mjs`](../tests/team/security/role_checks.spec.mjs) (`8 / 8 PASS`, raw log in [`docs/evidence/phase6/rbac_checks_evidence.json`](./evidence/phase6/rbac_checks_evidence.json)):

| Check ID | Role | Action Tested | Expected Result | Observed Result | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-RBAC-01** | Lab User (`lab_user`) | `POST /create_access_request/` | **ALLOWED** (`status=0`, DB persisted) | **ALLOWED** (`status=0`, persisted in SQLite) | `rbac_checks_evidence.json` |
| **SEC-RBAC-02** | Lab User (`lab_user`) | `POST /edit_access_request/<id>/` with injected `approve_request=Approve` | **DENIED** approval (`status` stays `0`, `0` grants) | **DENIED** approval (`status=0`, `reviewer=null`, `grants=0`) | `rbac_checks_evidence.json` |
| **SEC-RBAC-03** | Lab User (`other_requester`) | `POST /edit_access_request/<id>/` owned by `lab_user` | **DENIED** with error message; DB unchanged | **DENIED** (`"You are not allowed to edit this request."`) | `rbac_checks_evidence.json` |
| **SEC-RBAC-04** | Lab User (`lab_user`) | `GET /export_access_requests/` | **DENIED** (hidden in UI; direct request 302 `/login/`) | **DENIED** (`HTTP 302 -> /login/?next=/export_access_requests/`) | `rbac_checks_evidence.json` |
| **SEC-RBAC-05** | Facility Reviewer (`facility_reviewer`) | Approve `/edit_access_request/<id>/` + `GET /export_access_requests/` | **ALLOWED** (`status=1`, `2` grants, CSV HTTP 200) | **ALLOWED** (`status=1`, `grants=2`, HTTP 200) | `rbac_checks_evidence.json` |
| **SEC-RBAC-06** | Facility Reviewer (`facility_reviewer`) | `GET /delete_access_request/<id>/` owned by `lab_user` | **DENIED** (HTTP 400; `deleted=false`) | **DENIED** (HTTP 400; `deleted=false`) | `rbac_checks_evidence.json` |
| **SEC-RBAC-07** | Area Reviewer (`area_only_reviewer`) | Deny `/edit_access_request/<id>/` | **ALLOWED** (`status=2`, `0` grants) | **ALLOWED** (`status=2`, `reviewer=area_only_reviewer`, `grants=0`) | `rbac_checks_evidence.json` |
| **SEC-RBAC-08** | Anonymous | `GET /access_requests/` | **DENIED** (HTTP 302 `/login/`) | **DENIED** (`HTTP 302 -> /login/?next=/access_requests/`) | `rbac_checks_evidence.json` |

---

## 3. OWASP ZAP Passive Scan, Source-Corroborated Control Review & `pip-audit`

### A. Verified Security Controls (Source + Runtime Corroborated)
1. **Session Cookie & Timeout Controls (`sqe_local/settings.py:125-127`, `NEMO/middleware.py:64-99`):**
   - `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = "Lax"`, `CSRF_COOKIE_SAMESITE = "Lax"`, and `XFrameOptionsMiddleware` (`sqe_local/settings.py:60`) plus anti-clickjacking script in `base.html:17-35`.
   - OWASP ZAP passive scan flagged **0** `HttpOnly` violations on `sessionid` (only `csrftoken`, which Django intentionally leaves JS-readable unless `CSRF_COOKIE_HTTPONLY=True` and AJAX doesn't read `csrftoken`).
   - `SessionTimeout.process_view` (`NEMO/middleware.py:91-98`) explicitly returns `403 Forbidden` for timed-out AJAX calls and refreshes active sessions cleanly.
2. **Role & Decision Authorization Controls (`NEMO/views/access_requests.py:111, 133, 169, 251`, `NEMO/decorators.py:92-120`):**
   - Server-side `user in access_request.reviewers()` gate prevents privilege escalation even if a requester forges `approve_request` POST parameters (`SEC-RBAC-02` verified).
   - `@user_office_or_manager_required` blocks CSV exports from non-managers (`SEC-RBAC-04` verified).

### B. OWASP ZAP Passive Scan Findings (Proxied During Live Playwright Workflows)
Executed via [`scripts/run_zap_passive_scan.py`](../scripts/run_zap_passive_scan.py) (`ghcr.io/zaproxy/zaproxy:stable`, `10/10` Playwright security & usability specs proxied through `127.0.0.1:8090` -> `host.docker.internal:8000`). Summary: **1 High, 15 Medium, 58 Low, 39 Informational** (`113` total alert instances across `11` unique rules; full HTML/JSON archived in `docs/evidence/phase6/zap_passive_*`):

| Finding ID | Component | Evidence (ZAP / Source) | Likely Impact | Recommended Fix | Root Cause | Severity | Risk & Risk Register Link |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **SEC-ZAP-01** | Bundled JS `moment.min.js` | ZAP High (`CWE-1395`): `/static/moment.min.js` `v2.29.3` | Known ReDoS / path traversal CVEs in `moment < 2.29.4` if untrusted format strings are parsed. | Upgrade `moment.min.js` to `>= 2.29.4` (or migrate to `dayjs`/`Intl`). | Upstream NEMO 8.2.1 bundles legacy `moment.js` v2.29.3 in `NEMO/static/`. | **High** | Client-side ReDoS / CVE exposure -> **`PR-10`** |
| **SEC-ZAP-02** | Bundled JS `bootstrap.min.js` (`v3.4.1`) & `jquery.min.js` (`v2.1.3`) | ZAP Medium (`CWE-1395`): `/static/bootstrap/js/bootstrap.min.js`, `/static/jquery.min.js` | Legacy XSS / prototype-pollution CVEs in Bootstrap 3.4.1 tooltip/popover and jQuery 2.1.3. | Upgrade jQuery to `3.7.x` and Bootstrap to `5.x` (or sanitize all dynamic HTML). | Upstream NEMO 8.2.1 relies on Bootstrap 3 + jQuery 2.1.3 UI stack. | **Medium** | Client-side DOM XSS vector -> **`PR-10`** |
| **SEC-ZAP-03** | Missing `Content-Security-Policy` Header | ZAP Medium (`CWE-693`, x13): `Content Security Policy (CSP) Header Not Set` on HTML responses | Absence of CSP increases blast radius of any future reflected/stored XSS injection. | Configure `django-csp` policy (`default-src 'self'`, nonce-based scripts) after refactoring inline `onclick` handlers. | Upstream NEMO relies on inline `<script>` blocks and `onclick` attributes (`access_request.html`). | **Medium** | Unmitigated XSS execution scope -> **`PR-05`** |
| **SEC-ZAP-04** | State-Changing GET Endpoint (`/delete_access_request/<id>/`) | Source Review (`NEMO/views/access_requests.py:165` `@require_GET`, `access_requests_table.html:50`) & SonarQube Hotspot `S3752` | Cross-origin `<img>`/link CSRF or accidental browser prefetch could soft-delete a user's `PENDING` request if `SameSite=Lax` is bypassed/navigated. | Change `delete_access_request` to `@require_POST` with CSRF token form in `access_requests_table.html`. | Delete action implemented as `<a href=...>` GET link instead of POST form. | **High** | State-changing CSRF via GET -> **`PR-05`** |
| **SEC-ZAP-05** | `csrftoken` Cookie Missing `HttpOnly` & Static `X-Content-Type-Options` / `Server` Header | ZAP Low (`CWE-1004` x12 `Set-Cookie: csrftoken`, `CWE-693` x13, `CWE-497` x33) | Minor metadata leak (`WSGIServer/0.2`) and MIME-sniffing on dev static files; `csrftoken` readable by JS by Django default. | Serve static assets behind nginx/WhiteNoise with `X-Content-Type-Options: nosniff` and strip `Server` header in production; set `SESSION_COOKIE_SECURE=True` under TLS. | Local Django `runserver` serves static files directly over HTTP (`DEBUG=True`). | **Low** | Low local exposure; production nginx handles headers -> **`PR-05`** |

### C. Dependency Vulnerability Audit (`pip-audit 2.10.1`)
Executed `.\venv\Scripts\python.exe -m pip_audit --skip-editable -f json -o docs\evidence\phase6\pip_audit_report.json`:
- **Packages Audited:** **82** Python distributions in `venv/` (`80` pinned PyPI packages including `Django==5.2.18`, `djangorestframework==3.18.3`, `cryptography==50.0.2`, `pillow==13.0.0`, `requests==2.34.2`, `PyYAML==6.0.4`, `ldap3==2.9.1`, `django-auditlog==3.4.1`, `django-filter==26.2`, plus `2` editable local packages `nemo` & `sqe-nemo-mutators`).
- **Known CVEs Found:** **0 vulnerabilities found** (`EXIT: 0`). Full checked package list archived in [`docs/evidence/phase6/pip_audit_report.txt`](./evidence/phase6/pip_audit_report.txt).

---

## 4. Comparable Grafana k6 OSS Load Benchmarks

### Target Operation & Pre-Test Threshold Justification (`EC-03`, `PR-09`)
- **Operation Under Load:** `GET /access_requests/` (authenticated as `lab_user`), invoked asynchronously on every `/user_requests/access/` page load (`NEMO/views/access_requests.py:45-85`). It executes `mark_requests_expired()`, ORM `prefetch_related(...)`, role filtering, and notification cleanup.
- **Pre-Set Targets (Defined BEFORE Running k6):**
  - **`p95 <= 500 ms`:** Since `/access_requests/` is fetched interactively by users loading the Access Requests tab, keeping 95th-percentile server latency at or below 500 ms maintains responsive UI rendering without triggering perceived stalls or spinner hangs.
  - **Unexpected Failure Rate `< 1.0%`:** Read-only dashboard listing under normal concurrent lab load (`1 VU` and `5 VUs`) must complete reliably (`HTTP 200` with expected markup) with under 1% transient errors.

### Test Environment
- **Tool:** Grafana `k6.exe v2.4.0 (go1.26.11, windows/amd64)`
- **Host Machine:** Windows 11 (`10.0.26300-SP0`), Intel64 Family 6 Model 186 Stepping 2 (`20` logical CPUs), Python `3.12.0`, Django `5.2.18` `runserver --noreload`, SQLite (`sqe_nemo.db` reset via `e2e_db_helper.py reset` before each run).
- **Script:** [`tests/team/performance/access_requests_load.js`](../tests/team/performance/access_requests_load.js) (`constant-vus` scenario running `65s` steady-state per run — exceeding the `>= 60s` requirement).

### Four Comparable Runs (2x `1 VU`, 2x `5 VUs` — `>= 60s` Steady State Each)

| Run ID | Virtual Users | Steady Duration | Total Requests | Throughput (RPS) | Avg Latency (ms) | `p95` Latency (ms) | Unexpected Failure % | vs. `p95 <= 500 ms` & `< 1%` Targets |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **k6-1VU-R1** | `1` | `65s` | `514` | `7.892` | `26.587` | **`38.421`** | **`0.00%`** | **PASS** (92.3% headroom) |
| **k6-1VU-R2** | `1` | `65s` | `375` | `5.758` | `73.397` | **`136.413`** | **`0.00%`** | **PASS** (72.7% headroom) |
| **k6-5VU-R1** | `5` | `65s` | `1514` | `23.146` | `114.294` | **`225.470`** | **`0.00%`** | **PASS** (54.9% headroom) |
| **k6-5VU-R2** | `5` | `65s` | `1866` | `28.616` | `73.921` | **`227.656`** | **`0.00%`** | **PASS** (54.5% headroom) |

- **Interpretation & Risk Link (`PR-09`, `EC-03`):** All 4 runs met both `p95 <= 500 ms` and `< 1.0%` failure targets (`0` failed requests across `4,269` total requests). However, `p95` scales from `38–136 ms` (`1 VU`) to `225–228 ms` (`5 VUs`) under `runserver` + SQLite because `access_requests()` executes `mark_requests_expired()` on every GET plus Python-level loops over `creator_and_other_users()` / `reviewers()` (`PR-09`). Under much larger request histories (`1,000+` rows) or higher concurrency, moving expiration to a background cron/Celery task and pushing reviewer filtering into SQL `Q()` expressions is recommended.

---

## 5. Controlled Failure-and-Recovery Integration Test (`PR-04`, `EC-03`)

Implemented in [`tests/team/recovery/test_failure_and_recovery.py`](../tests/team/recovery/test_failure_and_recovery.py) (`1 / 1 PASSED` in `2.01s`):
1. **Setup:** Created a `PENDING` `TemporaryPhysicalAccessRequest` (`rec_lab_user` + buddy `rec_buddy_user`) for `Recovery Access Level`.
2. **Fault Injection:** Patched `NEMO.views.access_requests.TemporaryPhysicalAccess.objects.create` with a test double raising `django.db.OperationalError("Simulated database lock before grant write completes")` when `rec_reviewer` POSTs `approve_request`.
3. **Post-Failure Verification:** Confirmed `TemporaryPhysicalAccessRequest` remained in `status=PENDING (0)` with `reviewer=None`, `1` request row total, and `0` `TemporaryPhysicalAccess` grant rows persisted.
4. **Restore & Retry:** Exited the fault patch and retried the exact approval POST (`302` redirect).
5. **Final State & Zero-Duplicate Assertion:** Confirmed `status=APPROVED (1)`, `reviewer=rec_reviewer`, `1` request row total, and **exact `2` `TemporaryPhysicalAccess` rows** (`rec_buddy_user`, `rec_lab_user`) with **0 duplicates**; furthermore verified a repeated approval POST is rejected (`"Only pending requests can be modified."`) and creates **0** additional grants.
- **Note on `PR-04` Architectural Observation:** Because `create_access_request` (`NEMO/views/access_requests.py:137-144`) does not wrap `create_temporary_access(access_request)` and `form.save()` in `transaction.atomic()`, a failure *after* the first grant row is inserted (mid-loop) would leave orphaned `TemporaryPhysicalAccess` rows if non-atomic SQLite commits each `create()`. Wrapping lines 133-152 in `@transaction.atomic` is recommended as a hardening fix (`PR-04`).
