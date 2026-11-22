# Phase 4: OpenAPI Specification, Automated EP/3-Point BVA Data Generation & API/Integration Testing

**Course:** SE3002 — Software Quality Engineering (Fall 2026) — Section A  
**Area 2 Owner:** Mohsin Khan (`24I-3135`, Git: `mohsinkhandevs`)  
**Tool Stack:** OpenAPI 3.0.3 (`PyYAML 6.0.4`), custom generator (`scripts/generate_api_test_data.py`), `pytest 9.2.0` + `requests 2.34.2` against local live Django/DRF server  
**Key Artifacts:**
- OpenAPI Specification: `openapi/temporary_physical_access_requests.yaml`
- Spec-Driven EP & 3-Point BVA Generator: `scripts/generate_api_test_data.py`
- Generated Test Dataset: `tests/team/api/generated_test_data.json`
- Two-Constraint Regeneration Demo: `scripts/demo_openapi_regeneration.py`, `openapi/temporary_physical_access_requests_two_constraints_demo.yaml`, `docs/evidence/openapi_regeneration_demo/`
- API & Integration Test Suites: `tests/team/api/test_api_ep_bva_generated.py` & `tests/team/api/test_api_integration_and_cross_workflow.py`
- Raw Execution Log: `docs/evidence/phase4_api_pytest_output.txt` (**154 / 154 passed in 21.29s**)

---

## 1. OpenAPI 3.0.3 Specification & Spec-Driven EP / 3-Point BVA Generator

The OpenAPI 3.0.3 contract (`openapi/temporary_physical_access_requests.yaml`) models all endpoints in our selected module:
- `GET /api/temporary_physical_access_requests/` (with query filters `id`, `creator`, `physical_access_level`, `status`, `reviewer`, `deleted`, `page`)
- `POST /api/temporary_physical_access_requests/` (`TemporaryPhysicalAccessRequestWrite`)
- `GET /api/temporary_physical_access_requests/{id}/` (`TemporaryPhysicalAccessRequestRead`)
- `PUT /api/temporary_physical_access_requests/{id}/` (`TemporaryPhysicalAccessRequestWrite`)
- `PATCH /api/temporary_physical_access_requests/{id}/` (`TemporaryPhysicalAccessRequestPatch`)
- `DELETE /api/temporary_physical_access_requests/{id}/`
- `GET /api/physical_access_levels/` (reference readback endpoint)

### Generator Capabilities (`scripts/generate_api_test_data.py`)
Running:
```powershell
.\venv\Scripts\python.exe scripts\generate_api_test_data.py --spec openapi\temporary_physical_access_requests.yaml --output tests\team\api\generated_test_data.json
```
dynamically parses any OpenAPI 3.0 YAML/JSON schema and emits:
- **46 Request-Body EP Cases** (every valid and invalid partition across all 10 fields; strictly one invalid value per test case).
- **52 Request-Body 3-Point BVA Cases** (`just below`, `exactly at`, `just above` every `minimum`, `maximum`, `minLength`, `maxLength`, `minItems`, `maxItems`, `x-min-offset-minutes`, `x-min-duration-minutes`, and `x-max-duration-hours` boundary).
- **85 Query & Path Parameter EP + 3-Point BVA Cases** across all declared parameters.
- **7 State-Transition Cases** (`3` allowed transitions from `PENDING`, `4` disallowed transitions from `APPROVED`, `DENIED`, `EXPIRED`).

---

## 2. Two-Constraint Regeneration Demo & Live Viva Adaptability

Executed via `.\venv\Scripts\python.exe scripts\demo_openapi_regeneration.py` (evidence in `docs/evidence/openapi_regeneration_demo/regeneration_diff.json` and `regeneration_pytest_effect.txt`):

| Constraint Changed in OpenAPI Spec | Baseline Value | Mutated Value | Regenerated Dataset Effect |
| :--- | :---: | :---: | :--- |
| `TemporaryPhysicalAccessRequestWrite.properties.other_users.minItems` | `1` (`min_users=2`) | `2` (`min_users=3`) | Baseline valid payload automatically updated `${buddy_user_ids:1} -> ${buddy_user_ids:2}`; 3-point BVA shifted `(0, 1, 2) -> (1, 2, 3)` buddies |
| `TemporaryPhysicalAccessRequestWrite.properties.description.maxLength` | `500` | `200` | 3-point BVA shifted `(499, 500, 501) -> (199, 200, 201)` characters |

