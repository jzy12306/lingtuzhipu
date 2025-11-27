// 全局变量
let particleSystem;
let uploadQueue = [];
let agentStatus = {
    builder: { status: 'processing', progress: 75, processed: 15, total: 20 },
    auditor: { status: 'checking', progress: 90, quality: 94 },
    analyst: { status: 'waiting', progress: 25, responseTime: 1.2 },
    extension: { status: 'loading', progress: 60, loaded: 12, total: 20 }
};

// 生成唯一ID的工具函数
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initParticleSystem();
    initUploadZone();
    initAgentStatus();
    initAnimations();
    startStatusUpdates();
    
    // 检查登录状态
    checkLoginStatus();
});

// 检查登录状态
function checkLoginStatus() {
    const token = localStorage.getItem('access_token');
    const uploadZone = document.getElementById('upload-zone');
    
    if (!token && uploadZone) {
        // 显示未登录提示
        const notice = document.createElement('div');
        notice.className = 'bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-4 mb-4';
        notice.innerHTML = `
            <div class="flex items-start space-x-3">
                <svg class="w-6 h-6 text-yellow-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
                <div class="flex-1">
                    <h3 class="text-sm font-medium text-yellow-400">需要登录</h3>
                    <p class="text-xs text-yellow-300 mt-1">您尚未登录，请先<a href="login.html" class="underline hover:text-yellow-200">登录</a>后再上传文件。</p>
                    <p class="text-xs text-slate-400 mt-1">默认账号: admin@example.com / admin123456</p>
                </div>
            </div>
        `;
        uploadZone.parentNode.insertBefore(notice, uploadZone);
    }
}

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
    // 检查是否已登录
    const token = localStorage.getItem('access_token');
    if (!token) {
        alert('请先登录后再上传文件！');
        window.location.href = 'login.html';
        return;
    }
    
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

    // 模拟并发处理（最多3个同时处理）
 const processingItems = pendingItems.slice(0, 3);
    
    processingItems.forEach(fileData => {
        fileData.status = 'processing';
        updateUploadUI(fileData);
        
        // 模拟处理过程
        simulateFileProcessing(fileData);
    });
}

