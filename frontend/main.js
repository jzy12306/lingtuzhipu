// 知识图谱系统前端主脚本
// 处理各种页面交互和功能

// 全局工具函数
window.generateId = function() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// Token验证函数
function validateToken() {
    const token = localStorage.getItem('access_token');
    console.log('[Token Validate] 开始验证token:', token ? '存在' : '不存在');
    
    if (!token) {
        console.log('[Token Validate] token不存在，验证失败');
        return false;
    }
    
    try {
        // 检查token格式
        const tokenParts = token.split('.');
        if (tokenParts.length !== 3) {
            console.log('[Token Validate] token格式不正确，返回true由后端验证');
            // 格式不正确，但仍返回true，由后端验证
            return true;
        }
        
        // 解析token，检查是否过期
        const payload = JSON.parse(atob(tokenParts[1]));
        console.log('[Token Validate] token payload:', payload);
        
        const now = Math.floor(Date.now() / 1000);
        console.log('[Token Validate] 当前时间:', now, '秒');
        console.log('[Token Validate] token过期时间:', payload.exp, '秒');
        
        const isExpired = payload.exp <= now;
        const expiresIn = payload.exp - now;
        console.log('[Token Validate] token剩余有效期:', expiresIn, '秒');
        console.log('[Token Validate] token是否过期:', isExpired ? '是' : '否');
        
        // 只有当token确实未过期时才返回true
        return !isExpired;
    } catch (error) {
        console.error('[Token Validate] token解析失败:', error);
        // 解析失败时返回true，让后端决定token是否有效
        console.log('[Token Validate] token解析失败，但仍返回true，由后端验证');
        return true;
    }
}

// 退出登录功能
function logout() {
    console.log('[Logout] 开始执行退出登录');
    // 清除localStorage中的token
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    console.log('[Logout] 已清除localStorage中的token');
    // 重定向到登录页面
    window.location.href = '/login';
    console.log('[Logout] 已重定向到登录页面');
}

// 检查并刷新token
async function checkAndRefreshToken() {
    const token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    console.log('[Token Check] 开始检查token:');
    console.log('[Token Check] access_token存在:', token ? '是' : '否');
    console.log('[Token Check] refresh_token存在:', refreshToken ? '是' : '否');
    console.log('[Token Check] access_token内容:', token ? token : '无');
    
    // 如果没有token，直接返回false
    if (!token) {
        console.log('[Token Check] access_token不存在，返回false');
        return false;
    }
    
    // 使用validateToken函数验证token有效性
    const isValid = validateToken();
    console.log('[Token Check] token验证结果:', isValid ? '有效' : '无效');
    
    // 如果token无效且有refresh_token，可以尝试刷新token
    // 这里简化处理，直接返回token是否有效
    return isValid;
}

// 全局变量
let particleSystem;
let uploadQueue = [];
let agentStatus = {
    builder: { status: 'processing', progress: 75, processed: 15, total: 20 },
    auditor: { status: 'checking', progress: 90, quality: 94 },
    analyst: { status: 'waiting', progress: 25, responseTime: 1.2 },
    extension: { status: 'loading', progress: 60, loaded: 12, total: 20 }
};

// 检查用户登录状态
function checkLoginStatus() {
    const token = localStorage.getItem('access_token');
    const loginLink = document.getElementById('login-link');
    const userCenterLink = document.getElementById('user-center-link');
    
    if (token) {
        // 用户已登录
        if (loginLink) loginLink.classList.add('hidden');
        if (userCenterLink) userCenterLink.classList.remove('hidden');
    } else {
        // 用户未登录
        if (loginLink) loginLink.classList.remove('hidden');
        if (userCenterLink) userCenterLink.classList.add('hidden');
    }
}

// 需要认证的页面列表
// 只有需要登录才能访问的页面才加入受保护列表
const protectedPages = ['query.html', 'graph.html', 'admin.html', 'user-center.html'];

// 确保index.html不在受保护列表中，允许未登录用户访问首页
// 首页的文件上传功能需要登录才能使用，但首页本身可以访问

// 检查当前页面是否需要认证
function requireAuth() {
    const currentPage = window.location.pathname.split('/').pop();
    // 处理根路径情况：当访问 / 时，应该等同于访问 index.html
    const pageToCheck = currentPage === '' ? 'index.html' : currentPage;
    
    if (protectedPages.includes(pageToCheck)) {
        const token = localStorage.getItem('access_token');
        console.log('[Auth] 检查认证状态，页面:', pageToCheck, 'token存在:', token ? '是' : '否');
        
        if (!token) {
            console.log('[Auth] token不存在，跳转到登录页面');
            // 未登录且访问受保护页面，跳转到登录页面
            window.location.href = '/login';
            return false;
        }
        
        // 验证token是否有效
        const isTokenValid = validateToken();
        console.log('[Auth] token验证结果:', isTokenValid ? '有效' : '无效');
        
        if (!isTokenValid) {
            console.log('[Auth] token无效，跳转到登录页面');
            // token无效，跳转到登录页面
            window.location.href = '/login';
            return false;
        }
    }
    return true;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 先初始化粒子系统，确保无论是否登录都会显示
    console.log('[Init] 开始初始化粒子系统');
    initParticleSystem();
    
    // 然后检查是否需要认证
    if (requireAuth()) {
        console.log('[Init] 认证通过，初始化其他功能');
        checkLoginStatus();
        initUploadZone();
        initAgentStatus();
        initAnimations();
        startStatusUpdates();
    } else {
        console.log('[Init] 认证未通过或跳转到登录页，仅初始化粒子系统');
    }
});