**Live Test Consumption Proof:** Setting `$env:SQE_GENERATED_DATA_PATH = "docs\evidence\openapi_regeneration_demo\generated_after.json"` and running `pytest tests/team/api/test_api_ep_bva_generated.py -k "minItems or maxLength"` immediately executes all 6 shifted BVA cases (`1, 2, 3` buddies and `199, 200, 201` description length) without modifying a single line of test code. During the viva, given any updated OpenAPI spec, Mohsin can re-run `generate_api_test_data.py --spec <updated.yaml>` and re-execute `pytest tests/team/api` live.

---

## 3. API & Integration Coverage Summary (154 Automated Tests)

| Coverage Criterion | Test Count | Verification Scope |
| :--- | :---: | :--- |
| Request-Body Equivalence Partitioning (1 invalid value/test) | 46 | Requiredness, nullability, types, enums `[0,1,2,3]`, FKs, ISO dates, booleans, arrays + DB/API readback |
| Request-Body 3-Point BVA (`below`, `at`, `above`) | 52 | All numeric, length, buddy-count (`minItems`/`maxItems`), start-time offset, and duration limits |
| Query & Path Parameter EP + 3-Point BVA | 43 | `id`, `creator`, `physical_access_level`, `status`, `reviewer`, `deleted`, `page` (with `page_size`), path `{id}` (`0, -1, 999999, 1000000, "abc"`) |
| Authentication, RBAC & HTTP Method / Schema Criteria | 2 | Unauthenticated (`403`), invalid token (`403`), view-only `other_requester` (`200 GET`, `403 POST/PATCH/DELETE`), `405` on `PUT /collection/`, `200 OPTIONS`, full response schema validation, `/api/physical_access_levels/` readback |
| CRUD Idempotency & Repeated Requests | 1 | Repeated `PUT` (idempotent `200`, 0 duplicates), repeated `DELETE` (`204 -> 404`), repeated `POST` duplicate-creation weakness probe |
| State Transitions (Allowed + Disallowed per State) | 7 | `0->1`, `0->2`, `0->3` (allowed) + `1->0`, `1->2`, `2->1`, `3->1` (disallowed — exposes W-API-04) |
| Cross-Workflow Persistent State Readbacks (`WF-1 <-> WF-2`) | 2 | WF-1 API create -> WF-2 UI approve -> API/DB readback (`status=1`, `reviewer` set, `2` `TemporaryPhysicalAccess` rows) -> post-approval WF-1 edit rejected & API readback intact; API approval 0-grant gap & BOLA probe |
| OpenAPI 2-Constraint Regeneration Contract | 1 | Programmatic diff assertion on regenerated baseline & 3-point BVA cases |
| **Total Phase 4 API & Integration Suite** | **154** | **154 passed / 0 failed (21.29s)** |

---

## 4. Documented API Endpoint Weaknesses (Linked to Risk Register)

Real execution against NEMO v8.2.1 (`aa5ac6e20e4e35e6f67ab7d2133b8188679ae746`) confirmed that `NEMO`'s custom DRF `ModelSerializer` **does** invoke `model.full_clean()` (correctly rejecting `end_time <= start_time` with `400 Bad Request`), while exposing **9 genuine endpoint weaknesses**:

