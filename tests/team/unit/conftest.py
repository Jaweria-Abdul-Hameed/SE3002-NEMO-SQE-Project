"""Shared fixtures for Phase 3 white-box unit tests (Area 1 — Jaweria Abdul Hameed)."""

from datetime import timedelta

import pytest
from django.utils import timezone

from NEMO.models import (
    Area,
    Customization,
    PhysicalAccessLevel,
    RequestStatus,
    TemporaryPhysicalAccessRequest,
    User,
)
from scripts.seed_synthetic_data import seed


@pytest.fixture
def access_env(db):
    """Seed synthetic accounts, areas, access levels, and customizations (no pre-existing requests)."""
    from NEMO.views.customization import UserRequestsCustomization

    summary = seed(with_samples=False)
    UserRequestsCustomization.set("access_requests_minimum_users", "2")
    UserRequestsCustomization.set("access_requests_display_max", "")
    UserRequestsCustomization.set("access_requests_title", "Access requests")
    users = {u.username: u for u in User.objects.all()}

    # Non-reviewer staff / user-office account to exercise the `elif user_is_reviewer:` False branch
    user_office_staff, _ = User.objects.update_or_create(
        username="user_office_staff",
        defaults={
            "first_name": "Usman",
            "last_name": "Farooq",
            "email": "user_office@example.org",
            "is_active": True,
            "is_user_office": True,
            "is_staff": True,
            "is_facility_manager": False,
            "training_required": False,
        },
    )
    users["user_office_staff"] = user_office_staff

    # Second area with NO explicit area reviewers (tests fallback to facility managers in reviewers())
    fallback_area, _ = Area.objects.update_or_create(
        name="Fallback Optics Lab",
        defaults={"requires_reservation": False, "buddy_system_allowed": True},
    )
    fallback_area.access_request_reviewers.clear()
    fallback_level, _ = PhysicalAccessLevel.objects.update_or_create(
        name="Fallback Optics 24/7",
        defaults={
            "area": fallback_area,
            "schedule": PhysicalAccessLevel.Schedule.ALWAYS,
            "allow_user_request": True,
        },
    )

    # Third area reviewed exclusively by a dedicated reviewer (tests reviewer exclusion filter)
    other_reviewer, _ = User.objects.update_or_create(
        username="other_area_reviewer",
        defaults={
            "first_name": "Kamran",
            "last_name": "Ali",
            "email": "other_area_reviewer@example.org",
            "is_active": True,
            "is_facility_manager": False,
            "training_required": False,
        },
    )
    users["other_area_reviewer"] = other_reviewer

    isolated_area, _ = Area.objects.update_or_create(
        name="Isolated Laser Bay",
        defaults={"requires_reservation": False, "buddy_system_allowed": True},
    )
    isolated_area.access_request_reviewers.set([other_reviewer])
    isolated_level, _ = PhysicalAccessLevel.objects.update_or_create(
        name="Isolated Laser 24/7",
        defaults={
            "area": isolated_area,
            "schedule": PhysicalAccessLevel.Schedule.ALWAYS,
            "allow_user_request": True,
        },
    )

    cleanroom_level = PhysicalAccessLevel.objects.get(id=summary["physical_access_level_id"])
    non_requestable_level = PhysicalAccessLevel.objects.get(id=summary["non_requestable_level_id"])

    return {
        "users": users,
        "cleanroom_level": cleanroom_level,
        "non_requestable_level": non_requestable_level,
        "fallback_level": fallback_level,
        "isolated_level": isolated_level,
        "tokens": summary["tokens"],
    }


def make_form_post_data(
    physical_access_level,
    start_time,
    end_time,
    other_users=None,
    description="Unit test access request",
    extra=None,
):
    """Build Django POST payload dictionary for TemporaryPhysicalAccessRequestForm."""
    fmt = "%Y-%m-%d %H:%M:%S"
    data = {
        "physical_access_level": physical_access_level.id,
        "start_time": timezone.localtime(start_time).strftime(fmt) if start_time else "",
        "end_time": timezone.localtime(end_time).strftime(fmt) if end_time else "",
        "description": description,
    }
    if other_users is not None:
        data["other_users"] = [u.id for u in other_users]
    if extra:
        data.update(extra)
    return data


def make_access_request(
    creator,
    physical_access_level,
    *,
    buddies=(),
    start_offset_hours=24,
    duration_hours=3,
    status=RequestStatus.PENDING,
    deleted=False,
    reviewer=None,
    description="Synthetic unit test request",
):
    """Create and persist a TemporaryPhysicalAccessRequest for unit testing."""
    now = timezone.now()
    start_time = now + timedelta(hours=start_offset_hours)
    end_time = start_time + timedelta(hours=duration_hours)
    req = TemporaryPhysicalAccessRequest.objects.create(
        creator=creator,
        last_updated_by=creator,
        physical_access_level=physical_access_level,
        description=description,
        start_time=start_time,
        end_time=end_time,
        status=status,
        deleted=deleted,
        reviewer=reviewer,
    )
    if buddies:
        req.other_users.set(buddies)
    return req


def set_min_users(value: str):
    """Update access_requests_minimum_users customization (both DB and NEMO cache)."""
    from NEMO.views.customization import UserRequestsCustomization

    UserRequestsCustomization.set("access_requests_minimum_users", str(value))
