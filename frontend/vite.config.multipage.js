import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// 自定义插件：处理HTML中的main.js引用
const mainJsPlugin = () => {
  return {
    name: 'main-js-plugin',
    transformIndexHtml(html, context) {
      // 替换所有HTML文件中的main.js引用为构建后的正确路径
      if (context.filename.includes('index.html')) {
        // index.html已经正确处理，跳过
        return html;
      }
      
      // 对于其他HTML文件，替换main.js引用
      return html.replace(
        /<script\s+src=["']main\.js["']><\/script>/g,
        '<script type="module" src="/assets/main-56b7f0c5.js"></script>'
      );
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