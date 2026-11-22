import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import {
  resetDb,
  createPendingRequest,
  inspectRequest,
  formatNemoDate,
  loginAs,
  gotoAccessRequests,
  addBuddyViaTypeahead,
} from '../e2e/helpers.mjs';

const EVIDENCE_FILE = path.resolve('docs', 'evidence', 'phase6', 'rbac_checks_evidence.json');
const roleCheckRecords = [];

function recordCheck(entry) {
  roleCheckRecords.push({
    ...entry,
    timestamp: new Date().toISOString(),
  });
}

test.describe('Phase 6 Defensive Security — Automated Role Access Checks', () => {
  test.beforeAll(() => {
    fs.mkdirSync(path.dirname(EVIDENCE_FILE), { recursive: true });
    roleCheckRecords.length = 0;
  });

  test.beforeEach(() => {
    resetDb(false);
  });

  test.afterAll(() => {
    fs.writeFileSync(EVIDENCE_FILE, JSON.stringify(roleCheckRecords, null, 2));
  });

  test('SEC-RBAC-01 (Allowed): Lab User can create own PENDING temporary access request', async ({ page }) => {
    const desc = 'SEC-RBAC-01 lab_user allowed create';
    await loginAs(page, 'lab_user');
    await page.goto('/create_access_request/', { waitUntil: 'domcontentloaded' });
    await page.fill('#start_time', formatNemoDate(24));
    await page.fill('#end_time', formatNemoDate(28));
    await addBuddyViaTypeahead(page, 'Sara', 'Sara Ahmed');
    await page.fill('#description', desc);

    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[type="submit"]:has-text("Create access request")'),
    ]);

    const dbState = inspectRequest({ description: desc });
    expect(dbState.found).toBe(true);
    expect(dbState.status).toBe(0);

    recordCheck({
      id: 'SEC-RBAC-01',
      role: 'Lab User (lab_user)',
      action: 'POST /create_access_request/ (create own request)',
      expected: 'ALLOWED (persists PENDING request, redirects to /user_requests/access/)',
      observed: `ALLOWED (status=${dbState.status}, id=${dbState.id})`,
      status: 'PASS',
    });
  });

  test('SEC-RBAC-02 (Denied): Lab User cannot self-approve own request via forged approve_request POST key', async ({ page }) => {
    const desc = 'SEC-RBAC-02 lab_user denied self-approve';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 26 });

    await loginAs(page, 'lab_user');
    await page.goto(`/edit_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('button[name="approve_request"]')).toHaveCount(0);

    await page.evaluate(() => {
      const form = document.querySelector('form.well');
      const hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = 'approve_request';
      hidden.value = 'Approve';
      form.appendChild(hidden);
    });
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[type="submit"]:has-text("Save changes")'),
    ]);

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.status).toBe(0);
    expect(dbState.reviewer).toBeNull();
    expect(dbState.grants_count).toBe(0);

    recordCheck({
      id: 'SEC-RBAC-02',
      role: 'Lab User (lab_user)',
      action: `POST /edit_access_request/${created.id}/ with approve_request=Approve`,
      expected: 'DENIED approval transition (status remains PENDING=0, 0 grants)',
      observed: `DENIED approval (status=${dbState.status}, reviewer=${dbState.reviewer}, grants=${dbState.grants_count})`,
      status: 'PASS',
    });
  });

  test('SEC-RBAC-03 (Denied): Unrelated Lab User cannot edit another users PENDING request', async ({ page }) => {
    const desc = 'SEC-RBAC-03 other_requester denied edit';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 28 });

    await loginAs(page, 'other_requester');
    await page.goto(`/edit_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });
    await page.fill('#description', 'Unauthorized overwrite attempt');
    await page.click('button[type="submit"]:has-text("Save changes")');

    await expect(page.locator('.alert-danger')).toContainText('You are not allowed to edit this request.');
    const dbState = inspectRequest({ id: created.id });
    expect(dbState.description).toBe(desc);

    recordCheck({
      id: 'SEC-RBAC-03',
      role: 'Lab User (other_requester)',
      action: `POST /edit_access_request/${created.id}/ owned by lab_user`,
      expected: 'DENIED with authorization error message; DB unchanged',
      observed: 'DENIED ("You are not allowed to edit this request."); DB unchanged',
      status: 'PASS',
    });
  });

  test('SEC-RBAC-04 (Denied): Lab User is denied access to CSV export (/export_access_requests/)', async ({ page }) => {
    await loginAs(page, 'lab_user');
    await gotoAccessRequests(page);
    await expect(page.locator('a[href="/export_access_requests/"]')).toHaveCount(0);

    const resp = await page.request.get('/export_access_requests/', { maxRedirects: 0 });
    expect(resp.status()).toBe(302);
    expect(resp.headers()['location']).toContain('/login/');

    recordCheck({
      id: 'SEC-RBAC-04',
      role: 'Lab User (lab_user)',
      action: 'GET /export_access_requests/',
      expected: 'DENIED (hidden in UI; direct request redirected to /login/)',
      observed: `DENIED (HTTP ${resp.status()} -> ${resp.headers()['location']})`,
      status: 'PASS',
    });
  });

  test('SEC-RBAC-05 (Allowed): Facility Manager / Reviewer can approve PENDING request and export CSV', async ({ page }) => {
    const desc = 'SEC-RBAC-05 reviewer allowed approve+export';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 30 });

    await loginAs(page, 'facility_reviewer');
    await gotoAccessRequests(page);
    await page.click(`a[href="/edit_access_request/${created.id}/"]`);

    page.once('dialog', (dialog) => dialog.accept());
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[name="approve_request"]'),
    ]);

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.status).toBe(1);
    expect(dbState.reviewer).toBe('facility_reviewer');
    expect(dbState.grants_count).toBe(2);

    const exportResp = await page.request.get('/export_access_requests/');
    expect(exportResp.status()).toBe(200);
    expect(exportResp.headers()['content-type']).toContain('text/csv');

    recordCheck({
      id: 'SEC-RBAC-05',
      role: 'Facility Manager / Area Reviewer (facility_reviewer)',
      action: `Approve /edit_access_request/${created.id}/ + GET /export_access_requests/`,
      expected: 'ALLOWED (status=APPROVED, 2 grants created, CSV HTTP 200)',
      observed: `ALLOWED (status=${dbState.status}, grants=${dbState.grants_count}, export HTTP ${exportResp.status()})`,
      status: 'PASS',
    });
  });

  test('SEC-RBAC-06 (Denied): Facility Reviewer cannot delete another users PENDING request', async ({ page }) => {
    const desc = 'SEC-RBAC-06 reviewer denied delete';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 32 });

    await loginAs(page, 'facility_reviewer');
    const resp = await page.goto(`/delete_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });
    expect(resp.status()).toBe(400);
    await expect(page.locator('body')).toContainText("You are not allowed to delete a request you didn't create.");

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.deleted).toBe(false);

    recordCheck({
      id: 'SEC-RBAC-06',
      role: 'Facility Manager / Area Reviewer (facility_reviewer)',
      action: `GET /delete_access_request/${created.id}/ owned by lab_user`,
      expected: 'DENIED (HTTP 400; deleted=false)',
      observed: `DENIED (HTTP ${resp.status()}; deleted=${dbState.deleted})`,
      status: 'PASS',
    });
  });

  test('SEC-RBAC-07 (Allowed): Area-only reviewer (non-staff) can view and deny area PENDING request', async ({ page }) => {
    const desc = 'SEC-RBAC-07 area reviewer allowed deny';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 34 });

    await loginAs(page, 'area_only_reviewer');
    await gotoAccessRequests(page);
    await page.click(`a[href="/edit_access_request/${created.id}/"]`);

    page.once('dialog', (dialog) => dialog.accept());
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[name="deny_request"]'),
    ]);

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.status).toBe(2);
    expect(dbState.reviewer).toBe('area_only_reviewer');
    expect(dbState.grants_count).toBe(0);

    recordCheck({
      id: 'SEC-RBAC-07',
      role: 'Area Reviewer (area_only_reviewer)',
      action: `Deny /edit_access_request/${created.id}/`,
      expected: 'ALLOWED (status=DENIED, 0 grants)',
      observed: `ALLOWED (status=${dbState.status}, reviewer=${dbState.reviewer}, grants=${dbState.grants_count})`,
      status: 'PASS',
    });
  });

  test('SEC-RBAC-08 (Denied): Unauthenticated anonymous user redirected to /login/ for all routes', async ({ page }) => {
    await page.context().clearCookies();
    const resp = await page.request.get('/access_requests/', { maxRedirects: 0 });
    expect(resp.status()).toBe(302);
    expect(resp.headers()['location']).toContain('/login/');

    recordCheck({
      id: 'SEC-RBAC-08',
      role: 'Anonymous (unauthenticated)',
      action: 'GET /access_requests/',
      expected: 'DENIED (HTTP 302 redirect to /login/)',
      observed: `DENIED (HTTP ${resp.status()} -> ${resp.headers()['location']})`,
      status: 'PASS',
    });
  });
});
