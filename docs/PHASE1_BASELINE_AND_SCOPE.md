# Phase 1: MIS Selection, Reproducible Baseline & Scope Definition

**Course:** SE3002 — Software Quality Engineering (Fall 2026)  
**Section:** A  
**Group (Trio — 3 Members):**
- **Member 1:** Jaweria Abdul Hameed (`24I-3025`, GitHub: `Jaweria-Abdul-Hameed`) — **Area 1** (Static analysis, white-box unit testing, MCC/MC-DC, mutation analysis, CI quality gate)
- **Member 2:** Mohsin Khan (`24I-3135`, GitHub: `mohsinkhandevs`) — **Area 2** (OpenAPI specification, automated EP/3-point BVA data generator, API & integration testing)
- **Member 3:** Muhammad Aun (`24P-3099`, GitHub: `m-aun-005`) — **Area 3** (Use cases — 2/member = 6 total, Playwright E2E, usability & accessibility, defensive security, k6 performance & failure recovery)
- **Shared Ownership:** Test plan, 5x5 risk register, exit criteria, traceability matrix, defect/RCA management, weekly GQM reports, completion report, AI-use log

---

## 1. Selected Open-Source MIS & Registration Record

| Field | Value |
| :--- | :--- |
| **MIS Name** | NEMO (NanoFab Equipment Management and Operations) v8.2.1 |
| **Team GitHub Repo** | `https://github.com/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project` |
| **Upstream GitHub URL** | `https://github.com/usnistgov/NEMO` |
| **Licence** | NIST Software Licensing Statement (Public Domain — `LICENSE.md`) |
| **Exact Baseline Commit Hash** | `aa5ac6e20e4e35e6f67ab7d2133b8188679ae746` |
| **Technology Stack** | Python 3.12.0, Django 5.2.18, Django REST Framework 3.18.3, SQLite (`sqe_nemo.db`) |
| **Selected Module** | Temporary Physical Access Requests (`NEMO/views/access_requests.py`, `NEMO/forms.py`, `NEMO/models.py`, `NEMO/views/api.py`, `NEMO/serializers.py`) |
| **Browser UI Routes** | `/user_requests/access/`, `/access_requests/`, `/create_access_request/`, `/edit_access_request/<id>/`, `/delete_access_request/<id>/`, `/export_access_requests/` |
| **HTTP REST API Endpoint** | `/api/temporary_physical_access_requests/` and `/api/temporary_physical_access_requests/<id>/` |
| **Shared Sheet Registration** | Registered in Section `A` tab (`https://github.com/usnistgov/NEMO`) |

### Eligibility Verification
- **Browser UI:** Django server-rendered Bootstrap UI (`NEMO/templates/requests/access_requests/access_requests.html`, `access_request.html`, `access_requests_table.html`).
- **HTTP API:** DRF `TemporaryPhysicalAccessRequestViewSet` (`ModelViewSet`) registered at `router.register("temporary_physical_access_requests", api.TemporaryPhysicalAccessRequestViewSet)` in `NEMO/urls.py:101`.
- **Persistent Storage:** Relational persistence via Django ORM on SQLite (`NEMO_TemporaryPhysicalAccessRequest`, `NEMO_TemporaryPhysicalAccess`, `NEMO_Notification`, `NEMO_Customization`).
- **Testable Source Code:** Full Python/Django source tree with isolated team suites under `tests/team/`.

---

## 2. Reproducible Setup, Seed & Reset Instructions

### Prerequisites
- Python 3.12 (`python --version`)
- Git (`git --version`)

