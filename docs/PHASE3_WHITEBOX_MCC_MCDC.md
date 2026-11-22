# Phase 3: White-Box Unit Testing, Complete MCC Truth Tables & MC/DC Analysis

**Course:** SE3002 — Software Quality Engineering (Fall 2026) — Section A  
**Area 1 Owner:** Jaweria Abdul Hameed (`24I-3025`)  
**Tool Stack:** `pytest 9.2.0`, `pytest-django 4.14.0`, `coverage.py 7.17.4` (branch mode)  
**Test Files (Isolated in `tests/team/unit/`):**
- `tests/team/unit/test_baseline_smoke.py` (2 tests)
- `tests/team/unit/test_access_requests_whitebox.py` (27 tests: business rules, BVA, state transitions, roles, email, CSV)
- `tests/team/unit/test_mcdc_decisions.py` (36 tests: complete MCC truth tables & MC/DC independence pairs across D1–D5)
- `tests/team/unit/test_mutation_killers.py` (added after baseline mutation analysis to kill every killable surviving mutant)

---

## 1. 100% Statement & Branch Coverage Verification

Measured with `coverage run -m pytest tests/team/unit --nomigrations` (`branch = True` in `.coveragerc`; raw evidence in `docs/evidence/phase3_unit_coverage.json`):

| Server-Side Business Logic Target | Line Range | Statements Covered | Statement % | Branches Covered | Branch % | Uncovered Code Justification |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `NEMO/views/access_requests.py` (all 9 functions) | L1–L295 | **148 / 148** | **100.0%** | **50 / 50** | **100.0%** | None (0 uncovered statements, 0 partial branches) |
| `NEMO/forms.py :: TemporaryPhysicalAccessRequestForm` | L532–L549 | **13 / 13** | **100.0%** | **4 / 4** | **100.0%** | None (0 uncovered statements, 0 partial branches) |
| `NEMO/models.py :: TemporaryPhysicalAccess` & `TemporaryPhysicalAccessRequest` | L581–L664 | **51 / 51** | **100.0%** | **6 / 6** | **100.0%** | None (0 uncovered statements, 0 partial branches) |
| **Total Target Server-Side Business Logic** | — | **212 / 212** | **100.0%** | **60 / 60** | **100.0%** | **0 uncovered statements, 0 uncovered branches** |

*Note:* Upstream tests in `NEMO/tests/` are strictly excluded from execution and coverage counts.

---

## 2. State-Transition Matrix Coverage (BR-3)

Every allowed state transition AND at least one disallowed transition from EVERY state is automated in `tests/team/unit/test_access_requests_whitebox.py`:

