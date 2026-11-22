"""Seed synthetic test data for the NEMO Temporary Physical Access Requests module."""

import argparse
import os
import sys
from datetime import timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sqe_local.settings")

import django

django.setup()

from django.contrib.auth.models import Permission
from django.utils import timezone
from rest_framework.authtoken.models import Token

from NEMO.models import (
    Area,
    Customization,
    PhysicalAccessLevel,
    RequestStatus,
    TemporaryPhysicalAccess,
    TemporaryPhysicalAccessRequest,
    User,
)


def _ensure_user(
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    *,
    is_active: bool = True,
    is_facility_manager: bool = False,
    is_staff: bool = False,
    is_user_office: bool = False,
    is_superuser: bool = False,
) -> User:
    user, _ = User.objects.update_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "is_active": is_active,
            "is_facility_manager": is_facility_manager,
            "is_staff": is_staff,
            "is_user_office": is_user_office,
            "is_superuser": is_superuser,
            "training_required": False,
        },
    )
    if is_active:
        Token.objects.get_or_create(user=user)
    return user


def seed(with_samples: bool = True) -> dict:
    # 1. Users for the two primary roles + buddies + negative test accounts
    lab_user = _ensure_user(
        "lab_user",
        "Ali",
        "Raza",
        "lab_user@example.org",
    )
    buddy_user = _ensure_user(
        "buddy_user",
        "Sara",
        "Ahmed",
        "buddy_user@example.org",
    )
    buddy_user_2 = _ensure_user(
        "buddy_user_2",
        "Zain",
        "Malik",
        "buddy_user_2@example.org",
    )
    other_requester = _ensure_user(
        "other_requester",
        "Hina",
        "Tariq",
        "other_requester@example.org",
    )
    facility_reviewer = _ensure_user(
        "facility_reviewer",
        "Dr. Nadia",
        "Siddiqui",
        "facility_reviewer@example.org",
        is_facility_manager=True,
        is_staff=True,
    )
    area_only_reviewer = _ensure_user(
        "area_only_reviewer",
        "Bilal",
        "Qureshi",
        "area_only_reviewer@example.org",
    )
    inactive_user = _ensure_user(
        "inactive_user",
        "Inactive",
        "Account",
        "inactive@example.org",
        is_active=False,
    )

    # Grant DRF model permissions on TemporaryPhysicalAccessRequest for API role testing
    tpar_perms = Permission.objects.filter(
        content_type__app_label="NEMO",
        content_type__model="temporaryphysicalaccessrequest",
    )
    lab_api_codenames = {
        "view_temporaryphysicalaccessrequest",
        "add_temporaryphysicalaccessrequest",
        "change_temporaryphysicalaccessrequest",
        "delete_temporaryphysicalaccessrequest",
    }
    lab_user.user_permissions.set(tpar_perms.filter(codename__in=lab_api_codenames))
    facility_reviewer.user_permissions.set(tpar_perms)
    # other_requester intentionally has NO add/change/delete perms unless granted in specific tests,
    # keeping view permission only for RBAC API contrast:
    other_requester.user_permissions.set(
        tpar_perms.filter(codename="view_temporaryphysicalaccessrequest")
    )

    # 2. Customizations
    Customization.objects.update_or_create(
        name="access_requests_minimum_users",
        defaults={"value": "2"},
    )
    Customization.objects.update_or_create(
        name="access_requests_title",
        defaults={"value": "Access requests"},
    )
    Customization.objects.update_or_create(
        name="site_title",
        defaults={"value": "NEMO SQE Lab"},
    )

    # 3. Areas & Physical Access Levels
    cleanroom_area, _ = Area.objects.update_or_create(
        name="Cleanroom Bay A",
        defaults={
            "requires_reservation": False,
            "buddy_system_allowed": True,
        },
    )
    cleanroom_area.access_request_reviewers.set([facility_reviewer, area_only_reviewer])

    vault_area, _ = Area.objects.update_or_create(
        name="Cryo Vault B",
        defaults={
            "requires_reservation": False,
            "buddy_system_allowed": False,
        },
    )

    cleanroom_level, _ = PhysicalAccessLevel.objects.update_or_create(
        name="Cleanroom 24/7 Temporary Access",
        defaults={
            "area": cleanroom_area,
            "schedule": PhysicalAccessLevel.Schedule.ALWAYS,
            "allow_user_request": True,
        },
    )
    non_requestable_level, _ = PhysicalAccessLevel.objects.update_or_create(
        name="Cryo Vault Direct Only",
        defaults={
            "area": vault_area,
            "schedule": PhysicalAccessLevel.Schedule.WEEKDAYS,
            "allow_user_request": False,
        },
    )

    # 4. Optional synthetic sample requests spanning lifecycle states
    if with_samples and not TemporaryPhysicalAccessRequest.objects.exists():
        now = timezone.now()
        pending_req = TemporaryPhysicalAccessRequest.objects.create(
            creator=lab_user,
            last_updated_by=lab_user,
            physical_access_level=cleanroom_level,
            description="Synthetic pending cleanroom weekend lithography run",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=4),
            status=RequestStatus.PENDING,
        )
        pending_req.other_users.add(buddy_user)

        approved_req = TemporaryPhysicalAccessRequest.objects.create(
            creator=lab_user,
            last_updated_by=facility_reviewer,
            reviewer=facility_reviewer,
            physical_access_level=cleanroom_level,
            description="Synthetic approved cleanroom wafer inspection",
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=3),
            status=RequestStatus.APPROVED,
        )
        approved_req.other_users.add(buddy_user)
        for granted_user in approved_req.creator_and_other_users():
            TemporaryPhysicalAccess.objects.create(
                user=granted_user,
                physical_access_level=cleanroom_level,
                start_time=approved_req.start_time,
                end_time=approved_req.end_time,
            )

        denied_req = TemporaryPhysicalAccessRequest.objects.create(
            creator=other_requester,
            last_updated_by=facility_reviewer,
            reviewer=facility_reviewer,
            physical_access_level=cleanroom_level,
            description="Synthetic denied maintenance window overlap",
            start_time=now + timedelta(days=3),
            end_time=now + timedelta(days=3, hours=2),
            status=RequestStatus.DENIED,
        )
        denied_req.other_users.add(buddy_user)

    tokens = {
        u.username: Token.objects.get(user=u).key
        for u in [lab_user, buddy_user, other_requester, facility_reviewer, area_only_reviewer]
    }
    return {
        "users": [lab_user.username, buddy_user.username, buddy_user_2.username, other_requester.username, facility_reviewer.username, area_only_reviewer.username, inactive_user.username],
        "tokens": tokens,
        "physical_access_level_id": cleanroom_level.id,
        "non_requestable_level_id": non_requestable_level.id,
        "requests_count": TemporaryPhysicalAccessRequest.objects.count(),
        "grants_count": TemporaryPhysicalAccess.objects.count(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed synthetic SQE test data into NEMO SQLite DB.")
    parser.add_argument("--no-samples", action="store_true", help="Seed users/areas/levels only, without sample requests.")
    args = parser.parse_args()
    summary = seed(with_samples=not args.no_samples)
    print("Seeded synthetic NEMO data successfully:")
    for key, val in summary.items():
        print(f"  {key}: {val}")
