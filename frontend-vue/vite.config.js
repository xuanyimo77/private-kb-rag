import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
// Vite 配置：
// - 路径别名 @ -> src
// - 开发环境把 /api 代理到后端 FastAPI（默认 127.0.0.1:8000），避免跨域
// 后端地址可通过环境变量 VITE_BACKEND_ORIGIN 覆盖
var backendOrigin = process.env.VITE_BACKEND_ORIGIN || 'http://127.0.0.1:8000';
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        },
    },
    server: {
        port: 5173,
        proxy: {
            // 前端请求以 /api 开头，代理时去掉 /api 前缀转发到后端
            '/api': {
                target: backendOrigin,
                changeOrigin: true,
                rewrite: function (path) { return path.replace(/^\/api/, ''); },
            },
        },
    },
    build: {
        // 分包：第三方库单独打包，利于缓存
        rollupOptions: {
            output: {
                manualChunks: {
                    vue: ['vue', 'vue-router', 'pinia'],
                    element: ['element-plus', '@element-plus/icons-vue'],
                    markdown: ['markdown-it'],
                },
            },
        },
    },
});
