/**
 * Run @axe-core/playwright and Google Lighthouse (Accessibility, Best Practices, SEO)
 * against key NEMO access-request screens in an authenticated Chromium session.
 *
 * Usage:
 *   node scripts/run_accessibility_audits.mjs --phase before
 *   node scripts/run_accessibility_audits.mjs --phase after --only create_access_request
 */

import { chromium } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import lighthouse from 'lighthouse';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync, spawn } from 'node:child_process';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:8000';
const TEST_PASSWORD = process.env.SQE_LOCAL_TEST_PASSWORD || 'nemo-sqe-test-2026';
const PYTHON_EXE = path.resolve('venv', 'Scripts', 'python.exe');

function parseArgs() {
  const args = process.argv.slice(2);
  let phase = 'before';
  let only = null;
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === '--phase' && args[i + 1]) {
      phase = args[i + 1];
      i += 1;
    } else if (args[i] === '--only' && args[i + 1]) {
      only = args[i + 1];
      i += 1;
    }
  }
  return { phase, only };
}

async function waitForServer(url, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const resp = await fetch(`${url}/login/`);
      if (resp.ok) return;
    } catch {
      // retry
    }
    await new Promise((r) => setTimeout(r, 400));
  }
  throw new Error(`Server did not become ready at ${url}`);
}

async function ensureServerRunning() {
  try {
    const resp = await fetch(`${BASE_URL}/login/`);
    if (resp.ok) return null;
  } catch {
    // start local runserver
  }
  const proc = spawn(PYTHON_EXE, ['manage.py', 'runserver', '127.0.0.1:8000', '--noreload'], {
    env: { ...process.env, DJANGO_SETTINGS_MODULE: 'sqe_local.settings' },
    stdio: 'ignore',
  });
  await waitForServer(BASE_URL);
  return proc;
}

async function loginInPage(page, username) {
  await page.context().clearCookies();
  await page.goto(`${BASE_URL}/login/`, { waitUntil: 'domcontentloaded' });
  await page.fill('#username', username);
  await page.fill('#password', TEST_PASSWORD);
  await Promise.all([
    page.waitForURL((u) => !u.pathname.startsWith('/login'), { timeout: 15000 }),
    page.click('#login_form button[type="submit"]'),
  ]);
}

function summarizeAxe(results) {
  return {
    url: results.url,
    violations_count: results.violations.length,
    passes_count: results.passes.length,
    incomplete_count: results.incomplete.length,
    violations: results.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      description: v.description,
      help: v.help,
      helpUrl: v.helpUrl,
      nodes: v.nodes.map((n) => ({
        target: n.target,
        html: n.html,
        failureSummary: n.failureSummary,
      })),
    })),
  };
}

function summarizeLighthouse(lhr) {
  const categories = {};
  for (const [k, v] of Object.entries(lhr.categories || {})) {
    categories[k] = Math.round((v.score ?? 0) * 100);
  }
  const failedAudits = [];
  for (const [id, audit] of Object.entries(lhr.audits || {})) {
    if (audit.score !== null && audit.score < 1) {
      failedAudits.push({
        id,
        title: audit.title,
        score: audit.score,
        displayValue: audit.displayValue || null,
        items_count: audit.details?.items?.length || 0,
        sample_items: (audit.details?.items || []).slice(0, 5),
      });
    }
  }
  return {
    finalUrl: lhr.finalUrl,
    scores: categories,
    failed_audits: failedAudits,
  };
}

