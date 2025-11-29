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
            console.log('[Token Validate] token格式不正确，验证失败');
            return false;
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
        // 解析失败时返回false，因为这意味着token格式确实有问题
        console.log('[Token Validate] token解析失败，验证失败');
        return false;
    }
}

// 检查并刷新token
async function checkAndRefreshToken() {
    const token = localStorage.getItem('access_token');
    console.log('[Token Check] 开始检查token:', token ? '存在' : '不存在');
    
    if (!token) {
        console.log('[Token Check] token不存在，返回false');
        return false;
    }
    
    try {
        // 检查token格式
        const tokenParts = token.split('.');
        if (tokenParts.length !== 3) {
            console.log('[Token Check] token格式不正确，返回false');
            return false;
        }
        
        // 解析token，检查是否过期
        const payload = JSON.parse(atob(tokenParts[1]));
        console.log('[Token Check] token payload:', payload);
        
        const now = Math.floor(Date.now() / 1000);
        console.log('[Token Check] 当前时间:', now, '秒');
        console.log('[Token Check] token过期时间:', payload.exp, '秒');
        
        const expiresIn = payload.exp - now;
        console.log('[Token Check] token剩余有效期:', expiresIn, '秒');
        
        // 只有当token确实已过期时才返回false
        // 否则让API调用尝试发送请求，由后端决定token是否有效
        if (expiresIn <= 0) {
            console.log('[Token Check] token已过期，返回false');
            return false;
        }
        
        console.log('[Token Check] token有效，返回true');
        return true;
    } catch (error) {
        console.error('[Token Check] 检查token失败:', error);
        // 解析失败时不返回false，让API调用尝试发送请求，由后端决定token是否有效
        // 这样可以避免前端误判token无效
        console.log('[Token Check] token解析失败，但仍返回true，由后端验证');
        return true;
    }
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
const protectedPages = ['index.html', 'query.html', 'graph.html', 'admin.html', 'user-center.html'];

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
            window.location.href = 'login.html';
            return false;
        }
        
        // 验证token是否有效
        const isTokenValid = validateToken();
        console.log('[Auth] token验证结果:', isTokenValid ? '有效' : '无效');
        
        if (!isTokenValid) {
            console.log('[Auth] token无效，跳转到登录页面');
            // token无效，跳转到登录页面
            window.location.href = 'login.html';
            return false;
        }
    }
    return true;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否需要认证
    if (requireAuth()) {
        checkLoginStatus();
        initParticleSystem();
        initUploadZone();
        initAgentStatus();
        initAnimations();
        startStatusUpdates();
    }
});

