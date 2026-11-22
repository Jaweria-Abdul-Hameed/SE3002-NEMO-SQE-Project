"""Sync 22 real test-discovered defects to GitHub Issues with severity, priority, triage, and risk links."""

import json
import subprocess
import sys
import time
from pathlib import Path

DEFECTS = [
    {
        "id": "W-API-01",
        "title": "[API] W-API-01: API bypasses minimum buddy count (BR-1 / PR-01)",
        "severity": "High",
        "priority": "P1",
        "type": "api",
        "risk": "PR-01",
        "status": "closed",
        "triage": "Resolved in PR #1 (Fixed in TemporaryPhysicalAccessRequestSerializer)",
        "body": """### Defect Description
`POST /api/temporary_physical_access_requests/` accepts `other_users: []` (0 buddies) even when `access_requests_minimum_users = 2`.

### Test Evidence
- Discovered by automated 3-point BVA test `BVA3-other_users-minItems-below_minItems`.
- Persisted invalid pending request with 0 buddies directly to database.

### Root Cause
Minimum buddy validation lived exclusively in `TemporaryPhysicalAccessRequestForm.clean()`, completely absent in `TemporaryPhysicalAccessRequestSerializer`.

### Triage & Resolution
- **Triage Decision:** Critical fix required.
- **Resolution:** Implemented in PR #1 by adding `validate()` in `TemporaryPhysicalAccessRequestSerializer` checking `len(other_users) + 1 >= min_users`.
- **Linked Risk:** PR-01 (Severity: 25)""",
    },
    {
        "id": "W-API-02",
        "title": "[API] W-API-02: API accepts past start_time for non-reviewers (BR-1 / PR-01)",
        "severity": "High",
        "priority": "P1",
        "type": "api",
        "risk": "PR-01",
        "status": "open",
        "triage": "Scheduled for Release v8.3.0",
        "body": """### Defect Description
`POST /api/temporary_physical_access_requests/` allows regular `lab_user` to submit requests with `start_time` in the past (`start_time = now - 55m`).

### Test Evidence
- Flagged by `BVA3-start_time-offset-below_min_offset` (returned HTTP 200).
- Upstream start-time check is located in UI view `create_access_request` (`NEMO/views/access_requests.py:123-128`), bypassing REST API.

### Recommended Fix
Add `start_time >= timezone.now()` check in `TemporaryPhysicalAccessRequestSerializer.validate()`.

### Linked Risk
PR-01, PR-06""",
    },
    {
        "id": "W-API-03",
        "title": "[API] W-API-03: API allows arbitrary illegal state transitions (BR-3 / PR-03)",
        "severity": "Critical",
        "priority": "P0",
        "type": "api",
        "risk": "PR-03",
        "status": "open",
        "triage": "Critical Hotfix Candidate for v8.3.0",
        "body": """### Defect Description
`PATCH /api/temporary_physical_access_requests/{id}/` permits illegal state transitions: `APPROVED -> PENDING`, `APPROVED -> DENIED`, `DENIED -> APPROVED`, and `EXPIRED -> APPROVED`.

### Test Evidence
- Tested in `test_api_state_transitions_disallowed_exposes_weakness_w_api_04`.
- Returned HTTP 200 and updated state in database.

### Root Cause
DRF `ModelViewSet` exposes generic updates without state machine transition guards on `status`.

### Linked Risk
PR-01, PR-03""",
    },
    {
        "id": "W-API-04",
        "title": "[API] W-API-04: API approval never creates TemporaryPhysicalAccess grants (FR-07 / PR-04)",
        "severity": "Critical",
        "priority": "P0",
        "type": "api",
        "risk": "PR-04",
        "status": "open",
        "triage": "Critical Architecture Fix for v8.3.0",
        "body": """### Defect Description
Setting `status=1 (APPROVED)` via REST API `PATCH` marks the request `APPROVED`, but creates **0** `TemporaryPhysicalAccess` records in the database. In contrast, UI approval creates 2 grants.

### Test Evidence
- Discovered in `test_cross_workflow_api_approval_side_effect_gap_and_bola_weakness`.
- `TemporaryPhysicalAccess.objects.count() == 0` after API approval.

### Root Cause
Grant generation logic lives in UI view (`NEMO/views/access_requests.py:186-193`), not in a shared domain service or model hook.

### Linked Risk
PR-01, PR-04""",
    },
    {
        "id": "W-API-05",
        "title": "[API] W-API-05: Broken Object-Level Authorization (BOLA) on API (BR-4 / PR-02)",
        "severity": "Critical",
        "priority": "P0",
        "type": "api",
        "risk": "PR-02",
        "status": "open",
        "triage": "Security Advisory Candidate",
        "body": """### Defect Description
Any authenticated user can `PATCH` another user's request, approve it, and set themselves as the `reviewer`.

### Test Evidence
- Verified in `test_cross_workflow_api_approval_side_effect_gap_and_bola_weakness`.
- `lab_user` approved `other_requester`'s request via API.

### Root Cause
`DjangoModelPermissions` checks model-level permissions only, omitting object-level permissions (`IsCreatorOrAreaReviewer`).

### Linked Risk
PR-02 (Severity: 15)""",
    },
    {
        "id": "W-API-06",
        "title": "[API] W-API-06: API DELETE hard-deletes records instead of soft-deleting (FR-05 / PR-03)",
        "severity": "High",
        "priority": "P2",
        "type": "api",
        "risk": "PR-03",
        "status": "open",
        "triage": "Scheduled for Release v8.3.0",
        "body": """### Defect Description
`DELETE /api/temporary_physical_access_requests/{id}/` completely removes the record from the database instead of setting `deleted=True`.

### Test Evidence
- Verified in `test_api_crud_put_patch_delete_idempotency_and_duplicate_post_weakness`.
- Deleted record is no longer queryable even with `deleted=True`.

### Root Cause
DRF `DestroyModelMixin` invokes `.delete()` instead of custom soft-delete.

### Linked Risk
PR-03""",
    },
    {
        "id": "W-API-07",
        "title": "[API] W-API-07: Missing bounds on description and buddy list (BR-1 / PR-06)",
        "severity": "Medium",
        "priority": "P2",
        "type": "api",
        "risk": "PR-06",
        "status": "open",
        "triage": "Backlog",
        "body": """### Defect Description
API accepts empty descriptions, descriptions over 500 characters, and more than 10 buddies without validation errors.

### Linked Risk
PR-06""",
    },
    {
        "id": "W-API-08",
        "title": "[API] W-API-08: API accepts non-requestable physical_access_level (BR-1 / PR-01)",
        "severity": "Medium",
        "priority": "P2",
        "type": "api",
        "risk": "PR-01",
        "status": "open",
        "triage": "Backlog",
        "body": """### Defect Description
API `POST` accepts `physical_access_level` where `allow_user_request=False`. UI hides these levels, but API permits requests for restricted areas.

### Linked Risk
PR-01""",
    },
    {
        "id": "W-API-09",
        "title": "[API] W-API-09: Duplicate POST requests create duplicate database records (PR-04)",
        "severity": "Low",
        "priority": "P3",
        "type": "api",
        "risk": "PR-04",
        "status": "open",
        "triage": "Low Priority / Feature Request",
        "body": """### Defect Description
Repeated identical `POST` submissions within seconds create duplicate pending requests. API returns HTTP 200 instead of 201 Created.

### Linked Risk
PR-04""",
    },
    {
        "id": "UA-01",
        "title": "[A11Y] UA-01: Missing accessible name on buddy removal link-name (WCAG 4.1.2 / PR-08)",
        "severity": "Serious",
        "priority": "P1",
        "type": "accessibility",
        "risk": "PR-08",
        "status": "closed",
        "triage": "Remediated in Phase 5 (access_request.html)",
        "body": """### Defect Description
The remove buddy control was implemented as an icon-only `<a href="javascript:void">` without text or `aria-label`. Flagged by axe-core as Serious `link-name`.

### Remediation
Replaced with accessible `<button type="button" aria-label="Remove buddy {{ user.get_name }}">`. axe-core violations dropped from 4 to 1.

### Linked Risk
PR-08 (Severity: 12)""",
    },
    {
        "id": "UA-02",
        "title": "[A11Y] UA-02: Missing <main> landmark on access request screens (WCAG 1.3.1 / PR-08)",
        "severity": "Moderate",
        "priority": "P2",
        "type": "accessibility",
        "risk": "PR-08",
        "status": "closed",
        "triage": "Remediated in Phase 5 (access_request.html)",
        "body": """### Defect Description
Access request form had no `<main>` landmark element, preventing screen reader users from jumping directly to primary content.

### Remediation
Added `<main aria-labelledby="request-page-title">`.

### Linked Risk
PR-08""",
    },
    {
        "id": "UA-03",
        "title": "[A11Y] UA-03: Dynamic buddy list insertion lacks aria-live region (WCAG 4.1.3 / PR-08)",
        "severity": "Moderate",
        "priority": "P2",
        "type": "accessibility",
        "risk": "PR-08",
        "status": "closed",
        "triage": "Remediated in Phase 5 (access_request.html)",
        "body": """### Defect Description
Adding buddies via JavaScript did not announce updates to assistive technology.

### Remediation
Added `aria-live="polite"` to `#other_users_container`.

### Linked Risk
PR-08""",
    },
    {
        "id": "UA-04",
        "title": "[A11Y] UA-04: Invalid HTML attribute maxlength='None' on description (PR-08)",
        "severity": "Minor",
        "priority": "P3",
        "type": "accessibility",
        "risk": "PR-08",
        "status": "closed",
        "triage": "Remediated in Phase 5 (access_request.html)",
        "body": """### Defect Description
Django rendered `maxlength="None"` as string literal on textarea, failing HTML validation.

### Remediation
Removed attribute when length is None.

### Linked Risk
PR-08""",
    },
    {
        "id": "UA-05",
        "title": "[A11Y] UA-05: Low contrast on pending status badge (#999 on #f5f5f5) (WCAG 1.4.3 / PR-08)",
        "severity": "Minor",
        "priority": "P3",
        "type": "accessibility",
        "risk": "PR-08",
        "status": "open",
        "triage": "Next Theme Update",
        "body": """### Defect Description
Pending status badge gray text has a contrast ratio of 2.8:1, below WCAG AA requirement of 4.5:1.

### Linked Risk
PR-08""",
    },
    {
        "id": "UA-06",
        "title": "[A11Y] UA-06: Missing explicit label on buddy search input (WCAG 3.3.2 / PR-08)",
        "severity": "Moderate",
        "priority": "P2",
        "type": "accessibility",
        "risk": "PR-08",
        "status": "open",
        "triage": "Next Sprint",
        "body": """### Defect Description
Buddy search field relied on placeholder text without associated `<label for="...">`.

### Linked Risk
PR-08""",
    },
    {
        "id": "UA-07",
        "title": "[A11Y] UA-07: Table action buttons tap target below 48x48px on mobile (PR-08)",
        "severity": "Minor",
        "priority": "P3",
        "type": "accessibility",
        "risk": "PR-08",
        "status": "open",
        "triage": "Responsive Design Backlog",
        "body": """### Defect Description
Lighthouse flagged table action icons as having tap target size 28x28px, below the recommended 48x48px mobile target.

### Linked Risk
PR-08""",
    },
    {
        "id": "SEC-01",
        "title": "[SEC] SEC-01: Outdated client-side library moment.js v2.29.3 (CVE-2022-31129 / PR-02)",
        "severity": "High",
        "priority": "P1",
        "type": "security",
        "risk": "PR-02",
        "status": "open",
        "triage": "Upgrade in Next Sprint",
        "body": """### Defect Description
OWASP ZAP passive scan flagged `moment.js v2.29.3` bundled in `NEMO/static/`. Vulnerable to ReDoS in RFC2822 date parser (CVE-2022-31129).

### Recommendation
Upgrade to `moment.js >= 2.29.4` or migrate to modern `Intl` API.

### Linked Risk
PR-02, PR-07""",
    },
    {
        "id": "SEC-02",
        "title": "[SEC] SEC-02: Missing Content-Security-Policy (CSP) headers (PR-02)",
        "severity": "Medium",
        "priority": "P2",
        "type": "security",
        "risk": "PR-02",
        "status": "open",
        "triage": "Middleware Configuration",
        "body": """### Defect Description
OWASP ZAP identified that HTTP responses lack `Content-Security-Policy` header, allowing inline scripts and styles.

### Linked Risk
PR-02""",
    },
    {
        "id": "SEC-03",
        "title": "[SEC] SEC-03: Delete operation triggered via HTTP GET (SonarQube S3752 / PR-05)",
        "severity": "Medium",
        "priority": "P2",
        "type": "security",
        "risk": "PR-05",
        "status": "open",
        "triage": "Scheduled for Security Hardening",
        "body": """### Defect Description
`delete_access_request` accepts HTTP `GET` requests, allowing state deletion via link traversal without CSRF protection.

### Recommendation
Add `@require_POST` decorator.

### Linked Risk
PR-05 (Severity: 12)""",
    },
    {
        "id": "SEC-04",
        "title": "[SEC] SEC-04: Missing HttpOnly flag on csrftoken cookie (PR-02)",
        "severity": "Low",
        "priority": "P3",
        "type": "security",
        "risk": "PR-02",
        "status": "open",
        "triage": "Documented Accepted Risk",
        "body": """### Defect Description
`csrftoken` cookie is set without `HttpOnly`. By Django design, client-side AJAX scripts read this cookie to populate `X-CSRFToken` header.

### Linked Risk
PR-02""",
    },
    {
        "id": "PERF-01",
        "title": "[PERF] PERF-01: Concurrency bottleneck in mark_requests_expired() (PR-07)",
        "severity": "Medium",
        "priority": "P2",
        "type": "performance",
        "risk": "PR-07",
        "status": "open",
        "triage": "Architectural Refactor",
        "body": """### Defect Description
`access_requests()` list view executes `mark_requests_expired()` on every request, running write queries inside read views and causing SQLite lock contention under 5 VUs.

### Recommendation
Offload `mark_requests_expired()` to periodic background worker (Celery / cron).

### Linked Risk
PR-07 (Severity: 15)""",
    },
    {
        "id": "PERF-02",
        "title": "[PERF] PERF-02: Missing composite database index on status and end_time (PR-07)",
        "severity": "Low",
        "priority": "P3",
        "type": "performance",
        "risk": "PR-07",
        "status": "open",
        "triage": "Database Optimization",
        "body": """### Defect Description
Filtering pending requests involves table scan across `status` and `end_time`.

### Recommendation
Add composite index `db_index` on `(status, end_time)`.

### Linked Risk
PR-07""",
    },
]