async function main() {
  const { phase, only } = parseArgs();
  const outDir = path.resolve('docs', 'evidence', 'phase5', phase);
  fs.mkdirSync(outDir, { recursive: true });

  // Reset DB deterministically and find pending ID for edit/review screen
  const resetOut = JSON.parse(
    execFileSync(PYTHON_EXE, [path.resolve('scripts', 'e2e_db_helper.py'), 'reset'], {
      encoding: 'utf-8',
      env: { ...process.env, DJANGO_SETTINGS_MODULE: 'sqe_local.settings' },
    }).trim()
  );
  const pendingInfo = JSON.parse(
    execFileSync(
      PYTHON_EXE,
      [
        path.resolve('scripts', 'e2e_db_helper.py'),
        'inspect',
        '--description',
        'Synthetic pending cleanroom weekend lithography run',
      ],
      { encoding: 'utf-8', env: { ...process.env, DJANGO_SETTINGS_MODULE: 'sqe_local.settings' } }
    ).trim()
  );

  const serverProc = await ensureServerRunning();
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'nemo-lh-'));
  const debugPort = 9222;

  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: true,
    viewport: { width: 1280, height: 800 },
    args: [`--remote-debugging-port=${debugPort}`],
  });

  const summary = { phase, baseUrl: BASE_URL, resetRequests: resetOut.requests_count, screens: {} };

  try {
    const page = context.pages()[0] || (await context.newPage());

    const targets = [
      {
        key: 'login',
        url: `${BASE_URL}/login/`,
        authUser: null,
        waitFor: '#login_form',
      },
      {
        key: 'access_requests_dashboard',
        url: `${BASE_URL}/user_requests/access/`,
        authUser: 'lab_user',
        waitFor: '#pending_access_requests',
      },
      {
        key: 'create_access_request',
        url: `${BASE_URL}/create_access_request/`,
        authUser: 'lab_user',
        waitFor: 'form.well',
      },
      {
        key: 'review_access_request',
        url: `${BASE_URL}/edit_access_request/${pendingInfo.id}/`,
        authUser: 'facility_reviewer',
        waitFor: 'button[name="approve_request"]',
      },
    ].filter((t) => !only || t.key === only);

    for (const target of targets) {
      if (target.authUser) {
        await loginInPage(page, target.authUser);
      } else {
        await page.context().clearCookies();
      }

      await page.goto(target.url, { waitUntil: 'networkidle' });
      await page.waitForSelector(target.waitFor, { timeout: 15000 });

      // If on create/edit screen, add one buddy chip so dynamic UI elements (like remove_other_user link) are also audited!
      if (target.key === 'create_access_request') {
        await page.fill('#search_other_users', 'Sara');
        const sug = page.locator('.tt-suggestion', { hasText: 'Sara Ahmed' }).first();
        await sug.waitFor({ state: 'visible', timeout: 8000 });
        await sug.click();
      }

      // 1. Run @axe-core/playwright
      const axeResults = await new AxeBuilder({ page }).analyze();
      const axeSummary = summarizeAxe(axeResults);
      fs.writeFileSync(path.join(outDir, `axe_${target.key}.json`), JSON.stringify(axeResults, null, 2));

      // 2. Run Google Lighthouse on the same logged-in Chromium session
      const lhRunnerResult = await lighthouse(target.url, {
        port: debugPort,
        output: ['json', 'html'],
        logLevel: 'error',
        onlyCategories: ['accessibility', 'best-practices', 'seo'],
        disableStorageReset: true,
        formFactor: 'desktop',
        screenEmulation: { mobile: false, width: 1280, height: 800, deviceScaleFactor: 1, disabled: false },
      });

      const [lhJson, lhHtml] = lhRunnerResult.report;
      fs.writeFileSync(path.join(outDir, `lighthouse_${target.key}.json`), lhJson);
      fs.writeFileSync(path.join(outDir, `lighthouse_${target.key}.html`), lhHtml);
      const lhSummary = summarizeLighthouse(lhRunnerResult.lhr);

      summary.screens[target.key] = {
        url: target.url,
        axe: axeSummary,
        lighthouse: lhSummary,
      };
      console.log(
        `[${phase}] ${target.key}: axe violations=${axeSummary.violations_count}, Lighthouse scores=${JSON.stringify(
          lhSummary.scores
        )}`
      );
    }

    fs.writeFileSync(path.join(outDir, 'audit_summary.json'), JSON.stringify(summary, null, 2));
  } finally {
    await context.close();
    fs.rmSync(userDataDir, { recursive: true, force: true });
    if (serverProc) serverProc.kill();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
