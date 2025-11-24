import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Spin, message } from 'antd';
import axios from 'axios';

// 页面组件
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import DocumentManagementPage from './pages/DocumentManagementPage';
import QueryAnalysisPage from './pages/QueryAnalysisPage';
import KnowledgeGraphPage from './pages/KnowledgeGraphPage';
import ProfilePage from './pages/ProfilePage';
import SettingsPage from './pages/SettingsPage';

// 组件和工具
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import { AuthContextProvider, useAuth } from './context/AuthContext';
import { API_BASE_URL } from './utils/config';

const { Content } = Layout;

// 配置axios默认设置
axios.defaults.baseURL = API_BASE_URL;
axios.defaults.timeout = 30000;

// 请求拦截器
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // 处理401错误（未授权）
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(error);
        }
        
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken
        });
        
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        return axios(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    // 处理其他错误
    const errorMessage = error.response?.data?.detail || error.message || '请求失败';
    message.error(errorMessage);
    
    return Promise.reject(error);
  }
);

// 受保护的路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// 主应用布局组件
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  
  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };
  
  return (
    <Layout className="app-layout" style={{ minHeight: '100vh' }}>
      <Sidebar collapsed={collapsed} />
      <Layout className="site-layout">
        <Header collapsed={collapsed} onToggle={toggleSidebar} />
        <Content
          className="site-layout-background"
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            overflow: 'auto'
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

// 主要应用路由
const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      
      {/* 受保护的路由 */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <AppLayout>
            <DashboardPage />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/documents" element={
        <ProtectedRoute>
          <AppLayout>
            <DocumentManagementPage />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/query" element={
        <ProtectedRoute>
          <AppLayout>
            <QueryAnalysisPage />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/graph" element={
        <ProtectedRoute>
          <AppLayout>
            <KnowledgeGraphPage />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/profile" element={
        <ProtectedRoute>
          <AppLayout>
            <ProfilePage />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/settings" element={
        <ProtectedRoute>
          <AppLayout>
            <SettingsPage />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      {/* 重定向默认路由 */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

// 主应用组件
const App: React.FC = () => {
  const [isInitializing, setIsInitializing] = useState(true);
  
  useEffect(() => {
    // 初始化应用
    const initializeApp = async () => {
      try {
        // 可以在这里添加一些初始化逻辑，比如检查系统状态
        const response = await axios.get('/api/status', { timeout: 5000 });
        console.log('系统状态:', response.data);
      } catch (error) {
        console.error('初始化失败:', error);
      } finally {
        setIsInitializing(false);
      }
    };
    
    initializeApp();
  }, []);
  
  if (isInitializing) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" tip="正在启动应用..." />
      </div>
    );
  }
  
  return (
    <AuthContextProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthContextProvider>
  );
};

export default App;