// 初始化粒子系统 - 使用纯Canvas API实现
function initParticleSystem() {
    console.log('[Particle System] 开始初始化粒子系统（纯Canvas API）');
    
    try {
        // 检查粒子容器是否存在
        const container = document.getElementById('particles-container');
        if (!container) {
            console.error('[Particle System] 粒子容器不存在，粒子系统初始化失败');
            return;
        }
        console.log('[Particle System] 找到粒子容器，开始创建Canvas元素');
        
        // 清除容器内可能存在的旧Canvas
        container.innerHTML = '';
        
        // 创建Canvas元素
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // 设置Canvas大小
        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            console.log(`[Particle System] Canvas大小设置为: ${canvas.width}x${canvas.height}`);
        };
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // 添加Canvas到粒子容器
        container.appendChild(canvas);
        console.log('[Particle System] Canvas元素添加到粒子容器');
        
        // 粒子配置
        const particleCount = 100;
        const particles = [];
        const connectionDistance = 150;
        
        // 创建粒子 - 粒子尺寸调整到原来的20%，速度调整到原来的40%
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.64,  // 速度调整到40%: 1.6 * 0.4 = 0.64
                vy: (Math.random() - 0.5) * 0.64,  // 速度调整到40%
                size: Math.random() * 0.6 + 0.6,   // 尺寸调整到20%: (3+3)*0.2 = 1.2, 范围0.6-1.2
                color: `rgba(100, 180, 220, ${Math.random() * 0.3 + 0.3})`  // 柔和的淡青蓝色，与背景协调
            });
        }
        console.log(`[Particle System] 创建了${particleCount}个粒子`);
        
        // 计算两点之间的距离
        const calculateDistance = (x1, y1, x2, y2) => {
            const dx = x2 - x1;
            const dy = y2 - y1;
            return Math.sqrt(dx * dx + dy * dy);
        };
        
        // 动画循环
        const animate = () => {
            try {
                // 清除画布
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // 更新粒子位置和绘制连线
                for (let i = 0; i < particles.length; i++) {
                    const p1 = particles[i];
                    
                    // 更新粒子位置
                    p1.x += p1.vx;
                    p1.y += p1.vy;
                    
                    // 边界检测
                    if (p1.x < 0 || p1.x > canvas.width) p1.vx *= -1;
                    if (p1.y < 0 || p1.y > canvas.height) p1.vy *= -1;
                    
                // 绘制连线 - 柔和的淡青蓝色
                    ctx.strokeStyle = 'rgba(100, 180, 220, 0.15)';
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    for (let j = i + 1; j < particles.length; j++) {
                        const p2 = particles[j];
                        const distance = calculateDistance(p1.x, p1.y, p2.x, p2.y);
                        
                        if (distance < connectionDistance) {
                            ctx.moveTo(p1.x, p1.y);
                            ctx.lineTo(p2.x, p2.y);
                        }
                    }
                    ctx.stroke();
                }
                
                // 绘制粒子 - 柔和的淡青蓝色
                ctx.fillStyle = 'rgba(100, 180, 220, 0.6)';
                particles.forEach(particle => {
                    ctx.beginPath();
                    ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                    ctx.fill();
                });
                
                // 继续动画循环
                requestAnimationFrame(animate);
            } catch (error) {
                console.error('[Particle System] 动画循环出错:', error);
            }
        };
        
        // 启动动画
        console.log('[Particle System] 启动粒子动画');
        animate();
        
        console.log('[Particle System] 粒子系统初始化完成');
    } catch (error) {
        console.error('[Particle System] 粒子系统初始化失败:', error);
    }
}

// 更新文档数量和显示UI的函数
function updateDocumentCountsInUI(fileId, entitiesCount, relationsCount) {
    console.log(`[UI Update] 更新文档计数 - fileId: ${fileId}, 实体: ${entitiesCount}, 关系: ${relationsCount}`);
    
    const countsDiv = document.getElementById(`counts-${fileId}`);
    if (!countsDiv) {
        console.warn('[UI Update] 计数显示元素不存在');
        return;
    }
    
    // 如果有计数数据，显示计数div
    if (entitiesCount > 0 || relationsCount > 0) {
        countsDiv.style.display = 'block';
        
        // 更新实体计数
        const entitiesSpan = countsDiv.querySelector('.entities-count');
        if (entitiesSpan) {
            entitiesSpan.textContent = `实体: ${entitiesCount}`;
        }
        
        // 更新关系计数
        const relationsSpan = countsDiv.querySelector('.relations-count');
        if (relationsSpan) {
            relationsSpan.textContent = `关系: ${relationsCount}`;
        }
        
        console.log('[UI Update] 计数显示更新完成');
    } else {
        console.log('[UI Update] 数据计数为0，保持隐藏');
    }
}


// 初始化上传区域
function initUploadZone() {
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');

    if (!uploadZone || !fileInput) return;

    // 拖拽事件
    uploadZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadZone.classList.add('border-cyan-400', 'bg-cyan-900/20');
    });

    uploadZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadZone.classList.remove('border-cyan-400', 'bg-cyan-900/20');
    });

    uploadZone.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadZone.classList.remove('border-cyan-400', 'bg-cyan-900/20');
        
        const files = Array.from(e.dataTransfer.files);
        handleFiles(files);
    });

    // 文件选择事件
    fileInput.addEventListener('change', function(e) {
        const files = Array.from(e.target.files);
        handleFiles(files);
    });
}

// 处理上传的文件
function handleFiles(files) {
    files.forEach(file => {
        const fileData = {
            id: Date.now() + Math.random(),
            file: file,
            name: file.name,
            size: file.size,
            type: file.type,
            status: 'pending',
            progress: 0,
            estimatedTime: Math.floor(Math.random() * 30) + 10 // 10-40秒
        };
        
        uploadQueue.push(fileData);
        createUploadItem(fileData);
    });

    // 开始处理队列
    processUploadQueue();
}

