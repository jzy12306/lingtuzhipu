import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// 自定义插件：保留HTML中的main.js引用
// main.js 是独立的传统脚本，不需要被 Vite 处理，直接复制到 dist 目录
const mainJsPlugin = () => {
  return {
    name: 'main-js-plugin',
    transformIndexHtml(html, context) {
      // 不做任何替换，保持原样引用 main.js
      // main.js 会通过 Dockerfile 单独复制到 nginx 目录
      return html;
    }
  };
};

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [mainJsPlugin()],
  
  // 多页面应用配置
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        // 传统页面
        index: resolve(__dirname, 'index.html'),
        login: resolve(__dirname, 'login.html'),
        register: resolve(__dirname, 'register.html'),
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
  
  // 开发服务器配置
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
  
  // 优化依赖预构建
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', '@mui/material', '@mui/icons-material']
  }
})