| Current State | Trigger / Action | Allowed? | Expected Result & Postcondition | Automated Unit Test |
| :--- | :--- | :---: | :--- | :--- |
| `PENDING (0), deleted=False` | Creator edits fields (future start, valid buddies) | **Allowed** | Remains `PENDING (0)`, fields updated, `last_updated_by=creator` | `test_edit_access_request_by_creator_keeps_pending_and_updates_fields` |
| `PENDING (0), deleted=False` | Reviewer edits without decision button | **Allowed** | Remains `PENDING (0)`, past `start_time` permitted, `reviewer=None` | `test_state_transition_reviewer_edit_without_decision_keeps_pending` |
| `PENDING (0), deleted=False` | Reviewer submits `approve_request` | **Allowed** | Transitions `PENDING -> APPROVED (1)`, sets `reviewer`, creates `TemporaryPhysicalAccess` for creator + all buddies | `test_state_transition_pending_to_approved_creates_grants` |
| `PENDING (0), deleted=False` | Reviewer submits `deny_request` | **Allowed** | Transitions `PENDING -> DENIED (2)`, sets `reviewer`, creates **0** `TemporaryPhysicalAccess` rows | `test_state_transition_pending_to_denied_creates_zero_grants` |
| `PENDING (0), deleted=False` | `mark_requests_expired()` with `end_time < now` | **Allowed** | Transitions `PENDING -> EXPIRED (3)`, deletes pending notifications | `test_state_transition_pending_to_expired_via_mark_requests_expired` |
| `PENDING (0), deleted=False` | Creator invokes `delete_access_request` | **Allowed** | Sets `deleted=True`, removes notifications | `test_state_transition_pending_to_deleted_by_creator` |
| `APPROVED (1), deleted=False` | Edit via `edit_access_request` / Delete via `delete_access_request` | **Disallowed** | Edit rejected (`Only pending requests can be modified.`); Delete returns `400 Bad Request` | `test_disallowed_edit_from_non_pending_or_deleted_states[1]`, `test_disallowed_delete_from_non_pending_states[1]` |
| `DENIED (2), deleted=False` | Edit via `edit_access_request` / Delete via `delete_access_request` | **Disallowed** | Edit rejected (`Only pending requests can be modified.`); Delete returns `400 Bad Request` | `test_disallowed_edit_from_non_pending_or_deleted_states[2]`, `test_disallowed_delete_from_non_pending_states[2]` |
| `EXPIRED (3), deleted=False` | Edit via `edit_access_request` / Delete via `delete_access_request` | **Disallowed** | Edit rejected (`Only pending requests can be modified.`); Delete returns `400 Bad Request` | `test_disallowed_edit_from_non_pending_or_deleted_states[3]`, `test_disallowed_delete_from_non_pending_states[3]` |
| `PENDING (0), deleted=True` | Edit via `edit_access_request` | **Disallowed** | Edit rejected (`You are not allowed to edit expired or deleted requests.`) | `test_disallowed_edit_from_non_pending_or_deleted_states[0-True]` |

---

## 3. Complete MCC Truth Tables & Derived MC/DC Independence Pairs

All 5 compound Boolean decisions (`>= 2` atomic conditions) in `NEMO/views/access_requests.py` and `NEMO/models.py` are enumerated completely below, with MC/DC independence pairs extracted directly from each MCC table and automated in `tests/team/unit/test_mcdc_decisions.py`.

### Decision D1 — Edit Authorization Guard (`NEMO/views/access_requests.py:106, 111`)
**Predicate:** $D_1 = E \land A \land B$
- $E$: `edit` (`bool(access_request)`)
- $A$: `access_request.creator != user`
- $B$: `user not in access_request.reviewers()`
- **Decision True Effect:** Appends `"You are not allowed to edit this request."`

#### Complete MCC Truth Table ($2^3 = 8$ rows)

