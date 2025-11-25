import React, { useState } from 'react';
import { Card, Form, Input, Button, Typography, message, Spin, Divider } from 'antd';
import { LockOutlined, UserOutlined, MailOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { APP_CONFIG } from '../utils/config';

const { Title, Paragraph } = Typography;

const RegisterPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0); // 验证码倒计时
  const navigate = useNavigate();
  const [form] = Form.useForm();

  // 发送验证码
  const handleSendVerificationCode = async () => {
    try {
      const email = form.getFieldValue('email');
      if (!email) {
        message.error('请输入邮箱地址');
        return;
      }

      // 这里应该调用发送验证码的API
      // await axios.post('/api/auth/send-verification-code', { email });
      
      // 设置倒计时（60秒）
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      
      message.success('验证码已发送至您的邮箱');
    } catch (error: any) {
      console.error('发送验证码失败:', error);
      let errorMessage = '发送验证码失败，请重试';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      message.error(errorMessage);
    }
  };

  // 处理注册提交
  const handleRegister = async (values: { username: string; email: string; password: string; verificationCode: string }) => {
    try {
      setLoading(true);
      
      // 这里应该调用注册API
      // await axios.post('/api/auth/register', {
      //   username: values.username,
      //   email: values.email,
      //   password: values.password,
      //   verification_code: values.verificationCode
      // });
      
      message.success('注册成功');
      navigate('/login');
    } catch (error: any) {
      console.error('注册失败:', error);
      
      // 解析错误信息
      let errorMessage = '注册失败，请重试';
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

  // 处理返回登录
  const handleBackToLogin = () => {
    navigate('/login');
  };

  return (
    <div 
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '24px',
      }}
    >
      {/* 注册表单卡片 */}
      <Card 
        style={{
          width: 450,
          maxWidth: '100%',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          borderRadius: 12,
          zIndex: 2,
          overflow: 'hidden',
        }}
      >
        {/* 注册头部 */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Title level={2} style={{ marginBottom: '8px' }}>
            注册 {APP_CONFIG.APP_NAME}
          </Title>
          <Paragraph type="secondary">
            创建您的账户以开始使用系统
          </Paragraph>
        </div>
        
        {/* 注册表单 */}
        <Form
          form={form}
          name="register"
          onFinish={handleRegister}
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
            name="email"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input
              prefix={<MailOutlined className="site-form-item-icon" />}
              placeholder="邮箱地址"
              size="large"
              autoComplete="email"
            />
          </Form.Item>
          
          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 8, message: '密码长度至少为8个字符' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined className="site-form-item-icon" />}
              placeholder="密码"
              size="large"
              autoComplete="new-password"
            />
          </Form.Item>
          
          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined className="site-form-item-icon" />}
              placeholder="确认密码"
              size="large"
              autoComplete="new-password"
            />
          </Form.Item>
          
          <Form.Item>
            <div style={{ display: 'flex', gap: '12px' }}>
              <Form.Item
                name="verificationCode"
                noStyle
                rules={[{ required: true, message: '请输入验证码' }]}
              >
                <Input
                  placeholder="验证码"
                  size="large"
                  style={{ flex: 1 }}
                />
              </Form.Item>
              
              <Button
                onClick={handleSendVerificationCode}
                disabled={countdown > 0}
                size="large"
              >
                {countdown > 0 ? `${countdown}秒后重发` : '发送验证码'}
              </Button>
            </div>
          </Form.Item>
          
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              style={{ width: '100%' }}
              loading={loading}
              disabled={loading}
            >
              {loading ? <Spin size="small" /> : '注册'}
            </Button>
          </Form.Item>
        </Form>
        
        <Divider style={{ margin: '16px 0' }} />
        
        {/* 其他操作 */}
        <div style={{ textAlign: 'center' }}>
          <Button 
            type="link" 
            onClick={handleBackToLogin}
            style={{ width: '100%' }}
          >
            已有账号? 立即登录
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default RegisterPage;