### One-Time Virtual Environment Setup (Windows PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -e . pytest pytest-django coverage requests pyyaml
```

### Database Initialization, Seeding & State Reset
The repository includes a committed, non-invasive local configuration package (`sqe_local/settings.py` and `sqe_local/auth_backend.py`) plus deterministic scripts in `scripts/`:

- **Reset DB to clean seeded state (with synthetic sample requests):**
  ```powershell
  .\venv\Scripts\python.exe scripts\reset_local_db.py
  ```
- **Reset DB to base accounts/areas only (no pre-existing requests):**
  ```powershell
  .\venv\Scripts\python.exe scripts\reset_local_db.py --no-samples
  ```
- **Re-seed / ensure synthetic records without deleting DB:**
  ```powershell
  .\venv\Scripts\python.exe scripts\seed_synthetic_data.py
  ```

### Start the Local NEMO Server
```powershell
$env:DJANGO_SETTINGS_MODULE = "sqe_local.settings"
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### Run Team Tests (Isolated from Upstream `NEMO/tests/`)
```powershell
.\venv\Scripts\python.exe -m pytest tests/team
```

### Synthetic Accounts & Test Data (`scripts/seed_synthetic_data.py`)
Default synthetic login password for all active test accounts (via `LocalSyntheticAuthBackend`, configurable with `SQE_LOCAL_TEST_PASSWORD`): `nemo-sqe-test-2026`.

| Username | Role / Purpose | Key Flags |
| :--- | :--- | :--- |
| `lab_user` | Workflow 1 Requester (Lab User) | `is_active=True`, `is_facility_manager=False`, API model perms for `temporaryphysicalaccessrequest` |
| `buddy_user` | Active Buddy User | `is_active=True`, listed as buddy in requests |
| `buddy_user_2` | Second Active Buddy User | `is_active=True`, used for minimum-user boundary > 2 |
| `other_requester` | Unrelated Lab User | `is_active=True`, `view_temporaryphysicalaccessrequest` API perm only |
| `facility_reviewer` | Workflow 2 Reviewer (Facility Manager) | `is_active=True`, `is_facility_manager=True`, `is_staff=True`, in `Cleanroom Bay A` reviewers |
| `area_only_reviewer` | Area-Specific Reviewer | `is_active=True`, `is_facility_manager=False`, in `Cleanroom Bay A` reviewers |
| `inactive_user` | Negative Auth Test Account | `is_active=False` |

Seeded Areas & Levels:
- `Cleanroom Bay A` -> `Cleanroom 24/7 Temporary Access` (`allow_user_request=True`, `schedule=ALWAYS`)
- `Cryo Vault B` -> `Cryo Vault Direct Only` (`allow_user_request=False`, `schedule=WEEKDAYS`)
- `UserRequestsCustomization`: `access_requests_minimum_users = "2"` (meaning at least `2 - 1 = 1` buddy user required).

---

## 3. Two Related Workflows & Shared Persistent State

### Workflow 1: Lab User — Submit, Edit, and Delete Temporary Access Request
- **Starting Condition:** `lab_user` is authenticated (`training_required=False`, `is_active=True`), at least one `PhysicalAccessLevel` has `allow_user_request=True`, at least one active facility manager exists, and `access_requests_minimum_users` is configured (default `2`).
- **User Actions:**
  1. Navigate to `/user_requests/access/` and click **New request** (`/create_access_request/`).
  2. Enter `start_time` (in the future), `end_time` (`> start_time`), select `physical_access_level`, select >= 1 buddy in `other_users`, enter `description`, and submit.
  3. While status remains `PENDING (0)`, open `/edit_access_request/<id>/` to modify fields and save, or click **Delete** (`/delete_access_request/<id>/`).
- **Expected Outcome:**
  - Create persists `TemporaryPhysicalAccessRequest` with `status=0 (PENDING)`, `creator=lab_user`, `last_updated_by=lab_user`, `deleted=False`, and creates `Notification` (`TEMPORARY_ACCESS_REQUEST`) for area reviewers.
  - Edit updates fields while keeping `status=0 (PENDING)`.
  - Delete sets `deleted=True` and removes associated notifications.

