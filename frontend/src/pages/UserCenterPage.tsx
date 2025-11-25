import React, { useState } from 'react';
import { Layout, Menu, Card, Avatar, Badge, Button, Dropdown, Typography } from 'antd';
import { UserOutlined, KeyOutlined, MailOutlined, SecurityScanOutlined, UserSwitchOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const { Content } = Layout;
const { Title, Text } = Typography;

// 用户中心导航栏组件
const UserCenterNavBar: React.FC<{
  activeMenu: string;
  onMenuChange: (key: string) => void;
}> = ({ activeMenu, onMenuChange }) => {
  return (
    <div className="user-center-navbar bg-slate-800 p-4 rounded-lg mb-6">
      <Menu
        mode="horizontal"
        selectedKeys={[activeMenu]}
        onClick={(e) => onMenuChange(e.key)}
        className="bg-transparent border-b-0"
        style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '20px',
          backgroundColor: 'transparent',
          borderBottom: 'none'
        }}
        items={[
          {
            key: 'profile',
            icon: <UserOutlined className="text-cyan-400" />,
            label: '个人资料',
            className: 'text-slate-200 hover:text-white hover:bg-slate-700'
          },
          {
            key: 'users',
            icon: <UserSwitchOutlined className="text-cyan-400" />,
            label: '用户管理',
            className: 'text-slate-200 hover:text-white hover:bg-slate-700'
          },
          {
            key: 'security',
            icon: <SecurityScanOutlined className="text-cyan-400" />,
            label: '账户安全',
            className: 'text-slate-200 hover:text-white hover:bg-slate-700'
          },
          {
            key: 'notifications',
            icon: <MailOutlined className="text-cyan-400" />,
            label: '通知设置',
            className: 'text-slate-200 hover:text-white hover:bg-slate-700'
          }
        ]}
      />
    </div>
  );
};

