# Phase 5: Usability, Keyboard Navigation & Accessibility Evaluation

**Project:** SE3002 Software Quality Engineering Final Project (Fall 2026)  
**Target MIS:** NEMO v8.2.1 (`aa5ac6e20e4e35e6f67ab7d2133b8188679ae746`)  
**Area Owner:** Area 3 — Muhammad Aun (`24P-3099`)  
**Linked Risks:** `PR-08` (Accessibility & keyboard barriers on access request screens — Score 8, Medium), `EC-04`

---

## 1. Automated Playwright Task Completion, Error-Guidance & Keyboard Navigation Tests

Implemented in [`tests/team/usability/usability_and_keyboard.spec.mjs`](../tests/team/usability/usability_and_keyboard.spec.mjs) using Chromium (`1280x800`) against synthetic accounts (`lab_user`, `facility_reviewer`):

| Test ID | Workflow | Scenario & Assertions Verified | Result |
| :--- | :--- | :--- | :--- |
| **USA-WF1-ERR-KBD** | Workflow 1 (`lab_user`) | 1. Opens `/create_access_request/`, submits with 0 buddies (`access_requests_minimum_users=2`, `BR-1`).<br>2. Asserts the rendered error explicitly tells the user how to fix it (`"You need at least 1 other buddy for this request"`).<br>3. Executes **keyboard-only navigation** (`Tab`, `Escape` on datetimepicker, `ArrowDown` + `Enter` on buddy typeahead) asserting `document.activeElement` reaches `#start_time -> #end_time -> #physical_access_level -> #search_other_users -> #description -> button[type="submit"]` in expected order, and submits via `Enter`.<br>4. Asserts request appears under `#pending_access_requests` and persists in SQLite (`status=0`, `other_users=['buddy_user']`). | **PASS** |
| **USA-WF2-TASK** | Workflow 2 (`facility_reviewer`) | 1. Logs in as `facility_reviewer`, opens `/user_requests/access/`, clicks **Review** on a pending request.<br>2. Clicks **Approve** (`approve_request`) and accepts the confirmation dialog.<br>3. Asserts confirmation under `#approved_access_requests` showing `Dr. Nadia Siddiqui` and verifies `status=1` and `2` `TemporaryPhysicalAccess` grants in SQLite. | **PASS** |

---

## 2. Before-Fix Audit: `@axe-core/playwright` + Google Lighthouse (4 Key Screens)

Executed via [`scripts/run_accessibility_audits.mjs`](../scripts/run_accessibility_audits.mjs) (`--phase before`) using an authenticated Chromium debugging session (`disableStorageReset: true`) across:
1. `/login/` (Authentication entry)
2. `/user_requests/access/` (Access Requests Dashboard)
3. `/create_access_request/` (Workflow 1 Create/Edit screen, with buddy chip added so dynamic DOM elements are scanned)
4. `/edit_access_request/<id>/` (Workflow 2 Reviewer Approve/Deny screen)

### Baseline Scores & Violation Counts (Before Remediation)

| Key Screen | URL | axe-core Violations | Lighthouse Accessibility | Lighthouse Best Practices | Lighthouse SEO |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Login** | `/login/` | `3` | `91` | `100` | `100` |
| **Access Requests Dashboard** | `/user_requests/access/` | `5` | `88` | `100` | `91` |
| **Create Access Request** | `/create_access_request/` | `4` *(1 Serious)* | `90` | `100` | `100` |
| **Review Access Request** | `/edit_access_request/<id>/` | `4` *(1 Serious)* | `86` | `100` | `100` |

### Prioritized Findings (Overlapping Issues Across Lighthouse & axe-core Counted Once)

