var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var _a, _b, _c, _d, _e, _f, _g;
import { defineConfig, devices } from '@playwright/test';
var E2E_BACKEND_PORT = (_a = process.env.E2E_BACKEND_PORT) !== null && _a !== void 0 ? _a : '9000';
var E2E_FRONTEND_PORT = (_b = process.env.E2E_FRONTEND_PORT) !== null && _b !== void 0 ? _b : '5173';
var E2E_PYTHON = (_c = process.env.E2E_PYTHON) !== null && _c !== void 0 ? _c : '../backend/.venv/bin/python';
var E2E_DATABASE_URL = (_d = process.env.E2E_DATABASE_URL) !== null && _d !== void 0 ? _d : 'sqlite:///./e2e.db';
export default defineConfig({
    testDir: './e2e',
    fullyParallel: false,
    forbidOnly: !!process.env.CI,
    retries: 0,
    workers: 1,
    reporter: 'html',
    timeout: Number((_e = process.env.E2E_TEST_TIMEOUT) !== null && _e !== void 0 ? _e : 30000),
    use: {
        baseURL: "http://127.0.0.1:".concat(E2E_FRONTEND_PORT),
        trace: 'on-first-retry',
        actionTimeout: Number((_f = process.env.E2E_ACTION_TIMEOUT) !== null && _f !== void 0 ? _f : 10000),
        navigationTimeout: Number((_g = process.env.E2E_NAVIGATION_TIMEOUT) !== null && _g !== void 0 ? _g : 15000),
    },
    projects: [
        {
            name: 'chromium',
            use: __assign({}, devices['Desktop Chrome']),
        },
    ],
    webServer: [
        {
            command: "".concat(E2E_PYTHON, " -m alembic upgrade head && ").concat(E2E_PYTHON, " -m app.seed && ").concat(E2E_PYTHON, " -m uvicorn app.main:app --host 127.0.0.1 --port ").concat(E2E_BACKEND_PORT),
            url: "http://127.0.0.1:".concat(E2E_BACKEND_PORT, "/api/health/live"),
            cwd: '../backend',
            timeout: 180000,
            reuseExistingServer: false,
            stdout: 'pipe',
            stderr: 'pipe',
            env: {
                DATABASE_URL: E2E_DATABASE_URL,
            },
        },
        {
            command: "npm run dev -- --host 127.0.0.1 --port ".concat(E2E_FRONTEND_PORT, " --strictPort --bypass-lock"),
            url: "http://127.0.0.1:".concat(E2E_FRONTEND_PORT),
            timeout: 180000,
            reuseExistingServer: false,
            stdout: 'pipe',
            stderr: 'pipe',
            env: {
                BACKEND_PORT: E2E_BACKEND_PORT,
            },
        },
    ],
});
