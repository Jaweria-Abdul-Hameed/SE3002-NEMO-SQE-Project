# Phase 5: Complete Use Case Specifications (2 Per Member = 6 Total)

**Project:** SE3002 Software Quality Engineering Final Project (Fall 2026)  
**Target MIS:** NEMO v8.2.1 (`aa5ac6e20e4e35e6f67ab7d2133b8188679ae746`)  
**Module:** Temporary Physical Access Requests (`NEMO/views/access_requests.py`)  
**Area Owner:** Area 3 — Muhammad Aun (`24P-3099`), with 2 Use Cases derived per group member (`UC-01`..`UC-06`)

---

## Use Case Allocation Across Group Members

| UC ID | Member Owner | Roll No. | Use Case Title | Linked FRs & Business Rules | Risk Link |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UC-01** | Jaweria Abdul Hameed | `24I-3025` | Lab User Submits a New Temporary Physical Access Request | `FR-01`, `FR-02`, `BR-1`, `BR-2` | `PR-06` |
| **UC-02** | Jaweria Abdul Hameed | `24I-3025` | Lab User Views Status Buckets & Edits a Pending Access Request | `FR-03`, `FR-04`, `FR-09`, `BR-2`, `BR-3` | `PR-02`, `PR-03` |
| **UC-03** | Mohsin Khan | `24I-3135` | Lab User Soft-Deletes a Pending Access Request | `FR-05`, `FR-09`, `BR-3`, `BR-4` | `PR-03`, `PR-05` |
| **UC-04** | Mohsin Khan | `24I-3135` | Facility Manager / Area Reviewer Approves a Pending Access Request | `FR-06`, `FR-07`, `BR-2`, `BR-3`, `BR-4` | `PR-02`, `PR-04` |
| **UC-05** | Muhammad Aun | `24P-3099` | Facility Manager / Area Reviewer Denies a Pending Access Request | `FR-06`, `FR-08`, `FR-09`, `BR-2`, `BR-3` | `PR-02`, `PR-03` |
| **UC-06** | Muhammad Aun | `24P-3099` | Auto-Expiration of Past-Due Requests & Facility Manager CSV Export | `FR-09`, `FR-10`, `BR-3`, `BR-4` | `PR-07`, `PR-02` |

---

## UC-01: Lab User Submits a New Temporary Physical Access Request
- **Owner:** Jaweria Abdul Hameed (`24I-3025`)
- **Primary Actor:** Lab User (`lab_user`)
- **Linked Requirements & Rules:** `FR-01`, `FR-02`, `BR-1` (buddy minimum, `end_time > start_time`, `start_time >= now`), `BR-2`
- **Preconditions:**
  1. `lab_user` is authenticated (`is_active=True`, `training_required=False`).
  2. At least one requestable `PhysicalAccessLevel` (`Cleanroom 24/7 Temporary Access`, `allow_user_request=True`) and active buddy user (`buddy_user`) exist.
  3. `UserRequestsCustomization.access_requests_minimum_users` is configured (default `2`, requiring `>= 1` buddy).
- **Main Flow (`UC-01-MAIN`):**
  1. Lab User navigates to `/user_requests/access/` and clicks **New request** (`/create_access_request/`).
  2. Lab User enters a valid future `start_time` and `end_time` (`end_time > start_time`), selects `Cleanroom 24/7 Temporary Access`, types `Sara Ahmed` in the buddy search field and selects `buddy_user`, and enters a description.
  3. Lab User clicks **Create access request**.
  4. System validates form fields and business rules, persists `TemporaryPhysicalAccessRequest` (`status=PENDING`, `creator=lab_user`, `deleted=False`), creates `Notification` records for area reviewers, and redirects to `/user_requests/access/` displaying the new request in the **Pending** table.
- **Alternative Flows:**
  - **UC-01-ALT-1 (Multiple Buddies & Raised Minimum Threshold):** When `access_requests_minimum_users = 3`, Lab User adds 2 buddies (`buddy_user` and `buddy_user_2`) via the autocomplete input; submission succeeds and persists both buddies in `other_users`.
  - **UC-01-ALT-2 (Buddy Visibility on Dashboard):** After `lab_user` submits a request listing `buddy_user`, `buddy_user` logs in and navigates to `/user_requests/access/`; the shared request appears in `buddy_user`'s **Pending** list without Edit/Delete buttons (read-only buddy view).
- **Exception Flows:**
  - **UC-01-EXC-1 (Insufficient Buddies — Boundary Violation `BR-1`):** Lab User submits the form with 0 buddies selected; system rejects submission, remains on `/create_access_request/`, renders `"You need at least 1 other buddy for this request"` (`NEMO/forms.py:546`), and persists zero new rows.
  - **UC-01-EXC-2 (Past `start_time` or `end_time <= start_time`):** Lab User submits a `start_time` in the past (or `end_time <= start_time`); system stays on `/create_access_request/`, displays field error `"The start time must be later than the current time"` (or `"The end time must be later than the start time"`), and persists zero new rows.