def create_labels():
    labels = [
        ("severity:critical", "d73a4a", "Critical severity defect"),
        ("severity:high", "e11d48", "High severity defect"),
        ("severity:serious", "d93f0b", "Serious accessibility violation"),
        ("severity:moderate", "fb8c00", "Moderate accessibility violation"),
        ("severity:medium", "fb8c00", "Medium severity defect"),
        ("severity:minor", "0284c7", "Minor defect / violation"),
        ("severity:low", "0284c7", "Low severity defect"),
        ("type:api", "1d76db", "API and integration testing finding"),
        ("type:accessibility", "a21caf", "Usability and accessibility finding"),
        ("type:security", "b60205", "Defensive security / ZAP finding"),
        ("type:performance", "0e8a16", "Performance and concurrency finding"),
        ("priority:P0", "b60205", "P0 - Blocker"),
        ("priority:P1", "d93f0b", "P1 - High priority"),
        ("priority:P2", "fbca04", "P2 - Normal priority"),
        ("priority:P3", "0e8a16", "P3 - Low priority"),
    ]
    for name, color, desc in labels:
        subprocess.run(
            ["gh", "label", "create", name, "--color", color, "--description", desc, "--force"],
            capture_output=True,
        )


def main():
    print("Creating labels on GitHub repository...")
    create_labels()

    # Query existing issues so we do not duplicate
    existing_res = subprocess.run(
        ["gh", "issue", "list", "--state", "all", "--limit", "100", "--json", "number,title,state"],
        capture_output=True,
        text=True,
        check=True,
    )
    existing_list = json.loads(existing_res.stdout)
    existing_map = {item["title"]: item for item in existing_list}

    print(f"Syncing {len(DEFECTS)} defects to GitHub Issues...")
    created_issues = []

    for d in DEFECTS:
        labels = [
            f"severity:{d['severity'].lower()}",
            f"priority:{d['priority']}",
            f"type:{d['type']}",
        ]
        
        if d["title"] in existing_map:
            item = existing_map[d["title"]]
            issue_num = str(item["number"])
            issue_url = f"https://github.com/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project/issues/{issue_num}"
            print(f"Already exists: Issue #{issue_num} ({d['id']})")
            created_issues.append({"id": d["id"], "number": issue_num, "url": issue_url, "status": d["status"]})
            continue

        cmd = [
            "gh",
            "issue",
            "create",
            "--title",
            d["title"],
            "--body",
            d["body"],
        ]
        for lbl in labels:
            cmd.extend(["--label", lbl])

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            issue_url = res.stdout.strip()
            issue_num = issue_url.split("/")[-1]
            print(f"Created Issue #{issue_num}: {d['id']} -> {issue_url}")
            created_issues.append({"id": d["id"], "number": issue_num, "url": issue_url, "status": d["status"]})

            if d["status"] == "closed":
                close_comment = f"Closed as resolved: {d['triage']}."
                subprocess.run(["gh", "issue", "close", issue_num, "--comment", close_comment], capture_output=True)
                print(f"  Closed Issue #{issue_num} ({d['triage']})")
        else:
            print(f"Error creating issue for {d['id']}: {res.stderr}")

        time.sleep(0.5)

    out_file = Path("docs/evidence/phase7_github_issues_catalog.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(created_issues, indent=2), encoding="utf-8")
    print(f"Archived {len(created_issues)} synced issues to {out_file}")


if __name__ == "__main__":
    main()
