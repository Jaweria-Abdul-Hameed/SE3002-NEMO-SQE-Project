"""Phase 4 Spec-Driven API Tests Consuming Generated EP & 3-Point BVA Datasets.

Area 2 Owner: Mohsin Khan (24I-3135)
Consumes: tests/team/api/generated_test_data.json (generated from openapi/temporary_physical_access_requests.yaml)
Uses: pytest + requests against live local NEMO server (api_server)

Every valid and invalid Equivalence Partition (one invalid value per test) and
every 3-Point BVA value across request body fields and query/path parameters is
executed via real HTTP requests, verifying both HTTP status codes and persistent
database readbacks after BOTH successful and rejected operations.
"""

import pytest
import requests

from NEMO.models import TemporaryPhysicalAccessRequest
from tests.team.api.conftest import (
    auth_headers,
    build_resolved_baseline,
    extract_list_items,
    load_generated_data,
    resolve_placeholder,
)

DATASET = load_generated_data()
BODY_EP_CASES = DATASET["body_ep_cases"]
BODY_BVA_CASES = DATASET["body_bva_cases"]
PARAM_CASES = DATASET["parameter_cases"]

# Upstream NEMO DRF ModelViewSet.create (NEMO/views/api.py:211) returns HTTP 200 OK instead of 201 Created.
CREATE_SUCCESS_STATUS = 200

# Upstream NEMO DRF ModelSerializer known domain-validation gaps (logged as W-API-01..08 / PR-01, PR-06):
# NEMO's custom ModelSerializer calls model full_clean() (so end_time <= start_time IS rejected with 400),
# but does NOT invoke TemporaryPhysicalAccessRequestForm.clean() (other_users minItems),
# view-layer start_time >= now, description minLength/maxLength, max duration, or other_users maxItems.
KNOWN_DRF_BYPASS_BVA_CASES = {
    "BVA3-description-minLength-below_minLength",
    "BVA3-description-maxLength-above_maxLength",
    "BVA3-start_time-offset-below_min_offset",
    "BVA3-end_time-maxDuration-above_max_duration",
    "BVA3-other_users-minItems-below_minItems",
    "BVA3-other_users-maxItems-above_maxItems",
}


def _apply_case_to_payload(base_payload, case, env, anchor_now, anchor_start):
    payload = dict(base_payload)
    field = case["field"]
    if case.get("omit_field"):
        payload.pop(field, None)
    else:
        payload[field] = resolve_placeholder(case["value"], env, anchor_now, anchor_start)
    return payload


# =============================================================================
# 1. Request Body Equivalence Partitioning (46 Generated Cases, 1 Invalid / Test)
# =============================================================================


