import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    },
    // SPA路由重定向，所有404请求都重定向到index.html
    historyApiFallback: {
      rewrites: [
        { from: /^\/dashboard/, to: '/index.html' },
        { from: /^\/documents/, to: '/index.html' },
        { from: /^\/graph/, to: '/index.html' },
        { from: /^\/login/, to: '/index.html' },
        { from: /^\/query/, to: '/index.html' },
        { from: /^\/register/, to: '/index.html' },
        { from: /^\/query-history/, to: '/index.html' },
        { from: /^\/preferences/, to: '/index.html' },
        { from: /^\/admin/, to: '/index.html' },
        { from: /^\/organization/, to: '/index.html' },
      ]
    }
  },
  build: {
    outDir: 'dist',
    // 优化构建配置 - 支持多页面应用
    rollupOptions: {
      input: {
        // 主应用 (React) - 使用独立的React入口
        main: resolve(__dirname, 'index-react.html'),
        // 传统页面
        index: resolve(__dirname, 'index.html'),
        login: resolve(__dirname, 'login.html'),
        query: resolve(__dirname, 'query.html'),
        graph: resolve(__dirname, 'graph.html'),
        admin: resolve(__dirname, 'admin.html'),
        userCenter: resolve(__dirname, 'user-center.html'),
      },
      // 忽略 "use client" 指令警告
      onwarn(warning, warn) {
        if (warning.code === 'MODULE_LEVEL_DIRECTIVE') {
          return;
        }
        warn(warning);
      }
    },
    // 优化chunk大小
    chunkSizeWarningLimit: 1000
  },
  // 优化依赖预构建
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', '@mui/material', '@mui/icons-material']
  }
})