### Workflow 2: Facility Manager / Area Reviewer — Review, Approve, or Deny Request
- **Starting Condition:** `lab_user` has created a `PENDING` `TemporaryPhysicalAccessRequest` (`deleted=False`) for an area reviewed by `facility_reviewer` (or `area_only_reviewer`).
- **User Actions:**
  1. Reviewer navigates to `/user_requests/access/`, views Pending requests, and clicks **Review** (`/edit_access_request/<id>/`).
  2. Reviewer selects **Approve** (`approve_request` POST key) or **Deny** (`deny_request` POST key).
- **Expected Outcome:**
  - **Approve:** `TemporaryPhysicalAccessRequest.status` transitions `0 (PENDING) -> 1 (APPROVED)`, `reviewer` and `last_updated_by` are set to the reviewer, and `create_temporary_access()` inserts one `TemporaryPhysicalAccess` grant row per user in `{creator} | set(other_users)`. Reviewer notifications are cleared, creator/buddies are notified.
  - **Deny:** `TemporaryPhysicalAccessRequest.status` transitions `0 (PENDING) -> 2 (DENIED)`, `reviewer` is set, and **zero** `TemporaryPhysicalAccess` records are created.
  - Subsequent edits or deletions by any user on the `APPROVED` or `DENIED` request are rejected.

### Shared Persistent State Matrix

| Persistent Record / Model | Fields | Workflow 1 (Lab User) | Workflow 2 (Reviewer) |
| :--- | :--- | :--- | :--- |
| `TemporaryPhysicalAccessRequest` | `status`, `start_time`, `end_time`, `physical_access_level`, `other_users`, `reviewer`, `last_updated_by`, `deleted` | **Creates / Modifies / Soft-deletes** while `PENDING`; **Reads** updated `status` & `reviewer` to lock edits/deletes | **Reads** `PENDING` requests; **Modifies** `status` (`1`/`2`), `reviewer`, `last_updated_by` |
| `TemporaryPhysicalAccess` | `user`, `physical_access_level`, `start_time`, `end_time` | Indirectly **Consumes** granted physical access (and verifies no duplicate grants on deny/reject) | **Creates** on approval via `create_temporary_access()` |
| `Notification` | `user`, `notification_type`, `object_id` | **Creates** for reviewers on submit; **Deletes** own notifications on view or delete | **Deletes** reviewer notifications on decision; **Creates** update notification for creator/buddies |
| `Customization` (`requests`) | `access_requests_minimum_users` | **Reads** minimum total users during form validation (`clean()`) | **Reads** during review form validation (`clean()`) |

---

## 4. Functional Requirements, Roles, Business Rules & Test Basis

### Functional Requirements (>= 8 total, >= 3 per workflow)

| ID | Workflow | Requirement Description | Source Basis |
| :--- | :--- | :--- | :--- |
| **FR-01** | WF-1 | An authenticated Lab User shall be able to submit a new temporary physical access request specifying start time, end time, requestable access level, buddies, and description, persisting in `PENDING` status. | `NEMO/views/access_requests.py:90-154`, `NEMO/forms.py:532-548` |
| **FR-02** | WF-1 | The system shall reject a request submission or edit if the buddy count is below `access_requests_minimum_users - 1`, if `end_time <= start_time`, or if a non-reviewer submits `start_time < now`. | `NEMO/forms.py:541-547`, `NEMO/models.py:657-659`, `NEMO/views/access_requests.py:122-128` |
| **FR-03** | WF-1 | A Lab User shall only view non-deleted requests they created or are listed on as a buddy (`other_users`), grouped by Pending, Approved, Denied, and Expired. | `NEMO/views/access_requests.py:45-85` |
| **FR-04** | WF-1 | The creator of a `PENDING`, non-deleted request shall be able to edit its schedule, access level, buddies, and description while keeping status `PENDING`. | `NEMO/views/access_requests.py:102-154` |
| **FR-05** | WF-1 | The creator of a `PENDING` request shall be able to soft-delete it (`deleted=True`), removing it from active request lists and deleting related notifications. | `NEMO/views/access_requests.py:166-177` |
| **FR-06** | WF-2 | Facility managers and area-assigned `access_request_reviewers` shall see all `PENDING` requests for areas they review, plus their own/buddy requests, while non-reviewers are excluded. | `NEMO/views/access_requests.py:58-68`, `NEMO/models.py:650-655` |
| **FR-07** | WF-2 | An authorized reviewer shall be able to approve a `PENDING` request (`PENDING -> APPROVED`), recording `reviewer` and generating `TemporaryPhysicalAccess` records for the creator and every buddy. | `NEMO/views/access_requests.py:133-144, 180-187` |
| **FR-08** | WF-2 | An authorized reviewer shall be able to deny a `PENDING` request (`PENDING -> DENIED`), recording `reviewer` without creating any `TemporaryPhysicalAccess` grant records. | `NEMO/views/access_requests.py:139-144` |
| **FR-09** | WF-2 | Once a request is `APPROVED`, `DENIED`, `EXPIRED`, or `deleted=True`, the UI views shall reject subsequent modification or deletion attempts with validation/400 errors. | `NEMO/views/access_requests.py:106-112, 169-172` |
| **FR-10** | Shared / API | Loading the access requests page shall auto-expire past-due `PENDING` requests (`end_time < now -> EXPIRED`); authorized API clients shall access `/api/temporary_physical_access_requests/` subject to `DjangoModelPermissions`. | `NEMO/views/access_requests.py:46, 190-196`, `NEMO/views/api.py:978-996`, `NEMO/permissions.py:14-24` |

