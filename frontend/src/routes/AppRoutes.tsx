import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import type { FC } from 'react';

// 导入页面组件
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import HomePage from '../pages/HomePage';
import DocumentManagementPage from '../pages/DocumentManagementPage';
import GraphVisualizationPage from '../pages/GraphVisualizationPage';
import QueryPage from '../pages/QueryPage';
import ProfilePage from '../pages/ProfilePage';

// 导入布局组件
import Header from '../components/layout/Header';
import Sidebar from '../components/layout/Sidebar';
import Footer from '../components/layout/Footer';

// 导入认证组件
import ProtectedRoute from '../components/auth/ProtectedRoute';
import { useAuthContext } from '../context/AuthContext';

const { Content } = Layout;

// 主布局组件
const MainLayout: FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = React.useState(false);

  const toggleCollapsed = () => {
    setCollapsed(!collapsed);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header />
      <Layout hasSider>
        <Sidebar collapsed={collapsed} onCollapse={toggleCollapsed} />
        <Layout>
          <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', minHeight: 280 }}>
            {children}
          </Content>
          <Footer />
        </Layout>
      </Layout>
    </Layout>
  );
};

// 公共布局 - 无侧边栏和页脚
const PublicLayout: FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header showLogoOnly />
      <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', minHeight: 280 }}>
        {children}
      </Content>
    </Layout>
  );
};

// 主路由配置
const AppRoutes: FC = () => {
  const { isLoading } = useAuthContext();

  if (isLoading) {
    // 可以在这里添加一个加载动画
    return (
      <Layout style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div>正在加载...</div>
      </Layout>
    );
  }

  return (
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
        <Route element={<ProtectedRoute />}>
          {/* 首页 */}
          <Route path="/" element={
            <MainLayout>
              <HomePage />
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
          
          {/* 用户个人资料 */}
          <Route path="/profile" element={
            <MainLayout>
              <ProfilePage />
            </MainLayout>
          } />
        </Route>

        {/* 404 页面 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default AppRoutes;