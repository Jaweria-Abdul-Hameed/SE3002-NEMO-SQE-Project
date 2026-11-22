"""Controlled failure-and-recovery integration test for Workflow 2 approval state change.

Linked Risk: PR-04 (Stale grant data or partial write during approval)
Linked Exit Criterion: EC-03 (0 partial/duplicate TemporaryPhysicalAccess or request rows upon fault + retry)
Area 3 Owner: Muhammad Aun (24P-3099)
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import OperationalError
from django.urls import reverse
from django.utils import timezone

from NEMO.models import (
    Area,
    Notification,
    PhysicalAccessLevel,
    RequestStatus,
    TemporaryPhysicalAccess,
    TemporaryPhysicalAccessRequest,
    User,
)
from NEMO.views.customization import UserRequestsCustomization


@pytest.mark.django_db
def test_controlled_failure_and_recovery_on_approval_leaves_zero_duplicates(client):
    """Simulate a transient DB failure before grant creation completes, verify persisted state, restore, and retry."""
    UserRequestsCustomization.set("access_requests_minimum_users", "2")

    lab_user = User.objects.create(
        username="rec_lab_user",
        first_name="Ali",
        last_name="Raza",
        email="rec_lab@example.org",
        is_active=True,
        training_required=False,
    )
    buddy_user = User.objects.create(
        username="rec_buddy_user",
        first_name="Sara",
        last_name="Ahmed",
        email="rec_buddy@example.org",
        is_active=True,
        training_required=False,
    )
    reviewer = User.objects.create(
        username="rec_reviewer",
        first_name="Nadia",
        last_name="Siddiqui",
        email="rec_rev@example.org",
        is_active=True,
        is_facility_manager=True,
        is_staff=True,
    )

    area = Area.objects.create(name="Recovery Cleanroom", buddy_system_allowed=True)
    area.access_request_reviewers.add(reviewer)
    level = PhysicalAccessLevel.objects.create(
        name="Recovery Access Level",
        area=area,
        schedule=PhysicalAccessLevel.Schedule.ALWAYS,
        allow_user_request=True,
    )

    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(hours=4)
    access_request = TemporaryPhysicalAccessRequest.objects.create(
        creator=lab_user,
        last_updated_by=lab_user,
        physical_access_level=level,
        description="Controlled recovery approval test",
        start_time=start,
        end_time=end,
        status=RequestStatus.PENDING,
    )
    access_request.other_users.add(buddy_user)

    client.force_login(reviewer)
    edit_url = reverse("edit_access_request", kwargs={"request_id": access_request.id})
    post_payload = {
        "start_time": timezone.localtime(start).strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": timezone.localtime(end).strftime("%Y-%m-%d %H:%M:%S"),
        "physical_access_level": str(level.id),
        "other_users": [str(buddy_user.id)],
        "description": "Controlled recovery approval test",
        "approve_request": "Approve",
    }

    # 1. Inject controlled failure via test double BEFORE grant/status writes commit
    with patch(
        "NEMO.views.access_requests.TemporaryPhysicalAccess.objects.create",
        side_effect=OperationalError("Simulated database lock before grant write completes"),
    ):
        with pytest.raises(OperationalError, match="Simulated database lock"):
            client.post(edit_url, data=post_payload)

    # 2. Verify persisted state immediately after failure: still PENDING, no reviewer, 0 grants
    access_request.refresh_from_db()
    assert access_request.status == RequestStatus.PENDING
    assert access_request.reviewer is None
    assert TemporaryPhysicalAccessRequest.objects.filter(id=access_request.id).count() == 1
    assert TemporaryPhysicalAccess.objects.filter(physical_access_level=level).count() == 0

    # 3. Restore dependency (context exited) and retry the exact approval request
    retry_resp = client.post(edit_url, data=post_payload)
    assert retry_resp.status_code == 302

    # 4. Assert expected final state with ZERO duplicate grant or request records
    access_request.refresh_from_db()
    assert access_request.status == RequestStatus.APPROVED
    assert access_request.reviewer == reviewer
    assert access_request.last_updated_by == reviewer
    assert TemporaryPhysicalAccessRequest.objects.filter(description="Controlled recovery approval test").count() == 1

    grants = TemporaryPhysicalAccess.objects.filter(
        physical_access_level=level,
        start_time=access_request.start_time,
        end_time=access_request.end_time,
    )
    assert grants.count() == 2
    assert sorted(g.user.username for g in grants) == ["rec_buddy_user", "rec_lab_user"]

    # 5. Idempotency / duplicate-submission safety after approval: repeated approval POST is rejected & adds 0 grants
    duplicate_resp = client.post(edit_url, data=post_payload)
    assert duplicate_resp.status_code == 200
    assert "Only pending requests can be modified." in duplicate_resp.content.decode()
    assert grants.count() == 2
    assert Notification.objects.filter(
        notification_type=Notification.Types.TEMPORARY_ACCESS_REQUEST,
        object_id=access_request.id,
        user=reviewer,
    ).count() == 0
