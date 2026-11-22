"""Phase 3 Complete MCC Truth Tables & MC/DC Independence Pairs on Critical Decisions.

Owner: Jaweria Abdul Hameed (24I-3025) — Area 1
Critical Module: NEMO/views/access_requests.py & NEMO/models.py

Decisions Verified (Complete MCC + Derived MC/DC Independence Pairs):
  D1 (access_requests.py:106,111): E and A and B
     E = edit, A = (access_request.creator != user), B = (user not in access_request.reviewers())
  D2 (access_requests.py:123-127): A and (B or C) and D
     A = bool(cleaned_data), B = (not edit), C = (user not in access_request.reviewers()),
     D = (start_time < timezone.now())
  D3 (access_requests.py:133-141): Reviewer decision table (E=edit, R=user in reviewers, P=approve, Q=deny)
  D4a (access_requests.py:60):     (not R) and (not S)  [R=user_is_reviewer, S=user_is_staff]
  D4b (access_requests.py:66):     (not M) and (not V)  [M=user in creator_and_other_users, V=user in reviewers]
  D5 (models.py:658):              S and E and (end_time <= start_time)
"""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from NEMO.models import RequestStatus, TemporaryPhysicalAccess, TemporaryPhysicalAccessRequest
from tests.team.unit.conftest import make_access_request, make_form_post_data


# =============================================================================
# D1: Edit Authorization Guard (access_requests.py:106 & 111)
#     Predicate: E AND A AND B
#       E = edit (existing access_request)
#       A = (access_request.creator != user)
#       B = (user not in access_request.reviewers())
#     Outcome: True -> adds error "You are not allowed to edit this request."
#
#     MC/DC Independence Pairs (from full 8-row MCC):
#       - Condition E: (R8: T,T,T -> True) vs (R4: F,*,* -> False)
#       - Condition A: (R8: T,T,T -> True) vs (R6: T,F,T -> False)
#       - Condition B: (R8: T,T,T -> True) vs (R7: T,T,F -> False)
# =============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "row_id,edit_flag,actor_key,creator_key,expect_auth_error",
    [
        # E=False (creating new request; A & B short-circuited / N/A -> outcome False)
        ("D1-R1_R4_E_false", False, "other_requester", "lab_user", False),
        # E=True, A=False (actor == creator), B=False (actor is ALSO reviewer: facility_reviewer created it)
        ("D1-R5_TFF", True, "facility_reviewer", "facility_reviewer", False),
        # E=True, A=False (actor == creator), B=True (actor not reviewer) -> MC/DC pair for A
        ("D1-R6_TFT", True, "lab_user", "lab_user", False),
        # E=True, A=True (actor != creator), B=False (actor IS reviewer) -> MC/DC pair for B
        ("D1-R7_TTF", True, "facility_reviewer", "lab_user", False),
        # E=True, A=True (actor != creator), B=True (actor NOT reviewer) -> True (auth error) — baseline for E,A,B
        ("D1-R8_TTT", True, "other_requester", "lab_user", True),
    ],
)
def test_d1_edit_authorization_mcc_and_mcdc(
    client, access_env, row_id, edit_flag, actor_key, creator_key, expect_auth_error
):
    """Verify all feasible MCC rows and all 3 MC/DC independence pairs for D1."""
    u = access_env["users"]
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(hours=2)

    if edit_flag:
        req = make_access_request(
            u[creator_key],
            access_env["cleanroom_level"],
            buddies=[u["buddy_user"]],
        )
        url = reverse("edit_access_request", args=[req.id])
    else:
        url = reverse("create_access_request")

    client.force_login(u[actor_key])
    resp = client.post(
        url,
        data=make_form_post_data(
            access_env["cleanroom_level"],
            start,
            end,
            other_users=[u["buddy_user"]],
            description=f"D1 case {row_id}",
        ),
    )

    if expect_auth_error:
        assert resp.status_code == 200
        assert "You are not allowed to edit this request." in str(resp.context["form"].non_field_errors())
    else:
        assert resp.status_code == 302


