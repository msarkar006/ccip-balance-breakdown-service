import { defineConfig, devices } from '@playwright/test';

const E2E_BACKEND_PORT = process.env.E2E_BACKEND_PORT ?? '9000';
const E2E_FRONTEND_PORT = process.env.E2E_FRONTEND_PORT ?? '5173';
const E2E_PYTHON = process.env.E2E_PYTHON ?? '../backend/.venv/bin/python';
const E2E_DATABASE_URL = process.env.E2E_DATABASE_URL ?? 'sqlite:///./e2e.db';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'html',
  timeout: Number(process.env.E2E_TEST_TIMEOUT ?? 30_000),
  use: {
    baseURL: `http://127.0.0.1:${E2E_FRONTEND_PORT}`,
    trace: 'on-first-retry',
    actionTimeout: Number(process.env.E2E_ACTION_TIMEOUT ?? 10_000),
    navigationTimeout: Number(process.env.E2E_NAVIGATION_TIMEOUT ?? 15_000),
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: `${E2E_PYTHON} -m alembic upgrade head && ${E2E_PYTHON} -m app.seed && ${E2E_PYTHON} -m uvicorn app.main:app --host 127.0.0.1 --port ${E2E_BACKEND_PORT}`,
      url: `http://127.0.0.1:${E2E_BACKEND_PORT}/api/health/live`,
      cwd: '../backend',
      timeout: 180_000,
      reuseExistingServer: false,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        DATABASE_URL: E2E_DATABASE_URL,
      },
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${E2E_FRONTEND_PORT} --strictPort --bypass-lock`,
      url: `http://127.0.0.1:${E2E_FRONTEND_PORT}`,
      timeout: 180_000,
      reuseExistingServer: false,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        BACKEND_PORT: E2E_BACKEND_PORT,
      },
    },
  ],
});
