"""Phase 4 API & Integration Suite: RBAC, HTTP Methods, Schema, State Transitions, Idempotency & Cross-Workflow Readbacks.

Area 2 Owner: Mohsin Khan (24I-3135)
Covers:
  - API coverage criteria (all HTTP methods, status codes 200/204/400/401-403/404/405, schema contract)
  - Role-based API permissions (BR-4: unauthenticated, invalid token, view-only, lab_user, facility_reviewer)
  - Business-rule rejections & state transitions (allowed + disallowed from every state)
  - Repeated requests / idempotency (POST duplicate weakness vs PUT/DELETE idempotency)
  - Cross-workflow shared persistent state readbacks (UI <-> API <-> DB across Workflow 1 & Workflow 2)
  - Two-constraint OpenAPI regeneration contract verification
"""

from pathlib import Path

import pytest
import requests
from django.urls import reverse
from django.utils import timezone

from NEMO.models import RequestStatus, TemporaryPhysicalAccess, TemporaryPhysicalAccessRequest
from scripts.generate_api_test_data import generate_dataset
from tests.team.api.conftest import (
    auth_headers,
    build_resolved_baseline,
    extract_list_items,
    load_generated_data,
)

DATASET = load_generated_data()
CREATE_SUCCESS_STATUS = 200  # NEMO ModelViewSet.create returns 200 OK (W-API-10)
REQUIRED_READ_FIELDS = {
    "id",
    "creation_time",
    "creator",
    "last_updated",
    "last_updated_by",
    "physical_access_level",
    "description",
    "start_time",
    "end_time",
    "other_users",
    "status",
    "reviewer",
    "deleted",
}


# =============================================================================
# 1. Authentication, RBAC (BR-4) & HTTP Method / Schema Coverage
# =============================================================================


def test_api_authentication_and_rbac_matrix(api_server, api_env):
    """API-RBAC-01..05 (FR-10/BR-4): Unauth/bad token rejected; view-only user blocked on writes; schema verified."""
    base_url = f"{api_server.url}/api/temporary_physical_access_requests/"
    payload, _, _ = build_resolved_baseline(DATASET, api_env)

    # 1. Unauthenticated -> 403 (SessionAuthentication precedes TokenAuthentication in DRF config)
    r_unauth = requests.get(base_url, timeout=15)
    assert r_unauth.status_code in (401, 403)

    # 2. Invalid token -> 401/403 rejected
    r_bad_tok = requests.get(base_url, headers=auth_headers("0000000000000000000000000000000000000000"), timeout=15)
    assert r_bad_tok.status_code in (401, 403)

    # 3. View-only user (`other_requester`) -> GET 200, POST 403 Forbidden (0 records created!)
    view_headers = auth_headers(api_env["tokens"]["other_requester"])
    assert requests.get(base_url, headers=view_headers, timeout=15).status_code == 200
    r_forbid_post = requests.post(base_url, json=payload, headers=view_headers, timeout=15)
    assert r_forbid_post.status_code == 403
    assert TemporaryPhysicalAccessRequest.objects.count() == 0

    # 4. Lab user with model perms -> POST succeeds (200 in NEMO), schema matches OpenAPI Read schema
    lab_headers = auth_headers(api_env["tokens"]["lab_user"])
    r_create = requests.post(base_url, json=payload, headers=lab_headers, timeout=15)
    assert r_create.status_code == CREATE_SUCCESS_STATUS
    created = r_create.json()
    assert REQUIRED_READ_FIELDS.issubset(created.keys())
    detail_url = f"{base_url}{created['id']}/"

    # 5. View-only user still blocked from PUT/PATCH/DELETE -> 403, persisted state unchanged!
    assert requests.patch(detail_url, json={"description": "Blocked"}, headers=view_headers, timeout=15).status_code == 403
    assert requests.delete(detail_url, headers=view_headers, timeout=15).status_code == 403
    assert TemporaryPhysicalAccessRequest.objects.get(id=created["id"]).description == payload["description"]

    # 6. Unsupported HTTP method on collection (PUT /collection/) -> 405 Method Not Allowed
    assert requests.put(base_url, json=payload, headers=lab_headers, timeout=15).status_code == 405

    # 7. OPTIONS supported -> 200
    assert requests.options(base_url, headers=lab_headers, timeout=15).status_code == 200


