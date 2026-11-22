import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import {
  resetDb,
  createPendingRequest,
  seedExpiredPending,
  inspectRequest,
  setMinUsers,
  formatNemoDate,
  loginAs,
  gotoAccessRequests,
  addBuddyViaTypeahead,
} from './helpers.mjs';

test.describe('Phase 5 Use Case E2E Suite (UC-01 through UC-06)', () => {
  test.beforeEach(async () => {
    resetDb(false);
  });

  // =========================================================================
  // UC-01: Lab User Submits a New Temporary Physical Access Request (Jaweria)
  // =========================================================================
  test('UC-01-MAIN: Lab User submits valid request -> appears in Pending & persisted in DB', async ({ page }) => {
    const desc = 'E2E UC-01 Main cleanroom deposition';
    await loginAs(page, 'lab_user');
    await gotoAccessRequests(page);

    await page.click('a[href="/create_access_request/"]');
    await expect(page).toHaveURL(/\/create_access_request\//);

    await page.fill('#start_time', formatNemoDate(24));
    await page.fill('#end_time', formatNemoDate(28));
    await addBuddyViaTypeahead(page, 'Sara', 'Sara Ahmed');
    await page.fill('#description', desc);

    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[type="submit"]:has-text("Create access request")'),
    ]);

    await page.waitForSelector('#pending_access_requests');
    await expect(page.locator('#pending_access_requests')).toContainText(desc);

    const dbState = inspectRequest({ description: desc });
    expect(dbState.found).toBe(true);
    expect(dbState.status).toBe(0);
    expect(dbState.deleted).toBe(false);
    expect(dbState.creator).toBe('lab_user');
    expect(dbState.other_users).toEqual(['buddy_user']);
    expect(dbState.grants_count).toBe(0);
    expect(dbState.notifications_count).toBeGreaterThan(0);
  });

  test('UC-01-ALT-1: Raised minimum user threshold (3) allows submit with 2 buddies', async ({ page }) => {
    setMinUsers(3);
    const desc = 'E2E UC-01 Alt-1 dual buddy request';
    await loginAs(page, 'lab_user');
    await page.goto('/create_access_request/', { waitUntil: 'domcontentloaded' });

    await page.fill('#start_time', formatNemoDate(30));
    await page.fill('#end_time', formatNemoDate(34));
    await addBuddyViaTypeahead(page, 'Sara', 'Sara Ahmed');
    await addBuddyViaTypeahead(page, 'Zain', 'Zain Malik');
    await page.fill('#description', desc);

    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[type="submit"]:has-text("Create access request")'),
    ]);

    await page.waitForSelector('#pending_access_requests');
    await expect(page.locator('#pending_access_requests')).toContainText(desc);

    const dbState = inspectRequest({ description: desc });
    expect(dbState.found).toBe(true);
    expect(dbState.status).toBe(0);
    expect(dbState.other_users).toEqual(['buddy_user', 'buddy_user_2']);
  });

  test('UC-01-ALT-2: Buddy sees shared Pending request in read-only mode without Edit/Delete', async ({ page }) => {
    const desc = 'E2E UC-01 Alt-2 buddy visibility';
    createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 36 });

    await loginAs(page, 'buddy_user');
    await gotoAccessRequests(page);

    const pendingTable = page.locator('#pending_access_requests');
    await expect(pendingTable).toContainText(desc);
    const row = pendingTable.locator('tr', { hasText: 'Ali Raza' }).first();
    await expect(row).toBeVisible();
    // Buddy is not creator/reviewer, so no Edit or Delete button for that request
    await expect(pendingTable.locator('a[title="Edit request"]')).toHaveCount(0);
    await expect(pendingTable.locator('a[title="Delete request"]')).toHaveCount(0);

    const dbState = inspectRequest({ description: desc });
    expect(dbState.other_users).toContain('buddy_user');
  });

  test('UC-01-EXC-1: Submitting with 0 buddies shows minimum-user boundary error and persists nothing', async ({ page }) => {
    const beforeCount = inspectRequest({ description: 'Synthetic pending cleanroom weekend lithography run' }).total_requests_count;
    const desc = 'E2E UC-01 Exc-1 zero buddies';

    await loginAs(page, 'lab_user');
    await page.goto('/create_access_request/', { waitUntil: 'domcontentloaded' });
    await page.fill('#start_time', formatNemoDate(24));
    await page.fill('#end_time', formatNemoDate(28));
    await page.fill('#description', desc);

    await page.click('button[type="submit"]:has-text("Create access request")');
    await expect(page).toHaveURL(/\/create_access_request\//);
    await expect(page.locator('form.well')).toContainText('You need at least 1 other buddy for this request');

    const dbState = inspectRequest({ description: desc });
    expect(dbState.found).toBe(false);
    const afterCount = inspectRequest({ description: 'Synthetic pending cleanroom weekend lithography run' }).total_requests_count;
    expect(afterCount).toBe(beforeCount);
  });

  test('UC-01-EXC-2: Submitting past start_time shows time-guard error and persists nothing', async ({ page }) => {
    const desc = 'E2E UC-01 Exc-2 past start time';

    await loginAs(page, 'lab_user');
    await page.goto('/create_access_request/', { waitUntil: 'domcontentloaded' });
    await page.fill('#start_time', formatNemoDate(-5));
    await page.fill('#end_time', formatNemoDate(4));
    await addBuddyViaTypeahead(page, 'Sara', 'Sara Ahmed');
    await page.fill('#description', desc);

    await page.click('button[type="submit"]:has-text("Create access request")');
    await expect(page).toHaveURL(/\/create_access_request\//);
    await expect(page.locator('form.well')).toContainText('The start time must be later than the current time');

    const dbState = inspectRequest({ description: desc });
    expect(dbState.found).toBe(false);
  });

  // =========================================================================
  // UC-02: Lab User Views Status Buckets & Edits a Pending Access Request
  // =========================================================================
  test('UC-02-MAIN: Creator views Pending/Approved buckets and edits own Pending request', async ({ page }) => {
    const initialDesc = 'E2E UC-02 Main initial description';
    const updatedDesc = 'E2E UC-02 Main updated description';
    const created = createPendingRequest({ creator: 'lab_user', description: initialDesc, buddies: ['buddy_user'], hoursAhead: 40 });

    await loginAs(page, 'lab_user');
    await gotoAccessRequests(page);

    await expect(page.locator('#pending_access_requests')).toContainText(initialDesc);
    await expect(page.locator('#approved_access_requests')).toContainText('Synthetic approved cleanroom wafer inspection');

    await page.click(`a[href="/edit_access_request/${created.id}/"]`);
    await expect(page).toHaveURL(new RegExp(`/edit_access_request/${created.id}/`));
    await page.fill('#description', updatedDesc);

    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[type="submit"]:has-text("Save changes")'),
    ]);

    await page.waitForSelector('#pending_access_requests');
    await expect(page.locator('#pending_access_requests')).toContainText(updatedDesc);

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.description).toBe(updatedDesc);
    expect(dbState.status).toBe(0);
    expect(dbState.last_updated_by).toBe('lab_user');
  });

  test('UC-02-ALT-1: Unrelated user dashboard excludes other users requests', async ({ page }) => {
    await loginAs(page, 'other_requester');
    await gotoAccessRequests(page);

    const content = await page.locator('#access-requests').innerText();
    expect(content).not.toContain('Synthetic pending cleanroom weekend lithography run');
    expect(content).not.toContain('Synthetic approved cleanroom wafer inspection');
    expect(content).toContain('Synthetic denied maintenance window overlap');
  });

  test('UC-02-ALT-2: Area reviewer edits Pending request without approving/denying keeps Pending', async ({ page }) => {
    const initialDesc = 'E2E UC-02 Alt-2 reviewer edit';
    const updatedDesc = 'E2E UC-02 Alt-2 reviewer clarified scope';
    const created = createPendingRequest({ creator: 'lab_user', description: initialDesc, buddies: ['buddy_user'], hoursAhead: 42 });

    await loginAs(page, 'area_only_reviewer');
    await page.goto(`/edit_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });
    await page.fill('#description', updatedDesc);

    // Trigger plain form submit without clicking Approve or Deny button
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.evaluate(() => document.querySelector('form.well').submit()),
    ]);

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.status).toBe(0);
    expect(dbState.description).toBe(updatedDesc);
    expect(dbState.last_updated_by).toBe('area_only_reviewer');
    expect(dbState.grants_count).toBe(0);
  });

  test('UC-02-EXC-1: Unrelated user edit POST is rejected with authorization error', async ({ page }) => {
    const initialDesc = 'E2E UC-02 Exc-1 protected request';
    const created = createPendingRequest({ creator: 'lab_user', description: initialDesc, buddies: ['buddy_user'], hoursAhead: 44 });

    await loginAs(page, 'other_requester');
    await page.goto(`/edit_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });
    await page.fill('#description', 'Tampered description');
    await page.click('button[type="submit"]:has-text("Save changes")');

    await expect(page.locator('.alert-danger')).toContainText('You are not allowed to edit this request.');
    const dbState = inspectRequest({ id: created.id });
    expect(dbState.description).toBe(initialDesc);
  });

  test('UC-02-EXC-2: Edit attempt on Approved request hides submit controls and rejects POST', async ({ page }) => {
    const approved = inspectRequest({ description: 'Synthetic approved cleanroom wafer inspection' });
    await loginAs(page, 'lab_user');
    await page.goto(`/edit_access_request/${approved.id}/`, { waitUntil: 'domcontentloaded' });

    // UI hides Save/Approve/Deny buttons for non-Pending request
    await expect(page.locator('form.well button[type="submit"]')).toHaveCount(0);

    // Direct POST via browser form submission is rejected
    await page.fill('#description', 'Attempted post-approval edit');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
      page.evaluate(() => document.querySelector('form.well').submit()),
    ]);
    await expect(page.locator('.alert-danger')).toContainText('Only pending requests can be modified.');

    const dbState = inspectRequest({ id: approved.id });
    expect(dbState.status).toBe(1);
    expect(dbState.description).toBe('Synthetic approved cleanroom wafer inspection');
  });

  // =========================================================================
  // UC-03: Lab User Soft-Deletes a Pending Access Request (Mohsin)
  // =========================================================================
  test('UC-03-MAIN: Creator confirms delete -> soft-deleted in DB & removed from UI', async ({ page }) => {
    const desc = 'E2E UC-03 Main delete target';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 48 });

    await loginAs(page, 'lab_user');
    await gotoAccessRequests(page);
    await expect(page.locator('#pending_access_requests')).toContainText(desc);

    page.once('dialog', (dialog) => dialog.accept());
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click(`a[href="/delete_access_request/${created.id}/"]`),
    ]);

    await page.waitForSelector('#access-requests');
    await expect(page.locator('#access-requests')).not.toContainText(desc);

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.deleted).toBe(true);
    expect(dbState.notifications_count).toBe(0);
  });

  test('UC-03-ALT-1: Dismissing confirm dialog cancels delete and preserves request', async ({ page }) => {
    const desc = 'E2E UC-03 Alt-1 cancel delete';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 50 });

    await loginAs(page, 'lab_user');
    await gotoAccessRequests(page);

    page.once('dialog', (dialog) => dialog.dismiss());
    await page.click(`a[href="/delete_access_request/${created.id}/"]`);

    await expect(page.locator('#pending_access_requests')).toContainText(desc);
    const dbState = inspectRequest({ id: created.id });
    expect(dbState.deleted).toBe(false);
    expect(dbState.status).toBe(0);
  });

  test('UC-03-ALT-2: Soft-deleted request is absent from Reviewer queue', async ({ page }) => {
    const desc = 'E2E UC-03 Alt-2 hidden from reviewer';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 52 });

    await loginAs(page, 'lab_user');
    await gotoAccessRequests(page);
    page.once('dialog', (dialog) => dialog.accept());
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click(`a[href="/delete_access_request/${created.id}/"]`),
    ]);

    await loginAs(page, 'facility_reviewer');
    await gotoAccessRequests(page);
    await expect(page.locator('#access-requests')).not.toContainText(desc);
  });

  test('UC-03-EXC-1: Non-creator delete URL returns HTTP 400 and preserves request', async ({ page }) => {
    const desc = 'E2E UC-03 Exc-1 non-creator delete';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 54 });

    await loginAs(page, 'other_requester');
    const resp = await page.goto(`/delete_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });
    expect(resp.status()).toBe(400);
    await expect(page.locator('body')).toContainText("You are not allowed to delete a request you didn't create.");

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.deleted).toBe(false);
  });

  test('UC-03-EXC-2: Delete attempt on Approved request returns HTTP 400 and preserves record', async ({ page }) => {
    const approved = inspectRequest({ description: 'Synthetic approved cleanroom wafer inspection' });

    await loginAs(page, 'lab_user');
    const resp = await page.goto(`/delete_access_request/${approved.id}/`, { waitUntil: 'domcontentloaded' });
    expect(resp.status()).toBe(400);
    await expect(page.locator('body')).toContainText('You are not allowed to delete a request that is not pending.');

    const dbState = inspectRequest({ id: approved.id });
    expect(dbState.deleted).toBe(false);
    expect(dbState.status).toBe(1);
  });

  // =========================================================================
  // UC-04: Facility Manager / Area Reviewer Approves Request (Mohsin)
  // =========================================================================
  test('UC-04-MAIN: Facility Reviewer approves Pending request -> Approved UI & grants persisted', async ({ page }) => {
    const desc = 'E2E UC-04 Main approval request';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 56 });

    await loginAs(page, 'facility_reviewer');
    await gotoAccessRequests(page);

    await page.click(`a[href="/edit_access_request/${created.id}/"]`);
    await expect(page.locator('#creator_readonly')).toBeDisabled();

    page.once('dialog', (dialog) => dialog.accept());
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[name="approve_request"]'),
    ]);

    await page.waitForSelector('#approved_access_requests');
    await expect(page.locator('#approved_access_requests')).toContainText(desc);

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.status).toBe(1);
    expect(dbState.reviewer).toBe('facility_reviewer');
    expect(dbState.grants_count).toBe(2);
    expect(dbState.granted_users).toEqual(['buddy_user', 'lab_user']);
    expect(dbState.reviewer_notifications_count).toBe(0);
    expect(dbState.notifications_count).toBe(2);
  });

  test('UC-04-ALT-1: Area-only reviewer (non-facility-manager) approves request & generates grants', async ({ page }) => {
    const desc = 'E2E UC-04 Alt-1 area reviewer approval';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 60 });

    await loginAs(page, 'area_only_reviewer');
    await gotoAccessRequests(page);
    await page.click(`a[href="/edit_access_request/${created.id}/"]`);

    page.once('dialog', (dialog) => dialog.accept());
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[name="approve_request"]'),
    ]);

    await expect(page.locator('#approved_access_requests')).toContainText(desc);
    const dbState = inspectRequest({ id: created.id });
    expect(dbState.status).toBe(1);
    expect(dbState.reviewer).toBe('area_only_reviewer');
    expect(dbState.grants_count).toBe(2);
  });

  test('UC-04-ALT-2: Reviewer start-time override allows approving request whose start_time has passed', async ({ page }) => {
    const desc = 'E2E UC-04 Alt-2 past-start reviewer override';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: -1 });

    await loginAs(page, 'facility_reviewer');
    await page.goto(`/edit_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });

    page.once('dialog', (dialog) => dialog.accept());
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[name="approve_request"]'),
    ]);

    await expect(page.locator('#approved_access_requests')).toContainText(desc);
    const dbState = inspectRequest({ id: created.id });
    expect(dbState.status).toBe(1);
    expect(dbState.grants_count).toBe(2);
  });

  test('UC-04-EXC-1: Non-reviewer submitting approve_request POST key cannot self-approve', async ({ page }) => {
    const desc = 'E2E UC-04 Exc-1 self-approve attempt';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 64 });

    await loginAs(page, 'lab_user');
    await page.goto(`/edit_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });

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
  });

  test('UC-04-EXC-2: Re-reviewing already Approved request hides Approve/Deny and blocks duplicate grants', async ({ page }) => {
    const approved = inspectRequest({ description: 'Synthetic approved cleanroom wafer inspection' });
    const initialTotalGrants = approved.total_grants_count;

    await loginAs(page, 'facility_reviewer');
    await page.goto(`/edit_access_request/${approved.id}/`, { waitUntil: 'domcontentloaded' });

    await expect(page.locator('button[name="approve_request"]')).toHaveCount(0);
    await expect(page.locator('button[name="deny_request"]')).toHaveCount(0);

    await Promise.all([
      page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
      page.evaluate(() => {
        const form = document.querySelector('form.well');
        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'approve_request';
        hidden.value = 'Approve';
        form.appendChild(hidden);
        form.submit();
      }),
    ]);

    await expect(page.locator('.alert-danger')).toContainText('Only pending requests can be modified.');
    const after = inspectRequest({ id: approved.id });
    expect(after.total_grants_count).toBe(initialTotalGrants);
  });

  // =========================================================================
  // UC-05: Facility Manager / Area Reviewer Denies Request (Muhammad Aun)
  // =========================================================================
  test('UC-05-MAIN: Reviewer denies Pending request -> Denied UI & 0 grants persisted', async ({ page }) => {
    const desc = 'E2E UC-05 Main denial request';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 70 });

    await loginAs(page, 'facility_reviewer');
    await gotoAccessRequests(page);
    await page.click(`a[href="/edit_access_request/${created.id}/"]`);

    page.once('dialog', (dialog) => dialog.accept());
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[name="deny_request"]'),
    ]);

    await page.waitForSelector('#denied_access_requests');
    await expect(page.locator('#denied_access_requests')).toContainText(desc);

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.status).toBe(2);
    expect(dbState.reviewer).toBe('facility_reviewer');
    expect(dbState.grants_count).toBe(0);
  });

  test('UC-05-ALT-1: Requester views Denied request with reviewer name and no Edit/Delete buttons', async ({ page }) => {
    const desc = 'E2E UC-05 Alt-1 requester views denied';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 72 });

    await loginAs(page, 'facility_reviewer');
    await page.goto(`/edit_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });
    page.once('dialog', (dialog) => dialog.accept());
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[name="deny_request"]'),
    ]);

    await loginAs(page, 'lab_user');
    await gotoAccessRequests(page);
    await expect(page.locator('#denied_access_requests')).toContainText(desc);
    await expect(page.locator('#denied_access_requests')).toContainText('Dr. Nadia Siddiqui');
    await expect(page.locator(`a[href="/edit_access_request/${created.id}/"]`)).toHaveCount(0);
  });

  test('UC-05-ALT-2: Dismissing Deny confirmation dialog keeps request Pending', async ({ page }) => {
    const desc = 'E2E UC-05 Alt-2 cancel deny';
    const created = createPendingRequest({ creator: 'lab_user', description: desc, buddies: ['buddy_user'], hoursAhead: 74 });

    await loginAs(page, 'facility_reviewer');
    await page.goto(`/edit_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });

    page.once('dialog', (dialog) => dialog.dismiss());
    await page.click('button[name="deny_request"]');

    await expect(page).toHaveURL(new RegExp(`/edit_access_request/${created.id}/`));
    const dbState = inspectRequest({ id: created.id });
    expect(dbState.status).toBe(0);
    expect(dbState.reviewer).toBeNull();
  });

  test('UC-05-EXC-1: Requester edit POST on Denied request is rejected', async ({ page }) => {
    const denied = inspectRequest({ description: 'Synthetic denied maintenance window overlap' });

    await loginAs(page, 'other_requester');
    await page.goto(`/edit_access_request/${denied.id}/`, { waitUntil: 'domcontentloaded' });
    await page.fill('#description', 'Attempt edit after deny');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
      page.evaluate(() => document.querySelector('form.well').submit()),
    ]);

    await expect(page.locator('.alert-danger')).toContainText('Only pending requests can be modified.');
    const dbState = inspectRequest({ id: denied.id });
    expect(dbState.status).toBe(2);
    expect(dbState.description).toBe('Synthetic denied maintenance window overlap');
  });

  test('UC-05-EXC-2: Requester delete on Denied request returns HTTP 400', async ({ page }) => {
    const denied = inspectRequest({ description: 'Synthetic denied maintenance window overlap' });

    await loginAs(page, 'other_requester');
    const resp = await page.goto(`/delete_access_request/${denied.id}/`, { waitUntil: 'domcontentloaded' });
    expect(resp.status()).toBe(400);
    await expect(page.locator('body')).toContainText('You are not allowed to delete a request that is not pending.');

    const dbState = inspectRequest({ id: denied.id });
    expect(dbState.deleted).toBe(false);
    expect(dbState.status).toBe(2);
  });

  // =========================================================================
  // UC-06: Auto-Expiration & Facility Manager CSV Export (Muhammad Aun)
  // =========================================================================
  test('UC-06-MAIN: Loading dashboard auto-expires past-due Pending & Facility Manager exports CSV', async ({ page }) => {
    const expDesc = 'E2E UC-06 Main past-due pending';
    const expReq = seedExpiredPending(expDesc);

    await loginAs(page, 'facility_reviewer');
    await gotoAccessRequests(page);

    await expect(page.locator('#expired_access_requests')).toContainText(expDesc);
    const dbState = inspectRequest({ id: expReq.id });
    expect(dbState.status).toBe(3);

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('a[href="/export_access_requests/"]'),
    ]);
    expect(download.suggestedFilename()).toMatch(/^access_requests_.*\.csv$/);
    const csvPath = await download.path();
    const csvText = fs.readFileSync(csvPath, 'utf-8');
    expect(csvText).toContain('Status,Created date');
    expect(csvText).toContain('Expired');
    expect(csvText).toContain('Approved');
  });

  test('UC-06-ALT-1: Lab User triggers auto-expire and Export button is hidden', async ({ page }) => {
    const expDesc = 'E2E UC-06 Alt-1 user auto-expire';
    const expReq = seedExpiredPending(expDesc);

    await loginAs(page, 'lab_user');
    await gotoAccessRequests(page);

    await expect(page.locator('#expired_access_requests')).toContainText(expDesc);
    await expect(page.locator('a[href="/export_access_requests/"]')).toHaveCount(0);

    const dbState = inspectRequest({ id: expReq.id });
    expect(dbState.status).toBe(3);
  });

  test('UC-06-ALT-2: Soft-deleted request is excluded from CSV export and Expired bucket', async ({ page }) => {
    const delDesc = 'E2E UC-06 Alt-2 deleted exclusion';
    const created = createPendingRequest({ creator: 'lab_user', description: delDesc, buddies: ['buddy_user'], hoursAhead: 80 });

    await loginAs(page, 'lab_user');
    await page.goto(`/delete_access_request/${created.id}/`, { waitUntil: 'domcontentloaded' });

    await loginAs(page, 'facility_reviewer');
    await gotoAccessRequests(page);
    await expect(page.locator('#access-requests')).not.toContainText(delDesc);

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('a[href="/export_access_requests/"]'),
    ]);
    const csvText = fs.readFileSync(await download.path(), 'utf-8');
    expect(csvText).not.toContain(delDesc);
  });

  test('UC-06-EXC-1: Lab User direct access to /export_access_requests/ is denied', async ({ page }) => {
    await loginAs(page, 'lab_user');
    const resp = await page.request.get('/export_access_requests/', { maxRedirects: 0 });
    expect(resp.status()).toBe(302);
    expect(resp.headers()['location']).toContain('/login/');
  });

  test('UC-06-EXC-2: Edit attempt on auto-Expired request is rejected with non-pending error', async ({ page }) => {
    const expDesc = 'E2E UC-06 Exc-2 expired lock';
    const expReq = seedExpiredPending(expDesc);

    await loginAs(page, 'lab_user');
    await gotoAccessRequests(page);

    await page.goto(`/edit_access_request/${expReq.id}/`, { waitUntil: 'domcontentloaded' });
    await page.fill('#description', 'Attempt edit expired');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
      page.evaluate(() => document.querySelector('form.well').submit()),
    ]);

    await expect(page.locator('.alert-danger')).toContainText('Only pending requests can be modified.');
    const dbState = inspectRequest({ id: expReq.id });
    expect(dbState.status).toBe(3);
  });
});
