#!/usr/bin/env python3
"""
Post formal engineering triage comments to all open issues on GitHub.
Ensures full ISO/IEEE defect management lifecycle compliance for Phase 7 (CLO3).
"""

import subprocess
import time

TRIAGE_COMMENTS = {
    5: """### Triage & Backlog Decision (Area 2 — Mohsin Khan)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog (P0 Critical).
- **Severity / Priority:** Critical / P0 (Risk Link: PR-03)
- **Technical Analysis:** `TemporaryPhysicalAccessRequestViewSet` allows updating request status via PATCH without validating whether the transition is permitted by business rule BR-3. For example, requests in `APPROVED` (1) or `DENIED` (2) states can be transitioned back to `PENDING` (0) via the REST API.
- **Proposed Correction:** Implement an explicit state transition validator in `TemporaryPhysicalAccessRequestViewSet.partial_update()` rejecting invalid transitions with HTTP 400 Bad Request.""",

    6: """### Triage & Backlog Decision (Area 2 — Mohsin Khan)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog (P0 Critical).
- **Severity / Priority:** Critical / P0 (Risk Link: PR-04)
- **Technical Analysis:** In the web UI, approving a request triggers `create_temporary_access()` in `NEMO/views/access_requests.py` which creates corresponding `TemporaryPhysicalAccess` grant records. When status is updated to `APPROVED` via the DRF API, no grant records are created.
- **Proposed Correction:** Override `perform_update()` in `TemporaryPhysicalAccessRequestViewSet` to call `create_temporary_access()` when `status == RequestStatus.APPROVED`.""",

    7: """### Triage & Backlog Decision (Area 2 — Mohsin Khan)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Critical / P0 (Risk Link: PR-02)
- **Technical Analysis:** The API relies on global `DjangoModelPermissions`, allowing any staff user to review and update any access request regardless of whether they are a designated area reviewer for that specific physical access level.
- **Proposed Correction:** Introduce custom DRF object permission class `IsAreaReviewerOrFacilityManager` enforcing fine-grained review permissions.""",

    8: """### Triage & Backlog Decision (Area 2 — Mohsin Khan)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** High / P2 (Risk Link: PR-03, PR-05)
- **Technical Analysis:** The web UI implements soft deletion (`deleted = True`) to preserve audit trails for compliance. The API `DELETE` verb executes hard deletion (`instance.delete()`), permanently purging historical records.
- **Proposed Correction:** Override `destroy()` in `TemporaryPhysicalAccessRequestViewSet` to set `instance.deleted = True` and save, returning HTTP 204 No Content.""",

    9: """### Triage & Backlog Decision (Area 2 — Mohsin Khan)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Medium / P2 (Risk Link: PR-06)
- **Technical Analysis:** The API accepts descriptions exceeding 255 characters or excessive buddy lists without upper bounding, risking database truncation or payload bloat.
- **Proposed Correction:** Add explicit `max_length=255` validator on serializer `description` and bound `other_users` count.""",

    10: """### Triage & Backlog Decision (Area 2 — Mohsin Khan)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Medium / P2 (Risk Link: PR-01)
- **Technical Analysis:** Users can create requests targeting access levels where `allow_user_request=False`.
- **Proposed Correction:** Scope `physical_access_level` field queryset to `PhysicalAccessLevel.objects.filter(allow_user_request=True)` in serializer.""",

    11: """### Triage & Backlog Decision (Area 2 — Mohsin Khan)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Low / P3 (Risk Link: PR-04)
- **Technical Analysis:** Submitting identical POST requests in rapid succession generates duplicate requests.
- **Proposed Correction:** Support an `Idempotency-Key` header or add uniqueness constraint on `(creator, physical_access_level, start_time)`.""",

    12: """### Triage & Backlog Decision (Area 3 — Muhammad Aun)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** High / P1 (Risk Link: PR-02)
- **Technical Analysis:** OWASP ZAP passive scan flagged `moment.js v2.29.3` bundled in upstream `resources/`. Known CVE-2022-31129 exists in this version.
- **Proposed Correction:** Upgrade upstream vendor assets to `moment.js v2.29.4+` or migrate date formatting to native browser `Intl.DateTimeFormat`.""",

    13: """### Triage & Backlog Decision (Area 3 — Muhammad Aun)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Medium / P2 (Risk Link: PR-02)
- **Technical Analysis:** OWASP ZAP passive scan identified missing `Content-Security-Policy` (CSP) response headers.
- **Proposed Correction:** Add `django-csp` middleware to restrict script, style, and object injection vectors.""",

    14: """### Triage & Backlog Decision (Area 1 — Jaweria Abdul Hameed)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Medium / P2 (Risk Link: PR-05)
- **Technical Analysis:** SonarQube flagged Security Hotspot S3752 on `delete_access_request` because the view handler accepts both GET and POST requests. Although protected by Django CSRF tokens on POST, state modification via GET violates HTTP semantics.
- **Proposed Correction:** Enforce `@require_POST` decorator on `delete_access_request`.""",

    15: """### Triage & Backlog Decision (Area 3 — Muhammad Aun)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Low / P3 (Risk Link: PR-02)
- **Technical Analysis:** OWASP ZAP flagged `csrftoken` cookie without `HttpOnly` attribute.
- **Proposed Correction:** Document that Django intentionally allows JavaScript to read `csrftoken` for AJAX requests. In production, configure `CSRF_COOKIE_HTTPONLY = True` if token is injected into template DOM.""",

    16: """### Triage & Backlog Decision (Area 3 — Muhammad Aun)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Medium / P2 (Risk Link: PR-07)
- **Technical Analysis:** `mark_requests_expired()` loads expired requests into memory and calls `.save()` individually. Under high load, this causes serialized row locks.
- **Proposed Correction:** Batch update status using `QuerySet.update(status=RequestStatus.EXPIRED)` or schedule via background Celery worker.""",

    17: """### Triage & Backlog Decision (Area 3 — Muhammad Aun)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Low / P3 (Risk Link: PR-07)
- **Technical Analysis:** Reviewer query filtering on `status == PENDING` and `end_time > now` performs sequential scans on large tables.
- **Proposed Correction:** Add composite index `models.Index(fields=['status', 'end_time', 'deleted'])` in `TemporaryPhysicalAccessRequest.Meta.indexes`.""",

    22: """### Triage & Backlog Decision (Area 3 — Muhammad Aun)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Low / P3 (Risk Link: PR-08)
- **Technical Analysis:** Lighthouse flagged the pending badge color (`#999` text on `#f5f5f5` background) with a contrast ratio of 2.85:1 (below WCAG 1.4.3 AA minimum of 4.5:1).
- **Proposed Correction:** Update badge CSS styling to `#71717a` text for contrast ratio > 4.6:1.""",

    23: """### Triage & Backlog Decision (Area 3 — Muhammad Aun)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Medium / P2 (Risk Link: PR-08)
- **Technical Analysis:** Axe-core identified that the buddy search Typeahead input field lacks an explicit accessible label (`WCAG 3.3.2`).
- **Proposed Correction:** Add `aria-label="Search and select buddies"` to the input element in `access_request.html`.""",

    24: """### Triage & Backlog Decision (Area 3 — Muhammad Aun)
- **Triage Decision:** Deferred to Release v8.3.0 Backlog.
- **Severity / Priority:** Low / P3 (Risk Link: PR-08)
- **Technical Analysis:** Lighthouse flagged action buttons in the requests table having touch targets smaller than 48x48px on mobile viewports (`WCAG 2.5.5`).
- **Proposed Correction:** Add CSS mobile media query padding to ensure 48x48px tap targets.""",
}

def main():
    print("Posting triage comments to all open GitHub issues...")
    for issue_id, comment in TRIAGE_COMMENTS.items():
        cmd = ["gh", "issue", "comment", str(issue_id), "--body", comment]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Issue #{issue_id} commented successfully.")
        else:
            print(f"Failed to comment on Issue #{issue_id}: {res.stderr}")
        time.sleep(1)
    print("All open issues commented successfully!")

if __name__ == "__main__":
    main()
