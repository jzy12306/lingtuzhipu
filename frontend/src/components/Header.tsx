import React, { useState } from 'react';
import { Layout, Button, Avatar, Dropdown, Space, Badge, Switch, Typography } from 'antd';
import { MenuOutlined, LogoutOutlined, SettingOutlined, UserOutlined, BellOutlined, SearchOutlined, MoonOutlined, SunOutlined } from '@ant-design/icons';
import { useAuth } from '../context/AuthContext';
import { APP_CONFIG } from '../utils/config';
import { useNavigate } from 'react-router-dom';

const { Header: AntHeader } = Layout;
const { Title } = Typography;

interface HeaderProps {
  collapsed: boolean;
  onToggle: () => void;
}

const Header: React.FC<HeaderProps> = ({ collapsed, onToggle }) => {
  const [darkMode, setDarkMode] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [notificationCount] = useState(3); // 模拟通知数量

  // 用户菜单
  const userMenuItems = [
    {
      key: 'profile',
      label: '个人资料',
      icon: <UserOutlined />,
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      label: '设置',
      icon: <SettingOutlined />,
      onClick: () => navigate('/settings'),
    },
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      danger: true,
      onClick: async () => {
        try {
          await logout();
          navigate('/login');
        } catch (error) {
          console.error('退出登录失败:', error);
        }
      },
    },
  ];

  // 切换暗黑模式
  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    // 这里可以实现暗黑模式的切换逻辑
    document.body.classList.toggle('dark-theme');
    // 保存到本地存储
    localStorage.setItem('theme', darkMode ? 'light' : 'dark');
  };

  return (
    <AntHeader
      className="site-layout-background"
      style={{
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.09)',
        zIndex: 1000,
      }}
    >
      {/* 左侧：菜单切换按钮和标题 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <Button
          type="text"
          icon={<MenuOutlined />}
          onClick={onToggle}
          style={{
            fontSize: '16px',
            width: 64,
            height: 64,
            padding: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        />
        <Title level={3} style={{ margin: 0, color: APP_CONFIG.THEME.PRIMARY_COLOR }}>
          {APP_CONFIG.APP_NAME}
        </Title>
      </div>

      {/* 右侧：搜索、通知、暗黑模式切换和用户信息 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* 搜索按钮 - 可以展开搜索框 */}
        <Button
          type="text"
          icon={<SearchOutlined />}
          style={{ fontSize: '18px' }}
          title="搜索"
        />

        {/* 通知图标 */}
        <Dropdown
          menu={{
            items: [
              {
                label: '有新的文档已处理完成',
                key: '1',
              },
              {
                label: '系统更新提醒',
                key: '2',
              },
              {
                label: '查询任务已完成',
                key: '3',
              },
            ],
          }}
          placement="bottomRight"
        >
          <Badge count={notificationCount} showZero>
            <Button
              type="text"
              icon={<BellOutlined />}
              style={{ fontSize: '18px' }}
              title="通知"
            />
          </Badge>
        </Dropdown>

        {/* 暗黑模式切换 */}
        <Space>
          {darkMode ? (
            <SunOutlined style={{ fontSize: '16px', marginRight: '-8px' }} />
          ) : (
            <MoonOutlined style={{ fontSize: '16px', marginRight: '-8px' }} />
          )}
          <Switch
            checked={darkMode}
            onChange={toggleDarkMode}
            size="small"
            title={darkMode ? '切换到亮色模式' : '切换到暗色模式'}
          />
        </Space>

        {/* 用户信息 */}
        <Dropdown
          menu={{
            items: userMenuItems,
          }}
          placement="bottomRight"
        >
          <Space style={{ cursor: 'pointer' }}>
            <Avatar
              src={user?.profile?.avatar || undefined}
              icon={<UserOutlined />}
              size="large"
            />
            <span style={{ fontSize: '14px' }}>
              {user?.profile?.full_name || user?.username || '未登录'}
            </span>
          </Space>
        </Dropdown>
      </div>
    </AntHeader>
  );
};

export default Header;