- **Postconditions:**
  - On `MAIN` / `ALT-1`: A new `TemporaryPhysicalAccessRequest` exists in SQLite with `status=0 (PENDING)`, `deleted=False`, `creator=lab_user`, expected `other_users`, and `0` `TemporaryPhysicalAccess` grant rows.
  - On `EXC-1` / `EXC-2`: Request count in SQLite is unchanged.

---

## UC-02: Lab User Views Status Buckets & Edits a Pending Access Request
- **Owner:** Jaweria Abdul Hameed (`24I-3025`)
- **Primary Actor:** Lab User (`lab_user`)
- **Linked Requirements & Rules:** `FR-03`, `FR-04`, `FR-09`, `BR-2` (edit authorization guard `D1`), `BR-3`
- **Preconditions:**
  1. `lab_user` is authenticated and owns a `PENDING`, non-deleted `TemporaryPhysicalAccessRequest`.
  2. Additional `APPROVED` / `DENIED` requests exist for visibility filtering verification.
- **Main Flow (`UC-02-MAIN`):**
  1. Lab User opens `/user_requests/access/` and verifies status buckets (`Pending`, `Approved`).
  2. Lab User clicks **Edit** on their `PENDING` request (`/edit_access_request/<id>/`).
  3. Lab User updates `description` (and/or `end_time`) and clicks **Save changes**.
  4. System validates ownership and `PENDING` status, updates the existing record keeping `status=PENDING` and `last_updated_by=lab_user`, and redirects to `/user_requests/access/` showing the updated description.
- **Alternative Flows:**
  - **UC-02-ALT-1 (Visibility Isolation for Unrelated Lab User):** Unrelated `other_requester` opens `/user_requests/access/` and sees only their own/buddy requests (`FR-03`); `lab_user`'s requests are excluded from `other_requester`'s rendered tables.
  - **UC-02-ALT-2 (Reviewer Edits Pending Request Without Decision):** `area_only_reviewer` opens `/edit_access_request/<id>/`, updates description, and saves without pressing Approve/Deny; request remains `PENDING` with `last_updated_by=area_only_reviewer`.
- **Exception Flows:**
  - **UC-02-EXC-1 (Unauthorized Edit Attempt by Non-Creator Non-Reviewer):** `other_requester` navigates directly to `/edit_access_request/<id>/` and submits a POST edit; system rejects with `"You are not allowed to edit this request."` and DB fields remain unchanged.
  - **UC-02-EXC-2 (Edit Attempt on Non-Pending Request `APPROVED`):** `lab_user` attempts to submit a POST edit to an already `APPROVED` request URL; system rejects with `"Only pending requests can be modified."` and DB remains locked in `APPROVED`.
- **Postconditions:**
  - On `MAIN`: Existing record is updated in place (`status=0`, `last_updated_by=lab_user`, no duplicate request created).
  - On `EXC-1` / `EXC-2`: Target `TemporaryPhysicalAccessRequest` attributes and `status` remain unmodified in SQLite.

---

## UC-03: Lab User Soft-Deletes a Pending Access Request
- **Owner:** Mohsin Khan (`24I-3135`)
- **Primary Actor:** Lab User (`lab_user`)
- **Linked Requirements & Rules:** `FR-05`, `FR-09`, `BR-3`, `BR-4`
- **Preconditions:**
  1. `lab_user` is authenticated and owns a `PENDING` `TemporaryPhysicalAccessRequest` (`deleted=False`).
- **Main Flow (`UC-03-MAIN`):**
  1. Lab User navigates to `/user_requests/access/`.
  2. Lab User clicks **Delete** on their `PENDING` request and accepts the browser confirmation dialog.
  3. System invokes `/delete_access_request/<id>/`, sets `deleted=True`, removes `TEMPORARY_ACCESS_REQUEST` notifications for that request, and redirects to `/user_requests/access/`.
  4. The deleted request no longer appears in the **Pending** table.
- **Alternative Flows:**
  - **UC-03-ALT-1 (Cancel Confirmation Dialog):** Lab User clicks **Delete** and dismisses (`Cancel`) the confirmation dialog; browser stays on `/user_requests/access/`, request remains visible, and `deleted=False` in SQLite.
  - **UC-03-ALT-2 (Deleted Request Hidden from Reviewer Queue):** After `lab_user` confirms deletion, `facility_reviewer` opens `/user_requests/access/` and verifies the soft-deleted request does not appear in the reviewer's Pending queue.