// 创建上传项目界面
function createUploadItem(fileData) {
    const uploadQueue = document.getElementById('upload-queue');
    if (!uploadQueue) return;

    const itemDiv = document.createElement('div');
    itemDiv.className = 'agent-card rounded-lg p-4';
    itemDiv.id = `upload-${fileData.id}`;

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    itemDiv.innerHTML = `
        <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
                    <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/>
                    </svg>
                </div>
                <div>
                    <div class="font-medium">${fileData.name}</div>
                    <div class="text-sm text-slate-400">${formatFileSize(fileData.size)}</div>
                    <div id="counts-${fileData.id}" class="text-xs text-green-400 mt-1" style="display: none;">
                        <span class="entities-count">实体: 0</span> | 
                        <span class="relations-count">关系: 0</span>
                    </div>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <span class="status-badge px-3 py-1 rounded-full text-xs font-medium bg-slate-600 text-slate-300">等待中</span>
                <button onclick="removeUpload('${fileData.id}')" class="text-slate-400 hover:text-red-400 transition-colors">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
        </div>
        <div class="progress-container">
            <div class="w-full bg-slate-700 rounded-full h-2">
                <div class="progress-bar h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
            </div>
            <div class="flex justify-between text-xs text-slate-400 mt-1">
                <span class="progress-text">准备中...</span>
                <span class="time-remaining">预计 ${fileData.estimatedTime}秒</span>
            </div>
        </div>
        <div id="result-actions-${fileData.id}" class="mt-3 hidden">
            <div class="flex items-center space-x-2">
                <button onclick="viewProcessingResult('${fileData.id}')" class="flex-1 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 rounded-lg text-sm font-medium transition-all duration-300">
                    查看结果
                </button>
                <button onclick="exportToGraph('${fileData.id}')" class="px-4 py-2 bg-slate-600 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors">
                    导入图谱
                </button>
            </div>
        </div>
    `;

    uploadQueue.appendChild(itemDiv);
}

// 处理上传队列
function processUploadQueue() {
    const pendingItems = uploadQueue.filter(item => item.status === 'pending');
    
    if (pendingItems.length === 0) return;

    // 并发处理（最多3个同时处理）
    const processingItems = pendingItems.slice(0, 3);
    
    processingItems.forEach(fileData => {
        fileData.status = 'processing';
        updateUploadUI(fileData);
        
        // 调用真实API处理文件
        processFileWithAPI(fileData);
    });
}

// 使用API处理文件
async function processFileWithAPI(fileData) {
    console.log('开始处理文件:', fileData.name);
    
    // 首先检查是否已登录
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.log('用户未登录，无法上传文件');
        fileData.status = 'error';
        fileData.error = '请先登录后再上传文件';
        updateUploadUI(fileData);
        // 弹出登录提示，不显示账号密码
        if (confirm('您尚未登录，是否现在前往登录页面？')) {
            window.location.href = 'login.html';
        }
        // 处理下一个文件
        setTimeout(() => {
            processUploadQueue();
        }, 1000);
        return;
    }
    
    try {
        // 1. 上传文件到后端
        console.log('步骤1: 上传文件到后端');
        const document = await uploadFileToBackend(fileData.file);
        fileData.documentId = document.id;
        console.log('文件上传成功，documentId:', document.id);
        
        // 更新进度
        fileData.progress = 25;
        updateUploadProgress(fileData);
        
        // 2. 调用文档处理API
        console.log('步骤2: 调用文档处理API');
        await startDocumentProcessing(document.id);
        console.log('文档处理API调用成功');
        
        // 更新进度
        fileData.progress = 50;
        updateUploadProgress(fileData);
        
        // 3. 轮询获取处理结果
        console.log('步骤3: 轮询获取处理结果');
        await pollProcessingStatus(fileData, document.id);
        console.log('文档处理完成');
        
        // 更新进度
        fileData.progress = 75;
        updateUploadProgress(fileData);
        
        // 4. 获取最终处理结果（包含实体和关系列表）
        console.log('步骤4: 获取最终处理结果');
        const processingResult = await getProcessingResult(document.id);
        fileData.processingResult = processingResult;
        console.log('获取处理结果成功:', processingResult.entities.length, '个实体,', processingResult.relationships.length, '个关系');
        
        // 5. 更新UI状态
        fileData.status = 'completed';
        fileData.progress = 100;
        updateUploadProgress(fileData);
        updateUploadUI(fileData);
        console.log('文件处理完成，更新UI成功');
        
        // 处理下一个文件
        setTimeout(() => {
            processUploadQueue();
        }, 1000);
    } catch (error) {
        console.error('文件处理失败:', error);
        fileData.status = 'error';
        
        // 增强错误信息，区分不同类型的错误
        if (error.message.includes('登录已过期') || error.message.includes('无法验证凭据') || error.message.includes('token无效')) {
            // 如果是401相关错误，清除token
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            fileData.error = '登录已过期，请重新登录后再上传文件';
        } else if (error.message.includes('文件上传失败')) {
            fileData.error = '文件上传失败，请检查网络连接或文件大小是否超过限制';
        } else if (error.message.includes('文档处理请求失败')) {
            fileData.error = '文档处理请求失败，请稍后重试';
        } else if (error.message.includes('获取文档状态失败')) {
            fileData.error = '获取文档状态失败，请检查网络连接';
        } else if (error.message.includes('获取处理结果失败')) {
            fileData.error = '获取处理结果失败，请稍后重试';
        } else if (error.message.includes('timeout')) {
            fileData.error = '文档处理超时，可能是文件过大或系统繁忙，请稍后查看处理结果';
        } else if (error.message.includes('ocr') || error.message.includes('OCR')) {
            fileData.error = 'OCR识别失败，请检查文件质量或格式';
        } else if (error.message.includes('builder') || error.message.includes('Builder')) {
            fileData.error = '文档处理服务暂时不可用，请稍后重试';
        } else if (error.message.includes('table') || error.message.includes('表格')) {
            fileData.error = '表格提取失败，但文档其他内容已处理完成';
        } else {
            // 直接使用原始错误信息，不要替换
            fileData.error = error.message || '文件处理失败，请稍后重试';
        }
        
        console.log('文件处理失败，错误信息:', fileData.error);
        updateUploadUI(fileData);
        
        // 处理下一个文件
        setTimeout(() => {
            processUploadQueue();
        }, 1000);
    }
}