### User Roles (2 Distinct Roles)

| Role | Definition in NEMO | Permitted Actions | Restricted Actions |
| :--- | :--- | :--- | :--- |
| **Lab User (Requester)** | `is_active=True`, `is_facility_manager=False`, not in `area.access_request_reviewers` | Create requests; view own/buddy requests; edit/delete own `PENDING` requests; API access per assigned `DjangoModelPermissions` | Cannot approve/deny requests; cannot edit/delete other users' requests; cannot export CSV (`@user_office_or_manager_required`); cannot submit past `start_time` |
| **Facility Manager / Area Reviewer** | `is_active=True` and (`is_facility_manager=True` or user in `area.access_request_reviewers`) | View all requests for reviewed areas; edit `PENDING` requests (including past-`start_time` override); approve or deny `PENDING` requests; Facility Manager can export CSV | Cannot delete another user's request (`delete_access_request` checks `access_request.creator != request.user`); cannot modify/delete non-`PENDING` or `deleted=True` requests |

### Four Business Rules

1. **BR-1 (Boundary / Limit Rules):**
   - *Buddy minimum:* `len(other_users) >= quiet_int(UserRequestsCustomization.get("access_requests_minimum_users"), 2) - 1` (`NEMO/forms.py:541-547`). Default `access_requests_minimum_users = 2` requires `>= 1` buddy (`other_users` count 0 fails, 1 passes).
   - *Time ordering:* `end_time > start_time` (`TemporaryPhysicalAccessRequest.clean()` in `NEMO/models.py:658-659`). Equal or earlier `end_time` raises `ValidationError`.
   - *Future start time:* For new requests or non-reviewers, `start_time >= timezone.now()` (`NEMO/views/access_requests.py:123-128`).
2. **BR-2 (Multi-Condition Boolean Decisions):**
   - *Edit ownership/reviewer guard:* `edit and access_request.creator != user and user not in access_request.reviewers()` (`access_requests.py:111`).
   - *Start-time reviewer override:* `cleaned_data and (not edit or user not in access_request.reviewers()) and cleaned_data.get("start_time") < timezone.now()` (`access_requests.py:123-128`).
   - *List visibility filter:* `not user_is_reviewer and not user_is_staff` vs reviewer filtering `user not in access_request.creator_and_other_users() and user not in access_request.reviewers()` (`access_requests.py:58-68`).
   - *Review decision trigger:* `edit and user in access_request.reviewers()` combined with `approve_request` or `deny_request` in `request.POST` (`access_requests.py:133-141`).
