"""Smoke tests verifying the isolated team test setup and synthetic baseline data."""

import pytest
from django.urls import reverse

from NEMO.models import PhysicalAccessLevel, RequestStatus, TemporaryPhysicalAccessRequest, User


@pytest.mark.django_db
def test_synthetic_seed_and_login_workflow():
    from scripts.seed_synthetic_data import seed

    summary = seed(with_samples=True)
    assert summary["requests_count"] == 3
    assert summary["grants_count"] == 2
    assert User.objects.filter(username="lab_user", is_active=True).exists()
    assert User.objects.filter(username="facility_reviewer", is_facility_manager=True).exists()
    assert PhysicalAccessLevel.objects.filter(allow_user_request=True).exists()


@pytest.mark.django_db
def test_access_requests_ui_and_api_baseline(client):
    from scripts.seed_synthetic_data import seed

    summary = seed(with_samples=True)
    # Browser login via LocalSyntheticAuthBackend
    logged_in = client.login(username="lab_user", password="nemo-sqe-test-2026")
    assert logged_in is True

    ui_resp = client.get(reverse("user_requests", kwargs={"tab": "access"}))
    assert ui_resp.status_code == 200
    assert b"Access requests" in ui_resp.content

    # REST API access with TokenAuthentication
    api_resp = client.get(
        "/api/temporary_physical_access_requests/",
        HTTP_AUTHORIZATION=f"Token {summary['tokens']['lab_user']}",
    )
    assert api_resp.status_code == 200
    payload = api_resp.json()
    results = payload["results"] if isinstance(payload, dict) and "results" in payload else payload
    assert any(item["status"] == RequestStatus.PENDING for item in results)
    assert TemporaryPhysicalAccessRequest.objects.filter(status=RequestStatus.APPROVED).exists()
