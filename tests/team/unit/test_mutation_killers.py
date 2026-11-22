"""Phase 3 Mutation-Killing Unit Tests: Eliminates All 33 Killable Surviving Mutants from Baseline Run.

Owner: Jaweria Abdul Hameed (24I-3025) — Area 1
Targets every killable mutant discovered in `docs/evidence/cr_baseline_report.txt`
(10 missing-test mutants + 23 weak-assertion mutants), raising raw mutation score
from 73.46% (119/162) to 93.83% (152/162) and equivalent-adjusted score to 100.0%.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from NEMO.models import (
    Notification,
    RequestStatus,
    TemporaryPhysicalAccessRequest,
    User,
)
from NEMO.utilities import bootstrap_primary_color
from NEMO.views.access_requests import send_request_received_email
from NEMO.views.notifications import create_access_request_notification
from tests.team.unit.conftest import make_access_request, make_form_post_data


# =============================================================================
# 1. Missing-Test Killers: Auth (@login_required) & HTTP Method (@require_GET / @require_http_methods)
#    Kills: L43, L44, L88, L89, L164, L165, L252 (7 RemoveDecorator mutants)
# =============================================================================


@pytest.mark.django_db
def test_mk_login_required_decorators_redirect_anonymous_users(client, access_env):
    """MK-01: Kills RemoveDecorator on @login_required (L43, L88, L164)."""
    u = access_env["users"]
    req = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])

    for url in (
        reverse("access_requests"),
        reverse("create_access_request"),
        reverse("delete_access_request", args=[req.id]),
    ):
        resp = client.get(url)
        assert resp.status_code == 302
        assert reverse("login") in resp.url


@pytest.mark.django_db
def test_mk_http_method_decorators_reject_disallowed_verbs(client, access_env):
    """MK-02: Kills RemoveDecorator on @require_GET / @require_http_methods (L44, L89, L165, L252)."""
    u = access_env["users"]
    req = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])

    client.force_login(u["lab_user"])
    assert client.post(reverse("access_requests")).status_code == 405
    assert client.delete(reverse("create_access_request")).status_code == 405
    assert client.post(reverse("delete_access_request", args=[req.id])).status_code == 405

    client.force_login(u["facility_reviewer"])
    assert client.post(reverse("export_access_requests")).status_code == 405


# =============================================================================
# 2. Missing-Test Killers: Bitwise OR vs XOR (L56), Staff Role Precedence (L59),
#    Exact Start-Time Boundary (L126), Expired Status in Email (L218)
# =============================================================================


@pytest.mark.django_db
def test_mk_creator_also_listed_in_other_users_remains_visible(client, access_env):
    """MK-03: Kills L56 ReplaceBinaryOperator_BitOr_BitXor (`|` vs `^` on creator + buddy)."""
    u = access_env["users"]
    req = make_access_request(
        u["lab_user"],
        access_env["cleanroom_level"],
        buddies=[u["lab_user"], u["buddy_user"]],
    )
    client.force_login(u["lab_user"])
    resp = client.get(reverse("access_requests"))
    assert resp.status_code == 200
    assert req in list(resp.context["pending_access_requests"])


@pytest.mark.django_db
def test_mk_user_office_without_is_staff_sees_all_requests(client, access_env):
    """MK-04: Kills L59 ReplaceOrWithAnd#1 (`is_user_office and is_staff` vs `or`)."""
    u = access_env["users"]
    office_only, _ = User.objects.update_or_create(
        username="office_only_nonstaff",
        defaults={
            "first_name": "Nadia",
            "last_name": "Office",
            "email": "office_only@example.org",
            "is_active": True,
            "is_user_office": True,
            "is_staff": False,
            "is_facility_manager": False,
            "training_required": False,
        },
    )
    req_isolated = make_access_request(u["other_requester"], access_env["isolated_level"], buddies=[u["buddy_user_2"]])

    client.force_login(office_only)
    resp = client.get(reverse("access_requests"))
    assert resp.status_code == 200
    assert req_isolated in list(resp.context["pending_access_requests"])


@pytest.mark.django_db
def test_mk_exact_start_time_equal_to_now_is_allowed(client, access_env):
    """MK-05: Kills L126 ReplaceComparisonOperator_Lt_LtE (`start_time < now` vs `<=`)."""
    u = access_env["users"]
    # Truncate microseconds so formatted POST value matches frozen timezone.now() to the exact second
    exact_now = timezone.now().replace(microsecond=0) + timedelta(minutes=10)
    end_time = exact_now + timedelta(hours=2)

    client.force_login(u["lab_user"])
    with patch("NEMO.views.access_requests.timezone.now", return_value=exact_now):
        resp = client.post(
            reverse("create_access_request"),
            data=make_form_post_data(
                access_env["cleanroom_level"],
                exact_now,
                end_time,
                other_users=[u["buddy_user"]],
                description="Exact boundary start == now",
            ),
        )
    assert resp.status_code == 302
    assert TemporaryPhysicalAccessRequest.objects.filter(description="Exact boundary start == now").exists()


# =============================================================================
# 3. Weak-Assertion Killers: Approved/Denied Lists (L71-72), Reviewer Notification
#    Retention (L76), GET Form Context & Unbound State (L98, L99, L102),
#    Reviewer vs Creator Notification Deletion (L149), Email Color & Expired (L218, L221)
# =============================================================================


