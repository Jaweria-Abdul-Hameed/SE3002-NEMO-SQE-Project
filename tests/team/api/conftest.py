"""Shared fixtures and OpenAPI placeholder resolver for Phase 4 API & Integration tests.

Area 2 Owner: Mohsin Khan (24I-3135)
"""

import json
import os
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from django.utils import timezone

from NEMO.models import Notification, TemporaryPhysicalAccess, TemporaryPhysicalAccessRequest, User
from scripts.seed_synthetic_data import seed

DEFAULT_GENERATED_DATA = Path(__file__).resolve().parent / "generated_test_data.json"


def load_generated_data(path: Path | None = None) -> dict[str, Any]:
    target = path or Path(os.getenv("SQE_GENERATED_DATA_PATH", str(DEFAULT_GENERATED_DATA)))
    return json.loads(target.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def api_server(django_db_setup, django_db_blocker):
    """Session-scoped local HTTP server for fast, real `requests` API & integration testing."""
    from pytest_django.live_server_helper import LiveServer

    with django_db_blocker.unblock():
        server = LiveServer("127.0.0.1")
        try:
            yield server
        finally:
            server.stop()


@pytest.fixture(scope="module")
def _api_base_seed(django_db_setup, django_db_blocker, api_server):
    """Seed users, tokens, areas, and access levels ONCE per API test module for fast execution."""
    with django_db_blocker.unblock():
        from NEMO.views.customization import UserRequestsCustomization

        summary = seed(with_samples=False)
        UserRequestsCustomization.set("access_requests_minimum_users", "2")

        buddy_ids = [
            User.objects.get(username="buddy_user").id,
            User.objects.get(username="buddy_user_2").id,
        ]
        for idx in range(3, 13):
            extra_buddy, _ = User.objects.update_or_create(
                username=f"bva_buddy_{idx}",
                defaults={
                    "first_name": f"Buddy{idx}",
                    "last_name": "Tester",
                    "email": f"bva_buddy_{idx}@example.org",
                    "is_active": True,
                    "training_required": False,
                },
            )
            buddy_ids.append(extra_buddy.id)

        users = {u.username: u for u in User.objects.all()}
        return {
            "users": users,
            "tokens": summary["tokens"],
            "cleanroom_level_id": summary["physical_access_level_id"],
            "non_requestable_level_id": summary["non_requestable_level_id"],
            "lab_user_id": users["lab_user"].id,
            "other_requester_id": users["other_requester"].id,
            "facility_reviewer_id": users["facility_reviewer"].id,
            "area_only_reviewer_id": users["area_only_reviewer"].id,
            "buddy_user_ids": buddy_ids,
        }


@pytest.fixture
def api_env(_api_base_seed, django_db_blocker):
    """Ensure clean request/grant/notification tables before & after every API test without flushing all 80 tables."""
    with django_db_blocker.unblock():
        Notification.objects.all().delete()
        TemporaryPhysicalAccess.objects.all().delete()
        TemporaryPhysicalAccessRequest.objects.all().delete()
        yield _api_base_seed
        Notification.objects.all().delete()
        TemporaryPhysicalAccess.objects.all().delete()
        TemporaryPhysicalAccessRequest.objects.all().delete()


def auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def extract_list_items(payload: Any) -> list[dict[str, Any]]:
    """NEMO XLSXFileListModelMixin returns a plain JSON list unless ?page_size= is passed."""
    if isinstance(payload, dict) and "results" in payload:
        return payload["results"]
    if isinstance(payload, list):
        return payload
    raise AssertionError(f"Unexpected list payload shape: {type(payload)}")


def resolve_placeholder(value: Any, env: dict[str, Any], anchor_now, anchor_start) -> Any:
    """Resolve symbolic placeholders emitted by scripts/generate_api_test_data.py into live DB values."""
    if not isinstance(value, str) or not value.startswith("${") or not value.endswith("}"):
        return value

    expr = value[2:-1]
    if expr in env:
        return env[expr]

    if expr.startswith("buddy_user_ids:"):
        count = int(expr.split(":")[1])
        return env["buddy_user_ids"][:count]

    if expr.startswith("rel_now_plus_minutes:"):
        mins = int(expr.split(":")[1])
        dt = anchor_now + timedelta(minutes=mins)
        return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    if expr.startswith("rel_start_plus_minutes:"):
        mins = int(expr.split(":")[1])
        dt = anchor_start + timedelta(minutes=mins)
        return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    raise KeyError(f"Unknown placeholder in generated dataset: {value}")


def build_resolved_baseline(dataset: dict[str, Any], env: dict[str, Any]) -> tuple[dict[str, Any], Any, Any]:
    """Resolve the OpenAPI baseline_valid_payload into a concrete JSON dict ready for HTTP POST/PUT."""
    anchor_now = timezone.now()
    anchor_start = anchor_now + timedelta(days=1)
    payload: dict[str, Any] = {}
    for k, v in dataset["baseline_valid_payload"].items():
        if k == "start_time":
            resolved = resolve_placeholder(v, env, anchor_now, anchor_start)
            payload[k] = resolved
            anchor_start = timezone.datetime.fromisoformat(resolved.replace("Z", "+00:00"))
        else:
            payload[k] = resolve_placeholder(v, env, anchor_now, anchor_start)
    payload["reviewer"] = None
    payload["status"] = 0
    payload["deleted"] = False
    return payload, anchor_now, anchor_start
