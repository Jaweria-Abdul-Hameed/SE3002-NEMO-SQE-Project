import { defineConfig } from '@playwright/test';

const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:8000';
const proxyServer = process.env.PLAYWRIGHT_PROXY_SERVER || undefined;
const pythonCmd = process.env.PYTHON_BIN || (process.platform === 'win32' ? '.\\venv\\Scripts\\python.exe' : 'python3');

export default defineConfig({
  testDir: './tests/team',
  testMatch: /.*\.(spec)\.(mjs|js)$/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45000,
  expect: {
    timeout: 10000,
  },
  reporter: [
    ['list'],
    ['json', { outputFile: 'docs/evidence/phase5/playwright_report.json' }],
    ['html', { outputFolder: 'docs/evidence/phase5/playwright-html-report', open: 'never' }],
  ],
  use: {
    baseURL,
    headless: true,
    viewport: { width: 1280, height: 800 },
    ignoreHTTPSErrors: true,
    ...(proxyServer ? { proxy: { server: proxyServer } } : {}),
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: process.env.SKIP_WEB_SERVER
    ? undefined
    : {
        command: `${pythonCmd} manage.py runserver 127.0.0.1:8000 --noreload`,
        url: 'http://127.0.0.1:8000/login/',
        reuseExistingServer: true,
        env: {
          ...process.env,
          DJANGO_SETTINGS_MODULE: 'sqe_local.settings',
        },
        timeout: 60000,
      },
});