3. **BR-3 (State-Transition Rules):**
   - Valid states: `PENDING (0)`, `APPROVED (1)`, `DENIED (2)`, `EXPIRED (3)`, plus soft-delete flag `deleted=True`.
   - Allowed transitions: `PENDING -> APPROVED` (reviewer approve), `PENDING -> DENIED` (reviewer deny), `PENDING -> EXPIRED` (`mark_requests_expired` when `end_time < now` and `deleted=False`), `PENDING -> deleted=True` (creator delete).
   - Disallowed transitions: Editing when `deleted=True` or `status != PENDING`; deleting when `status != PENDING`.
4. **BR-4 (Role-Based Access Permissions):**
   - View/Edit/Review permissions gated by `@login_required`, `creator` / `reviewers()` membership, and `@user_office_or_manager_required` on `csv_export`.
   - REST API `/api/temporary_physical_access_requests/` gated by `NEMO.permissions.DjangoModelPermissions` (`view_`, `add_`, `change_`, `delete_temporaryphysicalaccessrequest`).

### Defensible Test Basis & Documented Assumptions
All expected behaviors are anchored directly to NEMO v8.2.1 source code (`NEMO/views/access_requests.py`, `NEMO/forms.py`, `NEMO/models.py`, `NEMO/views/api.py`, `NEMO/serializers.py`, `NEMO/permissions.py`, `NEMO/templates/requests/access_requests/*.html`, `NEMO/views/customization.py`).  
**Documented Baseline Assumptions / Known Gaps to Probe in Testing:**
1. *Local authentication:* NEMO delegates auth to LDAP/Kerberos/RemoteUser in production; `sqe_local.auth_backend.LocalSyntheticAuthBackend` provides deterministic local password login against `NEMO.models.User` without altering upstream `NEMO/` auth code.
2. *DRF API vs Web View parity:* `TemporaryPhysicalAccessRequestViewSet` (`NEMO/views/api.py:978`) uses DRF's generic `ModelViewSet` and `TemporaryPhysicalAccessRequestSerializer` (`fields = "__all__"`), which invokes model `clean()` only if explicitly called by serializer validation (`ModelSerializer` in DRF does NOT call `full_clean()` automatically!) and does NOT invoke `TemporaryPhysicalAccessRequestForm.clean()` or `create_temporary_access()`. Testing will probe and document these exact API weaknesses rather than silently assuming parity.
3. *Delete HTTP method & `deleted` check:* `delete_access_request` (`NEMO/views/access_requests.py:165-177`) uses `@require_GET` and checks `status != PENDING` without checking `deleted=True`. This will be tested and logged as a defect/security finding in subsequent phases.

---

## 5. Member Ownership Matrix

| Area | Owner | Scope |
| :--- | :--- | :--- |
| **Area 1** | Jaweria Abdul Hameed (`24I-3025`) | SonarQube static analysis & CFG cyclomatic complexity, 100% statement/branch unit tests, MCC & MC/DC pairs, `mutmut`/custom mutation operators, GitHub Actions CI quality gate |
| **Area 2** | Mohsin Khan (`24I-3135`) | OpenAPI specification, spec-driven EP & 3-point BVA generator, 2-constraint regeneration demo, `pytest` + `Requests` API/integration tests & cross-workflow readbacks |
| **Area 3** | Muhammad Aun (`24P-3099`) | Use case specs (2/member = 6 total), Playwright (Chromium) E2E automation, task/keyboard navigation tests, Lighthouse + `@axe-core/playwright` audits & 1-screen fix, attack surface & access matrix, Playwright >= 4 role checks, OWASP ZAP passive scan + >= 2 controls, `pip-audit`, Grafana k6 OSS benchmarks, controlled failure-recovery test |
| **Shared** | All 3 Members | Baseline setup, Living Test Plan, 5x5 Risk Register, Exit Criteria, Traceability Matrix, GitHub Issues & RCAs, Weekly GQM reports, Test Completion Report, AI-Use Log, Final PDF/ZIP |
