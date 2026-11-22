# Phase 3: Mutation Analysis, Custom Business-Rule Operators & Surviving-Mutant Remediation

**Course:** SE3002 — Software Quality Engineering (Fall 2026) — Section A  
**Area 1 Owner:** Jaweria Abdul Hameed (`24I-3025`, Git: `Jaweria-Abdul-Hameed`)  
**Tool:** `Cosmic Ray 8.9.0` (Python 3.12, `stevedore` operator-provider plugin architecture)  
**Target Modules:** `NEMO/views/access_requests.py` (full core + custom mutation run, 162 mutants) and `NEMO/forms.py` (`TemporaryPhysicalAccessRequestForm`, custom `RelaxBuddyMinimumOperator`)  
**Raw Evidence Files:**
- Baseline Session & Report: `docs/evidence/cr_baseline.sqlite`, `docs/evidence/cr_baseline_report.txt`
- Final Session & Report: `docs/evidence/cr_final.sqlite`, `docs/evidence/cr_final_report.txt`
- Custom Forms Operator Session & Report: `docs/evidence/cr_forms_custom.sqlite`, `docs/evidence/cr_forms_custom_report.txt`
- Custom Operator Package: `sqe_mutators/sqe_mutators/operators.py`, `sqe_mutators/sqe_mutators/provider.py`
- Parallel Runner: `scripts/run_cosmic_ray_parallel.py`, `scripts/run_custom_forms_mutation.py`

---

## 1. Custom Business-Rule Mutation Operators (`sqe_mutators`, `nemo_br/*`)

Registered via `pyproject.toml` entry point `cosmic_ray.operator_providers -> nemo_br` (`4` custom operators implemented; `>= 2` required):

| Custom Operator (`nemo_br/*`) | Business Rule / Risk Modelled | Exact AST Mutation Performed | Target Mutants Generated | Baseline Killed | Final Killed |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `nemo_br/FlipApprovalStatusOperator` | **BR-3 / FR-07 / FR-08 / PR-03** (State-Transition Defect) | Swaps `RequestStatus.APPROVED <-> RequestStatus.DENIED` and `RequestStatus.PENDING -> RequestStatus.EXPIRED` | 10 (`access_requests.py`) | 8 / 10 (2 survived on L71–72) | **10 / 10 (100%)** |
| `nemo_br/SkipGrantCreationOperator` | **BR-3 / FR-07 / PR-04** (Missing Grant Side-Effect) | Replaces `create_temporary_access(access_request)` statement with `pass` | 1 (`access_requests.py`) | 1 / 1 | **1 / 1 (100%)** |
| `nemo_br/BypassReviewerCheckOperator` | **BR-2 / BR-4 / PR-02** (Reviewer Authorization Bypass) | Replaces `is_user_a_reviewer(user)` call with `True` | 1 (`access_requests.py`) | 1 / 1 | **1 / 1 (100%)** |
| `nemo_br/RelaxBuddyMinimumOperator` | **BR-1 / FR-02 / PR-06** (Off-by-One Buddy Boundary) | Replaces `minimum_total_users - 1` with `minimum_total_users - 2` in `NEMO/forms.py:543,546` | 2 (`forms.py`) | 2 / 2 | **2 / 2 (100%)** |

---

## 2. Before vs. After Mutation Score Summary (`NEMO/views/access_requests.py`)

Even with **100% statement (148/148) and 100% branch (50/50) coverage** on `NEMO/views/access_requests.py`, the initial 65-test white-box suite left **43 surviving mutants** (`73.46%` mutation score) — proving why structural coverage alone is insufficient for strong fault detection.

| Metric | Baseline Run (65 Unit Tests, 100% Stmt/Branch) | Final Run (74 Unit Tests + `test_mutation_killers.py`) | Delta |
| :--- | :---: | :---: | :---: |
| **Total Mutants Executed** | 162 (`150 core/*` + `12 nemo_br/*`) | 162 (`150 core/*` + `12 nemo_br/*`) | — |
| **Killed Mutants** | 119 | **151** | **+32 killed** |
| **Surviving Mutants (Total)** | 43 | **11** (all 11 mathematically equivalent) | **-32 surviving** |
| **Killable Mutants Remaining** | 32 | **0** | **100% of killables killed** |
| **Raw Mutation Score (`Killed / Total`)** | **73.46%** | **93.21%** | **+19.75 pp** |
| **Equivalent-Adjusted Mutation Score (`Killed / (Total - Equiv)`)** | 78.81% (`119/151`) | **100.00%** (`151/151`) | **+21.19 pp** |
| **Custom Business-Rule Mutants Killed (`nemo_br/*` total)** | 12 / 14 (`85.71%`) | **14 / 14 (`100.00%`)** | **+14.29 pp** |