| Row | $E$ (`edit`) | $A$ (`creator != user`) | $B$ (`not reviewer`) | Outcome $D_1$ | Feasibility & Short-Circuit Note | Automated Test ID |
| :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **R1–R4** | `F` | `*` (F/F/T/T) | `*` (F/T/F/T) | **False** | Feasible (when `edit=False`, `access_request is None`; $A,B$ short-circuited & undefined) | `D1-R1_R4_E_false` |
| **R5** | `T` | `F` | `F` | **False** | Feasible (`facility_reviewer` edits own request) | `D1-R5_TFF` |
| **R6** | `T` | `F` | `T` | **False** | Feasible (`lab_user` edits own request) | `D1-R6_TFT` |
| **R7** | `T` | `T` | `F` | **False** | Feasible (`facility_reviewer` edits `lab_user`'s request) | `D1-R7_TTF` |
| **R8** | `T` | `T` | `T` | **True** | Feasible (`other_requester` tries to edit `lab_user`'s request -> blocked) | `D1-R8_TTT` |

#### MC/DC Independence Pairs Derived from D1 MCC Table

| Condition | Pair (True Outcome vs False Outcome) | Held Constant | Independent Effect Verified |
| :---: | :--- | :--- | :--- |
| **$E$** | **R8** `(T, T, T -> True)` vs **R4** `(F, *, * -> False)` | Actor is non-creator, non-reviewer (`other_requester`) | Flipping `edit` alone flips $D_1$ |
| **$A$** | **R8** `(T, T, T -> True)` vs **R6** `(T, F, T -> False)` | $E=T$, $B=T$ | Flipping `creator != user` alone flips $D_1$ |
| **$B$** | **R8** `(T, T, T -> True)` vs **R7** `(T, T, F -> False)` | $E=T$, $A=T$ | Flipping `not reviewer` alone flips $D_1$ |

---

### Decision D2 — Past Start-Time Guard with Reviewer Override (`NEMO/views/access_requests.py:123-128`)
**Predicate:** $D_2 = A \land (B \lor C) \land D$
- $A$: `bool(cleaned_data)` (form had no prior errors)
- $B$: `not edit` (new request creation)
- $C$: `user not in access_request.reviewers()`
- $D$: `cleaned_data.get("start_time") < timezone.now()`
- **Decision True Effect:** Calls `form.add_error("start_time", "The start time must be later than the current time")`

#### Complete MCC Truth Table ($2^4 = 16$ rows)

| Row | $A$ (`cleaned`) | $B$ (`not edit`) | $C$ (`not reviewer`) | $D$ (`start < now`) | Outcome $D_2$ | Feasibility & Short-Circuit Note | Automated Test ID |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **R01–R08** | `F` | `F/T` | `F/T` | `F/T` | **False** | Short-circuited at $A=F$ (`cleaned_data` is `None`, so $D$ cannot be evaluated) | `D2-R01_R08_A_false_create`, `D2-R02_A_false_edit` |
| **R09** | `T` | `F` | `F` | `F` | **False** | Feasible (reviewer edits with future start) | `D2-R09_TFFF` |
| **R10** | `T` | `F` | `F` | `T` | **False** | Feasible (**Reviewer Override**: reviewer edits with past start -> allowed!) | `D2-R10_TFFT` |
| **R11** | `T` | `F` | `T` | `F` | **False** | Feasible (creator edits with future start) | `D2-R11_TFTF` |
| **R12** | `T` | `F` | `T` | `T` | **True** | Feasible (creator edits with past start -> rejected) | `D2-R12_TFTT` |
| **R13** | `T` | `T` | `F*` | `F` | **False** | Short-circuited on $C$ (reviewer creates new request with future start) | `D2-R13_TTFF` |
| **R14** | `T` | `T` | `F*` | `T` | **True** | Short-circuited on $C$ (reviewer creates new request with past start -> rejected!) | `D2-R14_TTFT` |
| **R15** | `T` | `T` | `T*` | `F` | **False** | Short-circuited on $C$ (lab_user creates new request with future start) | `D2-R15_TTTF` |
| **R16** | `T` | `T` | `T*` | `T` | **True** | Short-circuited on $C$ (lab_user creates new request with past start -> rejected) | `D2-R16_TTTT` |

*\*Note:* When $B = T$ (`not edit`), `access_request` is `None`, so Python's short-circuit `or` skips evaluating $C$ (`user not in access_request.reviewers()`). Testing both reviewer (`R13`, `R14`) and non-reviewer (`R15`, `R16`) actors verifies this short-circuit behavior cleanly.

#### MC/DC Independence Pairs Derived from D2 MCC Table

| Condition | Pair (True Outcome vs False Outcome) | Held Constant | Independent Effect Verified |
| :---: | :--- | :--- | :--- |
| **$A$** | **R16** `(T, T, T*, T -> True)` vs **R08** `(F, T, T*, * -> False)` | New request, `lab_user`, past start | Flipping `bool(cleaned_data)` alone flips $D_2$ |
| **$B$** | **R14** `(T, T, F*, T -> True)` vs **R10** `(T, F, F, T -> False)` | $A=T$, reviewer actor ($C=F$), $D=T$ | Flipping `not edit` alone flips $D_2$ |
| **$C$** | **R12** `(T, F, T, T -> True)` vs **R10** `(T, F, F, T -> False)` | $A=T$, $B=F$, $D=T$ | Flipping `user not in reviewers()` alone flips $D_2$ |
| **$D$** | **R12** `(T, F, T, T -> True)` vs **R11** `(T, F, T, F -> False)` | $A=T$, $B=F$, $C=T$ | Flipping `start_time < now` alone flips $D_2$ |

---

### Decision D3 — Reviewer Decision Table & Gate (`NEMO/views/access_requests.py:133-141`)
**Outer Gate:** $D_3 = E \land R$ (`edit and user in access_request.reviewers()`) combined with POST keys `P` (`approve_request`) and `Q` (`deny_request`).

| Rule ID | $E$ (`edit`) | $R$ (`in reviewers`) | $P$ (`approve_request`) | $Q$ (`deny_request`) | Expected Status | Expected `TemporaryPhysicalAccess` Grants | Automated Test ID |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **DT-1** | `F` | `T` | `T` | `F` | `PENDING (0)` | `0` | `D3-DT1_create_with_approve` |
| **DT-2** | `T` | `F` | `T` | `F` | `PENDING (0)` | `0` | `D3-DT2_creator_injects_approve` |
| **DT-3** | `T` | `T` | `F` | `F` | `PENDING (0)` | `0` | `D3-DT3_reviewer_no_decision` |
| **DT-4** | `T` | `T` | `T` | `F` | `APPROVED (1)` | `2` (creator + buddy) | `D3-DT4_reviewer_approves` |
| **DT-5** | `T` | `T` | `F` | `T` | `DENIED (2)` | `0` | `D3-DT5_reviewer_denies` |
| **DT-6** | `T` | `T` | `T` | `T` | `APPROVED (1)` | `2` (`approve_request` checked first) | `D3-DT6_both_approve_and_deny` |

**MC/DC Pairs for Outer Gate ($E \land R$):**
- Condition $E$: **DT-4** `(T, T -> enters gate)` vs **DT-1** `(F, T -> bypasses gate)`
- Condition $R$: **DT-4** `(T, T -> enters gate)` vs **DT-2** `(T, F -> bypasses gate)`

---

### Decisions D4a & D4b — List Visibility Guards (`NEMO/views/access_requests.py:60 & 66`)

**D4a:** $(\neg R) \land (\neg S)$ where $R =$ `user_is_reviewer`, $S =$ `user_is_staff` ($2^2 = 4$ MCC rows):
- **R1** `(F, F -> True)`: `lab_user` restricted to `my_requests` (`D4a-R1_FF`)
- **R2** `(F, T -> False)`: `user_office_staff` sees all requests (`D4a-R2_FT`) — **MC/DC pair for $S$ with R1**
- **R3** `(T, F -> False)`: `area_only_reviewer` enters `elif` (`D4a-R3_TF`) — **MC/DC pair for $R$ with R1**
- **R4** `(T, T -> False)`: `facility_reviewer` enters `elif` (`D4a-R4_TT`)

**D4b:** $(\neg M) \land (\neg V)$ where $M =$ `user in creator_and_other_users()`, $V =$ `user in reviewers()` ($2^2 = 4$ MCC rows):
- **R1** `(T, T -> False / Visible)`: `D4b-R1_in_both`
- **R2** `(T, F -> False / Visible)`: `D4b-R2_creator_only` — **MC/DC pair for $M$ with R4**
- **R3** `(F, T -> False / Visible)`: `D4b-R3_reviewer_only` — **MC/DC pair for $V$ with R4**
- **R4** `(F, F -> True / Excluded)`: `D4b-R4_neither`

---

### Decision D5 — Model Time-Order Validation (`NEMO/models.py:658`)
**Predicate:** $D_5 = S \land E \land C$ where $S=$ `bool(start_time)`, $E=$ `bool(end_time)`, $C=$ `end_time <= start_time` ($2^3 = 8$ rows; $C$ short-circuited when $S=F$ or $E=F$):
- **R1–R2** `(F, F, *) -> False`: `D5-R1_FFx`
- **R3–R4** `(F, T, *) -> False`: `D5-R3_FTx` — **MC/DC pair for $S$ with R8**
- **R5–R6** `(T, F, *) -> False`: `D5-R5_TFx` — **MC/DC pair for $E$ with R8**
- **R7** `(T, T, F) -> False`: `D5-R7_TTF` — **MC/DC pair for $C$ with R8**
- **R8** `(T, T, T) -> True (raises ValidationError)`: `D5-R8_TTT`
