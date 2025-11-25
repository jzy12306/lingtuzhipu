import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import type { FC } from 'react';

// 导入页面组件
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import DashboardPage from '../pages/DashboardPage';
import DocumentManagementPage from '../pages/DocumentManagementPage';
import GraphVisualizationPage from '../pages/GraphVisualizationPage';
import QueryPage from '../pages/QueryPage';
import UserCenterPage from '../pages/UserCenterPage';

// 导入布局组件
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import { AuthContextProvider } from '../context/AuthContext';

const { Content } = Layout;

// 主布局组件
const MainLayout: FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = React.useState(false);

  const toggleCollapsed = () => {
    setCollapsed(!collapsed);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header collapsed={collapsed} onToggle={toggleCollapsed} />
      <Layout hasSider>
        <Sidebar collapsed={collapsed} />
        <Layout>
          <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', minHeight: 280 }}>
            {children}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

// 公共布局 - 无侧边栏
const PublicLayout: FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header collapsed={false} onToggle={() => {}} />
      <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', minHeight: 280 }}>
        {children}
      </Content>
    </Layout>
  );
};

// 主路由配置
const AppRoutes: FC = () => {
  return (
    <AuthContextProvider>
      <Router>
        <Routes>
          {/* 公共路由 - 无需认证 */}
          <Route path="/login" element={
            <PublicLayout>
              <LoginPage />
            </PublicLayout>
          } />
          <Route path="/register" element={
            <PublicLayout>
              <RegisterPage />
            </PublicLayout>
          } />

          {/* 受保护的路由 - 需要认证 */}
          <Route path="/" element={
            <MainLayout>
              <DashboardPage />
            </MainLayout>
          } />
          
          {/* 文档管理 */}
          <Route path="/documents" element={
            <MainLayout>
              <DocumentManagementPage />
            </MainLayout>
          } />
          
          {/* 知识图谱可视化 */}
          <Route path="/visualization" element={
            <MainLayout>
              <GraphVisualizationPage />
            </MainLayout>
          } />
          
          {/* 智能查询 */}
          <Route path="/query" element={
            <MainLayout>
              <QueryPage />
            </MainLayout>
          } />
          
          {/* 用户中心 */}
          <Route path="/user-center" element={
            <MainLayout>
              <UserCenterPage />
            </MainLayout>
          } />

          {/* 404 页面 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthContextProvider>
  );
};

export default AppRoutes;