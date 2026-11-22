# SQE Final Project Implementation & Evaluation Checklist

**SE3002 · Software Quality Engineering · Fall 2026**  
*Automated testing of an open-source Management Information System (MIS) · Groups of 2–3 students (max 3) · 120 Marks · One final submission*

> **Area Ownership (Individually Examined in Viva):**
> - **Area 1:** Static analysis, white-box unit testing, mutation analysis, CI quality gate
> - **Area 2:** API/integration testing & automated test data generation
> - **Area 3:** Use cases, usability, accessibility, defensive security, performance & recovery *(pairs split Area 3)*
> - **Shared:** Test management & reporting
> - **Global Rules:** Use free, open-source tools only; every member commits their own work (checked in viva).

---

## Phase 1: MIS Selection, Registration & Reproducible Baseline *(5 Marks · CLO3 · Shared)*
*Lock in an eligible open-source web MIS within 5 days of announcement and establish a clean, reproducible local Git baseline.*

- [x] **Select & Register Eligible Open-Source MIS (Within 5 Days)**  
  Pick an existing open-source, web-based MIS on GitHub with a usable browser UI, HTTP API for the chosen workflows, persistent storage, and testable source code. Register in your section's tab of the shared Google Sheet within 5 days (1 repo per group per section, first come first served; same repo as another section is allowed only with zero plagiarism). Never select `frappe/erpnext`. Record upstream URL, licence, and exact baseline commit hash.
- [x] **Define Two Related Workflows & Shared Persistent State**  
  Select two related workflows within one module and run the MIS locally with synthetic records. For each workflow, document its starting condition, user action, and expected outcome. Identify at least one shared record or value that one workflow modifies and the other consumes, and list every shared record each workflow reads or changes.
- [x] **Document Requirements, 4 Business Rules, 2 Roles & Test Basis**  
  Specify ≥ 8 functional requirements across the workflows (≥ 3 per workflow), 2 user roles with distinct permissions, and 4 business rules that include: (1) a boundary or limit, (2) a decision with ≥ 2 Boolean conditions, and (3) a rule governing a state transition. Anchor all expected behaviour to repository documentation or a justified assumption recorded in your defensible test basis.
- [x] **Commit Baseline in Git, Isolate Team Tests & Assign Ownership**  
  Save the baseline version in Git and document exact commands to install, start the app, seed synthetic test data, and reset state between runs. Place all team-written tests in a dedicated folder (e.g. `tests/team/`) — upstream tests earn 0 marks. Formally record member ownership across Areas 1, 2, 3 (pairs split Area 3) and shared test management.

---

## Phase 2: Static Analysis, Test Plan, Risk Register & Exit Criteria *(17 Marks · CLO3 · Area 1 & Shared)*
*Baseline code quality with SonarQube and establish the risk-driven test plan, estimates, traceability, and release gates.*

- [x] **Run SonarQube Analysis & Hand-Calculate Cyclomatic Complexity** *(5 Marks · CLO3)*  
  Run `SonarQube` on the project and report complexity, duplication, code smells, bugs, vulnerabilities, coverage, technical debt, and quality ratings, explaining what each metric reveals about quality and risk. Draw the Control Flow Graph (CFG) for one business-rule function, hand-calculate its cyclomatic complexity, and compare your calculation against SonarQube.
- [x] **Author Living Test Plan & Three-Point Effort Estimates** *(7 Marks w/ Traceability · CLO3)*  
  Create and continuously update the Test Plan covering scope, approach by risk level, roles, environment, synthetic test data, schedule, entry/exit/suspension/resumption criteria, and risks. Produce three-point effort estimates (optimistic, most likely, pessimistic) per testing area to compare against actual effort at project end.
- [x] **Build 5×5 Risk Register & Measurable Exit Criteria** *(5 Marks · CLO3)*  
  Log ≥ 8 product risks and ≥ 2 project risks scored `likelihood × impact` (1–5) on a 5×5 matrix; explicitly map risk levels to chosen test techniques and testing depth. Define ≥ 3 measurable exit/release criteria (functional, performance, usability, or security) with ≥ 2 tied directly to the highest-scored risks.
- [x] **Initialize Traceability Matrix, Weekly Tracking & AI-Use Record**  
  Build a requirements traceability matrix tracking coverage across unit, API, and E2E suites. Start weekly progress reports against the plan (with control actions and GQM metrics: `defect density`, `requirements coverage`, `reopen rate`) and maintain the AI-use record (tool, purpose, output, human checks/edits; retain all prompts).