# =============================================================================
# D2: Start-Time Past Guard with Reviewer Override (access_requests.py:123-128)
#     Predicate: A AND (B OR C) AND D
#       A = bool(cleaned_data)
#       B = (not edit)
#       C = (user not in access_request.reviewers())
#       D = (cleaned_data.get("start_time") < timezone.now())
#     Outcome: True -> adds start_time error "The start time must be later than the current time"
#
#     MC/DC Independence Pairs (derived from full 16-row MCC table):
#       - Condition A: (R16: T,T,*,T -> True) vs (R8: F,T,*,* -> False)
#       - Condition B: (R16: T,T,*,T -> True) vs (R10: T,F,F,T -> False)  [with reviewer actor]
#       - Condition C: (R12: T,F,T,T -> True) vs (R10: T,F,F,T -> False)
#       - Condition D: (R12: T,F,T,T -> True) vs (R11: T,F,T,F -> False)
# =============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "row_id,cleaned_ok,edit_flag,actor_key,start_in_past,expect_start_error",
    [
        # A=False (form already invalid due to end_time <= start_time -> cleaned_data is None; short-circuits)
        ("D2-R01_R08_A_false_create", False, False, "lab_user", True, False),
        ("D2-R02_A_false_edit", False, True, "lab_user", True, False),
        # A=True, B=False (edit), C=False (reviewer), D=False (future) -> False
        ("D2-R09_TFFF", True, True, "facility_reviewer", False, False),
        # A=True, B=False (edit), C=False (reviewer), D=True (past) -> False [reviewer override! MC/DC pair for B & C]
        ("D2-R10_TFFT", True, True, "facility_reviewer", True, False),
        # A=True, B=False (edit), C=True (non-reviewer), D=False (future) -> False [MC/DC pair for D]
        ("D2-R11_TFTF", True, True, "lab_user", False, False),
        # A=True, B=False (edit), C=True (non-reviewer), D=True (past) -> True [MC/DC anchor for C & D]
        ("D2-R12_TFTT", True, True, "lab_user", True, True),
        # A=True, B=True (create), C=N/A (short-circuited; actor=reviewer), D=False (future) -> False
        ("D2-R13_TTFF", True, False, "facility_reviewer", False, False),
        # A=True, B=True (create), C=N/A (short-circuited; actor=reviewer), D=True (past) -> True [MC/DC pair for B]
        ("D2-R14_TTFT", True, False, "facility_reviewer", True, True),
        # A=True, B=True (create), C=N/A (short-circuited; actor=lab_user), D=False (future) -> False
        ("D2-R15_TTTF", True, False, "lab_user", False, False),
        # A=True, B=True (create), C=N/A (short-circuited; actor=lab_user), D=True (past) -> True [MC/DC anchor for A]
        ("D2-R16_TTTT", True, False, "lab_user", True, True),
    ],
)
def test_d2_start_time_guard_mcc_and_mcdc(
    client, access_env, row_id, cleaned_ok, edit_flag, actor_key, start_in_past, expect_start_error
):
    """Verify every feasible MCC row and all 4 MC/DC independence pairs (A, B, C, D) for D2."""
    u = access_env["users"]
    now = timezone.now()
    start = now - timedelta(hours=1) if start_in_past else now + timedelta(days=2)
    end = start + timedelta(hours=3)

    if edit_flag:
        req = make_access_request(
            u["lab_user"],
            access_env["cleanroom_level"],
            buddies=[u["buddy_user"]],
        )
        url = reverse("edit_access_request", args=[req.id])
    else:
        url = reverse("create_access_request")

    post_data = make_form_post_data(
        access_env["cleanroom_level"],
        start,
        end,
        other_users=[u["buddy_user"]],
        description=f"D2 case {row_id}",
    )
    if not cleaned_ok:
        # Force a pre-existing form error (missing required physical_access_level) so form.clean() returns None
        post_data["physical_access_level"] = ""

    client.force_login(u[actor_key])
    resp = client.post(url, data=post_data)

    if expect_start_error:
        assert resp.status_code == 200
        assert "The start time must be later than the current time" in str(resp.context["form"].errors.get("start_time", ""))
    elif not cleaned_ok:
        assert resp.status_code == 200
        assert "start_time" not in resp.context["form"].errors
    else:
        assert resp.status_code == 302


