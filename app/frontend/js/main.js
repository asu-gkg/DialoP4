// DialoP4前端JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // 全局变量
    let conversationId = null;
    let paperAnalysisResult = null;
    let currentCodeResult = null;
    let currentEvaluationResult = null;
    
    // DOM元素
    const messagesContainer = document.getElementById('messagesContainer');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const paperUpload = document.getElementById('paperUpload');
    const uploadButton = document.getElementById('uploadButton');
    const uploadStatus = document.getElementById('uploadStatus');
    const paperAnalysisSection = document.getElementById('paperAnalysisSection');
    const paperAnalysis = document.getElementById('paperAnalysis');
    const generateCodeBtn = document.getElementById('generateCodeBtn');
    const codeOutput = document.getElementById('codeOutput');
    const evaluateCodeBtn = document.getElementById('evaluateCodeBtn');
    const refineCodeBtn = document.getElementById('refineCodeBtn');
    const evaluationOutput = document.getElementById('evaluationOutput');
    
    // 生成唯一会话ID
    conversationId = generateUUID();
    
    // 初始化事件监听器
    initEventListeners();
    
    /**
     * 初始化所有事件监听器
     */
    function initEventListeners() {
        // 发送消息
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // 上传论文
        uploadButton.addEventListener('click', uploadPaper);
        
        // 生成代码
        generateCodeBtn.addEventListener('click', generateCode);
        
        // 评估和优化代码
        evaluateCodeBtn.addEventListener('click', evaluateCode);
        refineCodeBtn.addEventListener('click', refineCode);
    }
    
    /**
     * 发送消息到后端
     */
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // 添加用户消息到界面
        addMessage(message, 'user');
        
        // 清空输入框
        messageInput.value = '';
        
        // 显示加载状态
        const loadingMessageId = addLoadingMessage();
        
        // 发送请求到后端
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId
            })
        })
        .then(response => response.json())
        .then(data => {
            // 移除加载消息
            removeLoadingMessage(loadingMessageId);
            
            // 添加回复
            addMessage(data.response, 'bot');
        })
        .catch(error => {
            console.error('Error:', error);
            removeLoadingMessage(loadingMessageId);
            addMessage('抱歉，发生了错误，请稍后重试。', 'bot');
        });
    }
    
    /**
     * 上传论文到后端
     */
    function uploadPaper() {
        const fileInput = paperUpload;
        const file = fileInput.files[0];
        
        if (!file) {
            uploadStatus.innerHTML = `<div class="alert alert-warning">请先选择PDF文件</div>`;
            return;
        }
        
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            uploadStatus.innerHTML = `<div class="alert alert-danger">请上传PDF格式的文件</div>`;
            return;
        }
        
        // 显示上传中状态
        uploadStatus.innerHTML = `
            <div class="alert alert-info">
                <div class="d-flex align-items-center">
                    <div class="loading me-2"></div>
                    <div>正在上传和分析论文，这可能需要几分钟时间...</div>
                </div>
            </div>
        `;
        
        // 创建FormData对象
        const formData = new FormData();
        formData.append('file', file);
        formData.append('conversation_id', conversationId);
        
        // 发送到后端
        fetch('/api/upload-paper', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                uploadStatus.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            // 保存分析结果
            paperAnalysisResult = data.analysis;
            
            // 更新上传状态
            uploadStatus.innerHTML = `<div class="alert alert-success">论文上传并分析成功！</div>`;
            
            // 显示论文分析结果
            showPaperAnalysis(paperAnalysisResult);
            
            // 添加系统消息
            addMessage(`论文"${paperAnalysisResult.title}"已成功分析。您可以询问有关论文内容的问题，或者生成代码实现。`, 'bot');
        })
        .catch(error => {
            console.error('Error:', error);
            uploadStatus.innerHTML = `<div class="alert alert-danger">上传失败，请稍后重试</div>`;
        });
    }
    
    /**
     * 显示论文分析结果
     */
    function showPaperAnalysis(analysis) {
        // 显示分析部分
        paperAnalysisSection.style.display = 'block';
        
        // 创建分析内容HTML
        let html = `
            <h6>${analysis.title}</h6>
            <p><small>作者：${analysis.authors.join(', ')}</small></p>
            <div class="mt-3">
                <strong>摘要：</strong>
                <p>${analysis.summary}</p>
            </div>
            <div class="mt-2">
                <button class="btn btn-sm btn-outline-primary" type="button" data-bs-toggle="collapse" data-bs-target="#analysisDetails">
                    显示详细分析
                </button>
            </div>
            <div class="collapse mt-2" id="analysisDetails">
                <div class="card card-body">
                    <h6>关键概念</h6>
                    <p>${analysis.analysis.concepts.key_concepts}</p>
                    
                    <h6>创新点</h6>
                    <p>${analysis.analysis.concepts.innovations}</p>
                    
                    <h6>系统架构</h6>
                    <p>${analysis.analysis.architecture.overview}</p>
                </div>
            </div>
        `;
        
        paperAnalysis.innerHTML = html;
    }
    
    /**
     * 生成代码实现
     */
    function generateCode() {
        if (!paperAnalysisResult) {
            codeOutput.innerHTML = `<div class="alert alert-warning">请先上传并分析论文</div>`;
            return;
        }
        
        // 获取选中的代码类型
        const codeType = document.querySelector('input[name="codeType"]:checked').value;
        
        // 显示加载状态
        codeOutput.innerHTML = `
            <div class="alert alert-info">
                <div class="d-flex align-items-center">
                    <div class="loading me-2"></div>
                    <div>正在生成${codeType.toUpperCase()}代码，这可能需要几分钟时间...</div>
                </div>
            </div>
        `;
        
        // 发送请求到后端
        fetch('/api/generate-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                paper_id: paperAnalysisResult.result_id,
                code_type: codeType,
                conversation_id: conversationId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                codeOutput.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            // 保存代码结果
            currentCodeResult = data;
            
            // 显示代码
            displayCode(data, codeType);
        })
        .catch(error => {
            console.error('Error:', error);
            codeOutput.innerHTML = `<div class="alert alert-danger">生成代码失败，请稍后重试</div>`;
        });
    }
    
    /**
     * 显示生成的代码
     */
    function displayCode(codeData, codeType) {
        // 创建HTML内容
        let html = `<h5>${codeData.title} - ${codeType.toUpperCase()}实现</h5>`;
        
        if (codeType === 'python') {
            html += `
                <div class="nav nav-tabs mt-3" id="codeTab" role="tablist">
                    <button class="nav-link active" id="code-full-tab" data-bs-toggle="tab" data-bs-target="#code-full" type="button" role="tab">完整代码</button>
                    <button class="nav-link" id="code-example-tab" data-bs-toggle="tab" data-bs-target="#code-example" type="button" role="tab">使用示例</button>
                    <button class="nav-link" id="code-requirements-tab" data-bs-toggle="tab" data-bs-target="#code-requirements" type="button" role="tab">依赖需求</button>
                </div>
                <div class="tab-content mt-2" id="codeTabContent">
                    <div class="tab-pane fade show active" id="code-full" role="tabpanel">
                        <pre><code class="language-python">${escapeHtml(codeData.implementation.code)}</code></pre>
                    </div>
                    <div class="tab-pane fade" id="code-example" role="tabpanel">
                        <pre><code class="language-python">${escapeHtml(codeData.implementation.usage_example)}</code></pre>
                    </div>
                    <div class="tab-pane fade" id="code-requirements" role="tabpanel">
                        <pre><code>${escapeHtml(codeData.implementation.requirements)}</code></pre>
                    </div>
                </div>
            `;
        } else if (codeType === 'ns3') {
            html += `
                <div class="nav nav-tabs mt-3" id="codeTab" role="tablist">
                    <button class="nav-link active" id="code-full-tab" data-bs-toggle="tab" data-bs-target="#code-full" type="button" role="tab">完整实现</button>
                    <button class="nav-link" id="code-skeleton-tab" data-bs-toggle="tab" data-bs-target="#code-skeleton" type="button" role="tab">代码框架</button>
                    <button class="nav-link" id="code-notes-tab" data-bs-toggle="tab" data-bs-target="#code-notes" type="button" role="tab">实现说明</button>
                </div>
                <div class="tab-content mt-2" id="codeTabContent">
                    <div class="tab-pane fade show active" id="code-full" role="tabpanel">
                        <pre><code class="language-cpp">${escapeHtml(codeData.implementation.code)}</code></pre>
                    </div>
                    <div class="tab-pane fade" id="code-skeleton" role="tabpanel">
                        <pre><code class="language-cpp">${escapeHtml(codeData.skeleton.code)}</code></pre>
                    </div>
                    <div class="tab-pane fade" id="code-notes" role="tabpanel">
                        <div class="markdown-content">${marked.parse(codeData.skeleton.notes)}</div>
                    </div>
                </div>
            `;
        } else if (codeType === 'p4') {
            html += `
                <div class="nav nav-tabs mt-3" id="codeTab" role="tablist">
                    <button class="nav-link active" id="code-full-tab" data-bs-toggle="tab" data-bs-target="#code-full" type="button" role="tab">P4实现</button>
                    <button class="nav-link" id="code-skeleton-tab" data-bs-toggle="tab" data-bs-target="#code-skeleton" type="button" role="tab">代码框架</button>
                    <button class="nav-link" id="code-control-tab" data-bs-toggle="tab" data-bs-target="#code-control" type="button" role="tab">控制平面</button>
                </div>
                <div class="tab-content mt-2" id="codeTabContent">
                    <div class="tab-pane fade show active" id="code-full" role="tabpanel">
                        <pre><code class="language-c">${escapeHtml(codeData.implementation.code)}</code></pre>
                    </div>
                    <div class="tab-pane fade" id="code-skeleton" role="tabpanel">
                        <pre><code class="language-c">${escapeHtml(codeData.skeleton.code)}</code></pre>
                    </div>
                    <div class="tab-pane fade" id="code-control" role="tabpanel">
                        <div class="markdown-content">${marked.parse(codeData.skeleton.control_plane_requirements)}</div>
                        ${codeData.implementation.control_plane_code ? `<pre><code class="language-python">${escapeHtml(codeData.implementation.control_plane_code)}</code></pre>` : ''}
                    </div>
                </div>
            `;
        }
        
        codeOutput.innerHTML = html;
        
        // 高亮代码
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
    
    /**
     * 评估代码实现
     */
    function evaluateCode() {
        if (!currentCodeResult) {
            evaluationOutput.innerHTML = `<div class="alert alert-warning">请先生成代码</div>`;
            return;
        }
        
        // 显示加载状态
        evaluationOutput.innerHTML = `
            <div class="alert alert-info">
                <div class="d-flex align-items-center">
                    <div class="loading me-2"></div>
                    <div>正在评估代码，这可能需要几分钟时间...</div>
                </div>
            </div>
        `;
        
        // 发送请求到后端
        fetch('/api/evaluate-implementation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                paper_id: paperAnalysisResult.result_id,
                code_id: currentCodeResult.result_id,
                conversation_id: conversationId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                evaluationOutput.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            // 保存评估结果
            currentEvaluationResult = data;
            
            // 显示评估结果
            displayEvaluation(data);
        })
        .catch(error => {
            console.error('Error:', error);
            evaluationOutput.innerHTML = `<div class="alert alert-danger">评估代码失败，请稍后重试</div>`;
        });
    }
    
    /**
     * 显示代码评估结果
     */
    function displayEvaluation(evaluationData) {
        // 创建HTML内容
        let html = `
            <h5>${currentCodeResult.title} - ${evaluationData.code_type.toUpperCase()}评估</h5>
            
            <div class="card mt-3">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">正确性评分: ${evaluationData.correctness.score}/10</h6>
                    </div>
                </div>
                <div class="card-body">
                    <h6>分析</h6>
                    <p>${evaluationData.correctness.analysis}</p>
                    
                    <h6>发现的问题</h6>
                    <ul>
        `;
        
        // 添加问题列表
        let issues = evaluationData.correctness.issues;
        if (typeof issues === 'string') {
            issues = issues.split('\n').filter(issue => issue.trim());
        }
        
        issues.forEach(issue => {
            html += `<li>${issue}</li>`;
        });
        
        html += `
                    </ul>
                </div>
            </div>
            
            <div class="card mt-3">
                <div class="card-header">
                    <h6 class="mb-0">性能评估</h6>
                </div>
                <div class="card-body">
                    <p>${evaluationData.performance.estimation}</p>
                    
                    <h6>可能的瓶颈</h6>
                    <ul>
        `;
        
        // 添加瓶颈列表
        let bottlenecks = evaluationData.performance.bottlenecks;
        if (typeof bottlenecks === 'string') {
            bottlenecks = bottlenecks.split('\n').filter(b => b.trim());
        }
        
        bottlenecks.forEach(bottleneck => {
            html += `<li>${bottleneck}</li>`;
        });
        
        html += `
                    </ul>
                    
                    <h6>优化建议</h6>
                    <p>${evaluationData.performance.optimization}</p>
                </div>
            </div>
            
            <div class="card mt-3">
                <div class="card-header">
                    <h6 class="mb-0">改进建议</h6>
                </div>
                <div class="card-body">
                    <h6>需要改进的领域</h6>
                    <p>${evaluationData.improvements.areas}</p>
                    
                    <h6>具体建议</h6>
                    <ul>
        `;
        
        // 添加改进建议
        let suggestions = evaluationData.improvements.suggestions;
        if (typeof suggestions === 'string') {
            suggestions = suggestions.split('\n').filter(s => s.trim());
        }
        
        suggestions.forEach(suggestion => {
            html += `<li>${suggestion}</li>`;
        });
        
        html += `
                    </ul>
                </div>
            </div>
        `;
        
        evaluationOutput.innerHTML = html;
    }
    
    /**
     * 优化代码实现
     */
    function refineCode() {
        if (!currentCodeResult) {
            evaluationOutput.innerHTML = `<div class="alert alert-warning">请先生成代码</div>`;
            return;
        }
        
        // 获取用户反馈
        const userFeedback = prompt('请输入对代码的反馈和要求（可选）:');
        
        // 显示加载状态
        evaluationOutput.innerHTML = `
            <div class="alert alert-info">
                <div class="d-flex align-items-center">
                    <div class="loading me-2"></div>
                    <div>正在优化代码，这可能需要几分钟时间...</div>
                </div>
            </div>
        `;
        
        // 发送请求到后端
        fetch('/api/refine-implementation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                paper_id: paperAnalysisResult.result_id,
                code_id: currentCodeResult.result_id,
                feedback: userFeedback || '',
                conversation_id: conversationId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                evaluationOutput.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            // 显示优化结果
            displayRefinement(data);
        })
        .catch(error => {
            console.error('Error:', error);
            evaluationOutput.innerHTML = `<div class="alert alert-danger">优化代码失败，请稍后重试</div>`;
        });
    }
    
    /**
     * 显示代码优化结果
     */
    function displayRefinement(refinementData) {
        // 获取最后一次迭代的信息
        const lastIteration = refinementData.refinement_history[refinementData.refinement_history.length - 1];
        
        // 创建HTML内容
        let html = `
            <h5>${refinementData.title} - 代码优化</h5>
            
            <div class="card mt-3">
                <div class="card-header">
                    <h6 class="mb-0">优化后的代码</h6>
                </div>
                <div class="card-body">
                    <pre><code class="language-${getLanguageClass(refinementData.code_type)}">${escapeHtml(refinementData.refined_code)}</code></pre>
                </div>
            </div>
            
            <div class="card mt-3">
                <div class="card-header">
                    <h6 class="mb-0">优化评估</h6>
                </div>
                <div class="card-body">
                    <h6>改进评估</h6>
                    <p>${lastIteration.evaluation.improvement_assessment}</p>
                    
                    <h6>主要变更</h6>
                    <p>${lastIteration.changes.changelog}</p>
                    
                    <h6>剩余问题</h6>
                    <p>${lastIteration.evaluation.remaining_issues}</p>
                </div>
            </div>
        `;
        
        evaluationOutput.innerHTML = html;
        
        // 高亮代码
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
    
    /**
     * 添加消息到聊天界面
     */
    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // 将普通文本中的换行符转换为<br>
        const formattedMessage = message.replace(/\n/g, '<br>');
        messageDiv.innerHTML = formattedMessage;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    /**
     * 添加加载消息
     */
    function addLoadingMessage() {
        const id = 'loading-' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.id = id;
        messageDiv.innerHTML = '<div class="loading"></div>';
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return id;
    }
    
    /**
     * 移除加载消息
     */
    function removeLoadingMessage(id) {
        const loadingMessage = document.getElementById(id);
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }
    
    /**
     * 生成UUID
     */
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    /**
     * 转义HTML特殊字符
     */
    function escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
    
    /**
     * 获取代码语言类
     */
    function getLanguageClass(codeType) {
        switch(codeType) {
            case 'python': return 'python';
            case 'ns3': return 'cpp';
            case 'p4': return 'c';
            default: return 'plaintext';
        }
    }
}); 