- **Exception Flows:**
  - **UC-03-EXC-1 (Non-Creator Delete Attempt):** `other_requester` (or even `facility_reviewer`, per `NEMO/views/access_requests.py:169`) navigates directly to `/delete_access_request/<id>/`; system returns HTTP `400 Bad Request` (`"You are not allowed to delete a request you didn't create."`) and `deleted` stays `False`.
  - **UC-03-EXC-2 (Delete Attempt on Approved Request):** `lab_user` navigates directly to `/delete_access_request/<approved_id>/`; system returns HTTP `400 Bad Request` (`"You are not allowed to delete a request that is not pending."`) and `deleted` stays `False`.
- **Postconditions:**
  - On `MAIN`: `TemporaryPhysicalAccessRequest.deleted == True`, `status == 0`, and `Notification` count for that `object_id` is `0`.
  - On `ALT-1`, `EXC-1`, `EXC-2`: `deleted == False` and request remains intact in SQLite.

---

## UC-04: Facility Manager / Area Reviewer Approves a Pending Access Request
- **Owner:** Mohsin Khan (`24I-3135`)
- **Primary Actor:** Facility Manager (`facility_reviewer`) or Area Reviewer (`area_only_reviewer`)
- **Linked Requirements & Rules:** `FR-06`, `FR-07`, `BR-2` (`D3` reviewer decision gate & `D2` start-time override), `BR-3`, `BR-4`
- **Preconditions:**
  1. `lab_user` has submitted a `PENDING` request (`deleted=False`) for `Cleanroom 24/7 Temporary Access` with buddy `buddy_user`.
  2. Reviewer is logged in (`facility_reviewer` or `area_only_reviewer`).
- **Main Flow (`UC-04-MAIN`):**
  1. Reviewer opens `/user_requests/access/` and sees the `PENDING` request in the **Pending** table with a **Review** action link.
  2. Reviewer clicks **Review** (`/edit_access_request/<id>/`), verifies the **Creator** read-only field, and clicks **Approve** (`approve_request`) confirming the dialog.
  3. System sets `status=APPROVED (1)`, `reviewer=facility_reviewer`, `last_updated_by=facility_reviewer`, creates `TemporaryPhysicalAccess` grant records for `{lab_user, buddy_user}`, clears reviewer notifications, and redirects to `/user_requests/access/` showing the request under **Approved** with reviewer name.
- **Alternative Flows:**
  - **UC-04-ALT-1 (Area-Only Reviewer Approval):** `area_only_reviewer` (`is_facility_manager=False`, `is_staff=False`, listed in `Cleanroom Bay A` `access_request_reviewers`) logs in and approves a `PENDING` request; approval succeeds and generates grants identically to Facility Manager.
  - **UC-04-ALT-2 (Reviewer Approves Request Whose Start Time Has Passed Before Review `BR-2`):** When a `PENDING` request's `start_time < now` (but `end_time > now`), `facility_reviewer` approves it; reviewer start-time override (`D2`) allows approval without past-`start_time` validation failure.
- **Exception Flows:**
  - **UC-04-EXC-1 (Non-Reviewer Submits `approve_request` POST Flag):** `lab_user` (creator, not a reviewer) opens `/edit_access_request/<id>/` and crafts/submits a POST containing `approve_request=1`; system ignores the approval flag (`D3`: `user not in reviewers()`), keeps `status=PENDING`, and creates `0` `TemporaryPhysicalAccess` grants.
  - **UC-04-EXC-2 (Re-Reviewing an Already Approved Request):** Reviewer navigates to `/edit_access_request/<approved_id>/`; UI hides Approve/Deny buttons and direct POST is rejected (`"Only pending requests can be modified."`) with zero duplicate `TemporaryPhysicalAccess` grants created.
- **Postconditions:**
  - On `MAIN` / `ALT-1` / `ALT-2`: `status=1 (APPROVED)`, `reviewer` populated, and `TemporaryPhysicalAccess` rows exist for creator and every buddy (`grants_count == 1 + len(other_users)`).
  - On `EXC-1`: `status=0 (PENDING)`, `grants_count == 0`.
  - On `EXC-2`: No additional `TemporaryPhysicalAccess` rows added.

---

## UC-05: Facility Manager / Area Reviewer Denies a Pending Access Request
- **Owner:** Muhammad Aun (`24P-3099`)
- **Primary Actor:** Facility Manager (`facility_reviewer`) / Area Reviewer (`area_only_reviewer`)
- **Linked Requirements & Rules:** `FR-06`, `FR-08`, `FR-09`, `BR-2`, `BR-3`
- **Preconditions:**
  1. A `PENDING` request exists for `Cleanroom 24/7 Temporary Access` with `lab_user` + `buddy_user`.
