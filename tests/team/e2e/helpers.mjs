import { execFileSync } from 'node:child_process';
import path from 'node:path';

export const TEST_PASSWORD = process.env.SQE_LOCAL_TEST_PASSWORD || 'nemo-sqe-test-2026';
const PYTHON_EXE = path.resolve('venv', 'Scripts', 'python.exe');
const DB_HELPER = path.resolve('scripts', 'e2e_db_helper.py');

export function runDbHelper(args) {
  const stdout = execFileSync(PYTHON_EXE, [DB_HELPER, ...args], {
    encoding: 'utf-8',
    env: {
      ...process.env,
      DJANGO_SETTINGS_MODULE: 'sqe_local.settings',
    },
  });
  return JSON.parse(stdout.trim());
}

export function resetDb(noSamples = false) {
  const args = ['reset'];
  if (noSamples) args.push('--no-samples');
  return runDbHelper(args);
}

export function createPendingRequest({ creator = 'lab_user', description, buddies = ['buddy_user'], hoursAhead = 24 }) {
  return runDbHelper([
    'create-pending',
    '--creator',
    creator,
    '--description',
    description,
    '--hours-ahead',
    String(hoursAhead),
    '--buddies',
    ...buddies,
  ]);
}

export function seedExpiredPending(description) {
  return runDbHelper(['seed-expired-pending', '--description', description]);
}

export function inspectRequest({ id, description }) {
  const args = ['inspect'];
  if (id !== undefined) {
    args.push('--id', String(id));
  } else {
    args.push('--description', description);
  }
  return runDbHelper(args);
}

export function setMinUsers(value) {
  return runDbHelper(['set-min-users', '--value', String(value)]);
}

export function formatNemoDate(offsetHours) {
  // Format as YYYY-MM-DD HH:mm:ss in America/New_York (matching NEMO DateTimeField input_formats[0])
  const target = new Date(Date.now() + offsetHours * 3600 * 1000);
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/New_York',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(target);
  const map = Object.fromEntries(parts.map((p) => [p.type, p.value]));
  return `${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}:${map.second}`;
}

export async function loginAs(page, username, password = TEST_PASSWORD) {
  await page.context().clearCookies();
  await page.goto('/login/', { waitUntil: 'domcontentloaded' });
  await page.fill('#username', username);
  await page.fill('#password', password);
  await Promise.all([
    page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 15000 }),
    page.click('#login_form button[type="submit"]'),
  ]);
}

export async function gotoAccessRequests(page) {
  await page.goto('/user_requests/access/', { waitUntil: 'domcontentloaded' });
  // #access-requests pane is loaded asynchronously via jQuery $.get
  await page.waitForSelector('#access-requests button, #access-requests a[href*="create_access_request"], #access-requests .italic', {
    timeout: 15000,
  });
}

export async function addBuddyViaTypeahead(page, searchText, expectedDisplaySubstring) {
  const input = page.locator('#search_other_users');
  await input.click();
  await input.fill(searchText);
  const suggestion = page.locator('.tt-suggestion', { hasText: expectedDisplaySubstring }).first();
  await suggestion.waitFor({ state: 'visible', timeout: 8000 });
  await suggestion.click();
}
