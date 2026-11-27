import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), '');
    return {
        plugins: [react()],
        server: {
            port: 5173,
            proxy: {
                '/api': {
                    target: "http://127.0.0.1:".concat(env.BACKEND_PORT || 9000),
                    changeOrigin: true,
                },
            },
        },
    };
});
