# Viva Defense Rehearsal, Component Q&A & Live Mutation Guide

**Course:** SE3002 — Software Quality Engineering (Fall 2026) — Section A  
**Group Trio (Roll Numbers & Ownership):**
1. **Jaweria Abdul Hameed (`24I-3025`)** — **Area 1:** Static analysis, SonarQube, CFG CC, White-box unit testing, MCC truth tables, MC/DC pairs, Cosmic Ray mutation analysis, custom mutators, CI quality gate workflow.
2. **Mohsin Khan (`24I-3135`)** — **Area 2:** OpenAPI 3.0.3 specification, automated EP & 3-point BVA test data generator, 2-constraint regeneration demo, REST API & integration testing, PR #1 documented fix.
3. **Muhammad Aun (`24P-3099`)** — **Area 3:** 6 Use Case specifications, Playwright Chromium E2E automation, Usability & keyboard navigation, axe-core & Lighthouse audits + 1-screen remediation, OWASP ZAP passive scanning, pip-audit dependency audit, Grafana k6 OSS load benchmarks, failure-and-recovery test double, PR #2 blocked demonstration.
4. **Shared Across All Members:** System selection, reproducible baseline, Living Test Plan, 5×5 Risk Register, Exit Criteria, Traceability Matrix, GitHub Issues defect lifecycle, 2 Major RCAs (5 Whys + Fishbone), Pareto analysis, Weekly GQM reports, PERT vs actual effort, Test Completion Report & Release decision, AI-use disclosure.

---

## 1. Quick-Start Test Rerun Commands for Live Defense

Every member must be able to rerun their owned tests live in under 30 seconds and explain every assertion.

```powershell
# -------------------------------------------------------------
# 0. Global Setup & Local DB Reset (Always run first)
# -------------------------------------------------------------
.\venv\Scripts\python.exe scripts\reset_local_db.py

# -------------------------------------------------------------
# Area 1: Jaweria Abdul Hameed (24I-3025)
# -------------------------------------------------------------
# Run White-Box Unit Tests with 100% Statement & Branch Coverage:
.\venv\Scripts\coverage.exe run --source=NEMO --branch -m pytest tests/team/unit --reuse-db -v
.\venv\Scripts\coverage.exe report -m --include="*access_requests*"

# Run Complete MC/DC Decisions Suite (D1 through D5):
.\venv\Scripts\python.exe -m pytest tests/team/unit/test_mcdc_decisions.py -v

# Run Custom Business-Rule Mutation Operators (14/14 killed = 100%):
.\venv\Scripts\python.exe scripts\run_custom_forms_mutation.py

# Run Strict CI Quality Gate Checker:
.\venv\Scripts\python.exe scripts\ci_quality_gate_check.py

# -------------------------------------------------------------
# Area 2: Mohsin Khan (24I-3135)
# -------------------------------------------------------------
# Run Automated EP & 3-Point BVA Test Data Generator:
.\venv\Scripts\python.exe scripts\generate_api_test_data.py

# Run OpenAPI 2-Constraint Contract Regeneration Demo:
.\venv\Scripts\python.exe scripts\demo_openapi_regeneration.py

# Run Entire 155 API & Integration Test Suite:
.\venv\Scripts\python.exe -m pytest tests/team/api --reuse-db -v

# Run W-API-01 Regression Fix Test (PR #1 Verification):
.\venv\Scripts\python.exe -m pytest tests/team/api/test_api_integration_and_cross_workflow.py -k "test_w_api_01" -v

# -------------------------------------------------------------
# Area 3: Muhammad Aun (24P-3099)
# -------------------------------------------------------------
# Run All 40 Playwright Chromium Browser Tests (E2E + Usability + Security):
node node_modules/@playwright/test/cli.js test

# Run 30 E2E Use Case Flows Specifically:
node node_modules/@playwright/test/cli.js test tests/team/e2e/use_cases.spec.mjs

# Run Usability & Keyboard Navigation Suite:
node node_modules/@playwright/test/cli.js test tests/team/usability/usability_and_keyboard.spec.mjs

# Run Role-Based Access Control Checks (SEC-RBAC-01..08):
node node_modules/@playwright/test/cli.js test tests/team/security/role_checks.spec.mjs

# Run Controlled Failure-and-Recovery State-Change Test:
.\venv\Scripts\python.exe -m pytest tests/team/recovery/test_failure_and_recovery.py -v

# Run pip-audit Dependency Vulnerability Check:
.\venv\Scripts\pip-audit.exe --skip-editable
```

---

## 2. Area 1 Viva Defense: Static Analysis, White-Box, MC/DC, Mutation & CI Gate
**Owner:** Jaweria Abdul Hameed (`24I-3025`)

### Key Explanations & Viva Questions
- **Q1: Why did SonarQube report Cyclomatic Complexity = 50 on `access_requests()`? How did you verify it?**  
  *Answer:* `access_requests()` handles role-based query filtering across 4 roles, date-filtering, search-string filtering, CSV export branching, and requests-expired processing. We constructed the Control Flow Graph (CFG) for the permission-branching core: with $N=14$ basic blocks and $E=19$ edges, $V(G) = E - N + 2P = 19 - 14 + 2(1) = 7$, exactly matching predicate counting ($P_c + 1 = 6 + 1 = 7$).
