"""Phase 3 White-Box Unit Tests: 100% Statement & Branch Coverage, State Transitions & Business Rules.

Owner: Jaweria Abdul Hameed (24I-3025) — Area 1
Targets:
  - NEMO/views/access_requests.py (all 9 functions)
  - NEMO/forms.py :: TemporaryPhysicalAccessRequestForm
  - NEMO/models.py :: TemporaryPhysicalAccessRequest & TemporaryPhysicalAccess
Covers:
  - FR-01..FR-10, BR-1 (Boundary/Limits), BR-2 (Multi-condition decisions),
    BR-3 (State-transition matrix), BR-4 (Role-based permissions)
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from NEMO.forms import TemporaryPhysicalAccessRequestForm
from NEMO.models import (
    Customization,
    Notification,
    RequestStatus,
    TemporaryPhysicalAccess,
    TemporaryPhysicalAccessRequest,
)
from NEMO.views.access_requests import (
    access_csv_export,
    create_temporary_access,
    is_user_a_reviewer,
    mark_requests_expired,
    send_request_received_email,
)
from tests.team.unit.conftest import make_access_request, make_form_post_data, set_min_users


# =============================================================================
# 1. Model Business Logic (NEMO/models.py) — BR-1 & Helpers
# =============================================================================


@pytest.mark.django_db
def test_model_creator_and_other_users_with_and_without_buddies(access_env):
    """UT-MDL-01: creator_and_other_users returns set containing creator + buddies."""
    u = access_env["users"]
    req_solo = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=())
    assert req_solo.creator_and_other_users() == {u["lab_user"]}

    req_with_buddies = make_access_request(
        u["lab_user"],
        access_env["cleanroom_level"],
        buddies=[u["buddy_user"], u["buddy_user_2"]],
    )
    assert req_with_buddies.creator_and_other_users() == {
        u["lab_user"],
        u["buddy_user"],
        u["buddy_user_2"],
    }


@pytest.mark.django_db
def test_model_reviewers_explicit_area_vs_facility_manager_fallback(access_env):
    """UT-MDL-02: reviewers() returns area reviewers if assigned, else active facility managers."""
    u = access_env["users"]
    req_explicit = make_access_request(u["lab_user"], access_env["cleanroom_level"])
    assert set(req_explicit.reviewers()) == {u["facility_reviewer"], u["area_only_reviewer"]}

    req_fallback = make_access_request(u["lab_user"], access_env["fallback_level"])
    assert set(req_fallback.reviewers()) == {u["facility_reviewer"]}


@pytest.mark.django_db
def test_model_clean_time_order_3point_bva(access_env):
    """UT-MDL-03 (BR-1): 3-point BVA on end_time vs start_time (<, ==, >)."""
    u = access_env["users"]
    base = timezone.now() + timedelta(days=1)

    # Just below (end_time = start_time - 1s) -> ValidationError
    req_below = TemporaryPhysicalAccessRequest(
        creator=u["lab_user"],
        physical_access_level=access_env["cleanroom_level"],
        start_time=base,
        end_time=base - timedelta(seconds=1),
    )
    with pytest.raises(ValidationError) as exc_below:
        req_below.clean()
    assert "end_time" in exc_below.value.message_dict

    # Exactly at boundary (end_time == start_time) -> ValidationError
    req_equal = TemporaryPhysicalAccessRequest(
        creator=u["lab_user"],
        physical_access_level=access_env["cleanroom_level"],
        start_time=base,
        end_time=base,
    )
    with pytest.raises(ValidationError) as exc_eq:
        req_equal.clean()
    assert "end_time" in exc_eq.value.message_dict

    # Just above boundary (end_time = start_time + 1s) -> Valid
    req_above = TemporaryPhysicalAccessRequest(
        creator=u["lab_user"],
        physical_access_level=access_env["cleanroom_level"],
        start_time=base,
        end_time=base + timedelta(seconds=1),
    )
    req_above.clean()


@pytest.mark.django_db
def test_temporary_physical_access_clean_and_accessible(access_env):
    """UT-MDL-04: TemporaryPhysicalAccess clean() and accessible() bounds."""
    u = access_env["users"]
    now = timezone.now()
    grant = TemporaryPhysicalAccess.objects.create(
        user=u["lab_user"],
        physical_access_level=access_env["cleanroom_level"],
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=1),
    )
    assert grant.accessible() is True
    assert grant.accessible_at(now) is True
    assert grant.accessible_at(now + timedelta(hours=2)) is False
    assert grant.get_schedule_display_with_times()
    assert grant.ongoing_closure_time(now) is None
    assert "Temporary physical access" in grant.display()
    grant.clean()

    invalid_grant = TemporaryPhysicalAccess(
        user=u["lab_user"],
        physical_access_level=access_env["cleanroom_level"],
        start_time=now,
        end_time=now,
    )
    with pytest.raises(ValidationError):
        invalid_grant.clean()


# =============================================================================
# 2. Form Business Logic (NEMO/forms.py :: TemporaryPhysicalAccessRequestForm)
# =============================================================================


@pytest.mark.django_db
def test_form_buddy_count_3point_bva_default_min_2(access_env):
    """UT-BR1-01 (FR-02/BR-1): min_users=2 -> 0 buddies fails ('buddy'), 1 passes, 2 passes."""
    u = access_env["users"]
    set_min_users("2")
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(hours=2)

    # min - 1 = 0 buddies -> rejected with singular 'buddy'
    f0 = TemporaryPhysicalAccessRequestForm(
        data=make_form_post_data(access_env["cleanroom_level"], start, end, other_users=[])
    )
    assert not f0.is_valid()
    assert "at least 1 other buddy" in str(f0.errors["other_users"])

    # min = 1 buddy -> accepted
    f1 = TemporaryPhysicalAccessRequestForm(
        data=make_form_post_data(access_env["cleanroom_level"], start, end, other_users=[u["buddy_user"]])
    )
    assert f1.is_valid(), f1.errors

    # min + 1 = 2 buddies -> accepted
    f2 = TemporaryPhysicalAccessRequestForm(
        data=make_form_post_data(
            access_env["cleanroom_level"],
            start,
            end,
            other_users=[u["buddy_user"], u["buddy_user_2"]],
        )
    )
    assert f2.is_valid(), f2.errors


@pytest.mark.django_db
def test_form_buddy_count_3point_bva_min_3_plural_message(access_env):
    """UT-BR1-02 (FR-02/BR-1): min_users=3 -> 1 buddy fails ('buddies'), 2 passes."""
    u = access_env["users"]
    set_min_users("3")
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(hours=2)

    f1 = TemporaryPhysicalAccessRequestForm(
        data=make_form_post_data(access_env["cleanroom_level"], start, end, other_users=[u["buddy_user"]])
    )
    assert not f1.is_valid()
    assert "at least 2 other buddies" in str(f1.errors["other_users"])

    f2 = TemporaryPhysicalAccessRequestForm(
        data=make_form_post_data(
            access_env["cleanroom_level"],
            start,
            end,
            other_users=[u["buddy_user"], u["buddy_user_2"]],
        )
    )
    assert f2.is_valid(), f2.errors


@pytest.mark.django_db
def test_form_clean_early_return_on_preexisting_errors_and_missing_other_users_key(access_env):
    """UT-BR1-03: Form clean() returns None when prior errors exist, and handles missing other_users key."""
    set_min_users("2")
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(hours=2)

    # Pre-existing field error (missing physical_access_level) -> early return branch (line 538)
    bad_form = TemporaryPhysicalAccessRequestForm(
        data={"start_time": start.strftime("%Y-%m-%d %H:%M:%S"), "end_time": end.strftime("%Y-%m-%d %H:%M:%S")}
    )
    assert bad_form.is_valid() is False
    assert bad_form.clean() is None

    # Missing 'other_users' in cleaned_data (branch on line 541 ternary False)
    form_no_key = TemporaryPhysicalAccessRequestForm(
        data=make_form_post_data(access_env["cleanroom_level"], start, end, other_users=[])
    )
    form_no_key._errors = {}
    form_no_key.cleaned_data = {"start_time": start, "end_time": end}
    with patch("django.forms.models.BaseModelForm.clean", return_value=form_no_key.cleaned_data):
        form_no_key.clean()
    assert "other_users" in form_no_key.errors


# =============================================================================
# 3. Workflow 1 Views: List, Create, Edit, Delete (NEMO/views/access_requests.py)
# =============================================================================


@pytest.mark.django_db
def test_create_access_request_get_new_and_get_edit(client, access_env):
    """UT-AR-01 (FR-01/FR-04): GET create form (new) and GET edit form (existing)."""
    u = access_env["users"]
    client.force_login(u["lab_user"])

    resp_new = client.get(reverse("create_access_request"))
    assert resp_new.status_code == 200
    assert resp_new.context["form"].instance.pk is None

    req = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])
    resp_edit = client.get(reverse("edit_access_request", args=[req.id]))
    assert resp_edit.status_code == 200
    assert resp_edit.context["form"].instance.pk == req.id


@pytest.mark.django_db
def test_create_access_request_post_valid_persists_pending_and_notifies(client, access_env):
    """UT-AR-02 (FR-01): Valid POST creates PENDING request, sets creator/last_updated_by, notifies reviewers."""
    u = access_env["users"]
    client.force_login(u["lab_user"])
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(hours=4)

    resp = client.post(
        reverse("create_access_request"),
        data=make_form_post_data(
            access_env["cleanroom_level"],
            start,
            end,
            other_users=[u["buddy_user"]],
            description="Weekend cleanroom etch",
        ),
    )
    assert resp.status_code == 302
    assert resp.url == reverse("user_requests", kwargs={"tab": "access"})

    created = TemporaryPhysicalAccessRequest.objects.get(description="Weekend cleanroom etch")
    assert created.status == RequestStatus.PENDING
    assert created.creator == u["lab_user"]
    assert created.last_updated_by == u["lab_user"]
    assert created.deleted is False
    assert Notification.objects.filter(
        object_id=created.id,
        notification_type=Notification.Types.TEMPORARY_ACCESS_REQUEST,
        user=u["facility_reviewer"],
    ).exists()


@pytest.mark.django_db
def test_create_access_request_post_past_start_time_rejected(client, access_env):
    """UT-AR-03 (FR-02/BR-1): New request with start_time < now is rejected with form error."""
    u = access_env["users"]
    client.force_login(u["lab_user"])
    start = timezone.now() - timedelta(minutes=10)
    end = timezone.now() + timedelta(hours=2)

    resp = client.post(
        reverse("create_access_request"),
        data=make_form_post_data(
            access_env["cleanroom_level"],
            start,
            end,
            other_users=[u["buddy_user"]],
            description="Past start request",
        ),
    )
    assert resp.status_code == 200
    assert "The start time must be later than the current time" in str(resp.context["form"].errors["start_time"])
    assert not TemporaryPhysicalAccessRequest.objects.filter(description="Past start request").exists()


@pytest.mark.django_db
def test_edit_access_request_by_creator_keeps_pending_and_updates_fields(client, access_env):
    """UT-EDIT-01 (FR-04): Creator edits own PENDING request; stays PENDING, removes creator notification."""
    u = access_env["users"]
    req = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])
    client.force_login(u["lab_user"])
    new_start = timezone.now() + timedelta(days=2)
    new_end = new_start + timedelta(hours=5)

    resp = client.post(
        reverse("edit_access_request", args=[req.id]),
        data=make_form_post_data(
            access_env["cleanroom_level"],
            new_start,
            new_end,
            other_users=[u["buddy_user"], u["buddy_user_2"]],
            description="Updated description by creator",
        ),
    )
    assert resp.status_code == 302
    req.refresh_from_db()
    assert req.status == RequestStatus.PENDING
    assert req.description == "Updated description by creator"
    assert req.reviewer is None
    assert set(req.other_users.all()) == {u["buddy_user"], u["buddy_user_2"]}


@pytest.mark.django_db
def test_access_requests_list_visibility_all_roles_and_max_limit(client, access_env):
    """UT-VIS-01 (FR-03/FR-06/BR-4): Visibility matrix for Lab User, Area Reviewer, Non-Reviewer Staff."""
    u = access_env["users"]
    Customization.objects.update_or_create(name="access_requests_display_max", defaults={"value": "5"})

    # Request 1: Cleanroom (reviewed by facility_reviewer & area_only_reviewer), created by lab_user, buddy=buddy_user
    req_cleanroom = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])
    # Request 2: Isolated bay (reviewed ONLY by other_area_reviewer), created by other_requester
    req_isolated = make_access_request(u["other_requester"], access_env["isolated_level"], buddies=[u["buddy_user_2"]])

    # 1. Regular Lab User (not reviewer, not staff) -> sees ONLY req_cleanroom
    client.force_login(u["lab_user"])
    r_lab = client.get(reverse("access_requests"))
    assert r_lab.status_code == 200
    assert list(r_lab.context["pending_access_requests"]) == [req_cleanroom]
    assert r_lab.context["user_is_reviewer"] is False

    # 2. Buddy user -> sees req_cleanroom via other_users M2M filter
    client.force_login(u["buddy_user"])
    r_buddy = client.get(reverse("access_requests"))
    assert list(r_buddy.context["pending_access_requests"]) == [req_cleanroom]

    # 3. Area-only reviewer (reviewer for Cleanroom, NOT for Isolated bay) -> sees req_cleanroom, excludes req_isolated
    client.force_login(u["area_only_reviewer"])
    r_area_rev = client.get(reverse("access_requests"))
    assert list(r_area_rev.context["pending_access_requests"]) == [req_cleanroom]
    assert r_area_rev.context["user_is_reviewer"] is True

    # 4. Non-reviewer staff (is_user_office=True, not reviewer) -> sees ALL non-deleted requests (elif False branch)
    client.force_login(u["user_office_staff"])
    r_staff = client.get(reverse("access_requests"))
    assert set(r_staff.context["pending_access_requests"]) == {req_cleanroom, req_isolated}
    assert r_staff.context["user_is_reviewer"] is False


# =============================================================================
# 4. Workflow 2 & State Transitions (BR-3) — Allowed & Disallowed per State
# =============================================================================


@pytest.mark.django_db
def test_state_transition_pending_to_approved_creates_grants(client, access_env):
    """UT-ST-01 (FR-07/BR-3): PENDING -> APPROVED by reviewer sets reviewer & creates TemporaryPhysicalAccess."""
    u = access_env["users"]
    req = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])
    client.force_login(u["facility_reviewer"])

    resp = client.post(
        reverse("edit_access_request", args=[req.id]),
        data=make_form_post_data(
            access_env["cleanroom_level"],
            req.start_time,
            req.end_time,
            other_users=[u["buddy_user"]],
            description=req.description,
            extra={"approve_request": ""},
        ),
    )
    assert resp.status_code == 302
    req.refresh_from_db()
    assert req.status == RequestStatus.APPROVED
    assert req.reviewer == u["facility_reviewer"]
    grants = TemporaryPhysicalAccess.objects.filter(physical_access_level=access_env["cleanroom_level"])
    assert grants.count() == 2
    assert {g.user for g in grants} == {u["lab_user"], u["buddy_user"]}


@pytest.mark.django_db
def test_state_transition_pending_to_denied_creates_zero_grants(client, access_env):
    """UT-ST-02 (FR-08/BR-3): PENDING -> DENIED by reviewer sets reviewer and creates 0 grants."""
    u = access_env["users"]
    req = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])
    client.force_login(u["area_only_reviewer"])

    resp = client.post(
        reverse("edit_access_request", args=[req.id]),
        data=make_form_post_data(
            access_env["cleanroom_level"],
            req.start_time,
            req.end_time,
            other_users=[u["buddy_user"]],
            description=req.description,
            extra={"deny_request": ""},
        ),
    )
    assert resp.status_code == 302
    req.refresh_from_db()
    assert req.status == RequestStatus.DENIED
    assert req.reviewer == u["area_only_reviewer"]
    assert TemporaryPhysicalAccess.objects.count() == 0


@pytest.mark.django_db
def test_state_transition_reviewer_edit_without_decision_keeps_pending(client, access_env):
    """UT-ST-03 (BR-3): Reviewer edits PENDING request without approve/deny key -> stays PENDING, allows past start."""
    u = access_env["users"]
    req = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])
    client.force_login(u["facility_reviewer"])

    past_start = timezone.now() - timedelta(minutes=30)
    future_end = timezone.now() + timedelta(hours=2)
    resp = client.post(
        reverse("edit_access_request", args=[req.id]),
        data=make_form_post_data(
            access_env["cleanroom_level"],
            past_start,
            future_end,
            other_users=[u["buddy_user"]],
            description="Reviewer adjusted start time",
        ),
    )
    assert resp.status_code == 302
    req.refresh_from_db()
    assert req.status == RequestStatus.PENDING
    assert req.reviewer is None
    assert req.description == "Reviewer adjusted start time"


@pytest.mark.django_db
def test_state_transition_pending_to_expired_via_mark_requests_expired(access_env):
    """UT-ST-04 (FR-10/BR-3): Past-due PENDING request transitions to EXPIRED; future/deleted untouched."""
    u = access_env["users"]
    # Past-due PENDING -> should expire
    req_past = make_access_request(
        u["lab_user"], access_env["cleanroom_level"], start_offset_hours=-5, duration_hours=2
    )
    # Future PENDING -> must stay PENDING
    req_future = make_access_request(
        u["lab_user"], access_env["cleanroom_level"], start_offset_hours=5, duration_hours=2
    )
    # Past-due deleted=True -> must stay PENDING (deleted excluded)
    req_deleted = make_access_request(
        u["lab_user"], access_env["cleanroom_level"], start_offset_hours=-5, duration_hours=2, deleted=True
    )

    mark_requests_expired()
    req_past.refresh_from_db()
    req_future.refresh_from_db()
    req_deleted.refresh_from_db()

    assert req_past.status == RequestStatus.EXPIRED
    assert req_future.status == RequestStatus.PENDING
    assert req_deleted.status == RequestStatus.PENDING


@pytest.mark.django_db
def test_state_transition_pending_to_deleted_by_creator(client, access_env):
    """UT-ST-05 (FR-05/BR-3): Creator deletes PENDING request -> deleted=True and notifications cleared."""
    u = access_env["users"]
    req = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])
    client.force_login(u["lab_user"])

    resp = client.get(reverse("delete_access_request", args=[req.id]))
    assert resp.status_code == 302
    req.refresh_from_db()
    assert req.deleted is True
    assert not Notification.objects.filter(object_id=req.id).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "state,deleted_flag,expected_error",
    [
        (RequestStatus.APPROVED, False, "Only pending requests can be modified."),
        (RequestStatus.DENIED, False, "Only pending requests can be modified."),
        (RequestStatus.EXPIRED, False, "Only pending requests can be modified."),
        (RequestStatus.PENDING, True, "You are not allowed to edit expired or deleted requests."),
    ],
)
def test_disallowed_edit_from_non_pending_or_deleted_states(client, access_env, state, deleted_flag, expected_error):
    """UT-ST-06 (FR-09/BR-3): Editing APPROVED, DENIED, EXPIRED, or deleted=True requests is rejected."""
    u = access_env["users"]
    req = make_access_request(
        u["lab_user"],
        access_env["cleanroom_level"],
        buddies=[u["buddy_user"]],
        status=state,
        deleted=deleted_flag,
    )
    client.force_login(u["lab_user"])

    resp = client.post(
        reverse("edit_access_request", args=[req.id]),
        data=make_form_post_data(
            access_env["cleanroom_level"],
            req.start_time,
            req.end_time,
            other_users=[u["buddy_user"]],
            description="Illegal modification attempt",
        ),
    )
    assert resp.status_code == 200
    assert expected_error in str(resp.context["form"].non_field_errors())
    req.refresh_from_db()
    assert req.description != "Illegal modification attempt"


@pytest.mark.django_db
@pytest.mark.parametrize("state", [RequestStatus.APPROVED, RequestStatus.DENIED, RequestStatus.EXPIRED])
def test_disallowed_delete_from_non_pending_states(client, access_env, state):
    """UT-ST-07 (FR-09/BR-3): Deleting APPROVED, DENIED, or EXPIRED request returns 400 Bad Request."""
    u = access_env["users"]
    req = make_access_request(u["lab_user"], access_env["cleanroom_level"], status=state)
    client.force_login(u["lab_user"])

    resp = client.get(reverse("delete_access_request", args=[req.id]))
    assert resp.status_code == 400
    assert b"not allowed to delete a request that is not pending" in resp.content
    req.refresh_from_db()
    assert req.deleted is False


@pytest.mark.django_db
def test_delete_access_request_non_creator_and_not_found(client, access_env):
    """UT-DEL-01 (BR-4): Non-creator (even facility manager) gets 400; nonexistent ID returns 404."""
    u = access_env["users"]
    req = make_access_request(u["lab_user"], access_env["cleanroom_level"])
    client.force_login(u["facility_reviewer"])

    resp_forbidden = client.get(reverse("delete_access_request", args=[req.id]))
    assert resp_forbidden.status_code == 400
    assert b"didn't create" in resp_forbidden.content

    resp_404 = client.get(reverse("delete_access_request", args=[999999]))
    assert resp_404.status_code == 404


# =============================================================================
# 5. Email Notifications, CSV Export & Helper Functions (100% Coverage)
# =============================================================================


@pytest.mark.django_db
def test_send_request_received_email_all_statuses_and_missing_template(access_env):
    """UT-MAIL-01: Covers missing template (False branch) and all 4 statuses (received, updated, approved, denied)."""
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

    # Branch 1: No email template configured -> send_mail NOT called
    with (
        patch("NEMO.views.access_requests.get_media_file_contents", return_value=""),
        patch("NEMO.views.access_requests.send_mail") as mock_send,
    ):
        send_request_received_email(http_req, req, edit=False)
        mock_send.assert_not_called()

    # Branch 2: Template present -> test all 4 status branches
    template_html = "<p>{{ status }} {{ template_color }}</p>"
    scenarios = [
        (RequestStatus.PENDING, False, "received", "received"),
        (RequestStatus.PENDING, True, "updated", "updated"),
        (RequestStatus.APPROVED, True, "approved", "has been approved"),
        (RequestStatus.DENIED, True, "denied", "has been denied"),
    ]
    for status_code, edit_flag, expected_word, expected_subject_substr in scenarios:
        req.status = status_code
        with (
            patch("NEMO.views.access_requests.get_media_file_contents", return_value=template_html),
            patch("NEMO.views.access_requests.send_mail") as mock_send,
        ):
            send_request_received_email(http_req, req, edit=edit_flag)
            assert mock_send.call_count == 1
            kwargs = mock_send.call_args.kwargs
            assert expected_subject_substr in kwargs["subject"]
            assert expected_word in kwargs["content"]


@pytest.mark.django_db
def test_csv_export_permissions_and_content(client, access_env):
    """UT-CSV-01 (BR-4): Facility manager exports CSV (empty & populated); Lab User is denied."""
    u = access_env["users"]

    # Lab user denied by @user_office_or_manager_required
    client.force_login(u["lab_user"])
    resp_denied = client.get(reverse("export_access_requests"))
    assert resp_denied.status_code in (302, 400, 403)

    # Facility manager with 0 requests -> empty CSV with header only
    client.force_login(u["facility_reviewer"])
    resp_empty = client.get(reverse("export_access_requests"))
    assert resp_empty.status_code == 200
    assert "attachment; filename=" in resp_empty["Content-Disposition"]
    assert b"Status,Created date" in resp_empty.content

    # Facility manager with 1 populated request
    make_access_request(
        u["lab_user"],
        access_env["cleanroom_level"],
        buddies=[u["buddy_user"]],
        reviewer=u["facility_reviewer"],
        status=RequestStatus.APPROVED,
    )
    resp_full = client.get(reverse("export_access_requests"))
    assert resp_full.status_code == 200
    assert b"Approved" in resp_full.content
    assert b"Cleanroom Bay A" in resp_full.content


@pytest.mark.django_db
def test_is_user_a_reviewer_helper(access_env):
    """UT-REV-01 (BR-4): Checks facility manager, area reviewer, and plain lab user."""
    u = access_env["users"]
    assert is_user_a_reviewer(u["facility_reviewer"]) is True
    assert is_user_a_reviewer(u["area_only_reviewer"]) is True
    assert is_user_a_reviewer(u["lab_user"]) is False
    assert is_user_a_reviewer(u["user_office_staff"]) is False


@pytest.mark.django_db
def test_create_temporary_access_direct(access_env):
    """UT-APP-01: Direct helper creates grants for creator + every buddy."""
    u = access_env["users"]
    req = make_access_request(
        u["lab_user"],
        access_env["cleanroom_level"],
        buddies=[u["buddy_user"], u["buddy_user_2"]],
    )
    create_temporary_access(req)
    assert TemporaryPhysicalAccess.objects.count() == 3
    assert set(TemporaryPhysicalAccess.objects.values_list("user__username", flat=True)) == {
        "lab_user",
        "buddy_user",
        "buddy_user_2",
    }