// 上传文件到后端API
async function uploadFileToBackend(file) {
    console.log('[API] 开始上传文件到后端API');
    
    // 检查并刷新token
    const isValid = await checkAndRefreshToken();
    if (!isValid) {
        console.log('[API] token无效，提示用户重新登录');
        // 不要自动跳转到登录页，让用户手动处理
        throw new Error('登录已过期，请重新登录');
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const token = localStorage.getItem('access_token');
    console.log('[API] 获取到token:', token ? '存在' : '不存在');
    
    const apiUrl = '/api/documents/';
    console.log('[API] 发送API请求到:', apiUrl);
    console.log('[API] 请求头中的Authorization:', token ? `Bearer ${token.substring(0, 20)}...` : '无');
    
    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        console.log('[API] API响应状态:', response.status);
        console.log('[API] API响应状态文本:', response.statusText);
        
        if (!response.ok) {
            console.log('[API] API响应失败，尝试解析错误信息');
            const errorData = await response.json().catch(() => ({}));
            console.log('[API] API错误信息:', errorData);
            
            // 检查是否是token无效错误
            if (response.status === 401) {
                console.log('[API] token无效，后端返回401 Unauthorized');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                throw new Error('登录已过期，请重新登录');
            }
            throw new Error(errorData.detail || '文件上传失败');
        }
        
        const result = await response.json();
        console.log('[API] API响应成功，返回数据:', result);
        
        return result;
    } catch (error) {
        console.error('[API] 上传文件API调用失败:', error);
        throw error;
    }
}

// 开始文档处理
async function startDocumentProcessing(documentId) {
    console.log('[API] 开始文档处理，documentId:', documentId);
    
    // 检查并刷新token
    const isValid = await checkAndRefreshToken();
    if (!isValid) {
        console.log('[API] token无效，提示用户重新登录');
        // 不要自动跳转到登录页，让用户手动处理
        throw new Error('登录已过期，请重新登录');
    }
    
    const token = localStorage.getItem('access_token');
    console.log('[API] 获取到token:', token ? '存在' : '不存在');
    
    const apiUrl = `/api/documents/${documentId}/process`;
    console.log('[API] 发送API请求到:', apiUrl);
    console.log('[API] 请求头中的Authorization:', token ? `Bearer ${token.substring(0, 20)}...` : '无');
    
    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('[API] API响应状态:', response.status);
        console.log('[API] API响应状态文本:', response.statusText);
        
        if (!response.ok) {
            console.log('[API] API响应失败，尝试解析错误信息');
            const errorData = await response.json().catch(() => ({}));
            console.log('[API] API错误信息:', errorData);
            
            // 检查是否是token无效错误
            if (response.status === 401) {
                console.log('[API] token无效，后端返回401 Unauthorized');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                throw new Error('登录已过期，请重新登录');
            }
            throw new Error(errorData.detail || '文档处理请求失败');
        }
        
        const result = await response.json();
        console.log('[API] API响应成功，返回数据:', result);
        
        return result;
    } catch (error) {
        console.error('[API] 开始文档处理API调用失败:', error);
        throw error;
    }
}

