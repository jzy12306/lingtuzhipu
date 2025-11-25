import React, { useState } from 'react';
import { Layout, Menu, Typography, Divider } from 'antd';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  HomeOutlined,
  FileTextOutlined,
  SearchOutlined,
  DatabaseOutlined,
  UserOutlined,
  SettingOutlined,
  BarChartOutlined,
  FolderOutlined,
  CodeOutlined,
  CompassOutlined,
  MessageOutlined,
  UserSwitchOutlined
} from '@ant-design/icons';
import { useAuth } from '../context/AuthContext';
import { ROUTES } from '../utils/config';
import type { MenuProps } from 'antd';

const { Sider } = Layout;
const { Text } = Typography;

interface SidebarProps {
  collapsed: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const [currentActiveKey, setCurrentActiveKey] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  // 监听路由变化，更新当前激活的菜单项
  React.useEffect(() => {
    const pathname = location.pathname;
    
    // 根据当前路径设置激活的菜单项
    let activeKey = '';
    if (pathname === ROUTES.DASHBOARD) activeKey = 'dashboard';
    else if (pathname === ROUTES.DOCUMENTS) activeKey = 'documents';
    else if (pathname === ROUTES.QUERY) activeKey = 'query';
    else if (pathname === ROUTES.GRAPH) activeKey = 'graph';
    else if (pathname === ROUTES.PROFILE) activeKey = 'profile';
    else if (pathname === ROUTES.SETTINGS) activeKey = 'settings';
    else if (pathname === '/user-center') activeKey = 'user-center';
    
    setCurrentActiveKey(activeKey);
  }, [location.pathname]);

  // 菜单项配置
  const menuItems: MenuProps['items'] = [
    // 主要功能区域
    {
      label: '首页',
      key: 'dashboard',
      icon: <HomeOutlined />,
      onClick: () => navigate(ROUTES.DASHBOARD),
    },
    {
      label: '文档管理',
      key: 'documents',
      icon: <FileTextOutlined />,
      onClick: () => navigate(ROUTES.DOCUMENTS),
    },
    {
      label: '查询分析',
      key: 'query',
      icon: <SearchOutlined />,
      onClick: () => navigate(ROUTES.QUERY),
    },
    {
      label: '知识图谱',
      key: 'graph',
      icon: <DatabaseOutlined />,
      onClick: () => navigate(ROUTES.GRAPH),
      children: [
        {
          label: '图谱可视化',
          key: 'graph-visualization',
          onClick: () => navigate(`${ROUTES.GRAPH}?view=visualization`),
        },
        {
          label: '实体关系',
          key: 'graph-entities',
          onClick: () => navigate(`${ROUTES.GRAPH}?view=entities`),
        },
        {
          label: '图谱分析',
          key: 'graph-analysis',
          onClick: () => navigate(`${ROUTES.GRAPH}?view=analysis`),
        },
      ],
    },
    
    <Divider style={{ margin: '8px 0' }} key="divider1" />,
    
    // 智能体功能区域
    {
      label: '智能体服务',
      key: 'agents',
      icon: <MessageOutlined />,
      children: [
        {
          label: '构建者智能体',
          key: 'builder-agent',
          icon: <FolderOutlined />,
          onClick: () => navigate(`${ROUTES.DOCUMENTS}?tab=builder`),
        },
        {
          label: '分析师智能体',
          key: 'analyst-agent',
          icon: <BarChartOutlined />,
          onClick: () => navigate(`${ROUTES.QUERY}?tab=analyst`),
        },
        {
          label: '代码解释器',
          key: 'code-interpreter',
          icon: <CodeOutlined />,
          onClick: () => navigate(`${ROUTES.QUERY}?tab=code`),
        },
      ],
    },
    
    <Divider style={{ margin: '8px 0' }} key="divider2" />,
    
    // 个人和设置区域
    {
      label: '用户中心',
      key: 'user-center',
      icon: <UserSwitchOutlined />,
      onClick: () => navigate('/user-center'),
    },
    {
      label: '个人资料',
      key: 'profile',
      icon: <UserOutlined />,
      onClick: () => navigate(ROUTES.PROFILE),
    },
    {
      label: '系统设置',
      key: 'settings',
      icon: <SettingOutlined />,
      onClick: () => navigate(ROUTES.SETTINGS),
    },
  ];

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      collapsedWidth={80}
      width={256}
      theme="light"
      style={{
        height: '100vh',
        position: 'sticky',
        top: 0,
        overflow: 'auto',
      }}
    >
      {/* 侧边栏标题 */}
      <div style={{
        height: '64px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderBottom: '1px solid #f0f0f0',
      }}>
        {!collapsed && (
          <CompassOutlined style={{ fontSize: '24px', color: '#1890ff', marginRight: '8px' }} />
        )}
        {!collapsed && (
          <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
            灵图智谱
          </Text>
        )}
        {collapsed && (
          <CompassOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
        )}
      </div>
      
      {/* 菜单项 */}
      <Menu
        mode="inline"
        items={menuItems}
        selectedKeys={[currentActiveKey]}
        style={{
          height: '100%',
          borderRight: 0,
        }}
        // 设置子菜单展开/折叠的动画
        expandIconPosition="end"
        // 点击菜单项时自动折叠
        onClickMenuItem={() => {
          // 可以根据需要添加额外的处理逻辑
        }}
      />
      
      {/* 用户信息提示（可选） */}
      {!collapsed && (
        <div style={{
          padding: '16px',
          borderTop: '1px solid #f0f0f0',
          textAlign: 'center',
        }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            当前用户: {user?.username || '未知'}
          </Text>
        </div>
      )}
    </Sider>
  );
};

export default Sidebar;