---

## Phase 3: White-Box Unit Testing, MCC/MC-DC & Mutation Analysis *(16 Marks + Mutation of 8 · Area 1)*
*Achieve exhaustive structural coverage on server-side business logic and prove test-suite fault-detection power via mutation testing.*

- [ ] **Achieve 100% Statement & Branch Coverage on Server-Side Business Logic** *(16 Marks w/ MCC · CLO2)*  
  Use `pytest` + `coverage.py` (Python), `Vitest` (JS/TS), or `JUnit` + `JaCoCo` (Java). Reach 100% statement and branch coverage across all server-side business logic and explicitly justify any uncovered code. Cover all 4 business rules; apply decision tables (every rule with ≥ 2 conditions) and state transitions (every allowed + ≥ 1 disallowed change per state) wherever they fit; count each executable case once per test level.
- [ ] **Build Complete MCC Tables & Derive MC/DC Pairs on Critical Module**  
  For the critical business-rule module, enumerate complete Multiple Condition Coverage (MCC) truth tables, then extract the Modified Condition/Decision Coverage (MC/DC) independence pairs directly from those MCC tables and automate unit tests verifying each pair.
- [ ] **Run Mutation Tool & Add ≥ 2 Custom Business-Rule Mutation Operators** *(8 Marks w/ CI · CLO3)*  
  Run `mutmut` or `Cosmic Ray` (Python), `Stryker` (JS/TS), or `PIT` (Java) on the business-rule module and report the mutation score. Implement at least 2 custom mutation operators specifically modelling defects in your documented business rules.
- [ ] **Analyse ≥ 15 Surviving Mutants & Kill All Killable Mutants**  
  Inspect at least 15 surviving mutants, classifying each as `equivalent`, `missing test`, or `weak assertion`. Write new unit tests or strengthen existing assertions to kill every killable mutant and document the updated mutation score.

---

## Phase 4: OpenAPI Spec, Data Generation & API/Integration Testing *(17 Marks · CLO2 · Area 2)*
*Generate systematic EP and 3-point BVA datasets directly from an OpenAPI contract and validate all endpoint & cross-workflow behaviour.*

- [ ] **Author OpenAPI Spec & Build EP / 3-Point BVA Generator Script** *(7 Marks · CLO2)*  
  Write an OpenAPI specification covering your workflow endpoints (or verify and use the upstream spec if accurate). Build your own generator script that parses the OpenAPI spec and outputs Equivalence Partitioning (EP) classes and 3-point Boundary Value Analysis (BVA: just below, exactly at, just above every limit) inputs.
- [ ] **Demonstrate Two-Constraint Regeneration & Viva Adaptability**  
  Change two constraints in the OpenAPI specification, re-run the generator, and show the regenerated outputs and test effect. Keep the generator cleanly spec-driven so you can regenerate live during the viva when given an updated API spec.