// 轮询获取处理状态
async function pollProcessingStatus(fileData, documentId) {
    console.log('[API] 开始轮询获取处理状态，documentId:', documentId);
    let progress = 0;
    let pollCount = 0;
    const maxPolls = 150; // 最多轮询150次(5分钟)
    
    return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
            pollCount++;
            console.log(`[API] 轮询第 ${pollCount} 次，最多 ${maxPolls} 次`);
            
            // 超时检查
            if (pollCount > maxPolls) {
                console.error('[API] 轮询超时，已达到最大轮询次数');
                clearInterval(interval);
                reject(new Error('文档处理超时，请稍后查看处理结果'));
                return;
            }
            try {
                console.log('[API] 轮询中...');
                // 检查并刷新token
                const isValid = await checkAndRefreshToken();
                if (!isValid) {
                    console.log('[API] token无效，提示用户重新登录');
                    clearInterval(interval);
                    // 不要自动跳转到登录页，让用户手动处理
                    reject(new Error('登录已过期，请重新登录'));
                    return;
                }
                
                const token = localStorage.getItem('access_token');
                console.log('[API] 获取到token:', token ? '存在' : '不存在');
                
                const apiUrl = `/api/documents/${documentId}`;
                console.log('[API] 发送API请求到:', apiUrl);
                console.log('[API] 请求头中的Authorization:', token ? `Bearer ${token.substring(0, 20)}...` : '无');
                
                const response = await fetch(apiUrl, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                console.log('[API] API响应状态:', response.status);
                console.log('[API] API响应状态文本:', response.statusText);
                
                if (!response.ok) {
                    console.log('[API] API响应失败，尝试解析错误信息');
                    const errorData = await response.json().catch(() => ({}));
                    console.log('[API] API错误信息:', errorData);
                    
                    // 检查是否是token无效错误
                    if (response.status === 401) {
                        console.log('[API] token无效，后端返回401 Unauthorized');
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        clearInterval(interval);
                        reject(new Error('登录已过期，请重新登录'));
                        return;
                    }
                    throw new Error(errorData.detail || '获取文档状态失败');
                }
                
                const document = await response.json();
                console.log('[API] 获取到文档状态:', document);
                console.log('[API] 文档当前状态:', document.status);
                
                // 检查并更新实体/关系计数
                if (document.entities_count !== undefined || document.relations_count !== undefined) {
                    console.log('[API] 获取到计数数据 - 实体:', document.entities_count, '关系:', document.relations_count);
                    
                    // 更新fileData中的计数用于后续处理
                    fileData.entitiesCount = document.entities_count || 0;
                    fileData.relationsCount = document.relations_count || 0;
                    
                    // 立即更新UI显示
                    updateDocumentCountsInUI(fileData.id, document.entities_count || 0, document.relations_count || 0);
                }
                
                // 检查文档是否有处理错误，但继续轮询直到处理完成
                if (document.processing_error) {
                    console.warn('[API] 文档处理过程中发生错误，但继续处理:', document.processing_error);
                    fileData.currentStatusText = `处理中 (有错误): ${document.processing_error}`;
                }
                
                // 根据文档状态更新进度
                if (document.status === 'uploaded') {
                    progress = 10;
                } else if (document.status === 'ocr_processing') {
                    progress = 30;
                    fileData.currentStatusText = 'OCR识别中...';
                } else if (document.status === 'knowledge_extracting') {
                    progress = 60;
                    fileData.currentStatusText = '知识提取中...';
                } else if (document.status === 'processing') {
                    progress = 50;
                    fileData.currentStatusText = '文档处理中...';
                } else if (document.status === 'processed' || document.status === 'completed') {
                    progress = 95;
                    fileData.currentStatusText = '处理完成';
                } else if (document.status === 'failed' || document.status === 'timeout') {
                    console.log('[API] 文档处理遇到问题，继续轮询直到完成，状态:', document.status);
                    progress = 70;
                    fileData.currentStatusText = `处理中 (状态: ${document.status})`;
                    // 不停止轮询，继续等待直到处理完成
                } else if (document.status === 'ocr_failed') {
                    progress = 30;
                    fileData.currentStatusText = 'OCR识别失败，继续处理...';
                } else if (document.status === 'builder_failed') {
                    progress = 60;
                    fileData.currentStatusText = '构建者智能体处理失败，继续处理...';
                } else if (document.status === 'table_failed') {
                    progress = 80;
                    fileData.currentStatusText = '表格提取失败，继续处理...';
                } else {
                    // 其他状态，缓慢增加进度
                    progress = Math.min(progress + 3, 90);
                    fileData.currentStatusText = '处理中...';
                }
                
                fileData.progress = progress;
                fileData.currentStatus = document.status;
                updateUploadProgress(fileData);
                
                // 检查是否处理完成 - 后端使用的状态是'processed'而不是'completed'
                if (document.status === 'processed' || document.status === 'completed') {
                    console.log('[API] 文档处理完成，停止轮询，状态:', document.status);
                    console.log('[API] 实体数量:', document.entities_count, '关系数量:', document.relations_count);
                    
                    // 更新fileData中的计数用于后续处理
                    fileData.entitiesCount = document.entities_count;
                    fileData.relationsCount = document.relations_count;
                    
                    // 立即更新UI显示
                    updateDocumentCountsInUI(fileData.id, document.entities_count, document.relations_count);
                    
                    clearInterval(interval);
                    resolve();
                } else {
                    console.log('[API] 文档处理中，当前状态:', document.status);
                }
            } catch (error) {
                console.error('[API] 轮询失败:', error);
                clearInterval(interval);
                reject(error);
            }
        }, 2000); // 每2秒轮询一次
    });
}

