import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import axios from 'axios';
import { API_ENDPOINTS, STORAGE_KEYS } from '../utils/config';

// 用户类型定义
export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  created_at: string;
  last_login?: string;
  profile?: {
    avatar?: string;
    full_name?: string;
    phone?: string;
  };
}

// 认证上下文类型定义
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  checkPermission: (permission: string) => boolean;
}

// 创建上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 认证提供者属性类型
interface AuthProviderProps {
  children: ReactNode;
}

// 认证提供者组件
export const AuthContextProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化时检查用户登录状态
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
        if (!token) {
          setIsLoading(false);
          return;
        }

        // 尝试从本地存储获取用户信息
        const storedUser = localStorage.getItem(STORAGE_KEYS.USER_INFO);
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        }

        // 验证token并获取最新用户信息
        const response = await axios.get(API_ENDPOINTS.AUTH.ME);
        const userData = response.data;
        
        setUser(userData);
        localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(userData));
      } catch (error) {
        // Token无效或过期，清除本地存储
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.USER_INFO);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  // 登录方法
  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true);
      
      const response = await axios.post(API_ENDPOINTS.AUTH.LOGIN, {
        username,
        password
      });

      const { access_token, refresh_token, user: userData } = response.data;

      // 存储凭证和用户信息
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, access_token);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refresh_token);
      localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(userData));
      
      // 更新axios默认头
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // 设置用户状态
      setUser(userData);
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 登出方法
  const logout = async () => {
    try {
      setIsLoading(true);
      
      // 调用登出API
      await axios.post(API_ENDPOINTS.AUTH.LOGOUT);
    } catch (error) {
      console.error('登出API调用失败:', error);
    } finally {
      // 清除本地存储和状态
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.USER_INFO);
      
      // 清除axios默认头
      delete axios.defaults.headers.common['Authorization'];
      
      // 重置用户状态
      setUser(null);
      setIsLoading(false);
    }
  };

  // 更新用户资料
  const updateProfile = async (data: Partial<User>) => {
    if (!user) return;
    
    try {
      // 这里应该调用更新用户资料的API
      // const response = await axios.put(API_ENDPOINTS.USER.PROFILE, data);
      // const updatedUser = response.data;
      
      // 临时实现：本地更新
      const updatedUser = { ...user, ...data };
      setUser(updatedUser);
      localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(updatedUser));
    } catch (error) {
      throw error;
    }
  };

  // 检查权限
  const checkPermission = (permission: string): boolean => {
    if (!user) return false;
    
    // 管理员拥有所有权限
    if (user.role === 'admin') return true;
    
    // 检查用户是否有特定权限
    return user.permissions?.includes(permission) || false;
  };

  // 上下文值
  const contextValue: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    updateProfile,
    checkPermission
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// 自定义钩子，用于在组件中访问认证上下文
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthContextProvider');
  }
  
  return context;
};

// 权限检查装饰器
interface PermissionGuardProps {
  permission: string;
  fallback?: ReactNode;
  children: ReactNode;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  permission,
  fallback = null,
  children
}) => {
  const { user, isLoading, checkPermission } = useAuth();
  
  if (isLoading) {
    return null; // 或者返回加载指示器
  }
  
  const hasPermission = checkPermission(permission);
  
  return hasPermission ? <>{children}</> : fallback;
};

// 角色检查装饰器
interface RoleGuardProps {
  roles: string[];
  fallback?: ReactNode;
  children: ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({
  roles,
  fallback = null,
  children
}) => {
  const { user, isLoading } = useAuth();
  
  if (isLoading) {
    return null; // 或者返回加载指示器
  }
  
  const hasRole = user && roles.includes(user.role);
  
  return hasRole ? <>{children}</> : fallback;
};