@pytest.mark.django_db
def test_mk_access_requests_context_buckets_and_reviewer_notification_retained(client, access_env):
    """MK-06: Kills custom nemo_br/FlipApprovalStatusOperator#1 & #2 (L71-72) AND L76 delete=True."""
    u = access_env["users"]
    req_pending = make_access_request(
        u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]], status=RequestStatus.PENDING
    )
    req_approved = make_access_request(
        u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]], status=RequestStatus.APPROVED
    )
    req_denied = make_access_request(
        u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]], status=RequestStatus.DENIED
    )
    create_access_request_notification(req_pending)

    # Reviewer visits list page: approved/denied must land in their exact buckets, and pending reviewer notif stays!
    client.force_login(u["facility_reviewer"])
    resp = client.get(reverse("access_requests"))
    assert resp.status_code == 200
    assert list(resp.context["approved_access_requests"]) == [req_approved]
    assert list(resp.context["denied_access_requests"]) == [req_denied]
    assert Notification.objects.filter(
        user=u["facility_reviewer"],
        notification_type=Notification.Types.TEMPORARY_ACCESS_REQUEST,
        object_id=req_pending.id,
    ).exists()


@pytest.mark.django_db
def test_mk_create_access_request_get_context_filters_and_unbound_form(client, access_env):
    """MK-07: Kills L98 (allow_user_request=False), L99 (is_active=False), L102 (<= / is not POST)."""
    u = access_env["users"]
    client.force_login(u["lab_user"])

    resp = client.get(reverse("create_access_request"))
    assert resp.status_code == 200
    # Unbound form on GET kills L102 `<= "POST"` and `is not "POST"`
    assert resp.context["form"].is_bound is False
    assert not resp.context["form"].errors

    # Only requestable levels (allow_user_request=True) shown -> kills L98
    levels = list(resp.context["physical_access_levels"])
    assert access_env["cleanroom_level"] in levels
    assert access_env["non_requestable_level"] not in levels

    # Only active users (excluding self) shown -> kills L99
    other_users = list(resp.context["other_users"])
    assert u["buddy_user"] in other_users
    assert u["inactive_user"] not in other_users
    assert u["lab_user"] not in other_users


@pytest.mark.django_db
def test_mk_edit_notification_cleanup_reviewer_vs_creator(client, access_env):
    """MK-08: Kills L149 AddNot#15 (`if not user in access_request.reviewers()`)."""
    u = access_env["users"]
    req = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])
    create_access_request_notification(req)

    # 1. Creator edits -> other reviewers' notifications MUST still exist!
    client.force_login(u["lab_user"])
    resp_creator = client.post(
        reverse("edit_access_request", args=[req.id]),
        data=make_form_post_data(
            access_env["cleanroom_level"],
            req.start_time,
            req.end_time,
            other_users=[u["buddy_user"]],
            description="Creator edit keeps reviewer notifications",
        ),
    )
    assert resp_creator.status_code == 302
    assert Notification.objects.filter(
        user=u["area_only_reviewer"],
        notification_type=Notification.Types.TEMPORARY_ACCESS_REQUEST,
        object_id=req.id,
    ).exists()

    # 2. Facility reviewer approves -> ALL reviewers' notifications (including area_only_reviewer) MUST be deleted!
    client.force_login(u["facility_reviewer"])
    resp_rev = client.post(
        reverse("edit_access_request", args=[req.id]),
        data=make_form_post_data(
            access_env["cleanroom_level"],
            req.start_time,
            req.end_time,
            other_users=[u["buddy_user"]],
            description="Approved by facility reviewer",
            extra={"approve_request": ""},
        ),
    )
    assert resp_rev.status_code == 302
    assert not Notification.objects.filter(
        user=u["area_only_reviewer"],
        notification_type=Notification.Types.TEMPORARY_ACCESS_REQUEST,
        object_id=req.id,
    ).exists()


@pytest.mark.django_db
def test_mk_email_template_colors_and_expired_status_branch(access_env):
    """MK-09: Kills L218 `>= DENIED` (EXPIRED status) AND all 14 killable L221 color_type mutants."""
    u = access_env["users"]
    rf = RequestFactory()
    http_req = rf.get("/")
    http_req.user = u["lab_user"]

    req = make_access_request(
        u["lab_user"],
        access_env["cleanroom_level"],
        buddies=[u["buddy_user"]],
        reviewer=u["facility_reviewer"],
    )
    template_html = "STATUS={{ status }}|COLOR={{ template_color }}"
    cases = [
        (RequestStatus.APPROVED, True, "approved", bootstrap_primary_color("success")),
        (RequestStatus.DENIED, True, "denied", bootstrap_primary_color("danger")),
        (RequestStatus.PENDING, True, "updated", bootstrap_primary_color("info")),
        (RequestStatus.PENDING, False, "received", bootstrap_primary_color("info")),
        # EXPIRED (3): `3 >= DENIED (2)` would falsely yield "denied" instead of "updated" (kills L218 GtE)
        (RequestStatus.EXPIRED, True, "updated", bootstrap_primary_color("info")),
    ]
    for status_code, edit_flag, exp_status, exp_color in cases:
        req.status = status_code
        with (
            patch("NEMO.views.access_requests.get_media_file_contents", return_value=template_html),
            patch("NEMO.views.access_requests.send_mail") as mock_send,
        ):
            send_request_received_email(http_req, req, edit=edit_flag)
            assert mock_send.call_count == 1
            body = mock_send.call_args.kwargs["content"]
            assert f"STATUS={exp_status}|COLOR={exp_color}" == body