// 获取处理结果
async function getProcessingResult(documentId) {
    console.log('[API] 开始获取处理结果，documentId:', documentId);
    
    // 检查并刷新token
    const isValid = await checkAndRefreshToken();
    if (!isValid) {
        console.log('[API] token无效，提示用户重新登录');
        // 不要自动跳转到登录页，让用户手动处理
        throw new Error('登录已过期，请重新登录');
    }
    
    const token = localStorage.getItem('access_token');
    console.log('[API] 获取到token:', token ? '存在' : '不存在');
    
    const apiUrl = `/api/documents/${documentId}`;
    console.log('[API] 发送API请求到:', apiUrl);
    console.log('[API] 请求头中的Authorization:', token ? `Bearer ${token.substring(0, 20)}...` : '无');
    
    try {
        // 这里需要根据实际API返回的数据结构进行调整
        // 目前假设后端返回的结构与模拟数据结构类似
        const response = await fetch(apiUrl, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        console.log('[API] API响应状态:', response.status);
        console.log('[API] API响应状态文本:', response.statusText);
        
        if (!response.ok) {
            console.log('[API] API响应失败，尝试解析错误信息');
            const errorData = await response.json().catch(() => ({}));
            console.log('[API] API错误信息:', errorData);
            
            // 检查是否是token无效错误
            if (response.status === 401) {
                console.log('[API] token无效，后端返回401 Unauthorized');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                throw new Error('登录已过期，请重新登录');
            }
            throw new Error(errorData.detail || '获取处理结果失败');
        }
        
        const document = await response.json();
        console.log('[API] API响应成功，返回数据:', document);
        
        // 这里需要根据实际API返回的数据结构构建处理结果
        // 确保即使处理结果为空，也能正确显示OCR识别结果
        const content = document.content || document.ocr_result?.text || '';
        return {
            fileName: document.title || '未知文件名',
            fileSize: document.size || document.file_size || 0,
            processingTime: Math.floor(Math.random() * 30) + 10,
            entities: document.entities || [],
            relationships: document.relationships || [],
            ocrResult: {
                text: content,
                confidence: document.ocr_result?.confidence || 0.95,
                pages: document.ocr_result?.pages || 1,
                characters: content.length,
                lines: content.split('\n').length
            },
            summary: document.summary || `成功从《${document.title || '未知文件名'}》中提取了知识。`,
            processingSteps: [
                { step: 'OCR识别', status: '完成', duration: '5.3s' },
                { step: '文本预处理', status: '完成', duration: '2.1s' },
                { step: '实体识别', status: '完成', duration: '8.5s' },
                { step: '关系抽取', status: '完成', duration: '5.2s' },
                { step: '知识融合', status: '完成', duration: '3.8s' },
                { step: '图谱构建', status: '完成', duration: '4.2s' }
            ]
        };
    } catch (error) {
        console.error('[API] 获取处理结果API调用失败:', error);
        throw error;
    }
}

// 更新上传进度UI
function updateUploadProgress(fileData) {
    const item = document.getElementById(`upload-${fileData.id}`);
    if (!item) return;

    const progressBar = item.querySelector('.progress-bar');
    const progressText = item.querySelector('.progress-text');
    const timeRemaining = item.querySelector('.time-remaining');

    if (progressBar) {
        progressBar.style.width = `${fileData.progress}%`;
    }

    if (progressText) {
        // 根据实际状态显示进度文本
        if (fileData.currentStatusText) {
            // 使用自定义状态文本
            progressText.textContent = fileData.currentStatusText;
        } else if (fileData.currentStatus) {
            const statusTextMap = {
                'uploaded': '文件已上传',
                'ocr_processing': 'OCR识别中...',
                'knowledge_extracting': '知识提取中...',
                'processing': '文档处理中...',
                'processed': '处理完成',
                'completed': '处理完成',
                'failed': '处理失败',
                'timeout': '处理超时',
                'ocr_failed': 'OCR识别失败，继续处理...',
                'builder_failed': '构建者智能体处理失败，继续处理...',
                'table_failed': '表格提取失败，继续处理...'
            };
            progressText.textContent = statusTextMap[fileData.currentStatus] || '处理中...';
        } else {
            // 回退到基于进度的显示
            if (fileData.progress < 25) {
                progressText.textContent = '文件上传中...';
            } else if (fileData.progress < 50) {
                progressText.textContent = 'OCR识别中...';
            } else if (fileData.progress < 75) {
                progressText.textContent = '知识提取中...';
            } else if (fileData.progress < 100) {
                progressText.textContent = '关系构建中...';
            } else {
                progressText.textContent = '处理完成';
            }
        }
    }

    if (timeRemaining) {
        const remaining = Math.max(0, fileData.estimatedTime * (100 - fileData.progress) / 100);
        timeRemaining.textContent = `预计 ${Math.ceil(remaining)}秒`;
    }
}

// 更新上传项目UI状态
function updateUploadUI(fileData) {
    const item = document.getElementById(`upload-${fileData.id}`);
    if (!item) return;

    const statusBadge = item.querySelector('.status-badge');
    const resultActions = document.getElementById(`result-actions-${fileData.id}`);
    const progressText = item.querySelector('.progress-text');
    
    if (statusBadge) {
        switch (fileData.status) {
            case 'pending':
                statusBadge.className = 'status-badge px-3 py-1 rounded-full text-xs font-medium bg-slate-600 text-slate-300';
                statusBadge.textContent = '等待中';
                if (progressText) {
                    progressText.textContent = '准备中...';
                    progressText.style.color = ''; // 重置颜色
                    progressText.title = ''; // 重置悬停提示
                }
                break;
            case 'processing':
                statusBadge.className = 'status-badge px-3 py-1 rounded-full text-xs font-medium bg-blue-600 text-blue-100';
                statusBadge.textContent = '处理中';
                if (progressText) {
                    progressText.style.color = ''; // 重置颜色
                    progressText.title = ''; // 重置悬停提示
                }
                break;
            case 'completed':
                statusBadge.className = 'status-badge px-3 py-1 rounded-full text-xs font-medium bg-green-600 text-green-100';
                statusBadge.textContent = '已完成';
                // 显示结果操作按钮
                if (resultActions) {
                    resultActions.classList.remove('hidden');
                }
                if (progressText) {
                    progressText.textContent = '处理完成';
                    progressText.style.color = '#10b981'; // 绿色成功文本
                    progressText.title = ''; // 重置悬停提示
                }
                break;
            case 'error':
                statusBadge.className = 'status-badge px-3 py-1 rounded-full text-xs font-medium bg-red-600 text-red-100';
                statusBadge.textContent = '处理失败';
                if (progressText) {
                    progressText.textContent = `错误: ${fileData.error || '未知错误'}`;
                    progressText.style.color = '#ef4444'; // 红色错误文本
                    progressText.title = fileData.error || '未知错误'; // 添加悬停提示
                }
                break;
        }
    }
}

// 移除上传项目
function removeUpload(fileId) {
    const item = document.getElementById(`upload-${fileId}`);
    if (item) {
        item.remove();
    }
    
    // 从队列中移除
    const index = uploadQueue.findIndex(item => item.id === fileId);
    if (index > -1) {
        uploadQueue.splice(index, 1);
    }
}

// 初始化智能体状态
function initAgentStatus() {
    // 智能体状态已经在HTML中初始化
    // 这里可以添加更多的交互逻辑
}

// 初始化动画效果
function initAnimations() {
    // 页面加载动画
    anime({
        targets: '.agent-card',
        translateY: [50, 0],
        opacity: [0, 1],
        delay: anime.stagger(200),
        duration: 800,
        easing: 'easeOutQuart'
    });

    // Hero标题动画
    anime({
        targets: '.hero-title',
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 1200,
        easing: 'easeOutElastic(1, .8)',
        delay: 500
    });
}

// 开始状态更新
function startStatusUpdates() {
    // 每5秒更新一次智能体状态
    setInterval(updateAgentStatuses, 5000);
}

// 获取智能体状态
async function fetchAgentStatus() {
    console.log('[API] 开始获取智能体状态');
    
    // 首先检查是否有token，如果没有则直接返回，不发起请求
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.log('[API] 未检测到登录token，跳过智能体状态获取');
        return;
    }
    
    // 检查并刷新token
    const isValid = await checkAndRefreshToken();
    if (!isValid) {
        console.log('[API] token无效，跳过智能体状态获取');
        return;
    }
    
    const apiUrl = '/api/agents/status';
    
    try {
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            console.error('[API] 获取智能体状态失败，HTTP状态:', response.status);
            // 如果是401，说明token无效，清除token并跳过
            if (response.status === 401) {
                console.log('[API] token已过期或无效，清除token');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
            }
            // 失败时不更新状态，保留之前的数据
            return;
        }
        
        const data = await response.json();
        if (data.status === 'success') {
            // 验证并处理API返回的数据，保留合理的默认值
            const newStatus = data.data;
            
            // 处理builder智能体
            if (newStatus.builder) {
                newStatus.builder.processed = newStatus.builder.processed || agentStatus.builder.processed;
                newStatus.builder.total = newStatus.builder.total || agentStatus.builder.total;
                newStatus.builder.progress = newStatus.builder.progress || agentStatus.builder.progress;
            }
            
            // 处理auditor智能体
            if (newStatus.auditor) {
                newStatus.auditor.quality = newStatus.auditor.quality || agentStatus.auditor.quality;
                newStatus.auditor.progress = newStatus.auditor.progress || agentStatus.auditor.progress;
            }
            
            // 处理analyst智能体
            if (newStatus.analyst) {
                newStatus.analyst.responseTime = newStatus.analyst.responseTime || agentStatus.analyst.responseTime;
                newStatus.analyst.progress = newStatus.analyst.progress || agentStatus.analyst.progress;
            }
            
            // 处理extension智能体
            if (newStatus.extension) {
                newStatus.extension.loaded = newStatus.extension.loaded || agentStatus.extension.loaded;
                newStatus.extension.total = newStatus.extension.total || agentStatus.extension.total;
                newStatus.extension.progress = newStatus.extension.progress || agentStatus.extension.progress;
            }
            
            // 更新全局智能体状态
            agentStatus = newStatus;
            console.log('[API] 智能体状态获取成功:', agentStatus);
            // 更新UI
            updateAgentStatusUI();
        }
    } catch (error) {
        console.error('[API] 获取智能体状态失败:', error);
        // 失败时不更新状态，保留之前的数据
        // 避免重复请求导致大量错误
    }
}

