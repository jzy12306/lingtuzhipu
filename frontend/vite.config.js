// vite.config.js
export default {
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
    historyApiFallback: true
  },
  build: {
    outDir: 'dist',
    // SPA构建配置
    rollupOptions: {
      input: {
        main: './index.html'
      }
    }
  }
}