*Exit Criterion `EC-01` Verification:* Raw mutation score **93.21% >= 85% target**, **0** unaddressed killable mutants, justifying an **85% raw mutation score CI quality gate threshold** for Phase 7.

---

## 3. Surviving-Mutant Analysis (All 43 Baseline Survivors Inspected; >= 15 Required)

Every single surviving mutant from `docs/evidence/cr_baseline_report.txt` was inspected by diff, classified as **`missing test`**, **`weak assertion`**, or **`equivalent`**, and resolved via `tests/team/unit/test_mutation_killers.py` (`MK-01`..`MK-09`):

| # | Baseline Job ID | Line | Operator & Mutation | Classification | Remediation / Equivalence Proof | Final Status |
| :---: | :---: | :---: | :--- | :---: | :--- | :---: |
| 1 | `8ab5eeab` | L43 | `core/RemoveDecorator#0`: remove `@login_required` on `access_requests` | `missing test` | Added `MK-01` asserting anonymous `GET` redirects `302 -> /login` | **KILLED** |
| 2 | `71290c74` | L44 | `core/RemoveDecorator#1`: remove `@require_GET` on `access_requests` | `missing test` | Added `MK-02` asserting `POST /access_requests/` returns `405` | **KILLED** |
| 3 | `7ce31961` | L56 | `core/ReplaceBinaryOperator_BitOr_BitXor`: `Q(creator=user) | Q(...)` -> `^` | `missing test` | Added `MK-03` with creator also listed in `other_users` (`|` retains, `^` hides) | **KILLED** |
| 4 | `290ebbff` | L59 | `core/ReplaceOrWithAnd#0`: `is_facility_manager and is_user_office or is_staff` | `missing test` | Killed by `MK-04` (`is_facility_manager=False, is_user_office=True, is_staff=False` fails `(False and True) or False`) | **KILLED** |
| 5 | `662719f5` | L59 | `core/ReplaceOrWithAnd#1`: `is_facility_manager or is_user_office and is_staff` | `missing test` | Killed by `MK-04` (`office_only_nonstaff` sees all requests under `or`, hidden under `and`) | **KILLED** |
| 6 | `cdf1330f` | L71 | `nemo_br/FlipApprovalStatusOperator#1`: `approved_access_requests` filters `DENIED` | `weak assertion` | Added `MK-06` asserting exact `approved_access_requests` context queryset | **KILLED** |
| 7 | `8e018cf6` | L72 | `nemo_br/FlipApprovalStatusOperator#2`: `denied_access_requests` filters `APPROVED` | `weak assertion` | Added `MK-06` asserting exact `denied_access_requests` context queryset | **KILLED** |
| 8 | `0cec2c02` | L76 | `core/ReplaceFalseWithTrue#1`: `get_notifications(..., delete=True)` | `weak assertion` | Added `MK-06` asserting reviewer's pending notification persists in DB after viewing list | **KILLED** |
| 9 | `21f3aef5` | L88 | `core/RemoveDecorator#2`: remove `@login_required` on `create_access_request` | `missing test` | Added `MK-01` asserting anonymous `GET` redirects `302 -> /login` | **KILLED** |
| 10 | `7d7fb7eb` | L89 | `core/RemoveDecorator#3`: remove `@require_http_methods(["GET", "POST"])` | `missing test` | Added `MK-02` asserting `DELETE /create_access_request/` returns `405` | **KILLED** |
| 11 | `dd8022f0` | L98 | `core/ReplaceTrueWithFalse#0`: `allow_user_request=False` | `weak assertion` | Added `MK-07` asserting `cleanroom_level` in context & `non_requestable_level` excluded | **KILLED** |
| 12 | `1401ff18` | L99 | `core/ReplaceTrueWithFalse#1`: `User.objects.filter(is_active=False)` | `weak assertion` | Added `MK-07` asserting `buddy_user` in `other_users` & `inactive_user` excluded | **KILLED** |
| 13 | `3b0a013e` | L102 | `core/ReplaceComparisonOperator_Eq_GtE#0`: `request.method >= "POST"` | **`equivalent`** | `@require_http_methods(["GET", "POST"])` restricts methods to `{"GET", "POST"}`; `"GET" < "POST"`, so `m >= "POST" <=> m == "POST"` | Equivalent |
| 14 | `2b5a28bd` | L102 | `core/ReplaceComparisonOperator_Eq_IsNot#0`: `request.method is not "POST"` | `weak assertion` | Added `MK-07` asserting `GET` form has `is_bound is False` and no validation errors | **KILLED** |
| 15 | `3c10975c` | L102 | `core/ReplaceComparisonOperator_Eq_LtE#0`: `request.method <= "POST"` | `weak assertion` | Added `MK-07` asserting `GET` form has `is_bound is False` (`"GET" <= "POST"` falsely ran POST path) | **KILLED** |
| 16 | `13f7a683` | L109 | `core/ReplaceComparisonOperator_NotEq_Gt#0`: `status > RequestStatus.PENDING` | **`equivalent`** | `RequestStatus` domain is `{0, 1, 2, 3}` (all `>= 0`); `s > 0 <=> s != 0` for all valid states | Equivalent |
| 17 | `112ad9ef` | L126 | `core/ReplaceComparisonOperator_Lt_LtE#0`: `start_time <= timezone.now()` | `missing test` | Added `MK-05` freezing `timezone.now() == start_time` (exact boundary passes `<`, fails `<=`) | **KILLED** |
| 18 | `e6dc075f` | L136 | `core/ReplaceComparisonOperator_Eq_Is#1`: `next(iter(decision)) is "approve_request"` | **`equivalent`** | `decision` elements come directly from interned literal list `["approve_request", "deny_request"]` (L134) | Equivalent |
| 19 | `9812bd42` | L136 | `core/ReplaceComparisonOperator_Eq_LtE#1`: `next(iter(decision)) <= "approve_request"` | **`equivalent`** | Domain is `{"approve_request", "deny_request"}` where `"approve_request" < "deny_request"` | Equivalent |
| 20 | `85ac29ef` | L149 | `core/AddNot#15`: `if not user in access_request.reviewers():` | `weak assertion` | Added `MK-08` asserting creator edit preserves other reviewers' notifications while reviewer edit deletes them | **KILLED** |
| 21 | `9eaaaef1` | L164 | `core/RemoveDecorator#4`: remove `@login_required` on `delete_access_request` | `missing test` | Added `MK-01` asserting anonymous `GET` redirects `302 -> /login` | **KILLED** |
| 22 | `06a1ec28` | L165 | `core/RemoveDecorator#5`: remove `@require_GET` on `delete_access_request` | `missing test` | Added `MK-02` asserting `POST /delete_access_request/<id>/` returns `405` | **KILLED** |
| 23 | `6efa57bd` | L171 | `core/ReplaceComparisonOperator_NotEq_Gt#3`: `status > RequestStatus.PENDING` | **`equivalent`** | `RequestStatus` values are `{0, 1, 2, 3}`, so `s > 0 <=> s != 0` | Equivalent |
| 24 | `40374136` | L217 | `core/ReplaceComparisonOperator_Eq_Is#2`: `status is RequestStatus.APPROVED` | **`equivalent`** | CPython interns small integers `[-5, 256]`; `s is 1 <=> s == 1` | Equivalent |
| 25 | `cb533622` | L218 | `core/ReplaceComparisonOperator_Eq_GtE#3`: `status >= RequestStatus.DENIED` | `missing test` | Added `MK-09` testing `EXPIRED (3)` status (`3 >= 2` falsely yields `"denied"` instead of `"updated"`) | **KILLED** |
| 26 | `06121d3c` | L218 | `core/ReplaceComparisonOperator_Eq_Is#3`: `status is RequestStatus.DENIED` | **`equivalent`** | CPython small-int cache `[-5, 256]`; `s is 2 <=> s == 2` | Equivalent |
| 27–32, 35–38, 41–42 | *(12 job IDs)* | L221 | `AddNot#22/23`, `Eq_Gt#4/5`, `Eq_GtE#4/5`, `Eq_IsNot#4/5`, `Eq_Lt#4/5`, `Eq_NotEq#4/5` on `color_type` | `weak assertion` | Added `MK-09` asserting exact `bootstrap_primary_color("success"|"danger"|"info")` rendered into email body | **ALL 12 KILLED** |
| 33–34 | `096b0fbb`, `778931d0` | L221 | `Eq_Is#4/5`: `status is "approved"` / `status is "denied"` | **`equivalent`** | `status` is assigned exclusively from interned string literals `{"approved", "denied", "updated", "received"}` (L215–219) | Equivalent |
| 39–40 | `c1c7ce41`, `39e4365e` | L221 | `Eq_LtE#4/5`: `status <= "approved"` / `status <= "denied"` | **`equivalent`** | Alphabetical order is `"approved" < "denied" < "received" < "updated"`, so `"approved"` is the domain min and `"denied"` is the min after excluding `"approved"` | Equivalent |
| 43 | `8e75f0ee` | L252 | `core/RemoveDecorator#7`: remove `@require_GET` on `csv_export` | `missing test` | Added `MK-02` asserting `POST /export_access_requests/` returns `405` | **KILLED** |