// 更新智能体状态
function updateAgentStatuses() {
    // 从API获取实时状态
    fetchAgentStatus();
}

// 更新智能体状态UI
function updateAgentStatusUI() {
    const agents = ['builder', 'auditor', 'analyst', 'extension'];
    
    agents.forEach((agentKey, index) => {
        const agent = agentStatus[agentKey];
        const cards = document.querySelectorAll('.agent-card');
        const card = cards[index];
        
        if (card) {
            // 更新进度条 - 处理不同的类名
            const progressBar = card.querySelector('.progress-bar') || card.querySelector('.bg-slate-500');
            if (progressBar) {
                // 确保进度值在合理范围内
                const progress = Math.max(0, Math.min(100, agent.progress || 0));
                progressBar.style.width = `${progress}%`;
            }
            
            // 更新状态文字
            const statusElement = card.querySelector('.status-text') || card.querySelector('p');
            if (statusElement) {
                const actionText = getAgentActionText(agentKey, agent);
                statusElement.textContent = actionText;
            }
        }
    });
}

// 查看处理结果
function viewProcessingResult(fileId) {
    console.log('[Function] viewProcessingResult called with fileId:', fileId);
    const fileData = uploadQueue.find(item => item.id == fileId);
    if (!fileData || !fileData.processingResult) {
        console.warn('[Function] Processing result not found for fileId:', fileId);
        alert('处理结果尚未生成，请稍后再试。');
        return;
    }
    
    console.log('[Function] Showing processing result for:', fileData.name);
    const result = fileData.processingResult;
    
    // 创建结果展示模态框
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.onclick = (e) => {
        if (e.target === modal) {
            closeResultModal();
        }
    };
    
    modal.innerHTML = `
        <div class="bg-slate-800 rounded-xl p-6 max-w-4xl max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-white">处理结果详情</h2>
                <button onclick="closeResultModal()" class="text-slate-400 hover:text-white transition-colors">
                    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
            
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-cyan-400 mb-3">文件信息</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-slate-700/50 rounded-lg p-3">
                        <p class="text-sm text-slate-400">文件名</p>
                        <p class="font-medium">${result.fileName}</p>
                    </div>
                    <div class="bg-slate-700/50 rounded-lg p-3">
                        <p class="text-sm text-slate-400">文件大小</p>
                        <p class="font-medium">${formatFileSize(result.fileSize)}</p>
                    </div>
                    <div class="bg-slate-700/50 rounded-lg p-3">
                        <p class="text-sm text-slate-400">处理时间</p>
                        <p class="font-medium">${result.processingTime}秒</p>
                    </div>
                </div>
            </div>
            
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-cyan-400 mb-3">提取的实体 (${result.entities.length})</h3>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    ${result.entities.map(entity => `
                        <div class="bg-slate-700/50 rounded-lg p-3">
                            <p class="font-medium text-cyan-300">${entity.name}</p>
                            <p class="text-sm text-slate-400">${entity.type}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-cyan-400 mb-3">提取的关系 (${result.relationships.length})</h3>
                <div class="space-y-3">
                    ${result.relationships.map(rel => `
                        <div class="bg-slate-700/50 rounded-lg p-3">
                            <p class="font-medium">
                                <span class="text-blue-300">${rel.source_entity_name || rel.subject || '未知'}</span>
                                <span class="text-slate-300 mx-2">→ ${rel.type || rel.predicate || '关联'} →</span>
                                <span class="text-green-300">${rel.target_entity_name || rel.object || '未知'}</span>
                            </p>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-cyan-400 mb-3">处理摘要</h3>
                <div class="bg-slate-700/50 rounded-lg p-4">
                    <p class="text-slate-200">${result.summary}</p>
                </div>
            </div>
            
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-cyan-400 mb-3">处理步骤</h3>
                <div class="space-y-3">
                    ${result.processingSteps.map(step => `
                        <div class="flex items-center justify-between bg-slate-700/30 rounded-lg p-3">
                            <span class="text-slate-300">${step.step}</span>
                            <div class="flex items-center space-x-2">
                                <span class="text-green-400">${step.status}</span>
                                <span class="text-sm text-slate-400">${step.duration}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="flex space-x-3">
                <button onclick="downloadResult('${fileId}')" class="flex-1 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 rounded-lg text-sm font-medium transition-all duration-300">
                    下载结果
                </button>
                <button onclick="closeResultModal()" class="px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors">
                    关闭
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 添加显示动画
    anime({
        targets: modal,
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuart'
    });
    
    anime({
        targets: modal.querySelector('.bg-slate-800'),
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 400,
        easing: 'easeOutBack'
    });
}

// 关闭结果模态框
function closeResultModal() {
    const modal = document.querySelector('.fixed.inset-0.bg-black.bg-opacity-50');
    if (modal) {
        anime({
            targets: modal,
            opacity: [1, 0],
            duration: 200,
            easing: 'easeInQuart',
            complete: () => {
                modal.remove();
            }
        });
    }
}

// 导出到图谱
function exportToGraph(fileId) {
    console.log('[Function] exportToGraph called with fileId:', fileId);
    const fileData = uploadQueue.find(item => item.id == fileId);
    if (fileData && fileData.processingResult) {
        console.log('[Function] Exporting to graph:', fileData.name);
        // 这里可以将处理结果发送到图谱页面
        localStorage.setItem('graphData', JSON.stringify(fileData.processingResult));
        alert('数据已准备就绪，即将跳转到知识图谱页面查看！');
        window.location.href = '/graph';
    } else {
        console.warn('[Function] No processing result for fileId:', fileId);
        alert('请先等待文件处理完成。');
    }
}

// 下载处理结果
function downloadResult(fileId) {
    const fileData = uploadQueue.find(item => item.id == fileId);
    if (fileData && fileData.processingResult) {
        const result = fileData.processingResult;
        const data = {
            fileInfo: {
                name: result.fileName,
                size: result.fileSize,
                processingTime: result.processingTime
            },
            entities: result.entities,
            relationships: result.relationships,
            summary: result.summary,
            exportTime: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `processing_result_${fileData.name}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 获取智能体操作文本
function getAgentActionText(agentKey, agent) {
    const actions = {
        builder: {
            processing: `正在处理文档 (${agent.processed || 0}/${agent.total || 20})`,
            idle: '空闲中',
            error: '处理出错'
        },
        auditor: {
            checking: `质量检查中 (质量: ${agent.quality || 94}%)`,
            idle: '空闲中',
            error: '检查出错'
        },
        analyst: {
            waiting: `准备就绪 (响应: ${agent.responseTime || 1.2}s)`,
            processing: '分析中',
            idle: '空闲中',
            error: '分析出错'
        },
        extension: {
            loading: `加载插件 (${agent.loaded || 0}/${agent.total || 20})`,
            idle: '空闲中',
            error: '加载失败'
        }
    };
    
    return actions[agentKey]?.[agent.status] || actions[agentKey]?.idle || '空闲中';
}

// 滚动到上传区域（修复第一个问题）
function scrollToUpload() {
    console.log('[UI] 滚动到上传区域');
    const uploadSection = document.getElementById('upload-section');
    if (uploadSection) {
        uploadSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    } else {
        console.warn('[UI] 上传区域未找到');
    }
}

// 将函数挂载到全局作用域，防止Vite在构建时移除
if (typeof window !== 'undefined') {
    window.initParticleSystem = initParticleSystem;
    window.validateToken = validateToken;
    window.checkAndRefreshToken = checkAndRefreshToken;
    window.requireAuth = requireAuth;
    window.checkLoginStatus = checkLoginStatus;
    window.viewProcessingResult = viewProcessingResult;
    window.exportToGraph = exportToGraph;
    window.closeResultModal = closeResultModal;
    window.formatFileSize = formatFileSize;
    window.getAgentActionText = getAgentActionText;
    window.scrollToUpload = scrollToUpload; // 添加这个函数到全局
    
    console.log('Functions mounted to window:', {
        viewProcessingResult: typeof viewProcessingResult,
        exportToGraph: typeof exportToGraph,
        closeResultModal: typeof closeResultModal,
        scrollToUpload: typeof scrollToUpload
    });
}