import React, { useState } from 'react';
import { Card, Form, Input, Button, Checkbox, Typography, message, Spin, Divider } from 'antd';
import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { APP_CONFIG } from '../utils/config';
import backgroundImage from '../assets/background.jpg'; // 这里需要准备一张背景图片

const { Title, Paragraph } = Typography;

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  // 处理登录提交
  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      setLoading(true);
      
      // 调用登录API
      await login(values.username, values.password);
      
      message.success('登录成功');
      navigate('/dashboard');
    } catch (error: any) {
      console.error('登录失败:', error);
      
      // 解析错误信息
      let errorMessage = '登录失败，请重试';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 处理忘记密码
  const handleForgotPassword = () => {
    // 这里可以实现忘记密码的逻辑，或者显示提示信息
    message.info('忘记密码功能暂未实现');
  };

  // 处理注册
  const handleRegister = () => {
    // 这里可以实现注册的逻辑，或者显示提示信息
    message.info('注册功能暂未实现');
  };

  return (
    <div 
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        padding: '24px',
      }}
    >
      {/* 半透明遮罩，提升表单可读性 */}
      <div 
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(5px)',
          zIndex: 1,
        }}
      />
      
      {/* 登录表单卡片 */}
      <Card 
        style={{
          width: 400,
          maxWidth: '100%',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          borderRadius: 12,
          zIndex: 2,
          overflow: 'hidden',
        }}
      >
        {/* 登录头部 */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Title level={2} style={{ marginBottom: '8px' }}>
            {APP_CONFIG.APP_NAME}
          </Title>
          <Paragraph type="secondary">
            {APP_CONFIG.DESCRIPTION}
          </Paragraph>
        </div>
        
        {/* 登录表单 */}
        <Form
          form={form}
          name="login"
          initialValues={{ remember: true }}
          onFinish={handleLogin}
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { whitespace: true, message: '用户名不能包含空格' },
              { min: 3, message: '用户名长度至少为3个字符' },
              { max: 30, message: '用户名长度不能超过30个字符' },
            ]}
          >
            <Input
              prefix={<UserOutlined className="site-form-item-icon" />}
              placeholder="用户名"
              size="large"
              autoComplete="username"
            />
          </Form.Item>
          
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined className="site-form-item-icon" />}
              placeholder="密码"
              size="large"
              autoComplete="current-password"
            />
          </Form.Item>
          
          <Form.Item>
            <Form.Item name="remember" valuePropName="checked" noStyle>
              <Checkbox 
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              >
                记住我
              </Checkbox>
            </Form.Item>
            
            <a className="login-form-forgot" href="#" onClick={handleForgotPassword}>
              忘记密码?
            </a>
          </Form.Item>
          
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              className="login-form-button"
              size="large"
              style={{ width: '100%' }}
              loading={loading}
              disabled={loading}
            >
              {loading ? <Spin size="small" /> : '登录'}
            </Button>
          </Form.Item>
        </Form>
        
        <Divider style={{ margin: '16px 0' }} />
        
        {/* 其他操作 */}
        <div style={{ textAlign: 'center' }}>
          <Button 
            type="link" 
            onClick={handleRegister}
            style={{ width: '100%' }}
          >
            还没有账号? 立即注册
          </Button>
        </div>
        
        {/* 测试账号信息 */}
        <div 
          style={{
            marginTop: '16px',
            padding: '12px',
            backgroundColor: '#f0f2f5',
            borderRadius: 6,
            fontSize: '12px',
          }}
        >
          <p style={{ marginBottom: '4px', fontWeight: 'bold' }}>测试账号：</p>
          <p style={{ marginBottom: '4px' }}>用户名：admin</p>
          <p>密码：123456</p>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;