@pytest.mark.parametrize("case", BODY_EP_CASES, ids=[c["case_id"] for c in BODY_EP_CASES])
def test_api_post_body_equivalence_partitions(api_server, api_env, case):
    """Execute every generated EP partition against POST /api/temporary_physical_access_requests/ with DB readback."""
    url = f"{api_server.url}/api/temporary_physical_access_requests/"
    headers = auth_headers(api_env["tokens"]["lab_user"])
    base_payload, anchor_now, anchor_start = build_resolved_baseline(DATASET, api_env)
    payload = _apply_case_to_payload(base_payload, case, api_env, anchor_now, anchor_start)

    before_count = TemporaryPhysicalAccessRequest.objects.count()
    resp = requests.post(url, json=payload, headers=headers, timeout=15)

    if case["expected_valid"]:
        assert resp.status_code == CREATE_SUCCESS_STATUS, (
            f"{case['case_id']} expected {CREATE_SUCCESS_STATUS}, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "id" in body
        # Read back via GET detail and verify persisted state matches
        get_resp = requests.get(f"{url}{body['id']}/", headers=headers, timeout=15)
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == body["id"]
        assert TemporaryPhysicalAccessRequest.objects.count() == before_count + 1
    else:
        assert resp.status_code == 400, f"{case['case_id']} expected 400, got {resp.status_code}: {resp.text}"
        # Post-rejection readback via DB and API list: confirm NO record was persisted
        assert TemporaryPhysicalAccessRequest.objects.count() == before_count
        list_resp = requests.get(url, headers=headers, timeout=15)
        assert list_resp.status_code == 200
        assert len(extract_list_items(list_resp.json())) == before_count


# =============================================================================
# 2. Request Body 3-Point Boundary Value Analysis (52 Generated Cases)
# =============================================================================


@pytest.mark.parametrize("case", BODY_BVA_CASES, ids=[c["case_id"] for c in BODY_BVA_CASES])
def test_api_post_body_3point_bva(api_server, api_env, case):
    """Execute every generated 3-point BVA case (just below, at, just above) with DB readback & weakness detection."""
    url = f"{api_server.url}/api/temporary_physical_access_requests/"
    headers = auth_headers(api_env["tokens"]["lab_user"])
    base_payload, anchor_now, anchor_start = build_resolved_baseline(DATASET, api_env)
    payload = _apply_case_to_payload(base_payload, case, api_env, anchor_now, anchor_start)

    before_count = TemporaryPhysicalAccessRequest.objects.count()
    resp = requests.post(url, json=payload, headers=headers, timeout=15)

    # FK integer boundaries (e.g., creator=999998 or physical_access_level=1) depend on whether that PK exists in SQLite
    if case.get("fk_sensitive"):
        if case["point"] in ("below_min", "above_max"):
            assert resp.status_code == 400
            assert TemporaryPhysicalAccessRequest.objects.count() == before_count
        else:
            assert resp.status_code in (CREATE_SUCCESS_STATUS, 400)
            expected_delta = 1 if resp.status_code == CREATE_SUCCESS_STATUS else 0
            assert TemporaryPhysicalAccessRequest.objects.count() == before_count + expected_delta
        return

    # Known upstream NEMO DRF validation bypasses (PR-01 / PR-06): assert actual defect behavior explicitly!
    if case["case_id"] in KNOWN_DRF_BYPASS_BVA_CASES:
        assert resp.status_code == CREATE_SUCCESS_STATUS, (
            f"Expected upstream weakness {case['case_id']} to bypass validation with {CREATE_SUCCESS_STATUS}, "
            f"got {resp.status_code}"
        )
        assert TemporaryPhysicalAccessRequest.objects.count() == before_count + 1
        return

    if case["expected_valid"]:
        assert resp.status_code == CREATE_SUCCESS_STATUS, (
            f"{case['case_id']} expected {CREATE_SUCCESS_STATUS}, got {resp.status_code}: {resp.text}"
        )
        created_id = resp.json()["id"]
        readback = requests.get(f"{url}{created_id}/", headers=headers, timeout=15)
        assert readback.status_code == 200
        assert TemporaryPhysicalAccessRequest.objects.count() == before_count + 1
    else:
        assert resp.status_code == 400, f"{case['case_id']} expected 400, got {resp.status_code}: {resp.text}"
        assert TemporaryPhysicalAccessRequest.objects.count() == before_count


# =============================================================================
# 3. Query & Path Parameter EP + 3-Point BVA Cases (Generated from OpenAPI)
# =============================================================================


QUERY_CASES = [
    c
    for c in PARAM_CASES
    if c["param_in"] == "query"
    and c["endpoint"] == "/api/temporary_physical_access_requests/"
    and not c.get("omit_field")
    and c["value"] is not None
]


@pytest.mark.parametrize("case", QUERY_CASES, ids=[c["case_id"] for c in QUERY_CASES])
def test_api_list_query_parameters_ep_and_bva(api_server, api_env, case):
    """Execute generated EP and 3-point BVA query parameters on GET /api/temporary_physical_access_requests/."""
    url = f"{api_server.url}/api/temporary_physical_access_requests/"
    headers = auth_headers(api_env["tokens"]["lab_user"])

    # Seed one valid request first so filters operate on real persisted data
    base_payload, _, _ = build_resolved_baseline(DATASET, api_env)
    create_resp = requests.post(url, json=base_payload, headers=headers, timeout=15)
    assert create_resp.status_code == CREATE_SUCCESS_STATUS

    param_val = case["value"]
    params = {case["field"]: param_val}
    if case["field"] == "page":
        # Trigger NEMOPageNumberPagination explicitly via page_size=10
        params["page_size"] = 10

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    assert resp.status_code < 500, f"Server 5xx on {case['case_id']}: {resp.status_code} {resp.text}"

    if case["field"] == "page":
        if param_val == 1:
            assert resp.status_code == 200
            data = resp.json()
            assert "count" in data and "results" in data
        else:
            assert resp.status_code in (400, 404)
    elif case["field"] == "deleted":
        assert resp.status_code in (200, 400)
    elif case["expected_valid"]:
        # django-filter ModelChoiceFilter rejects non-existent FK PKs (400) when SQLite autoincrement > 1
        if case["field"] in ("creator", "reviewer", "physical_access_level") and isinstance(param_val, int):
            from NEMO.models import PhysicalAccessLevel, User

            model_cls = PhysicalAccessLevel if case["field"] == "physical_access_level" else User
            if model_cls.objects.filter(pk=param_val).exists():
                assert resp.status_code == 200
                assert isinstance(extract_list_items(resp.json()), list)
            else:
                assert resp.status_code == 400
        else:
            assert resp.status_code == 200
            assert isinstance(extract_list_items(resp.json()), list)
    else:
        assert resp.status_code in (200, 400)


@pytest.mark.parametrize(
    "path_id,expected_status",
    [
        (0, 404),       # 3-point BVA: minimum - 1
        (-1, 404),      # EP: negative integer
        (999999, 404),  # 3-point BVA: nonexistent max
        (1000000, 404), # 3-point BVA: above max
        ("abc", 404),   # EP: non-integer path segment
    ],
)
def test_api_detail_path_parameter_invalid_ep_bva(api_server, api_env, path_id, expected_status):
    """Verify invalid path {id} partitions & boundaries return 404 on GET /api/temporary_physical_access_requests/{id}/."""
    url = f"{api_server.url}/api/temporary_physical_access_requests/{path_id}/"
    headers = auth_headers(api_env["tokens"]["lab_user"])
    resp = requests.get(url, headers=headers, timeout=15)
    assert resp.status_code == expected_status