// 用户管理组件（从用户提供的div转换而来）
const UserManagement: React.FC = () => {
  const [users, setUsers] = useState([
    {
      id: 1,
      name: '管理员',
      email: 'admin@example.com',
      avatar: 'resources/avatars/user1.jpg',
      status: 'online'
    },
    {
      id: 2,
      name: '张分析师',
      email: 'analyst@example.com',
      avatar: 'resources/avatars/user2.jpg',
      status: 'online'
    },
    {
      id: 3,
      name: '李工程师',
      email: 'engineer@example.com',
      avatar: 'resources/avatars/user3.png',
      status: 'offline'
    },
    {
      id: 4,
      name: '王研究员',
      email: 'researcher@example.com',
      avatar: 'resources/avatars/user4.jpeg',
      status: 'online'
    },
    {
      id: 5,
      name: '陈数据师',
      email: 'data@example.com',
      avatar: 'resources/avatars/user5.jpg',
      status: 'away'
    }
  ]);

  const handleAddUser = () => {
    // 添加用户逻辑
    console.log('添加用户');
  };

  const handleEditUser = (id: number) => {
    // 编辑用户逻辑
    console.log('编辑用户:', id);
  };

  const handleDeleteUser = (id: number) => {
    // 删除用户逻辑
    if (window.confirm('确定要删除此用户吗？')) {
      setUsers(users.filter(user => user.id !== id));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'offline':
        return 'bg-red-500';
      case 'away':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <Card title="用户管理" className="bg-slate-800 border-0 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <Title level={4} className="text-white m-0">用户列表</Title>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={handleAddUser}
          className="bg-cyan-500 hover:bg-cyan-600 border-0"
        >
          添加用户
        </Button>
      </div>
      <div className="space-y-3" id="user-list">
        {users.map(user => (
          <div key={user.id} className="flex items-center space-x-3 p-2 bg-slate-700/30 rounded-lg">
            <div className="relative">
              <Avatar src={user.avatar} alt={user.name} className="w-8 h-8 rounded-full object-cover" />
              <div className={`absolute -bottom-1 -right-1 w-3 h-3 ${getStatusColor(user.status)} rounded-full border-2 border-slate-800`}></div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm text-white truncate">{user.name}</p>
              <p className="text-xs text-slate-400 truncate">{user.email}</p>
            </div>
            <div className="flex items-center space-x-1">
              <Button 
                type="text" 
                icon={<EditOutlined />} 
                onClick={() => handleEditUser(user.id)}
                className="text-slate-400 hover:text-cyan-400 p-2"
              />
              <Button 
                type="text" 
                icon={<DeleteOutlined />} 
                onClick={() => handleDeleteUser(user.id)}
                className="text-slate-400 hover:text-red-400 p-2"
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

// 个人资料组件
const ProfileSection: React.FC = () => {
  return (
    <Card title="个人资料" className="bg-slate-800 border-0 shadow-lg">
      <div className="text-center mb-6">
        <Avatar size={100} src="resources/avatars/user1.jpg" className="mb-4" />
        <Title level={3} className="text-white m-0">管理员</Title>
        <Text className="text-slate-400">admin@example.com</Text>
      </div>
      <div className="space-y-4">
        <div className="bg-slate-700/30 p-4 rounded-lg">
          <Text className="text-slate-400 block mb-2">基本信息</Text>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Text className="text-slate-400 text-xs">用户名</Text>
              <Text className="text-white block">admin</Text>
            </div>
            <div>
              <Text className="text-slate-400 text-xs">注册时间</Text>
              <Text className="text-white block">2024-06-01</Text>
            </div>
          </div>
        </div>
        <Button 
          type="primary" 
          block 
          className="bg-cyan-500 hover:bg-cyan-600 border-0"
        >
          编辑资料
        </Button>
      </div>
    </Card>
  );
};

// 账户安全组件
const SecuritySection: React.FC = () => {
  return (
    <Card title="账户安全" className="bg-slate-800 border-0 shadow-lg">
      <div className="space-y-4">
        <div className="bg-slate-700/30 p-4 rounded-lg flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <KeyOutlined className="text-cyan-400" />
            <div>
              <Text className="text-white">密码修改</Text>
              <Text className="text-slate-400 text-xs block">上次修改时间：2024-06-15</Text>
            </div>
          </div>
          <Button 
            type="primary" 
            className="bg-cyan-500 hover:bg-cyan-600 border-0"
          >
            修改
          </Button>
        </div>
        <div className="bg-slate-700/30 p-4 rounded-lg flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <MailOutlined className="text-cyan-400" />
            <div>
              <Text className="text-white">邮箱验证</Text>
              <Text className="text-slate-400 text-xs block">当前状态：已验证</Text>
            </div>
          </div>
          <Button 
            className="bg-slate-600 hover:bg-slate-500 border-0"
          >
            查看
          </Button>
        </div>
      </div>
    </Card>
  );
};

// 通知设置组件
const NotificationsSection: React.FC = () => {
  return (
    <Card title="通知设置" className="bg-slate-800 border-0 shadow-lg">
      <div className="text-center py-8">
        <Text className="text-slate-400">通知设置功能即将上线</Text>
      </div>
    </Card>
  );
};

// 主页面组件
const UserCenterPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState('profile');

  const renderContent = () => {
    switch (activeSection) {
      case 'profile':
        return <ProfileSection />;
      case 'users':
        return <UserManagement />;
      case 'security':
        return <SecuritySection />;
      case 'notifications':
        return <NotificationsSection />;
      default:
        return <ProfileSection />;
    }
  };

  return (
    <Layout className="min-h-screen bg-slate-900">
      <Content className="p-6">
        <div className="max-w-4xl mx-auto">
          <Title level={2} className="text-white mb-6 text-center">用户中心</Title>
          
          {/* 用户中心导航栏 */}
          <UserCenterNavBar 
            activeMenu={activeSection} 
            onMenuChange={setActiveSection} 
          />
          
          {/* 内容区域 */}
          {renderContent()}
        </div>
      </Content>
    </Layout>
  );
};

export default UserCenterPage;