# =============================================================================
# D3: Reviewer Decision Gate (access_requests.py:133-141)
#     Decision Table: E (edit), R (user in reviewers), P (approve_request in POST), Q (deny_request in POST)
#     MC/DC Independence Pairs for outer gate (E AND R):
#       - E: (T,T -> enters gate) vs (F,T -> stays PENDING on create even with approve_request in POST)
#       - R: (T,T -> enters gate) vs (T,F -> creator POSTing approve_request stays PENDING)
# =============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case_id,edit_flag,actor_key,post_flags,expected_status,expected_grants",
    [
        # E=False, R=True (reviewer creates new request with approve_request in POST) -> stays PENDING, 0 grants
        ("D3-DT1_create_with_approve", False, "facility_reviewer", {"approve_request": ""}, RequestStatus.PENDING, 0),
        # E=True, R=False (creator edits own request injecting approve_request in POST) -> stays PENDING, 0 grants
        ("D3-DT2_creator_injects_approve", True, "lab_user", {"approve_request": ""}, RequestStatus.PENDING, 0),
        # E=True, R=True, P=False, Q=False -> stays PENDING, 0 grants
        ("D3-DT3_reviewer_no_decision", True, "facility_reviewer", {}, RequestStatus.PENDING, 0),
        # E=True, R=True, P=True, Q=False -> APPROVED, 2 grants
        ("D3-DT4_reviewer_approves", True, "facility_reviewer", {"approve_request": ""}, RequestStatus.APPROVED, 2),
        # E=True, R=True, P=False, Q=True -> DENIED, 0 grants
        ("D3-DT5_reviewer_denies", True, "facility_reviewer", {"deny_request": ""}, RequestStatus.DENIED, 0),
        # E=True, R=True, P=True, Q=True -> approve_request takes precedence (next(iter(["approve_request", "deny_request"])))
        (
            "D3-DT6_both_approve_and_deny",
            True,
            "facility_reviewer",
            {"approve_request": "", "deny_request": ""},
            RequestStatus.APPROVED,
            2,
        ),
    ],
)
def test_d3_reviewer_decision_table_and_mcdc(
    client, access_env, case_id, edit_flag, actor_key, post_flags, expected_status, expected_grants
):
    """Verify full decision table & MC/DC pairs for D3 reviewer approval/denial gate."""
    u = access_env["users"]
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(hours=2)

    if edit_flag:
        req = make_access_request(u["lab_user"], access_env["cleanroom_level"], buddies=[u["buddy_user"]])
        url = reverse("edit_access_request", args=[req.id])
    else:
        req = None
        url = reverse("create_access_request")

    client.force_login(u[actor_key])
    resp = client.post(
        url,
        data=make_form_post_data(
            access_env["cleanroom_level"],
            start,
            end,
            other_users=[u["buddy_user"]],
            description=f"D3 {case_id}",
            extra=post_flags,
        ),
    )
    assert resp.status_code == 302
    saved = TemporaryPhysicalAccessRequest.objects.get(description=f"D3 {case_id}")
    assert saved.status == expected_status
    assert TemporaryPhysicalAccess.objects.count() == expected_grants


# =============================================================================
# D4a & D4b: List Visibility Decisions (access_requests.py:60 & 66)
#   D4a: (not user_is_reviewer) AND (not user_is_staff) -> 4 MCC rows
#   D4b: (user not in creator_and_other_users) AND (user not in reviewers) -> 4 MCC rows
# =============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "row_id,actor_key,sees_unrelated_isolated",
    [
        # D4a-R1 (R=F, S=F -> True: restricted to my_requests only)
        ("D4a-R1_FF", "lab_user", False),
        # D4a-R2 (R=F, S=T -> False: staff sees all) [MC/DC pair for S]
        ("D4a-R2_FT", "user_office_staff", True),
        # D4a-R3 (R=T, S=F -> False: area reviewer enters elif) [MC/DC pair for R]
        ("D4a-R3_TF", "area_only_reviewer", False),
        # D4a-R4 (R=T, S=T -> False: facility manager enters elif; sees cleanroom, excluded from isolated)
        ("D4a-R4_TT", "facility_reviewer", False),
    ],
)
def test_d4a_visibility_role_guard_mcc_and_mcdc(client, access_env, row_id, actor_key, sees_unrelated_isolated):
    """Verify all 4 MCC rows & MC/DC pairs for D4a (`not user_is_reviewer and not user_is_staff`)."""
    u = access_env["users"]
    req_isolated = make_access_request(u["other_requester"], access_env["isolated_level"], buddies=[u["buddy_user_2"]])

    client.force_login(u[actor_key])
    resp = client.get(reverse("access_requests"))
    assert resp.status_code == 200
    visible_ids = {r.id for r in resp.context["pending_access_requests"]}
    assert (req_isolated.id in visible_ids) is sees_unrelated_isolated


