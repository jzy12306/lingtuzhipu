// 前端配置文件

// API基础URL
export const API_BASE_URL = 'http://localhost:8000';

// 应用配置
export const APP_CONFIG = {
  // 应用名称
  APP_NAME: '灵图智谱',
  // 应用版本
  VERSION: '1.0.0',
  // 应用描述
  DESCRIPTION: '基于多智能体协作的垂直行业动态知识图谱构建与推理系统',
  
  // 主题配置
  THEME: {
    PRIMARY_COLOR: '#1890ff',
    SUCCESS_COLOR: '#52c41a',
    WARNING_COLOR: '#faad14',
    ERROR_COLOR: '#f5222d',
    
    // 暗色主题
    DARK_MODE: {
      PRIMARY_COLOR: '#177ddc',
      BACKGROUND_COLOR: '#141414',
    }
  },
  
  // 动画配置
  ANIMATION: {
    ENABLED: true,
    DURATION: 300,
  },
  
  // 性能配置
  PERFORMANCE: {
    // 知识图谱节点限制
    MAX_NODES: 1000,
    // 知识图谱边限制
    MAX_EDGES: 2000,
    // 批量操作限制
    BATCH_SIZE_LIMIT: 50,
  },
  
  // 文件上传配置
  FILE_UPLOAD: {
    MAX_SIZE: 50 * 1024 * 1024, // 50MB
    ALLOWED_EXTENSIONS: [
      '.txt', '.pdf', '.docx', '.md',
      '.csv', '.json', '.xml', '.xlsx'
    ],
    CHUNK_SIZE: 5 * 1024 * 1024, // 5MB
  },
  
  // 缓存配置
  CACHE: {
    TTL: 30 * 60 * 1000, // 30分钟
  },
  
  // 错误配置
  ERROR_CONFIG: {
    MAX_RETRY_COUNT: 3,
    RETRY_DELAY: 1000,
  },
  
  // 功能开关
  FEATURE_FLAGS: {
    ENABLE_LOCAL_LLM: true,
    ENABLE_REALTIME_COLLABORATION: false,
    ENABLE_ADVANCED_ANALYTICS: true,
  },
};

// 路由配置
export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  DOCUMENTS: '/documents',
  QUERY: '/query',
  GRAPH: '/graph',
  PROFILE: '/profile',
  SETTINGS: '/settings',
};

// API端点配置
export const API_ENDPOINTS = {
  // 认证相关
  AUTH: {
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    REFRESH: '/api/auth/refresh',
    ME: '/api/auth/me',
    REGISTER: '/api/auth/register',
    SEND_VERIFICATION_CODE: '/api/auth/send-verification-code',
  },
  
  // 文档管理相关
  DOCUMENTS: {
    LIST: '/api/documents',
    CREATE: '/api/documents',
    DETAIL: (id: string) => `/api/documents/${id}`,
    UPDATE: (id: string) => `/api/documents/${id}`,
    DELETE: (id: string) => `/api/documents/${id}`,
    PROCESS: (id: string) => `/api/documents/${id}/process`,
    BATCH_DELETE: '/api/documents/batch-delete',
    BATCH_PROCESS: '/api/documents/batch-process',
  },
  
  // 知识图谱相关
  KNOWLEDGE: {
    SEARCH: '/api/knowledge/search',
    NODE: (id: string) => `/api/knowledge/nodes/${id}`,
    RELATIONSHIP: (id: string) => `/api/knowledge/relationships/${id}`,
    STATS: '/api/knowledge/stats',
    EXPORT: '/api/knowledge/export',
  },
  
  // 分析师智能体相关
  ANALYST: {
    QUERY: '/api/analyst/query',
    EXECUTE_CODE: '/api/analyst/execute-code',
    SUGGESTIONS: '/api/analyst/suggestions',
    DASHBOARD: '/api/analyst/dashboard',
    FEATURES: '/api/analyst/features',
    HEALTH: '/api/analyst/health',
    BATCH_QUERY: '/api/analyst/batch/query',
  },
  
  // 系统状态
  STATUS: '/api/status',
};

// 存储键名
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_INFO: 'user_info',
  THEME: 'theme',
  LANGUAGE: 'language',
  PREFERENCES: 'user_preferences',
  RECENT_QUERIES: 'recent_queries',
  DRAFT_DOCUMENTS: 'draft_documents',
};

// 表单验证规则
export const VALIDATION_RULES = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
  USERNAME: /^[a-zA-Z0-9_]{3,30}$/,
  PHONE: /^1[3-9]\d{9}$/,
};

// 错误消息
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接失败，请检查您的网络设置',
  SERVER_ERROR: '服务器内部错误，请稍后重试',
  UNAUTHORIZED: '请先登录',
  FORBIDDEN: '您没有权限执行此操作',
  NOT_FOUND: '请求的资源不存在',
  BAD_REQUEST: '请求参数错误',
  FILE_TOO_LARGE: '文件大小超过限制',
  INVALID_FILE_TYPE: '不支持的文件类型',
  OPERATION_FAILED: '操作失败',
};

// 成功消息
export const SUCCESS_MESSAGES = {
  CREATED: '创建成功',
  UPDATED: '更新成功',
  DELETED: '删除成功',
  SAVED: '保存成功',
  PROCESSING: '处理中',
  COMPLETED: '操作完成',
  UPLOADED: '上传成功',
};

// 图标映射
export const ICON_MAPPINGS = {
  // 文档类型图标
  DOCUMENT_TYPES: {
    txt: 'file-text',
    pdf: 'file-pdf',
    docx: 'file-word',
    md: 'file-markdown',
    csv: 'file-excel',
    json: 'file-code',
    xml: 'file-code',
    xlsx: 'file-excel',
  },
  
  // 实体类型图标
  ENTITY_TYPES: {
    PERSON: 'user',
    ORGANIZATION: 'team',
    LOCATION: 'environment',
    EVENT: 'calendar',
    CONCEPT: 'bulb',
    PRODUCT: 'shopping-cart',
    DOCUMENT: 'file-text',
    KEYWORD: 'tags',
  },
};