- [ ] **Automate API & Integration Tests Consuming Generated Data** *(10 Marks · CLO2)*  
  Use `pytest` + `Requests` (or the project language's open-source test framework). API tests MUST consume the generator's output. Test every valid and invalid EP partition (one invalid value per test) and 3-point BVA on every input, meeting all API coverage criteria plus decision-table and state-transition checks wherever they fit.
- [ ] **Verify Rejections, Idempotency, Cross-Workflow Readbacks & Weaknesses**  
  Automate business-rule rejections, invalid state transitions, and repeated requests (asserting no duplicate records). Read back shared persistent records after BOTH successful and rejected requests across workflows. Report all endpoint weaknesses with root cause, severity, risk, fix, and risk-register link.

---

## Phase 5: Use Cases, Playwright E2E, Usability & Accessibility *(14 Marks · CLO2/CLO3 · Area 3)*
*Specify and automate full browser user journeys, then audit, fix, and re-verify usability and accessibility.*

- [ ] **Write Complete Use Case Specifications (2 Per Member)** *(3 Marks · CLO3)*  
  Derive 2 use cases per group member (4 for pairs, 6 for trios) from your functional requirements (from repo docs or written by you). Every use case must document preconditions, main flow, ≥ 2 alternative flows, ≥ 2 exception flows, and postconditions.
- [ ] **Automate Every Use Case Flow in Playwright (Chromium)** *(6 Marks · CLO2)*  
  Automate every main, alternative, and exception flow in `Playwright` with `Chromium`. Assert both the visible UI outcome shown to the user and the underlying persisted postconditions. Count each executable case once within the E2E level.
- [ ] **Automate Task Completion, Error-Guidance & Keyboard Navigation Tests** *(5 Marks w/ Audits · CLO3)*  
  Write 2 automated Playwright browser tests (1 per workflow, using test accounts; no human participants or manual walkthroughs required; may count toward use cases): open screen, complete task, assert confirmation. In one test, first submit a business-rule-rejected value, verify the error explains what to correct, then fix and succeed. In one test, simulate keyboard-only navigation asserting focus order through required fields + submit button and keyboard submission.
- [ ] **Run Lighthouse + axe-core, Fix One Screen & Compare Before/After**  
  Run `Google Lighthouse` (accessibility, best practices, SEO via logged-in DevTools or Lighthouse CI with login script) and full `@axe-core/playwright` scans on each use case's key screen. Count overlapping issues once; interpret and prioritise each with element, user impact, proposed fix, root cause, severity, risk, and risk-register link. Fix 1 screen (in the MIS or your own HTML page), rerun both tools, compare before vs after, and archive scripts, Playwright report, and before/after Lighthouse & axe-core reports.

---

## Phase 6: Defensive Security, Performance & Failure Recovery *(11 Marks · CLO2 · Area 3)*
*Validate authorization controls and dependencies defensively, benchmark p95 latency under load, and verify safe failure recovery.*

- [ ] **Map Attack Surface, Access Matrix & Automate ≥ 4 Role Checks** *(6 Marks w/ ZAP & Deps · CLO2)*  
  Assess security locally with synthetic data and test accounts. Document attack surface (routes & data in both workflows) and build an access matrix across your 2 test roles. Automate ≥ 4 access decisions in `Playwright` (including ≥ 1 allowed and ≥ 1 denied action), recording role, action, expected result, observed result, and evidence for every check.
- [ ] **Run OWASP ZAP Passive Scan, Control Review & Dependency Audit**  
  Run `OWASP ZAP` in passive mode while Playwright executes both workflows. Review ≥ 2 relevant security controls (e.g. session cookie attributes, role checks) corroborated via source code or config. Run `OWASP Dependency-Check` or `pip-audit` (stack-appropriate) and list all checked packages/versions. For every finding report component, evidence, likely impact, fix, root cause, severity, risk, and risk-register link (documented verified controls also earn credit when 0 findings occur).
- [ ] **Set Targets & Run Comparable Grafana k6 OSS Load Tests** *(5 Marks w/ Recovery · CLO2)*  
  Select 1 operation from either workflow. BEFORE testing, set and justify a `p95` response-time limit (ms) and acceptable unexpected-failure % per workload. Run 1 `Grafana k6 OSS` script with `1 VU` and `≥ 5 VUs` concurrently — 2 runs per setup (4 runs total), measuring ≥ 60s per run after reaching target VUs on the exact same build, machine, and starting data. Report `p95` (ms), RPS, and unexpected failure % for each run; compare vs targets and link findings to the risk register.
- [ ] **Automate Controlled Failure-and-Recovery Test for State Change**  
  Using your API/integration test runner, automate 1 controlled failure-and-recovery test on a state-changing operation (e.g. test double making a dependency unavailable before a write completes). Verify persisted state after failure, restore the dependency, retry, and assert the expected final state with zero duplicate records. Archive scripts, raw outputs, environment details, and target interpretation.

---

## Phase 7: CI Quality Gate, Defects, RCA & Test Completion *(12 Marks + CI Gate of 8 · Area 1 & Shared)*
*Enforce strict non-bypassable PR quality gates and finalize defect governance, GQM tracking, and the release decision.*

- [ ] **Enforce Strict GitHub Actions PR Quality Gate (No Escape Hatches)**  
  Configure `GitHub Actions` to run on every pull request: SonarQube, all test suites (unit, API, E2E), and mutation testing. Block merge and deployment on any failure or breach of evidence-justified coverage, mutation, and SonarQube thresholds. Strictly ban escape hatches (no `continue-on-error`, no `|| true`).
- [ ] **Demonstrate Two Pull Requests: Documented Fix & Blocked PR**  
  Include in the repository: (1) one documented fix delivered via PR proving the gate fails before the fix and passes after, and (2) one pull request that the pipeline correctly blocked from merging due to test/threshold failure.
- [ ] **Complete GitHub Issues Lifecycle, 2 Major RCAs & Pareto Analysis** *(7 Marks · CLO3)*  
  Log defects in GitHub Issues with severity, priority, status/lifecycle, and triage decision. Conduct root cause analysis (`5 Whys` + `Fishbone` diagram) for ≥ 2 major defects with corrective and preventive actions. Produce a Pareto analysis by defect category and verify every API, accessibility, security, and performance weakness is linked to the risk register.
- [ ] **Finalize Weekly GQM Reports, Actual Effort & Completion Report** *(5 Marks · CLO3)*  
  Compile weekly progress reports against the plan with control actions and GQM metrics (`defect density`, `requirements coverage`, `reopen rate`) read in context. Compare three-point estimates vs actual effort. Write the Test Completion Report covering tested/not tested scope, deviations, open defects, residual risk per risk, and an evidence-based **Release or Hold** decision showing actual vs target for all 3 release criteria.

---

## Phase 8: Final Packaging, Integrity Audit & Viva Readiness *(20 Marks · CLO1 · All Members)*
*Deliver one compliant PDF + Git zip package and prepare every member to defend tests, artefacts, and live mutations.*

- [ ] **Audit Repository Contents, Tool Versions & Per-Member Git Commits**  
  Verify every member committed their own work (commit history is checked in the viva). Confirm the repo contains: upstream URL/licence & baseline commit, reproducible setup/seed/reset instructions, runnable scripts & test data in `tests/team/`, exact tool versions, CI config, the documented fix PR, and the blocked PR.
- [ ] **Compile Complete PDF Report & AI-Use Disclosure Record**  
  Include public GitHub repo link, scope, risk register, traceability matrix, all test management documents, full results & evidence links for every testing activity, area ownership, root cause/severity/risk/fix (linked to risk register) for every API/a11y/security/performance finding, the complete AI-use record (tool, purpose, output, what you checked/changed; prompts kept), and the final Release or Hold decision (actual vs target for all 3 release criteria).
- [ ] **Package One Final Submission with Exact Naming & `.git` Folder**  
  Submit one PDF and one repository zip per group named `Project_RollNumber1_RollNumber2_RollNumber3_Section.pdf` and `.zip` (e.g. `Project_23I-0001_23I-0002_23I-0003_A.zip`; pairs omit the third roll number). Ensure the `.git` folder is included inside the zip so full commit history is preserved.
- [ ] **Rehearse Individual Test Reruns, Full-Scope Q&A & Live Task** *(20 Marks · CLO1)*  
  Prepare every member to: (1) rerun a selected test live and explain all assertions, (2) answer questions on their owned area AND every shared component (risk register, traceability, metrics, findings), and (3) execute the live task — given a business-rule change or updated OpenAPI spec, predict which tests and CI pipeline gate will fail, apply the change, and demonstrate the actual failure.

---

## Approved Free & Open-Source Tool Stack Reference

| Testing Activity | Required / Recommended Open-Source Tools |
| :--- | :--- |
| Unit Testing & Coverage | `pytest` + `coverage.py` (Python), `Vitest` (JS/TS), or `JUnit` + `JaCoCo` (Java) |
| Static Analysis & Metrics | `SonarQube` (plus manual CFG cyclomatic complexity verification) |
| Mutation Analysis | `mutmut` or `Cosmic Ray` (Python), `Stryker` (JS/TS), or `PIT` (Java) + ≥ 2 custom operators |
| API Test Data Generation | `OpenAPI` specification + team-built EP & 3-point BVA generator script |
| API & Integration Testing | `pytest` + `Requests`, or the project language's open-source test framework |
| Browser E2E & CI Quality Gate | `Playwright` with `Chromium` for E2E/role/keyboard tests; `GitHub Actions` for CI |
| Usability & Accessibility | `Google Lighthouse` (logged-in DevTools or Lighthouse CI) + `axe-core` (`@axe-core/playwright`) |
| Defensive Security | `OWASP ZAP` Passive Scanner, `OWASP Dependency-Check` or `pip-audit`, `Playwright` role checks |
| Performance & Recovery | `Grafana k6 OSS` for load runs; API/integration test runner + test double for failure recovery |

---

## Marking Rubric & Phase Mapping Summary (120 Marks Total)

| Component | Marks | CLO | Phase | Core Evidence Assessed |
| :--- | :---: | :---: | :---: | :--- |
| System and scope | 5 | CLO3 | Phase 1 | Registered repo, reproducible baseline, 2 workflows, ≥8 FRs, 4 rules, test basis |
| Static analysis and metrics | 5 | CLO3 | Phase 2 | SonarQube metrics analysed for quality/risk; hand CFG CC vs tool |
| Test plan, estimation & traceability | 7 | CLO3 | Phase 2, 7 | Justified test plan; 3-point vs actual effort; traceability & req coverage |
| Risk register and exit criteria | 5 | CLO3 | Phase 2 | ≥8 product + ≥2 project risks (5×5) mapped to depth; ≥3 exit criteria (≥2 top-risk) |
| White-box unit testing | 16 | CLO2 | Phase 3 | 100% stmt/branch on business logic; complete MCC & MC/DC pairs on critical module |
| API and integration testing | 10 | CLO2 | Phase 4 | EP & 3-point BVA on all inputs, API criteria, rejections, idempotency, cross-workflow |
| Automated test data generation | 7 | CLO2 | Phase 4 | OpenAPI spec, working EP/BVA generator, 2-constraint regeneration demo |
| Use case specification | 3 | CLO3 | Phase 5 | 2/member from reqs w/ preconditions, postconditions, ≥2 alt & ≥2 exception flows |
| Use case test automation | 6 | CLO2 | Phase 5 | Playwright tests automating every flow with UI & postcondition assertions |
| Mutation analysis & CI quality gate | 8 | CLO3 | Phase 3, 7 | Score, ≥2 custom ops, ≥15 surviving mutants, justified thresholds, blocked PR |
| Usability & accessibility evaluation | 5 | CLO3 | Phase 5 | Lighthouse + axe-core interpreted/prioritised; 1 screen fixed & re-verified; task/keyboard |
| Defensive security | 6 | CLO2 | Phase 6 | Access matrix + ≥4 Playwright role checks, ZAP passive + 2 controls, dependency audit |
| Performance and recovery | 5 | CLO2 | Phase 6 | Comparable k6 runs (1 & ≥5 VUs × 2, ≥60s) vs p95 targets; verified recovery state |
| Defect management & RCA | 7 | CLO3 | Phase 7 | GitHub Issues lifecycle/triage; ≥2 major RCAs (5 Whys + Fishbone); Pareto; risk links |
| Monitoring & completion report | 5 | CLO3 | Phase 2, 7 | Weekly plan tracking, GQM metrics in context, residual risk, Release/Hold decision |
| Viva, live task & AI-use record | 20 | CLO1 | Phase 8 | Individual area defense, test rerun, live rule/spec task, responsible disclosed AI use |
| **Total** | **120** | **—** | **Phases 1–8** | **Viva rule: any component can be reduced or set to 0 if unexplained in viva** |

---

> [!CAUTION]
> ### Critical Deductions & Disqualification Checklist — Do Not Submit Before Checking
> - **Viva Zero-Out Rule (up to 0 on any component):** The viva inspects every component. If you cannot explain any component (e.g. risk register, assertions, metrics), marks for that component are deducted — possibly to 0. Viva outcomes are final; *"we did it but forgot"* is not grounds for review.
> - **Academic Integrity & Undisclosed AI (0 on component / entire project + disciplinary referral):** Disclose every AI use (tool, purpose, output, what you checked/changed) and keep prompts. Never fabricate/edit reports, pipeline runs, or screenshots, copy from other groups/sections/upstream/online, share work, or use outside help. Submissions are checked across all sections, upstream, online sources, and Git history. **The whole group is responsible.**
> - **Registration, Forbidden Repo & Upstream Tests (0 marks):** Register within 5 days (1 repo/group/section, FCFS); never pick `frappe/erpnext`; upstream tests earn 0 marks — isolate your tests in `tests/team/`; max 3 members per group (no 4-member groups).
> - **CI Escape Hatches & Missing PR Proof (CI gate fails audit):** Never use `continue-on-error` or `|| true` in GitHub Actions. Must include both a documented fix PR (fails before, passes after) and a pipeline-blocked PR.
> - **Packaging, `.git` History & Authorship:** Zip MUST include the `.git` folder; PDF MUST link the public GitHub repo; follow exact naming `Project_Roll1_Roll2[_Roll3]_Section.{pdf,zip}`; every member must commit their own work.
