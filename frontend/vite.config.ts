/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { configDefaults } from 'vitest/config';

export default defineConfig(({ mode }) => {
  // '' loads every variable, including the process environment start.sh sets.
  const env = loadEnv(mode, process.cwd(), '');
  const backend = { target: `http://127.0.0.1:${env.BACKEND_PORT || 9000}` };
  return {
    plugins: [react()],
    // No `rewrite`: the backend mounts its routes under /api/v1, so the path goes through unchanged.
    server: { port: 5173, proxy: { '/api': backend } },
    preview: { proxy: { '/api': backend } },
    css: { preprocessorOptions: { scss: { quietDeps: true, silenceDeprecations: ['import', 'global-builtin'] } } },
    test: {
      environment: 'jsdom',
      globals: true,
      css: false,
      setupFiles: ['./src/test/setup.ts'],
      exclude: [...configDefaults.exclude, 'e2e/**'],
    },
  };
});