- **Main Flow (`UC-05-MAIN`):**
  1. Reviewer navigates to `/user_requests/access/` and clicks **Review** on the `PENDING` request.
  2. Reviewer clicks **Deny** (`deny_request`) and confirms the dialog.
  3. System transitions `status` from `PENDING (0)` to `DENIED (2)`, sets `reviewer`, creates **zero** `TemporaryPhysicalAccess` records, and redirects to `/user_requests/access/` displaying the request in the **Denied** table.
- **Alternative Flows:**
  - **UC-05-ALT-1 (Requester Observes Denied Outcome in UI):** After denial, `lab_user` logs in and navigates to `/user_requests/access/`; the request appears under **Denied** showing `Dr. Nadia Siddiqui` in the **Denied by** column with no Edit/Delete controls.
  - **UC-05-ALT-2 (Cancel Confirmation Dialog on Deny):** Reviewer clicks **Deny** and dismisses the browser confirmation dialog; request stays on the edit screen in `PENDING` state with `0` status changes.
- **Exception Flows:**
  - **UC-05-EXC-1 (Requester Attempts to Edit After Denial):** `lab_user` sends POST to `/edit_access_request/<denied_id>/`; system rejects with `"Only pending requests can be modified."` and `status` stays `DENIED (2)`.
  - **UC-05-EXC-2 (Requester Attempts to Delete After Denial):** `lab_user` navigates to `/delete_access_request/<denied_id>/`; system returns HTTP `400 Bad Request` (`"You are not allowed to delete a request that is not pending."`) and `deleted` stays `False`.
- **Postconditions:**
  - On `MAIN` / `ALT-1`: `status=2 (DENIED)`, `reviewer=facility_reviewer`, and `TemporaryPhysicalAccess` grant count for this request window is `0`.
  - On `ALT-2`: `status=0 (PENDING)`.
  - On `EXC-1` / `EXC-2`: `status=2 (DENIED)`, `deleted=False`.

---

## UC-06: Auto-Expiration of Past-Due Pending Requests & Facility Manager CSV Export
- **Owner:** Muhammad Aun (`24P-3099`)
- **Primary Actor:** Facility Manager (`facility_reviewer`) & Lab User (`lab_user`)
- **Linked Requirements & Rules:** `FR-09`, `FR-10`, `BR-3`, `BR-4`
- **Preconditions:**
  1. A `PENDING` request exists whose `end_time < timezone.now()` (`deleted=False`).
  2. Active non-deleted requests exist for CSV export.
- **Main Flow (`UC-06-MAIN`):**
  1. `facility_reviewer` navigates to `/user_requests/access/`.
  2. System executes `mark_requests_expired()`, transitions the past-due `PENDING` request to `EXPIRED (3)`, deletes pending notifications, and renders the request under the **Expired** section.
  3. `facility_reviewer` clicks **Export** (`/export_access_requests/`); system returns `text/csv` attachment (`Access_requests_<timestamp>.csv`) containing header columns (`Status`, `Created date`, ..., `Reviewer`) and active non-deleted rows.
- **Alternative Flows:**
  - **UC-06-ALT-1 (Lab User Triggers Expiration on Own Dashboard):** `lab_user` opens `/user_requests/access/` when a past-due `PENDING` request exists; `mark_requests_expired()` moves it to **Expired** and **Export** button is hidden from `lab_user`'s UI (`FR-10`, `BR-4`).
  - **UC-06-ALT-2 (Soft-Deleted Past-Due Request Excluded from Auto-Expire & CSV):** A soft-deleted (`deleted=True`) past-due request stays `deleted=True` (not transitioned by `mark_requests_expired()` and excluded from `/export_access_requests/` CSV output).
- **Exception Flows:**
  - **UC-06-EXC-1 (Lab User Accesses `/export_access_requests/` Directly):** `lab_user` navigates directly to `/export_access_requests/`; `@user_office_or_manager_required` blocks access (HTTP `400 Bad Request` / `403` error response) and serves zero CSV data.
  - **UC-06-EXC-2 (Edit Attempt on Auto-Expired Request):** `lab_user` attempts to edit the now-`EXPIRED` request at `/edit_access_request/<expired_id>/`; system rejects with `"Only pending requests can be modified."` and `status` stays `EXPIRED (3)`.
- **Postconditions:**
  - On `MAIN`: Past-due request has `status=3 (EXPIRED)` in SQLite and CSV response contains valid rows excluding `deleted=True` records.
  - On `EXC-1`: HTTP `400` returned to non-manager.
  - On `EXC-2`: `status=3 (EXPIRED)` preserved.