def test_api_physical_access_levels_readback_endpoint(api_server, api_env):
    """Verify reference endpoint /api/physical_access_levels/ requires auth and returns seeded levels."""
    url = f"{api_server.url}/api/physical_access_levels/"
    assert requests.get(url, timeout=15).status_code in (401, 403)

    from django.contrib.auth.models import Permission

    perm = Permission.objects.get(codename="view_physicalaccesslevel")
    api_env["users"]["facility_reviewer"].user_permissions.add(perm)
    headers = auth_headers(api_env["tokens"]["facility_reviewer"])

    resp = requests.get(url, params={"allow_user_request": "true"}, headers=headers, timeout=15)
    assert resp.status_code == 200
    results = extract_list_items(resp.json())
    assert any(item["id"] == api_env["cleanroom_level_id"] for item in results)


# =============================================================================
# 2. Full CRUD Lifecycle, Idempotency & Repeated Requests
# =============================================================================


def test_api_crud_put_patch_delete_idempotency_and_duplicate_post_weakness(api_server, api_env):
    """API-IDEM-01: Verify PUT/DELETE idempotency and probe repeated POST duplicate-creation weakness (W-API-09)."""
    base_url = f"{api_server.url}/api/temporary_physical_access_requests/"
    headers = auth_headers(api_env["tokens"]["lab_user"])
    payload, _, _ = build_resolved_baseline(DATASET, api_env)

    # Repeated identical POSTs: document weakness W-API-09 (no idempotency guard -> creates 2 distinct IDs)
    r1 = requests.post(base_url, json=payload, headers=headers, timeout=15)
    r2 = requests.post(base_url, json=payload, headers=headers, timeout=15)
    assert r1.status_code == CREATE_SUCCESS_STATUS and r2.status_code == CREATE_SUCCESS_STATUS
    id1, id2 = r1.json()["id"], r2.json()["id"]
    assert id1 != id2
    assert TemporaryPhysicalAccessRequest.objects.count() == 2

    # Repeated identical PUT on id1 -> strictly idempotent (status 200, still 2 total rows, same fields)
    updated_payload = dict(payload, description="Idempotent PUT update")
    put1 = requests.put(f"{base_url}{id1}/", json=updated_payload, headers=headers, timeout=15)
    put2 = requests.put(f"{base_url}{id1}/", json=updated_payload, headers=headers, timeout=15)
    assert put1.status_code == 200 and put2.status_code == 200
    assert put1.json()["description"] == put2.json()["description"] == "Idempotent PUT update"
    assert TemporaryPhysicalAccessRequest.objects.count() == 2

    # Repeated DELETE on id2 -> first returns 204, second returns 404 (idempotent, no extra deletions)
    del1 = requests.delete(f"{base_url}{id2}/", headers=headers, timeout=15)
    del2 = requests.delete(f"{base_url}{id2}/", headers=headers, timeout=15)
    assert del1.status_code == 204
    assert del2.status_code == 404
    assert TemporaryPhysicalAccessRequest.objects.count() == 1
    # Note W-API-06: API DELETE performed hard delete rather than soft-delete (deleted=True)
    assert not TemporaryPhysicalAccessRequest.objects.filter(id=id2).exists()


# =============================================================================
# 3. State Transitions (Allowed + Disallowed per State) via API
# =============================================================================