- **Q2: How did you derive MC/DC pairs from MCC truth tables?**  
  *Answer:* For each multi-condition Boolean rule (D1–D5), we first constructed the complete Truth Table ($2^n$ rows). For each condition $C_i$, we identified an independence pair $(r_A, r_B)$ where only $C_i$ flips ($T \leftrightarrow F$), all other conditions remain fixed, and the overall decision outcome flips. For D1 ($D_1 = E \land A \land B$, 8 rows), the MC/DC pairs are: for $E$ (Row 8 vs Row 4), for $A$ (Row 8 vs Row 6), and for $B$ (Row 8 vs Row 7). Each pair was automated as a distinct test case in `tests/team/unit/test_mcdc_decisions.py`.
- **Q3: What are your two custom mutation operators and why are they relevant to business rules?**  
  *Answer:* Built in `sqe_mutators/`:
  1. `RelaxBuddyMinimumOperator`: Replaces `access_requests_minimum_users` comparison (`< min_users` $\to$ `< (min_users - 1)` or `<= 0`), simulating boundary relaxation.
  2. `SkipGrantCreationOperator`: Mutates reviewer approval by deleting or skipping `create_temporary_access()`, simulating state transition without grant side-effects (`PR-04`).
  All 14 custom business-rule mutants were killed ($100\%$ score).
- **Q4: Why were 11 mutants surviving in Cosmic Ray and how were they proven equivalent?**  
  *Answer:* The 11 surviving mutants were analyzed line-by-line:
  - 4 mutants swapped commutative operands in `A or B` expressions (`edit or creator_only`).
  - 3 mutants replaced `status` variable reuse where the value is overwritten immediately.
  - 4 mutants altered unused default parameters in internal email helper wrappers.
  None represent executable semantic defects, yielding an equivalent-adjusted mutation score of $100.0\%$.
- **Q5: How does the CI Quality Gate prevent escapes?**  
  *Answer:* `.github/workflows/ci.yml` contains strictly NO `continue-on-error` and NO `|| true`. Any lint breach, test failure, coverage drop below 90% statement / 85% branch, or mutation drop below 90% exits with code 1, automatically blocking the PR.

---

## 3. Area 2 Viva Defense: OpenAPI Spec, Automated EP/BVA Generator & API Testing
**Owner:** Mohsin Khan (`24I-3135`)

### Key Explanations & Viva Questions
- **Q1: How does your test data generator read the OpenAPI spec and generate EP and 3-point BVA values?**  
  *Answer:* `scripts/generate_api_test_data.py` parses `openapi/temporary_physical_access_requests.yaml`. For every schema property, it inspects boundaries:
  - Numeric / String lengths: generates *just below* ($min - 1$), *exactly at* ($min$), and *just above* ($min + 1$) for lower bounds; and ($max - 1$), ($max$), ($max + 1$) for upper bounds.
  - Enum / Types: generates valid nominals and invalid types (null, string for int, negative for PK).
  - Generates 141 discrete cases stored in `tests/team/api/generated_test_data.json` consumed by `pytest.mark.parametrize`.
- **Q2: What happened when you changed two constraints in the OpenAPI spec?**  
  *Answer:* Demonstrated in `scripts/demo_openapi_regeneration.py`:
  1. Constraint 1: `other_users.minItems` changed from `1` $\to$ `2` (minimum buddies increased from 1 to 2).
  2. Constraint 2: `description.maxLength` changed from `500` $\to$ `200`.
  The generator dynamically adapted: boundary test values for `minItems` updated from $[0, 1, 2]$ to $[1, 2, 3]$, and `maxLength` updated from $[499, 500, 501]$ to $[199, 200, 201]$. Verified by programmatic diff assertions in `test_openapi_two_constraint_regeneration_produces_updated_bva_and_payload`.