| ID | Weakness Description & Observed Evidence | Root Cause | Severity | Risk | Proposed Fix | Risk Register Link |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: |
| **W-API-01** | **API bypasses minimum buddy count (`BR-1`):** `POST` with `other_users: []` (`0` buddies when `access_requests_minimum_users=2`) succeeds with `200` and persists invalid request (`BVA3-other_users-minItems-below_minItems`). | Minimum-buddy validation lives exclusively in `TemporaryPhysicalAccessRequestForm.clean()` (`NEMO/forms.py:541-547`), not in `TemporaryPhysicalAccessRequestSerializer` or `TemporaryPhysicalAccessRequest.clean()`. | **High** | High | Move `access_requests_minimum_users` validation into `TemporaryPhysicalAccessRequestSerializer.validate()` (or shared service validator). | **PR-01 (25), PR-06 (12)** |
| **W-API-02** | **API accepts past `start_time` for non-reviewers (`BR-1`):** `POST` with `start_time = now - 55m` by `lab_user` succeeds with `200` (`BVA3-start_time-offset-below_min_offset`). | Future start-time guard exists only inside `create_access_request` view (`NEMO/views/access_requests.py:123-128`). | **High** | High | Enforce `start_time >= timezone.now()` in serializer `validate()` unless request user is an authorized area reviewer editing an existing request. | **PR-01 (25), PR-06 (12)** |
| **W-API-03** | **API allows arbitrary illegal state transitions (`BR-3`):** `PATCH` succeeds (`200`) for `APPROVED -> PENDING`, `APPROVED -> DENIED`, `DENIED -> APPROVED`, and `EXPIRED -> APPROVED` (`test_api_state_transitions_disallowed_exposes_weakness_w_api_04`). | `TemporaryPhysicalAccessRequestSerializer` uses `fields = "__all__"` with no state-machine guard on `status` updates. | **Critical** | Critical | Reject status transitions from non-`PENDING` states (`APPROVED`, `DENIED`, `EXPIRED`) or `deleted=True` in serializer `validate()`. | **PR-01 (25), PR-03 (16)** |
| **W-API-04** | **API approval never creates `TemporaryPhysicalAccess` grant records (`FR-07`):** Setting `status=1 (APPROVED)` via `PATCH` persists `APPROVED` while `TemporaryPhysicalAccess.objects.count() == 0`, diverging from UI approval (`2` grants). | `TemporaryPhysicalAccessRequestViewSet` inherits generic `ModelViewSet` without calling `create_temporary_access()` or notification helpers on `PENDING -> APPROVED`. | **Critical** | Critical | Override `perform_update()` (within `transaction.atomic()`) to invoke `create_temporary_access()` and notifications when transitioning `PENDING -> APPROVED`. | **PR-01 (25), PR-04 (15)** |
| **W-API-05** | **Broken Object-Level Authorization (BOLA) on API (`BR-4`):** `lab_user` (neither creator nor reviewer) can `PATCH` `other_requester`'s request to `APPROVED` and assign themselves as `reviewer` (`test_cross_workflow_api_approval_side_effect_gap_and_bola_weakness`). | `NEMO.permissions.DjangoModelPermissions` checks model-level permissions only, with no per-object `creator` / `reviewers()` permission class or queryset scoping. | **Critical** | Critical | Add DRF object-level permission class (`IsCreatorOrAreaReviewer`) and filter `get_queryset()` by role matching `access_requests()`. | **PR-02 (15)** |
| **W-API-06** | **API `DELETE` hard-deletes records instead of soft-deleting (`FR-05`):** `DELETE /api/temporary_physical_access_requests/{id}/` physically removes the DB row (even for `APPROVED`/`DENIED` requests), erasing audit history. | Inherited `DestroyModelMixin.perform_destroy()` calls `instance.delete()` instead of setting `deleted=True` on `PENDING` requests only. | **High** | High | Override `perform_destroy()` to require `status == PENDING` + creator ownership and set `deleted=True` (`save(update_fields=["deleted"])`). | **PR-03 (16)** |
| **W-API-07** | **Missing upper/lower input bounds on `description`, `other_users`, and duration (`BR-1`):** Empty `description` (`""`), oversized `description` (`501+` chars), `11` buddies, and `>168h` windows all return `200` (`BVA3-description-*`, `BVA3-other_users-maxItems-*`, `BVA3-end_time-maxDuration-*`). | Model uses unbounded `TextField` / `ManyToManyField` without serializer max-length, max-items, or max-duration validators. | **Medium** | Medium | Add explicit serializer length/count/duration bounds aligned with OpenAPI specification. | **PR-06 (12)** |
| **W-API-08** | **API accepts non-requestable `physical_access_level` (`allow_user_request=False`):** `POST` with `Cryo Vault Direct Only` (`allow_user_request=False`) succeeds with `200` (`API-XW-02`). | Serializer's `PrimaryKeyRelatedField` queries `PhysicalAccessLevel.objects.all()` instead of filtering `allow_user_request=True`. | **Medium** | Medium | Restrict `physical_access_level` serializer queryset to `PhysicalAccessLevel.objects.filter(allow_user_request=True)`. | **PR-01 (25)** |
| **W-API-09** | **Non-idempotent repeated `POST` + non-standard `200` status (`W-API-10`):** Duplicate identical `POST`s create duplicate DB rows (`id1 != id2`), and `NEMO/views/api.py:211` returns HTTP `200 OK` instead of REST-standard `201 Created`. | `NEMO.views.api.ModelViewSet.create()` omits `status=status.HTTP_201_CREATED` and performs no idempotency/duplicate window check. | **Low** | Medium | Return `status=status.HTTP_201_CREATED` on single-object `POST` and optionally reject overlapping identical pending requests or support `Idempotency-Key`. | **PR-04 (15)** |