| Finding ID | Tools Detecting | Screen(s) | Element / Selector | User Impact | Proposed Fix | Root Cause | Severity | Risk & Risk Register Link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **UA-01** | axe-core (`link-name`) + Lighthouse (`link-name`) | Create & Review (`access_request.html:153`) | `<a class="grey hover-black" href="javascript:void" onclick="remove_other_user(this)"><span class="glyphicon glyphicon-remove-circle"></span></a>` | Screen reader users hear an unlabeled link (`javascript:void`) with no indication which buddy will be removed; `javascript:void` anchor also degrades keyboard/assistive semantics. | Replace anchor with semantic `<button type="button">` having `aria-label="Remove buddy <name>"`, `title`, and `aria-hidden="true"` on the decorative glyphicon span. | Icon-only link injected dynamically in `add_other_user()` omitted accessible text/label and used `javascript:void` pseudo-URL. | **Serious** | Screen reader & keyboard exclusion on buddy management -> **`PR-08`** |
| **UA-02** | axe-core (`landmark-one-main`, `region`) + Lighthouse (`landmark-one-main`) | All 4 screens (`access_request.html`, `base.html`, `login.html`) | `<html>` / `<div class="container" id="main-content">` | Assistive technology users cannot jump directly to main content via landmark navigation (`Skip to main content` targets a generic `<div>` rather than `<main>`). | Wrap page primary content in `<main aria-labelledby="access-request-heading">` (applied on `access_request.html` in 1-screen fix; shared `base.html` flagged for backlog). | Legacy Bootstrap 3 layout used generic `<div class="container">` instead of HTML5 `<main>` landmark. | **Moderate** | Degraded landmark navigation for AT users -> **`PR-08`** |
| **UA-03** | axe-core (`meta-viewport`) + Lighthouse (`meta-viewport`) | All 4 screens (`base.html:15`, `login.html:8`) | `<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">` | Low-vision users on mobile/tablet browsers are blocked from pinch-zooming or scaling text up to 200%+. | Remove `user-scalable=no` from viewport meta tag (`content="width=device-width, initial-scale=1"`). | Upstream NEMO `base.html`/`login.html` explicitly disabled user scaling. | **Moderate** | Low-vision zoom restriction -> **`PR-08`** |
| **UA-04** | axe-core (`heading-order`) + Lighthouse (`heading-order`) | Dashboard (`access_requests.html:23`) | `<h3><a ...>Pending (1)</a></h3>` inside `#access-requests` | Screen reader heading outline skips `<h2>` between `<h1>` (`Access requests`) and `<h3>` (`Pending`), confusing section hierarchy. | Change section headings (`Pending`, `Approved`, `Denied`, `Expired`) from `<h3>` to `<h2>` styled with existing heading sizing. | Template author chose `<h3>` for visual font size instead of semantic heading level. | **Moderate** | Broken heading hierarchy -> **`PR-08`** |
| **UA-05** | Lighthouse (`target-size`) | Dashboard, Create, Review (`base/navbar.html`) | `div#site-navigation > ul.nav > li.navbar-preferences > a` (`19px x 50.9px`) | Touch/motor-impaired users risk mis-tapping adjacent **Logout** button (`< 24x24px` target width/spacing). | Add minimum horizontal padding (`min-width: 24px; padding: 15px 12px`) to navbar icon link. | Icon-only navbar anchor relies on `16px` PNG width without touch padding. | **Moderate** | Accidental logout / target miss -> **`PR-08`** |
| **UA-06** | axe-core (`empty-table-header`) + Lighthouse (`td-has-header`) | Dashboard (`access_requests_table.html:10-18, 57-65`) | Empty `<th>` column 6 (`Pending`/`Expired` for Lab User) & `<td colspan="6">` description row | Screen readers encounter an unlabeled column header and unassociated description cells inside the data table. | Render `Actions` / `Details` header text (or `<span class="sr-only">Actions</span>`) in column 6 and associate description rows cleanly. | Conditional `{% if %}` header leaves `<th>` blank for non-reviewers on non-decided tables. | **Minor** | Ambiguous table cell readout -> **`PR-08`** |
| **UA-07** | Lighthouse SEO (`crawlable-anchors`) | Dashboard (`access_requests.html:24,37,50,63`) | `<a onclick="toggle_details(this)" data-toggle="collapse" data-target="#pending_access_requests" class="pointer">` | Anchors without `href` are non-crawlable and do not receive native keyboard focus (`Tab`) or `Enter` activation. | Use `<button type="button" class="btn-link" data-toggle="collapse" ...>` or `<a href="#pending_access_requests" ...>`. | Collapse trigger used `<a>` without `href` solely for `onclick` handler. | **Minor** | Keyboard/focus omission & SEO penalty -> **`PR-08`** |

