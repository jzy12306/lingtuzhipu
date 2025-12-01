import React, { useState } from 'react';

const LoginPage: React.FC = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // 清除对应字段的错误信息
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const newErrors: { [key: string]: string } = {};
    
    if (!formData.email.trim()) {
      newErrors.email = '邮箱不能为空';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '请输入有效的邮箱地址';
    }
    
    if (!formData.password) {
      newErrors.password = '密码不能为空';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        // 保存token到localStorage
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        // 跳转到首页
        window.location.href = '/';
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || '登录失败');
      }
    } catch (error) {
      setErrors({
        submit: error instanceof Error ? error.message : '登录失败，请稍后重试'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-800/50 backdrop-blur-md rounded-2xl shadow-2xl border border-slate-700/50 p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">登录</h1>
          <p className="text-slate-400">欢迎回到灵图智谱</p>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
              邮箱地址
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={`w-full px-4 py-3 rounded-lg bg-slate-700/50 border ${errors.email ? 'border-red-500' : 'border-slate-600'} text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all`}
              placeholder="输入邮箱地址"
              disabled={isSubmitting}
            />
            {errors.email && (
              <p className="text-red-400 text-sm mt-1">{errors.email}</p>
            )}
          </div>
          
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                密码
              </label>
              <a href="#" className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors">
                忘记密码？
              </a>
            </div>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={`w-full px-4 py-3 rounded-lg bg-slate-700/50 border ${errors.password ? 'border-red-500' : 'border-slate-600'} text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all`}
              placeholder="输入密码"
              disabled={isSubmitting}
            />
            {errors.password && (
              <p className="text-red-400 text-sm mt-1">{errors.password}</p>
            )}
          </div>
          
          {errors.submit && (
            <div className="bg-red-900/30 border border-red-500/50 text-red-400 rounded-lg p-4 mb-6">
              {errors.submit}
            </div>
          )}
          
          <button
            type="submit"
            className="w-full py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-semibold transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-800 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                登录中...
              </div>
            ) : (
              '登录'
            )}
          </button>
        </form>
        
        <div className="mt-8 text-center">
          <p className="text-slate-400">
            还没有账户？ <a href="/register" className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium">注册</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;