@pytest.mark.parametrize(
    "transition",
    DATASET["state_transitions"]["allowed"],
    ids=[f"allowed-{t['from']}-to-{t['to']}" for t in DATASET["state_transitions"]["allowed"]],
)
def test_api_state_transitions_allowed(api_server, api_env, transition):
    """API-ST-ALLOWED: Every allowed state transition from OpenAPI spec succeeds via PATCH and persists."""
    base_url = f"{api_server.url}/api/temporary_physical_access_requests/"
    rev_headers = auth_headers(api_env["tokens"]["facility_reviewer"])
    payload, _, _ = build_resolved_baseline(DATASET, api_env)
    payload["status"] = transition["from"]

    created = requests.post(base_url, json=payload, headers=rev_headers, timeout=15).json()
    patch_resp = requests.patch(
        f"{base_url}{created['id']}/",
        json={"status": transition["to"], "reviewer": api_env["facility_reviewer_id"]},
        headers=rev_headers,
        timeout=15,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == transition["to"]
    refreshed = TemporaryPhysicalAccessRequest.objects.get(id=created["id"])
    assert refreshed.status == transition["to"]


@pytest.mark.parametrize(
    "transition",
    DATASET["state_transitions"]["disallowed"],
    ids=[f"disallowed-{t['from']}-to-{t['to']}" for t in DATASET["state_transitions"]["disallowed"]],
)
def test_api_state_transitions_disallowed_exposes_weakness_w_api_04(api_server, api_env, transition):
    """API-ST-DISALLOWED (W-API-04 / PR-03): Documents that NEMO DRF allows invalid state transitions."""
    base_url = f"{api_server.url}/api/temporary_physical_access_requests/"
    rev_headers = auth_headers(api_env["tokens"]["facility_reviewer"])
    payload, _, _ = build_resolved_baseline(DATASET, api_env)
    payload["status"] = transition["from"]

    created = requests.post(base_url, json=payload, headers=rev_headers, timeout=15).json()
    patch_resp = requests.patch(
        f"{base_url}{created['id']}/",
        json={"status": transition["to"]},
        headers=rev_headers,
        timeout=15,
    )
    # Upstream weakness W-API-04: DRF ModelViewSet accepts illegal state mutation with 200 instead of 400
    assert patch_resp.status_code == 200
    assert TemporaryPhysicalAccessRequest.objects.get(id=created["id"]).status == transition["to"]


# =============================================================================
# 4. Cross-Workflow Persistent State Readbacks (WF-1 <-> WF-2, UI <-> API)
# =============================================================================


def test_cross_workflow_wf1_api_create_then_wf2_ui_approve_and_readback(api_server, api_env):
    """API-XW-01 (FR-01, FR-07, FR-09): WF-1 creates via API -> WF-2 approves via UI -> API & DB readback."""
    base_url = f"{api_server.url}/api/temporary_physical_access_requests/"
    lab_headers = auth_headers(api_env["tokens"]["lab_user"])
    payload, _, _ = build_resolved_baseline(DATASET, api_env)
    payload["description"] = "Cross-workflow API-to-UI approval"

    # Workflow 1: Lab User submits request via REST API
    create_resp = requests.post(base_url, json=payload, headers=lab_headers, timeout=15)
    assert create_resp.status_code == CREATE_SUCCESS_STATUS
    req_id = create_resp.json()["id"]
    assert TemporaryPhysicalAccess.objects.count() == 0

    # Workflow 2: Facility Manager logs in via browser session & approves through UI view
    session = requests.Session()
    login_url = f"{api_server.url}{reverse('login')}"
    session.get(login_url, timeout=15)
    csrftoken = session.cookies["csrftoken"]
    login_post = session.post(
        login_url,
        data={
            "username": "facility_reviewer",
            "password": "nemo-sqe-test-2026",
            "csrfmiddlewaretoken": csrftoken,
        },
        headers={"Referer": login_url},
        timeout=15,
    )
    assert login_post.status_code == 200

    req_obj = TemporaryPhysicalAccessRequest.objects.get(id=req_id)
    edit_url = f"{api_server.url}{reverse('edit_access_request', args=[req_id])}"
    session.get(edit_url, timeout=15)
    csrftoken = session.cookies["csrftoken"]
    fmt = "%Y-%m-%d %H:%M:%S"
    approve_resp = session.post(
        edit_url,
        data={
            "csrfmiddlewaretoken": csrftoken,
            "physical_access_level": req_obj.physical_access_level_id,
            "start_time": timezone.localtime(req_obj.start_time).strftime(fmt),
            "end_time": timezone.localtime(req_obj.end_time).strftime(fmt),
            "other_users": [api_env["buddy_user_ids"][0]],
            "description": req_obj.description,
            "approve_request": "",
        },
        headers={"Referer": edit_url},
        allow_redirects=False,
        timeout=15,
    )
    assert approve_resp.status_code == 302

    # Cross-workflow readback via REST API & DB: status=APPROVED, reviewer set, 2 grants created!
    readback = requests.get(f"{base_url}{req_id}/", headers=lab_headers, timeout=15)
    assert readback.status_code == 200
    rb_json = readback.json()
    assert rb_json["status"] == RequestStatus.APPROVED
    assert rb_json["reviewer"] == api_env["facility_reviewer_id"]
    assert TemporaryPhysicalAccess.objects.count() == 2

    # Post-approval rejection readback: WF-1 UI edit attempt on APPROVED request is rejected & state stays intact
    lab_session = requests.Session()
    lab_session.get(login_url, timeout=15)
    lab_session.post(
        login_url,
        data={
            "username": "lab_user",
            "password": "nemo-sqe-test-2026",
            "csrfmiddlewaretoken": lab_session.cookies["csrftoken"],
        },
        headers={"Referer": login_url},
        timeout=15,
    )
    lab_session.get(edit_url, timeout=15)
    rejected_edit = lab_session.post(
        edit_url,
        data={
            "csrfmiddlewaretoken": lab_session.cookies["csrftoken"],
            "physical_access_level": req_obj.physical_access_level_id,
            "start_time": timezone.localtime(req_obj.start_time).strftime(fmt),
            "end_time": timezone.localtime(req_obj.end_time).strftime(fmt),
            "other_users": [api_env["buddy_user_ids"][0]],
            "description": "Tampered after approval",
        },
        headers={"Referer": edit_url},
        timeout=15,
    )
    assert rejected_edit.status_code == 200
    assert "Only pending requests can be modified." in rejected_edit.text
    # Read back via API after rejection: original description and APPROVED status preserved!
    after_reject = requests.get(f"{base_url}{req_id}/", headers=lab_headers, timeout=15).json()
    assert after_reject["status"] == RequestStatus.APPROVED
    assert after_reject["description"] == "Cross-workflow API-to-UI approval"
    assert TemporaryPhysicalAccess.objects.count() == 2


def test_cross_workflow_api_approval_side_effect_gap_and_bola_weakness(api_server, api_env):
    """API-XW-02 (W-API-04, W-API-05, W-API-08): Proves API approval skips grants, lacks object-level auth, & allows non-requestable level."""
    base_url = f"{api_server.url}/api/temporary_physical_access_requests/"
    rev_headers = auth_headers(api_env["tokens"]["facility_reviewer"])
    lab_headers = auth_headers(api_env["tokens"]["lab_user"])

    # W-API-08: API accepts physical_access_level with allow_user_request=False
    payload, _, _ = build_resolved_baseline(DATASET, api_env)
    payload["creator"] = api_env["other_requester_id"]
    payload["physical_access_level"] = api_env["non_requestable_level_id"]
    created = requests.post(base_url, json=payload, headers=rev_headers, timeout=15)
    assert created.status_code == CREATE_SUCCESS_STATUS
    req_id = created.json()["id"]

    # W-API-05 (BOLA / PR-02): lab_user (NOT creator, NOT reviewer) can PATCH another user's request to APPROVED via API!
    bola_patch = requests.patch(
        f"{base_url}{req_id}/",
        json={"status": RequestStatus.APPROVED, "reviewer": api_env["lab_user_id"]},
        headers=lab_headers,
        timeout=15,
    )
    assert bola_patch.status_code == 200
    assert bola_patch.json()["status"] == RequestStatus.APPROVED

    # W-API-04 (PR-01 / PR-04): Despite status=APPROVED via API, ZERO TemporaryPhysicalAccess grant records were created!
    assert TemporaryPhysicalAccess.objects.count() == 0


# =============================================================================
# 5. OpenAPI Two-Constraint Regeneration Verification (Viva Adaptability)
# =============================================================================


def test_openapi_two_constraint_regeneration_produces_updated_bva_and_payload():
    """API-GEN-01: Proves changing 2 OpenAPI constraints regenerates updated EP/BVA datasets deterministically."""
    root = Path(__file__).resolve().parents[3]
    base_spec = root / "openapi" / "temporary_physical_access_requests.yaml"
    mutated_spec = root / "openapi" / "temporary_physical_access_requests_two_constraints_demo.yaml"

    before = generate_dataset(base_spec)
    after = generate_dataset(mutated_spec)

    assert before["meta"]["spec_sha256_16"] != after["meta"]["spec_sha256_16"]
    assert before["baseline_valid_payload"]["other_users"] == "${buddy_user_ids:1}"
    assert after["baseline_valid_payload"]["other_users"] == "${buddy_user_ids:2}"

    before_bva = {c["case_id"]: c for c in before["body_bva_cases"]}
    after_bva = {c["case_id"]: c for c in after["body_bva_cases"]}

    assert [
        before_bva["BVA3-other_users-minItems-below_minItems"]["item_count"],
        before_bva["BVA3-other_users-minItems-at_minItems"]["item_count"],
        before_bva["BVA3-other_users-minItems-above_minItems"]["item_count"],
    ] == [0, 1, 2]
    assert [
        after_bva["BVA3-other_users-minItems-below_minItems"]["item_count"],
        after_bva["BVA3-other_users-minItems-at_minItems"]["item_count"],
        after_bva["BVA3-other_users-minItems-above_minItems"]["item_count"],
    ] == [1, 2, 3]

    assert [
        before_bva["BVA3-description-maxLength-below_maxLength"]["length"],
        before_bva["BVA3-description-maxLength-at_maxLength"]["length"],
        before_bva["BVA3-description-maxLength-above_maxLength"]["length"],
    ] == [499, 500, 501]
    assert [
        after_bva["BVA3-description-maxLength-below_maxLength"]["length"],
        after_bva["BVA3-description-maxLength-at_maxLength"]["length"],
        after_bva["BVA3-description-maxLength-above_maxLength"]["length"],
    ] == [199, 200, 201]


def test_w_api_01_api_rejects_below_minimum_buddy_count_with_400(api_server, api_env):
    """Documented Fix PR Test (W-API-01 / BR-1):
    Assert that POST /api/temporary_physical_access_requests/ with empty other_users
    (0 buddies when access_requests_minimum_users=2) is rejected with HTTP 400 Bad Request.
    FAILS before fix in TemporaryPhysicalAccessRequestSerializer.validate(), PASSES after fix.
    """
    import datetime
    from NEMO.models import Customization
    Customization.objects.update_or_create(
        name="access_requests_minimum_users", defaults={"value": "2"}
    )
    now = timezone.now()
    start = now + datetime.timedelta(hours=2)
    end = now + datetime.timedelta(hours=4)
    payload = {
        "creator": api_env["users"]["lab_user"].id,
        "physical_access_level": api_env["cleanroom_level_id"],
        "description": "W-API-01 PR Fix Demonstration",
        "start_time": start.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end.strftime("%Y-%m-%d %H:%M:%S"),
        "other_users": [],
    }
    auth_headers = {"Authorization": f"Token {api_env['tokens']['lab_user']}"}
    url = f"{api_server}/api/temporary_physical_access_requests/"
    resp = requests.post(url, json=payload, headers=auth_headers, timeout=15)
    assert resp.status_code == 400, f"Expected 400 Bad Request for 0 buddies when min=2, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "other_users" in data, f"Expected 'other_users' validation error key, got: {data}"