---

## 3. One-Screen Remediation & Before vs. After Verification

**Remediated Screen:** `NEMO/templates/requests/access_requests/access_request.html` (serves both `/create_access_request/` and `/edit_access_request/<id>/`).

### Changes Applied
1. **Fixed `UA-01` (Serious `link-name`):** Replaced the unlabeled `<a href="javascript:void">` buddy-removal link in `add_other_user()` with a DOM-constructed `<button type="button" class="btn-link grey hover-black" aria-label="Remove buddy <name>" title="Remove buddy <name>">` containing `<span class="glyphicon glyphicon-remove-circle" aria-hidden="true"></span>`.
2. **Fixed `UA-02` (`landmark-one-main` & `region`):** Wrapped the page heading and form inside `<main aria-labelledby="access-request-heading">` with `id="access-request-heading"` on `<h1>`.
3. **Additional screen polish:** Added `aria-labelledby="other_users_heading"` and `aria-live="polite"` on `<ul id="other_users">` so screen readers announce dynamic buddy additions/removals, and guarded `maxlength` attribute output (`{% if form.fields.description.max_length %}`) to eliminate invalid `maxlength="None"`.

### Before vs. After Comparison (`docs/evidence/phase5/before/` vs. `after/`)

| Screen | Metric | Before Fix | After Fix | Delta | Remaining Issues (Shared `base.html`) |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`/create_access_request/`** | `@axe-core/playwright` Violations | `4` *(1 Serious, 3 Moderate)* | **`1`** *(0 Serious, 1 Moderate)* | **-3 (-75%)** | Only `meta-viewport` (`user-scalable=no` in `base.html`) |
| **`/create_access_request/`** | Lighthouse Accessibility | `90` | **`91`** | **+1** | `meta-viewport` + navbar `target-size` (`base.html`) |
| **`/create_access_request/`** | Lighthouse Best Practices / SEO | `100` / `100` | **`100` / `100`** | `0` | None |
| **`/edit_access_request/<id>/`** | `@axe-core/playwright` Violations | `4` *(1 Serious, 3 Moderate)* | **`1`** *(0 Serious, 1 Moderate)* | **-3 (-75%)** | Only `meta-viewport` (`base.html`) |
| **`/edit_access_request/<id>/`** | Lighthouse Accessibility | `86` | **`91`** | **+5** | `meta-viewport` + navbar `target-size` (`base.html`) |
| **`/edit_access_request/<id>/`** | Lighthouse Best Practices / SEO | `100` / `100` | **`100` / `100`** | `0` | None |

- **Exit Criterion `EC-04` Verification:** **0** Critical/Serious `@axe-core/playwright` violations on the remediated screen (`create_access_request` & `review_access_request`), Lighthouse Accessibility improved (`90 -> 91` and `86 -> 91`), and both Playwright task/error-guidance/keyboard tests passed **100%**.

---

## 4. Archived Evidence Artifacts

- Use Case Specs: [`docs/PHASE5_USE_CASES.md`](./PHASE5_USE_CASES.md)
- E2E & Usability Scripts: `tests/team/e2e/use_cases.spec.mjs`, `tests/team/usability/usability_and_keyboard.spec.mjs`, `scripts/run_accessibility_audits.mjs`
- Playwright Reports: `docs/evidence/phase5/playwright_report.json`, `docs/evidence/phase5/playwright-html-report/index.html`
- Before Reports: `docs/evidence/phase5/before/{audit_summary.json, axe_*.json, lighthouse_*.json, lighthouse_*.html}`
- After Reports: `docs/evidence/phase5/after/{audit_summary.json, axe_*.json, lighthouse_*.json, lighthouse_*.html}`