- **Q3: What critical defects did your API tests uncover that UI tests missed?**  
  *Answer:* Uncovered 9 major API weaknesses (`W-API-01` to `W-API-09`):
  - `W-API-01`: API accepted 0 buddies when `min_users=2` (fixed in PR #1).
  - `W-API-03`: Arbitrary state updates via `PATCH` (`APPROVED -> PENDING`).
  - `W-API-04`: API approval updated status to `APPROVED` without creating `TemporaryPhysicalAccess` records (grant gap).
  - `W-API-05`: BOLA vulnerability where `lab_user` approved another requester's request.
- **Q4: Walk through PR #1 (Documented Fix PR).**  
  *Answer:* PR #1 (`fix/w-api-01-buddy-count-serializer`) added failing regression test `test_w_api_01_api_rejects_below_minimum_buddy_count_with_400`. Before the fix, DRF returned HTTP 200, causing test failure (`assert 200 == 400`). We added `validate()` to `TemporaryPhysicalAccessRequestSerializer` in `NEMO/serializers.py`, reran CI, and all 230 tests passed.

---

## 4. Area 3 Viva Defense: E2E, Usability, Accessibility, Security & Performance
**Owner:** Muhammad Aun (`24P-3099`)

### Key Explanations & Viva Questions
- **Q1: How do your Playwright E2E tests assert both UI rendering and database postconditions?**  
  *Answer:* Every use case test in `tests/team/e2e/use_cases.spec.mjs` executes browser actions (e.g. fill inputs, click submit, assert alert banner in DOM) AND immediately queries SQLite via `scripts/e2e_db_helper.py` to assert backend records (`status=APPROVED`, `reviewer_id` set, `TemporaryPhysicalAccess.count() == 2`).
- **Q2: Explain the usability and keyboard-only test (`USA-WF1-ERR-KBD`).**  
  *Answer:* In `tests/team/usability/usability_and_keyboard.spec.mjs`, Playwright first submits an invalid form (0 buddies), verifies the error alert clearly guides the user on what to fix, then recovers using *only* keyboard events (`Tab`, `ArrowDown`, `Enter`, `Escape`) to focus inputs, select buddies, navigate to submit, and press Enter, confirming successful completion without a mouse.
- **Q3: What accessibility violations were found and how did you remediate the access request screen?**  
  *Answer:* In Phase 5, axe-core flagged Serious `link-name` (icon-only `<a href="javascript:void">` without accessible name). In `NEMO/templates/requests/access_requests/access_request.html`, we replaced it with `<button type="button" aria-label="Remove buddy {{ user.get_name }}">`, added landmark `<main>`, and added `aria-live="polite"`. In before vs. after comparison, violations dropped from 4 to 1, and Lighthouse Accessibility rose from 86 to 91.
- **Q4: What were the Grafana k6 load test results and how do they relate to your targets?**  
  *Answer:* We pre-set targets: $p95 \le 500\text{ ms}$, unexpected failures $< 1.0\%$. Executed 4 runs of 65s each on `GET /access_requests/`:
  - 1 VU (2 runs): $p95 = 38.4\text{ ms}$ and $136.4\text{ ms}$, 0.00% failures.
  - 5 VUs (2 runs): $p95 = 225.5\text{ ms}$ and $227.7\text{ ms}$, 0.00% failures.
  Both workloads easily satisfied our $500\text{ ms}$ limit.
- **Q5: Explain the controlled failure-and-recovery test.**  
  *Answer:* `tests/team/recovery/test_failure_and_recovery.py` uses `unittest.mock.patch` to inject an `OperationalError` during approval before grant creation completes. We assert transaction rollback (request remains `PENDING`, 0 grants). We then restore the database, retry approval, and assert exact state recovery (`APPROVED`, exactly 2 grants, 0 duplicate records).

---

## 5. Live Mutation / Spec Change Task (Rehearsal Sheet)

In the viva, the examiner will ask the team to apply a live business-rule change or an updated OpenAPI specification.

### Live Scenario A: Business Rule Change — Increase Minimum Buddy Count from 2 to 3
1. **Prediction:**
   - Any test expecting a request with 1 buddy (creator + 1 buddy = 2 users) to succeed will **FAIL**.
   - `test_form_buddy_count_3point_bva_default_min_2` in `tests/team/unit/test_access_requests_whitebox.py` will fail.
   - `test_w_api_01_api_rejects_below_minimum_buddy_count_with_400` will pass for 0 buddies but fail if tested with 1 buddy.
   - Playwright E2E nominal test with 1 buddy (`test_uc01_main_flow_lab_user_submits_pending_request`) will fail validation.
   - CI quality gate will block merge.
2. **Apply Change Live:**
   ```powershell
   # In terminal or via customization:
   .\venv\Scripts\python.exe -c "from NEMO.models import Customization; Customization.objects.update_or_create(name='access_requests_minimum_users', defaults={'value': '3'})"
   ```
3. **Run Tests & Demonstrate Predicted Failure:**
   ```powershell
   .\venv\Scripts\python.exe -m pytest tests/team/unit/test_access_requests_whitebox.py -k "buddy_count"
   ```
   *Observed Result:* Fails with validation error: "At least 3 users are required."
4. **Revert Change:**
   ```powershell
   .\venv\Scripts\python.exe scripts\reset_local_db.py
   ```

### Live Scenario B: OpenAPI Spec Mutation — Lower Maximum Duration from 168h to 24h
1. **Prediction:**
   - Regenerating test data will shift 3-point BVA upper bounds from $[167\text{h}, 168\text{h}, 169\text{h}]$ to $[23\text{h}, 24\text{h}, 25\text{h}]$.
   - API tests submitting requests lasting $> 24\text{h}$ will fail boundary assertions.
2. **Apply Change Live:**
   Run the automated 2-constraint demonstration script:
   ```powershell
   .\venv\Scripts\python.exe scripts\demo_openapi_regeneration.py
   ```
3. **Demonstrate Predicted Diff:**
   The script outputs the JSON diff showing updated boundaries in real time!
