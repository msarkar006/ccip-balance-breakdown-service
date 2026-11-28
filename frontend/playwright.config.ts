import { defineConfig } from '@playwright/test';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const backendDir = resolve(here, '../backend');
const backendPort = process.env.E2E_BACKEND_PORT ?? '9100';
const frontendPort = process.env.E2E_FRONTEND_PORT ?? '5173';
const py = process.env.E2E_PYTHON ?? 'python';
const quoted = py.includes(' ') ? `"${py}"` : py;

export default defineConfig({
  testDir: '../tests/e2e',
  retries: 0,
  workers: 1,
  timeout: Number(process.env.E2E_TEST_TIMEOUT ?? 30_000),
  reporter: [['list']],
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    actionTimeout: Number(process.env.E2E_ACTION_TIMEOUT ?? 10_000),
    navigationTimeout: Number(process.env.E2E_NAVIGATION_TIMEOUT ?? 15_000),
  },
  webServer: [
    {
      // Migrations (never create_all), then the idempotent seed, then the API.
      command: `${quoted} -m alembic upgrade head && ${quoted} -m app.seed && ${quoted} -m uvicorn app.main:app --host 127.0.0.1 --port ${backendPort}`,
      cwd: backendDir,
      env: {
        DATABASE_URL: process.env.E2E_DATABASE_URL ?? 'sqlite:///./e2e.db',
        ENVIRONMENT: 'development',
        SEED_ENABLED: 'true',
        JWT_SECRET_KEY: process.env.JWT_SECRET_KEY ?? 'e2e-only-secret-key-0123456789abcdef0123',
        CORS_ORIGINS: `http://127.0.0.1:${frontendPort},http://localhost:${frontendPort}`,
      },
      url: `http://127.0.0.1:${backendPort}/health`,
      reuseExistingServer: false,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort} --strictPort`,
      env: { BACKEND_PORT: backendPort },
      url: `http://127.0.0.1:${frontendPort}`,
      reuseExistingServer: false,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