// 初始化粒子系统
function initParticleSystem() {
    const container = document.getElementById('particles-container');
    if (!container) return;

    // 使用p5.js创建粒子背景
    new p5(function(p) {
        let particles = [];
        let connections = [];

        p.setup = function() {
            const canvas = p.createCanvas(p.windowWidth, p.windowHeight);
            canvas.parent('particles-container');
            
            // 创建粒子
            for (let i = 0; i < 50; i++) {
                particles.push({
                    x: p.random(p.width),
                    y: p.random(p.height),
                    vx: p.random(-0.5, 0.5),
                    vy: p.random(-0.5, 0.5),
                    size: p.random(2, 4)
                });
            }
        };

        p.draw = function() {
            p.clear();
            
            // 更新粒子位置
            particles.forEach(particle => {
                particle.x += particle.vx;
                particle.y += particle.vy;
                
                // 边界检测
                if (particle.x < 0 || particle.x > p.width) particle.vx *= -1;
                if (particle.y < 0 || particle.y > p.height) particle.vy *= -1;
            });

            // 绘制连接线
            p.stroke(6, 182, 212, 30);
            p.strokeWeight(1);
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dist = p.dist(particles[i].x, particles[i].y, particles[j].x, particles[j].y);
                    if (dist < 100) {
                        p.line(particles[i].x, particles[i].y, particles[j].x, particles[j].y);
                    }
                }
            }

            // 绘制粒子
            p.fill(6, 182, 212, 100);
            p.noStroke();
            particles.forEach(particle => {
                p.circle(particle.x, particle.y, particle.size);
            });
        };

        p.windowResized = function() {
            p.resizeCanvas(p.windowWidth, p.windowHeight);
        };
    });
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
    try {
        console.log('开始处理文件:', fileData.name);
        
        // 1. 上传文件到后端
        const document = await uploadFileToBackend(fileData.file);
        fileData.documentId = document.id;
        console.log('文件上传成功，documentId:', document.id);
        
        // 2. 调用文档处理API
        await startDocumentProcessing(document.id);
        console.log('文档处理API调用成功');
        
        // 3. 轮询获取处理结果
        await pollProcessingStatus(fileData, document.id);
        console.log('文档处理完成');
        
        // 4. 获取最终处理结果
        const processingResult = await getProcessingResult(document.id);
        fileData.processingResult = processingResult;
        console.log('获取处理结果成功');
        
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
        if (error.message.includes('登录已过期')) {
            fileData.error = '登录已过期，请重新登录';
            // 不自动跳转到登录页，让用户手动处理
        } else if (error.message.includes('无法验证凭据')) {
            fileData.error = '登录已过期，请重新登录';
            // 不自动跳转到登录页，让用户手动处理
        } else if (error.message.includes('文件上传失败')) {
            fileData.error = '文件上传失败，请检查网络连接或文件大小';
        } else if (error.message.includes('文档处理请求失败')) {
            fileData.error = '文档处理请求失败，请稍后重试';
        } else if (error.message.includes('获取文档状态失败')) {
            fileData.error = '获取文档状态失败，请稍后重试';
        } else if (error.message.includes('获取处理结果失败')) {
            fileData.error = '获取处理结果失败，请稍后重试';
        } else {
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
    
    const apiUrl = 'http://localhost:8000/api/documents/';
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
            if (errorData.detail === '无法验证凭据') {
                console.log('[API] token无效，后端返回"无法验证凭据"');
                // 不要自动跳转到登录页，让用户手动处理
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
    
    const apiUrl = `http://localhost:8000/api/documents/${documentId}/process/`;
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
            if (errorData.detail === '无法验证凭据') {
                console.log('[API] token无效，后端返回"无法验证凭据"');
                // 不要自动跳转到登录页，让用户手动处理
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
                
                const apiUrl = `http://localhost:8000/api/documents/${documentId}/`;
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
                    if (errorData.detail === '无法验证凭据') {
                        console.log('[API] token无效，后端返回"无法验证凭据"');
                        clearInterval(interval);
                        // 不要自动跳转到登录页，让用户手动处理
                        reject(new Error('登录已过期，请重新登录'));
                        return;
                    }
                    throw new Error(errorData.detail || '获取文档状态失败');
                }
                
                const document = await response.json();
                console.log('[API] 获取到文档状态:', document);
                console.log('[API] 文档当前状态:', document.status);
                
                // 根据文档状态更新进度
                if (document.status === 'uploaded') {
                    progress = 10;
                } else if (document.status === 'ocr_processing') {
                    progress = 30;
                } else if (document.status === 'knowledge_extracting') {
                    progress = 60;
                } else if (document.status === 'processing') {
                    progress = 50;
                } else if (document.status === 'processed' || document.status === 'completed') {
                    progress = 95;
                } else {
                    // 其他状态，缓慢增加进度
                    progress = Math.min(progress + 3, 90);
                }
                
                fileData.progress = progress;
                fileData.currentStatus = document.status;
                updateUploadProgress(fileData);
                
                // 检查是否处理完成 - 后端使用的状态是'processed'而不是'completed'
                if (document.status === 'processed' || document.status === 'completed') {
                    console.log('[API] 文档处理完成，停止轮询，状态:', document.status);
                    clearInterval(interval);
                    resolve();
                } else if (document.status === 'failed' || document.status === 'timeout') {
                    console.log('[API] 文档处理失败，停止轮询，状态:', document.status);
                    clearInterval(interval);
                    reject(new Error(`文档处理失败: ${document.processing_error || '未知错误'}`));
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
    
    const apiUrl = `http://localhost:8000/api/documents/${documentId}/`;
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
            if (errorData.detail === '无法验证凭据') {
                console.log('[API] token无效，后端返回"无法验证凭据"');
                // 不要自动跳转到登录页，让用户手动处理
                throw new Error('登录已过期，请重新登录');
            }
            throw new Error(errorData.detail || '获取处理结果失败');
        }
        
        const document = await response.json();
        console.log('[API] API响应成功，返回数据:', document);
        
        // 这里需要根据实际API返回的数据结构构建处理结果
        // 暂时使用模拟数据结构，后续需要根据实际API调整
        return {
            fileName: document.title,
            fileSize: document.size || 0,
            processingTime: Math.floor(Math.random() * 30) + 10,
            entities: document.entities || [],
            relationships: document.relationships || [],
            ocrResult: document.ocr_result || {
                text: document.content || '',
                confidence: 0.95,
                pages: 1,
                characters: (document.content || '').length,
                lines: (document.content || '').split('\n').length
            },
            summary: document.summary || `成功从《${document.title}》中提取了知识。`,
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
        if (fileData.currentStatus) {
            const statusTextMap = {
                'uploaded': '文件已上传',
                'ocr_processing': 'OCR识别中...',
                'knowledge_extracting': '知识提取中...',
                'processing': '文档处理中...',
                'processed': '处理完成',
                'completed': '处理完成',
                'failed': '处理失败',
                'timeout': '处理超时'
            };
            progressText.textContent = statusTextMap[fileData.currentStatus] || '处理中...';
        } else {
            // 回退到基于进度的显示
            if (fileData.progress < 25) {
                progressText.textContent = '文件上传中...';
            } else if (fileData.progress < 50) {
                progressText.textContent = 'OCR识别中...';
            } else if (fileData.progress < 75) {
                progressText.textContent = '实体抽取中...';
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

// 更新智能体状态
function updateAgentStatuses() {
    // 模拟状态变化
    Object.keys(agentStatus).forEach(agentKey => {
        const agent = agentStatus[agentKey];
        
        // 随机更新进度
        if (agent.progress < 100 && Math.random() > 0.5) {
            agent.progress = Math.min(100, agent.progress + Math.random() * 10);
        }
        
        // 更新其他指标
        if (agent.processed !== undefined && agent.total !== undefined) {
            if (agent.processed < agent.total && Math.random() > 0.7) {
                agent.processed++;
            }
        }
        
        if (agent.quality !== undefined) {
            agent.quality = Math.max(85, Math.min(100, agent.quality + (Math.random() - 0.5) * 2));
        }
        
        if (agent.responseTime !== undefined) {
            agent.responseTime = Math.max(0.5, Math.min(5, agent.responseTime + (Math.random() - 0.5) * 0.5));
        }
    });
    
    // 更新UI
    updateAgentStatusUI();
}

// 更新智能体状态UI
function updateAgentStatusUI() {
    const agents = ['builder', 'auditor', 'analyst', 'extension'];
    
    agents.forEach((agentKey, index) => {
        const agent = agentStatus[agentKey];
        const cards = document.querySelectorAll('.agent-card');
        const card = cards[index];
        
        if (card) {
            // 更新进度条
            const progressBar = card.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = `${agent.progress}%`;
            }
            
            // 更新状态文本
            const statusText = card.querySelector('.text-sm');
            if (statusText) {
                switch (agentKey) {
                    case 'builder':
                        statusText.textContent = `文档处理中... (${agent.processed}/${agent.total})`;
                        break;
                    case 'auditor':
                        statusText.textContent = `质量检查中... (${Math.round(agent.quality)}%)`;
                        break;
                    case 'analyst':
                        statusText.textContent = `等待查询... (${agent.responseTime.toFixed(1)}s)`;
                        break;
                    case 'extension':
                        statusText.textContent = `插件加载中... (${agent.loaded}/${agent.total})`;
                        break;
                }
            }
        }
    });
}

// 滚动到上传区域
function scrollToUpload() {
    const uploadSection = document.getElementById('upload-section');
    if (uploadSection) {
        uploadSection.scrollIntoView({ 
            behavior: 'smooth',
            block: 'center'
        });
    }
}

// 工具函数：格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}



// 查看处理结果
function viewProcessingResult(fileId) {
    const fileData = uploadQueue.find(item => item.id == fileId);
    if (!fileData || !fileData.processingResult) {
        alert('处理结果尚未生成，请稍后再试。');
        return;
    }
    
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
                <h3 class="text-lg font-semibold text-cyan-400 mb-3">处理摘要</h3>
                <div class="bg-slate-700/30 rounded-lg p-4">
                    <p class="text-slate-300 leading-relaxed">${result.summary}</p>
                </div>
            </div>
            
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-cyan-400 mb-3">OCR识别结果</h3>
                <div class="bg-slate-700/30 rounded-lg p-4 mb-4">
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        <div class="bg-slate-700/50 rounded-lg p-3">
                            <p class="text-sm text-slate-400">识别置信度</p>
                            <p class="font-medium">${(result.ocrResult.confidence * 100).toFixed(1)}%</p>
                        </div>
                        <div class="bg-slate-700/50 rounded-lg p-3">
                            <p class="text-sm text-slate-400">页数</p>
                            <p class="font-medium">${result.ocrResult.pages}页</p>
                        </div>
                        <div class="bg-slate-700/50 rounded-lg p-3">
                            <p class="text-sm text-slate-400">字符数</p>
                            <p class="font-medium">${result.ocrResult.characters}个</p>
                        </div>
                        <div class="bg-slate-700/50 rounded-lg p-3">
                            <p class="text-sm text-slate-400">行数</p>
                            <p class="font-medium">${result.ocrResult.lines}行</p>
                        </div>
                    </div>
                    <div class="bg-slate-800/50 rounded-lg p-4 max-h-64 overflow-y-auto">
                        <pre class="text-slate-300 text-sm whitespace-pre-wrap">${result.ocrResult.text}</pre>
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                    <h3 class="text-lg font-semibold text-cyan-400 mb-3">提取的实体 (${result.entities.length}个)</h3>
                    <div class="space-y-2 max-h-64 overflow-y-auto">
                        ${result.entities.map(entity => `
                            <div class="bg-slate-700/50 rounded-lg p-3">
                                <div class="flex items-center justify-between mb-1">
                                    <span class="font-medium">${entity.name}</span>
                                    <span class="text-xs px-2 py-1 bg-blue-600 rounded">${entity.type}</span>
                                </div>
                                <div class="text-sm text-slate-400">
                                    置信度: ${(entity.confidence * 100).toFixed(1)}%
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div>
                    <h3 class="text-lg font-semibold text-cyan-400 mb-3">关系抽取 (${result.relationships.length}个)</h3>
                    <div class="space-y-2 max-h-64 overflow-y-auto">
                        ${result.relationships.map(rel => `
                            <div class="bg-slate-700/50 rounded-lg p-3">
                                <div class="text-sm mb-1">
                                    <span class="text-blue-400">${rel.from}</span>
                                    <span class="text-slate-400">→</span>
                                    <span class="text-green-400">${rel.to}</span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span class="text-xs px-2 py-1 bg-purple-600 rounded">${rel.type}</span>
                                    <span class="text-xs text-slate-400">${(rel.confidence * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
            
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-cyan-400 mb-3">处理步骤</h3>
                <div class="space-y-2">
                    ${result.processingSteps.map(step => `
                        <div class="flex items-center justify-between bg-slate-700/30 rounded-lg p-3">
                            <div class="flex items-center space-x-3">
                                <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                                <span class="text-sm">${step.step}</span>
                            </div>
                            <div class="text-right">
                                <span class="text-xs px-2 py-1 bg-green-600/30 rounded">${step.status}</span>
                                <div class="text-xs text-slate-400 mt-1">${step.duration}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="flex items-center justify-center space-x-4">
                <button onclick="exportToGraph('${fileId}')" class="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 rounded-lg transition-all duration-300">
                    导入图谱
                </button>
                <button onclick="downloadResult('${fileId}')" class="px-6 py-2 bg-slate-600 hover:bg-slate-700 rounded-lg transition-colors">
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
                document.body.removeChild(modal);
            }
        });
    }
}

// 导出到图谱
function exportToGraph(fileId) {
    const fileData = uploadQueue.find(item => item.id == fileId);
    if (fileData && fileData.processingResult) {
        // 这里可以将处理结果发送到图谱页面
        localStorage.setItem('graphData', JSON.stringify(fileData.processingResult));
        alert('数据已准备就绪，即将跳转到知识图谱页面查看！');
        window.location.href = 'graph.html';
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

// 确保generateId函数存在
function generateId() {
    return '';
}

// 导出函数供其他页面使用
window.KnowledgeGraphSystem = {
    scrollToUpload,
    removeUpload,
    formatFileSize
};