@pytest.mark.django_db
@pytest.mark.parametrize(
    "row_id,creator_key,level_key,expect_visible_to_area_reviewer",
    [
        # D4b-R1: M=True (actor is creator), V=True (actor is reviewer) -> Excluded=False (Visible=True)
        ("D4b-R1_in_both", "area_only_reviewer", "cleanroom_level", True),
        # D4b-R2: M=True (actor is creator), V=False (actor NOT reviewer) -> Excluded=False (Visible=True) [MC/DC pair for M]
        ("D4b-R2_creator_only", "area_only_reviewer", "isolated_level", True),
        # D4b-R3: M=False (not creator/buddy), V=True (actor IS reviewer) -> Excluded=False (Visible=True) [MC/DC pair for V]
        ("D4b-R3_reviewer_only", "lab_user", "cleanroom_level", True),
        # D4b-R4: M=False (not creator/buddy), V=False (not reviewer) -> Excluded=True (Visible=False) [MC/DC anchor]
        ("D4b-R4_neither", "other_requester", "isolated_level", False),
    ],
)
def test_d4b_reviewer_exclusion_filter_mcc_and_mcdc(
    client, access_env, row_id, creator_key, level_key, expect_visible_to_area_reviewer
):
    """Verify all 4 MCC rows & MC/DC pairs for D4b reviewer exclusion filter."""
    u = access_env["users"]
    req = make_access_request(u[creator_key], access_env[level_key], buddies=[u["buddy_user"]])

    client.force_login(u["area_only_reviewer"])
    resp = client.get(reverse("access_requests"))
    assert resp.status_code == 200
    visible_ids = {r.id for r in resp.context["pending_access_requests"]}
    assert (req.id in visible_ids) is expect_visible_to_area_reviewer


# =============================================================================
# D5: Model Time-Order Validation (NEMO/models.py:658)
#     Predicate: S AND E AND C
#       S = bool(self.start_time), E = bool(self.end_time), C = (self.end_time <= self.start_time)
#     MC/DC Independence Pairs:
#       - S: (T,T,T -> raises) vs (F,T,N/A -> ok)
#       - E: (T,T,T -> raises) vs (T,F,N/A -> ok)
#       - C: (T,T,T -> raises) vs (T,T,F -> ok)
# =============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "row_id,has_start,has_end,end_lte_start,expect_error",
    [
        ("D5-R1_FFx", False, False, False, False),
        ("D5-R3_FTx", False, True, False, False),
        ("D5-R5_TFx", True, False, False, False),
        ("D5-R7_TTF", True, True, False, False),
        ("D5-R8_TTT", True, True, True, True),
    ],
)
def test_d5_model_clean_mcc_and_mcdc(access_env, row_id, has_start, has_end, end_lte_start, expect_error):
    """Verify all feasible MCC rows & MC/DC pairs for D5 (`start_time and end_time and end_time <= start_time`)."""
    u = access_env["users"]
    base = timezone.now() + timedelta(days=1)
    start = base if has_start else None
    if not has_end:
        end = None
    elif end_lte_start:
        end = base - timedelta(minutes=5)
    else:
        end = base + timedelta(hours=1)

    req = TemporaryPhysicalAccessRequest(
        creator=u["lab_user"],
        physical_access_level=access_env["cleanroom_level"],
        start_time=start,
        end_time=end,
    )
    if expect_error:
        with pytest.raises(ValidationError):
            req.clean()
    else:
        req.clean()
