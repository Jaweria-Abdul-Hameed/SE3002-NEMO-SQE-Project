import { test, expect } from '@playwright/test';
import {
  resetDb,
  createPendingRequest,
  inspectRequest,
  formatNemoDate,
  loginAs,
  gotoAccessRequests,
} from '../e2e/helpers.mjs';

test.describe('Phase 5 Usability, Error-Guidance & Keyboard Navigation Suite', () => {
  test.beforeEach(async () => {
    resetDb(false);
  });

  test('USA-WF1-ERR-KBD: Business-rule error guidance + recovery + keyboard-only navigation & submit', async ({ page }) => {
    const desc = 'Usability WF1 keyboard-submitted request';
    await loginAs(page, 'lab_user');
    await gotoAccessRequests(page);

    // Open Create Access Request screen
    await page.click('a[href="/create_access_request/"]');
    await expect(page).toHaveURL(/\/create_access_request\//);

    // Step 1: Submit a business-rule-rejected value (0 buddies violates BR-1 access_requests_minimum_users=2)
    await page.fill('#start_time', formatNemoDate(24));
    await page.fill('#end_time', formatNemoDate(28));
    await page.fill('#description', desc);
    await page.click('button[type="submit"]:has-text("Create access request")');

    // Assert the error explicitly explains what to correct
    await expect(page).toHaveURL(/\/create_access_request\//);
    await expect(page.locator('form.well')).toContainText('You need at least 1 other buddy for this request');

    // Step 2: Recover using keyboard-only navigation through required fields and submit button
    await page.locator('#start_time').focus();
    expect(await page.evaluate(() => document.activeElement?.id)).toBe('start_time');
    await page.keyboard.press('Escape'); // dismiss bootstrap-datetimepicker popup if open

    // Tab to #end_time
    await page.keyboard.press('Tab');
    expect(await page.evaluate(() => document.activeElement?.id)).toBe('end_time');
    await page.keyboard.press('Escape');

    // Tab to #physical_access_level
    await page.keyboard.press('Tab');
    expect(await page.evaluate(() => document.activeElement?.id)).toBe('physical_access_level');

    // Tab to #search_other_users (Buddies typeahead)
    await page.keyboard.press('Tab');
    expect(await page.evaluate(() => document.activeElement?.id)).toBe('search_other_users');

    // Add buddy solely via keyboard (type + ArrowDown + Enter)
    await page.keyboard.type('Sara');
    await page.locator('.tt-suggestion', { hasText: 'Sara Ahmed' }).first().waitFor({ state: 'visible', timeout: 8000 });
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    await expect(page.locator('#other_users input[name="other_users"]')).toHaveCount(1);

    // Note: add_other_user removes focus back to #search_other_users and appends a remove link in #other_users.
    // Tab until we reach #description, verifying #description is reachable via keyboard
    let activeId = await page.evaluate(() => document.activeElement?.id);
    let steps = 0;
    while (activeId !== 'description' && steps < 6) {
      await page.keyboard.press('Tab');
      activeId = await page.evaluate(() => document.activeElement?.id);
      steps += 1;
    }
    expect(activeId).toBe('description');

    // Tab to Submit button ("Create access request")
    await page.keyboard.press('Tab');
    const submitMeta = await page.evaluate(() => ({
      tag: document.activeElement?.tagName,
      type: document.activeElement?.getAttribute('type'),
      text: document.activeElement?.textContent?.trim(),
    }));
    expect(submitMeta.tag).toBe('BUTTON');
    expect(submitMeta.type).toBe('submit');
    expect(submitMeta.text).toContain('Create access request');

    // Submit using keyboard Enter key
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.keyboard.press('Enter'),
    ]);

    await page.waitForSelector('#pending_access_requests');
    await expect(page.locator('#pending_access_requests')).toContainText(desc);

    const dbState = inspectRequest({ description: desc });
    expect(dbState.found).toBe(true);
    expect(dbState.status).toBe(0);
    expect(dbState.other_users).toEqual(['buddy_user']);
  });

  test('USA-WF2-TASK: Facility Reviewer completes approval task & sees Approved confirmation', async ({ page }) => {
    const desc = 'Usability WF2 reviewer approval task';
    const created = createPendingRequest({
      creator: 'lab_user',
      description: desc,
      buddies: ['buddy_user'],
      hoursAhead: 36,
    });

    await loginAs(page, 'facility_reviewer');
    await gotoAccessRequests(page);

    await expect(page.locator('#pending_access_requests')).toContainText(desc);
    await page.click(`a[href="/edit_access_request/${created.id}/"]`);
    await expect(page).toHaveURL(new RegExp(`/edit_access_request/${created.id}/`));

    page.once('dialog', (dialog) => dialog.accept());
    await Promise.all([
      page.waitForURL(/\/user_requests\/access\//),
      page.click('button[name="approve_request"]'),
    ]);

    await page.waitForSelector('#approved_access_requests');
    await expect(page.locator('#approved_access_requests')).toContainText(desc);
    await expect(page.locator('#approved_access_requests')).toContainText('Dr. Nadia Siddiqui');

    const dbState = inspectRequest({ id: created.id });
    expect(dbState.status).toBe(1);
    expect(dbState.grants_count).toBe(2);
  });
});
