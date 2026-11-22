"""Deterministic DB reset, seeding, and postcondition inspection helper for Playwright E2E/Area 3 tests."""

import argparse
import json
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

from django.core.management import call_command
from django.utils import timezone

from NEMO.models import (
    Customization,
    Notification,
    PhysicalAccessLevel,
    RequestStatus,
    TemporaryPhysicalAccess,
    TemporaryPhysicalAccessRequest,
    User,
)
from NEMO.views.customization import UserRequestsCustomization
from scripts.seed_synthetic_data import seed


def cmd_reset(no_samples: bool = False) -> dict:
    TemporaryPhysicalAccess.objects.all().delete()
    TemporaryPhysicalAccessRequest.objects.all().delete()
    Notification.objects.filter(notification_type=Notification.Types.TEMPORARY_ACCESS_REQUEST).delete()
    summary = seed(with_samples=not no_samples)
    UserRequestsCustomization.set("access_requests_minimum_users", "2")
    return summary


def cmd_create_pending(creator_username: str, description: str, buddy_usernames: list[str], hours_ahead: int = 24) -> dict:
    creator = User.objects.get(username=creator_username)
    level = PhysicalAccessLevel.objects.get(name="Cleanroom 24/7 Temporary Access")
    now = timezone.now()
    req = TemporaryPhysicalAccessRequest.objects.create(
        creator=creator,
        last_updated_by=creator,
        physical_access_level=level,
        description=description,
        start_time=now + timedelta(hours=hours_ahead),
        end_time=now + timedelta(hours=hours_ahead + 4),
        status=RequestStatus.PENDING,
    )
    for b in buddy_usernames:
        req.other_users.add(User.objects.get(username=b))
    return _serialize_request(req)


def cmd_seed_expired_pending(description: str) -> dict:
    creator = User.objects.get(username="lab_user")
    buddy = User.objects.get(username="buddy_user")
    level = PhysicalAccessLevel.objects.get(name="Cleanroom 24/7 Temporary Access")
    now = timezone.now()
    req = TemporaryPhysicalAccessRequest.objects.create(
        creator=creator,
        last_updated_by=creator,
        physical_access_level=level,
        description=description,
        start_time=now - timedelta(hours=6),
        end_time=now - timedelta(hours=2),
        status=RequestStatus.PENDING,
    )
    req.other_users.add(buddy)
    return _serialize_request(req)


def _serialize_request(req: TemporaryPhysicalAccessRequest) -> dict:
    grants = TemporaryPhysicalAccess.objects.filter(
        physical_access_level=req.physical_access_level,
        start_time=req.start_time,
        end_time=req.end_time,
    )
    notifs = Notification.objects.filter(
        notification_type=Notification.Types.TEMPORARY_ACCESS_REQUEST,
        object_id=req.id,
    )
    reviewer_notifs = notifs.filter(user__in=req.reviewers())
    return {
        "id": req.id,
        "status": req.status,
        "status_display": req.get_status_display(),
        "deleted": req.deleted,
        "description": req.description,
        "creator": req.creator.username,
        "reviewer": req.reviewer.username if req.reviewer else None,
        "last_updated_by": req.last_updated_by.username if req.last_updated_by else None,
        "other_users": sorted(u.username for u in req.other_users.all()),
        "grants_count": grants.count(),
        "granted_users": sorted(g.user.username for g in grants.select_related("user")),
        "notifications_count": notifs.count(),
        "reviewer_notifications_count": reviewer_notifs.count(),
        "total_requests_count": TemporaryPhysicalAccessRequest.objects.count(),
        "total_grants_count": TemporaryPhysicalAccess.objects.count(),
    }


def cmd_inspect(request_id: int | None, description: str | None) -> dict:
    if request_id is not None:
        req = TemporaryPhysicalAccessRequest.objects.get(id=request_id)
    elif description is not None:
        req = TemporaryPhysicalAccessRequest.objects.filter(description=description).order_by("-id").first()
        if req is None:
            return {"found": False}
    else:
        raise ValueError("Specify --id or --description")
    data = _serialize_request(req)
    data["found"] = True
    return data


def cmd_set_min_users(value: int) -> dict:
    UserRequestsCustomization.set("access_requests_minimum_users", str(value))
    return {"access_requests_minimum_users": UserRequestsCustomization.get("access_requests_minimum_users")}


def main() -> int:
    parser = argparse.ArgumentParser(description="E2E DB helper for NEMO SQE tests")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_reset = sub.add_parser("reset")
    p_reset.add_argument("--no-samples", action="store_true")

    p_cp = sub.add_parser("create-pending")
    p_cp.add_argument("--creator", default="lab_user")
    p_cp.add_argument("--description", required=True)
    p_cp.add_argument("--buddies", nargs="*", default=["buddy_user"])
    p_cp.add_argument("--hours-ahead", type=int, default=24)

    p_exp = sub.add_parser("seed-expired-pending")
    p_exp.add_argument("--description", required=True)

    p_ins = sub.add_parser("inspect")
    p_ins.add_argument("--id", type=int, default=None)
    p_ins.add_argument("--description", type=str, default=None)

    p_min = sub.add_parser("set-min-users")
    p_min.add_argument("--value", type=int, required=True)

    args = parser.parse_args()
    if args.cmd == "reset":
        out = cmd_reset(no_samples=args.no_samples)
    elif args.cmd == "create-pending":
        out = cmd_create_pending(args.creator, args.description, args.buddies, args.hours_ahead)
    elif args.cmd == "seed-expired-pending":
        out = cmd_seed_expired_pending(args.description)
    elif args.cmd == "inspect":
        out = cmd_inspect(args.id, args.description)
    elif args.cmd == "set-min-users":
        out = cmd_set_min_users(args.value)
    else:
        raise ValueError(args.cmd)

    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