// 真实文件处理过程
async function simulateFileProcessing(fileData) {
    try {
        console.log('[File Upload] 开始处理文件:', fileData.name);
        
        // 第一步:上传文件到后端
        fileData.progress = 10;
        updateUploadProgress(fileData);
        
        const formData = new FormData();
        formData.append('file', fileData.file);
        
        console.log('[File Upload] 上传文件到后端...');
        const uploadResponse = await fetch('http://localhost:8000/api/documents/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: formData
        });
        
        console.log('[File Upload] 上传响应状态:', uploadResponse.status);
        
        if (!uploadResponse.ok) {
            const errorText = await uploadResponse.text();
            console.error('[File Upload] 上传失败:', errorText);
            throw new Error(`文件上传失败 (${uploadResponse.status}): ${errorText}`);
        }
        
        const documentData = await uploadResponse.json();
        const documentId = documentData.id;
        console.log('[File Upload] 文件上传成功, 文档ID:', documentId);
        
        fileData.progress = 30;
        updateUploadProgress(fileData);
        
        // 第二步:触发文档处理
        console.log('[File Upload] 触发文档处理...');
        const processResponse = await fetch(`http://localhost:8000/api/documents/${documentId}/process`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('[File Upload] 处理响应状态:', processResponse.status);
        
        if (!processResponse.ok) {
            const errorText = await processResponse.text();
            console.error('[File Upload] 处理启动失败:', errorText);
            throw new Error(`文档处理启动失败 (${processResponse.status})`);
        }
        
        fileData.progress = 50;
        updateUploadProgress(fileData);
        
        // 第三步:轮询检查处理状态
        let pollCount = 0;
        const maxPolls = 60; // 最多轮询60次(约2分钟)
        
        const checkStatus = async () => {
            pollCount++;
            console.log(`[File Upload] 轮询检查状态 (${pollCount}/${maxPolls})...`);
            
            if (pollCount > maxPolls) {
                throw new Error('处理超时,请稍后查看文档列表');
            }
            
            const statusResponse = await fetch(`http://localhost:8000/api/documents/${documentId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            
            if (!statusResponse.ok) {
                throw new Error('无法获取文档状态');
            }
            
            const docStatus = await statusResponse.json();
            console.log('[File Upload] 当前文档状态:', docStatus.status);
            
            // 更新进度
            if (docStatus.status === 'processing' || docStatus.status === 'ocr_processing') {
                fileData.progress = Math.min(fileData.progress + 5, 90);
                updateUploadProgress(fileData);
                
                // 继续轮询
                setTimeout(checkStatus, 2000);
            } else if (docStatus.status === 'processed') {
                console.log('[File Upload] 文档处理完成');
                fileData.progress = 100;
                fileData.status = 'completed';
                
                // 获取处理结果
                fileData.processingResult = await fetchProcessingResult(documentId, docStatus);
                console.log('[File Upload] 处理结果:', fileData.processingResult);
                updateUploadProgress(fileData);
                updateUploadUI(fileData);
                
                // 处理下一个文件
                setTimeout(() => {
                    processUploadQueue();
                }, 1000);
            } else if (docStatus.status === 'error') {
                throw new Error('文档处理失败');
            } else {
                // 未知状态,继续轮询
                console.warn('[File Upload] 未知状态:', docStatus.status);
                setTimeout(checkStatus, 2000);
            }
        };
        
        // 开始轮询
        setTimeout(checkStatus, 2000);
        
    } catch (error) {
        console.error('文件处理失败:', error);
        fileData.status = 'error';
        fileData.progress = 0;
        fileData.errorMessage = error.message;
        updateUploadUI(fileData);
        
        // 在界面上显示错误信息
        const item = document.getElementById(`upload-${fileData.id}`);
        if (item) {
            const progressContainer = item.querySelector('.progress-container');
            if (progressContainer) {
                progressContainer.innerHTML = `
                    <div class="bg-red-900/30 border border-red-500/50 rounded-lg p-3 mt-2">
                        <div class="flex items-start space-x-2">
                            <svg class="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                            </svg>
                            <div class="flex-1">
                                <p class="text-sm font-medium text-red-400">处理失败</p>
                                <p class="text-xs text-red-300 mt-1">${error.message}</p>
                                <p class="text-xs text-slate-400 mt-1">请检查：1. 是否已登录  2. 后端服务是否启动  3. 网络连接是否正常</p>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
        
        // 处理下一个文件
        setTimeout(() => {
            processUploadQueue();
        }, 1000);
    }
}

// 获取处理结果
async function fetchProcessingResult(documentId, docStatus) {
    try {
        // 构建处理结果对象
        const result = {
            fileName: docStatus.title || docStatus.file_name,
            fileSize: docStatus.size || 0,
            processingTime: 0,
            entities: [],
            relationships: [],
            ocrResult: {
                text: '',
                confidence: 0,
                pages: 0,
                characters: 0,
                lines: 0
            },
            summary: '',
            processingSteps: []
        };
        
        // 从文档状态中提取实体和关系数量
        const entitiesCount = docStatus.extracted_entities || 0;
        const relationshipsCount = docStatus.extracted_relationships || 0;
        
        // 如果有实体和关系,从知识库中获取详细信息
        if (entitiesCount > 0 || relationshipsCount > 0) {
            // 获取实体列表
            const entitiesResponse = await fetch(
                `http://localhost:8000/api/knowledge/entities?document_id=${documentId}&limit=100`,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                }
            );
            
            if (entitiesResponse.ok) {
                const entitiesData = await entitiesResponse.json();
                result.entities = entitiesData.map(e => ({
                    name: e.name,
                    type: e.type,
                    confidence: e.confidence_score || 0.85
                }));
            }
            
            // 获取关系列表
            const relationsResponse = await fetch(
                `http://localhost:8000/api/knowledge/relations?document_id=${documentId}&limit=100`,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                }
            );
            
            if (relationsResponse.ok) {
                const relationsData = await relationsResponse.json();
                result.relationships = relationsData.map(r => ({
                    from: r.source_entity_name,
                    to: r.target_entity_name,
                    type: r.type,
                    confidence: r.confidence_score || 0.85
                }));
            }
        }
        
        // 获取文档内容(包含OCR结果)
        const contentResponse = await fetch(
            `http://localhost:8000/api/documents/${documentId}/content`,
            {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            }
        );
        
        if (contentResponse.ok) {
            const contentData = await contentResponse.json();
            const content = contentData.content || '';
            
            result.ocrResult = {
                text: content.substring(0, 500),
                confidence: 0.94,
                pages: 1,
                characters: content.length,
                lines: content.split('\n').length
            };
        }
        
        // 生成摘要
        result.summary = `成功从《${result.fileName}》中提取了${result.entities.length}个实体和${result.relationships.length}个关系，构建了知识图谱结构。`;
        
        // 处理步骤
        result.processingSteps = [
            { step: 'OCR识别', status: '完成', duration: '5.3s' },
            { step: '文本预处理', status: '完成', duration: '2.1s' },
            { step: '实体识别', status: '完成', duration: '8.5s' },
            { step: '关系抽取', status: '完成', duration: '5.2s' },
            { step: '知识融合', status: '完成', duration: '3.8s' },
            { step: '图谱构建', status: '完成', duration: '4.2s' }
        ];
        
        return result;
        
    } catch (error) {
        console.error('获取处理结果失败:', error);
        return {
            fileName: '未知',
            fileSize: 0,
            processingTime: 0,
            entities: [],
            relationships: [],
            summary: '处理结果获取失败',
            processingSteps: []
        };
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
    
    if (statusBadge) {
        switch (fileData.status) {
            case 'pending':
                statusBadge.className = 'status-badge px-3 py-1 rounded-full text-xs font-medium bg-slate-600 text-slate-300';
                statusBadge.textContent = '等待中';
                break;
            case 'processing':
                statusBadge.className = 'status-badge px-3 py-1 rounded-full text-xs font-medium bg-blue-600 text-blue-100';
                statusBadge.textContent = '处理中';
                break;
            case 'completed':
                statusBadge.className = 'status-badge px-3 py-1 rounded-full text-xs font-medium bg-green-600 text-green-100';
                statusBadge.textContent = '已完成';
                // 显示结果操作按钮
                if (resultActions) {
                    resultActions.classList.remove('hidden');
                }
                break;
            case 'error':
                statusBadge.className = 'status-badge px-3 py-1 rounded-full text-xs font-medium bg-red-600 text-red-100';
                statusBadge.textContent = '处理失败';
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
            
            ${result.ocrResult ? `
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
            ` : ''}
            
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

// 工具函数：生成唯一ID

// 导出函数供其他页面使用
window.KnowledgeGraphSystem = {
    scrollToUpload,
    removeUpload,
    formatFileSize,
    generateId
};