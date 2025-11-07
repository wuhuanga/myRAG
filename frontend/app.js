// ============================================
// 全局状态
// ============================================

let API_BASE_URL = 'http://localhost:8000/api';
let currentInstances = [];

// ============================================
// 工具函数
// ============================================

function getApiUrl() {
    const input = document.getElementById('apiUrl');
    return input ? input.value.trim() + '/api' : API_BASE_URL;
}

function showLoading(show = true) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.toggle('active', show);
    }
}

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;

    notification.textContent = message;
    notification.className = `notification ${type} show`;

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

async function apiRequest(endpoint, options = {}) {
    showLoading(true);
    try {
        const url = `${getApiUrl()}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || data.message || '请求失败');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    } finally {
        showLoading(false);
    }
}

// ============================================
// Tab 切换
// ============================================

function showTab(tabId) {
    // 隐藏所有 tab
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // 移除所有按钮的 active 状态
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // 显示选中的 tab
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // 激活对应的按钮
    event.target.classList.add('active');

    // 如果切换到实例管理，刷新实例列表
    if (tabId === 'instances') {
        loadInstances();
    }
}

function showSubTab(subTabId) {
    // 隐藏所有子 tab
    document.querySelectorAll('.sub-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // 移除所有子按钮的 active 状态
    document.querySelectorAll('.sub-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // 显示选中的子 tab
    const selectedSubTab = document.getElementById(subTabId);
    if (selectedSubTab) {
        selectedSubTab.classList.add('active');
    }

    // 激活对应的按钮
    event.target.classList.add('active');
}

// ============================================
// API 状态检查
// ============================================

async function checkApiStatus() {
    try {
        const data = await apiRequest('/admin/health');
        const statusBadge = document.getElementById('apiStatus');
        if (statusBadge) {
            statusBadge.textContent = '已连接';
            statusBadge.classList.add('connected');
            statusBadge.classList.remove('error');
        }
        showNotification('API 连接成功', 'success');
        loadInstances();
    } catch (error) {
        const statusBadge = document.getElementById('apiStatus');
        if (statusBadge) {
            statusBadge.textContent = '连接失败';
            statusBadge.classList.add('error');
            statusBadge.classList.remove('connected');
        }
        showNotification(`连接失败: ${error.message}`, 'error');
    }
}

// ============================================
// 实例管理
// ============================================

async function loadInstances() {
    try {
        const data = await apiRequest('/admin/rag_instances');
        currentInstances = data.instances || [];

        // 更新实例列表显示
        const container = document.getElementById('instancesList');
        if (!container) return;

        if (currentInstances.length === 0) {
            container.innerHTML = '<p class="text-muted">暂无实例，请先创建一个 RAG 实例。</p>';
            return;
        }

        container.innerHTML = currentInstances.map(instance => `
            <div class="instance-card">
                <h3>${instance.rag_id}</h3>
                <div class="instance-info">
                    <div class="instance-info-item">
                        <strong>Workspace:</strong>
                        <span>${instance.workspace || '-'}</span>
                    </div>
                    <div class="instance-info-item">
                        <strong>工作目录:</strong>
                        <span>${instance.working_dir}</span>
                    </div>
                    <div class="instance-info-item">
                        <strong>LLM:</strong>
                        <span>${instance.llm_model}</span>
                    </div>
                    <div class="instance-info-item">
                        <strong>Embedding:</strong>
                        <span>${instance.embedding_model}</span>
                    </div>
                    <div class="instance-info-item">
                        <strong>创建时间:</strong>
                        <span>${new Date(instance.created_at).toLocaleString('zh-CN')}</span>
                    </div>
                </div>
                <div class="instance-actions">
                    <button class="btn-primary" onclick="selectInstance('${instance.rag_id}')">选择</button>
                    <button class="btn-danger" onclick="deleteInstance('${instance.rag_id}')">删除</button>
                </div>
            </div>
        `).join('');

        // 更新下拉选择框
        updateInstanceSelects();
    } catch (error) {
        showNotification(`加载实例失败: ${error.message}`, 'error');
    }
}

function updateInstanceSelects() {
    const selects = ['docRagId', 'queryRagId', 'graphRagId'];

    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (!select) return;

        const currentValue = select.value;
        select.innerHTML = currentInstances.length > 0
            ? `<option value="">请选择实例</option>` +
              currentInstances.map(inst =>
                  `<option value="${inst.rag_id}">${inst.rag_id} (${inst.workspace})</option>`
              ).join('')
            : '<option value="">暂无实例，请先创建</option>';

        // 恢复之前的选择
        if (currentValue) {
            select.value = currentValue;
        }
    });
}

function selectInstance(ragId) {
    // 切换到文档操作 tab 并选择该实例
    document.getElementById('docRagId').value = ragId;
    document.getElementById('queryRagId').value = ragId;
    document.getElementById('graphRagId').value = ragId;

    showNotification(`已选择实例: ${ragId}`, 'success');

    // 切换到文档 tab
    showTab('documents');
    document.querySelector('.tab-button:nth-child(2)').classList.add('active');
}

async function deleteInstance(ragId) {
    if (!confirm(`确定要删除实例 "${ragId}" 吗？此操作不可撤销。`)) {
        return;
    }

    try {
        await apiRequest(`/admin/rag_instances/${ragId}`, {
            method: 'DELETE',
        });
        showNotification(`实例 ${ragId} 已删除`, 'success');
        loadInstances();
    } catch (error) {
        showNotification(`删除失败: ${error.message}`, 'error');
    }
}

// ============================================
// 文档操作
// ============================================

async function uploadDocument(file, ragId, customId) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('rag_id', ragId);
    if (customId) {
        formData.append('custom_id', customId);
    }

    showLoading(true);
    try {
        const response = await fetch(`${getApiUrl()}/documents/upload`, {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || '上传失败');
        }

        return data;
    } finally {
        showLoading(false);
    }
}

async function insertText(ragId, content, docId, filePath) {
    return await apiRequest('/documents/insert', {
        method: 'POST',
        body: JSON.stringify({
            rag_id: ragId,
            content: content,
            doc_id: docId || undefined,
            file_path: filePath || 'manual_input.txt',
        }),
    });
}

async function loadDocStatus() {
    const ragId = document.getElementById('docRagId').value;
    if (!ragId) {
        showNotification('请先选择 RAG 实例', 'warning');
        return;
    }

    try {
        const data = await apiRequest(`/documents/status/${ragId}`);
        const container = document.getElementById('docStatus');
        if (!container) return;

        container.innerHTML = `
            <div class="instance-info">
                <div class="instance-info-item">
                    <strong>总文档数:</strong>
                    <span>${data.total_docs || 0}</span>
                </div>
                <div class="instance-info-item">
                    <strong>总实体数:</strong>
                    <span>${data.total_entities || 0}</span>
                </div>
                <div class="instance-info-item">
                    <strong>总关系数:</strong>
                    <span>${data.total_relations || 0}</span>
                </div>
                <div class="instance-info-item">
                    <strong>总文本块:</strong>
                    <span>${data.total_chunks || 0}</span>
                </div>
            </div>
        `;
    } catch (error) {
        showNotification(`获取状态失败: ${error.message}`, 'error');
    }
}

// ============================================
// 查询操作
// ============================================

async function performQuery(ragId, question, options) {
    return await apiRequest('/query', {
        method: 'POST',
        body: JSON.stringify({
            rag_id: ragId,
            question: question,
            mode: options.mode || 'hybrid',
            only_need_context: options.only_need_context !== false,
            top_k: parseInt(options.top_k) || 20,
            chunk_top_k: parseInt(options.chunk_top_k) || 10,
        }),
    });
}

// ============================================
// 图操作
// ============================================

async function createEntity(ragId, entityName, entityType, description) {
    return await apiRequest('/entities/create', {
        method: 'POST',
        body: JSON.stringify({
            rag_id: ragId,
            entity_name: entityName,
            entity_type: entityType || 'unknown',
            description: description || '',
            source_id: 'manual_creation',
            file_path: 'manual',
        }),
    });
}

async function getEntity(ragId, entityName) {
    return await apiRequest('/entities/info', {
        method: 'POST',
        body: JSON.stringify({
            rag_id: ragId,
            entity_name: entityName,
        }),
    });
}

async function createRelation(ragId, srcEntity, tgtEntity, description) {
    return await apiRequest('/relations/create', {
        method: 'POST',
        body: JSON.stringify({
            rag_id: ragId,
            src_entity: srcEntity,
            tgt_entity: tgtEntity,
            description: description || '',
            source_id: 'manual_creation',
        }),
    });
}

async function getRelation(ragId, srcEntity, tgtEntity) {
    return await apiRequest('/relations/info', {
        method: 'POST',
        body: JSON.stringify({
            rag_id: ragId,
            src_entity: srcEntity,
            tgt_entity: tgtEntity,
        }),
    });
}

async function exportData(format) {
    const ragId = document.getElementById('graphRagId').value;
    if (!ragId) {
        showNotification('请先选择 RAG 实例', 'warning');
        return;
    }

    try {
        showLoading(true);
        const url = `${getApiUrl()}/export/${ragId}?format=${format}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('导出失败');
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `${ragId}_export.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);

        showNotification(`导出成功: ${ragId}_export.${format}`, 'success');
    } catch (error) {
        showNotification(`导出失败: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================
// 表单处理
// ============================================

// 创建实例表单
document.getElementById('createInstanceForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const ragId = document.getElementById('ragId').value.trim();
    const workspace = document.getElementById('workspace').value.trim();
    const workingDir = document.getElementById('workingDir').value.trim();
    const llmModel = document.getElementById('llmModel').value.trim();
    const embeddingModel = document.getElementById('embeddingModel').value.trim();
    const vectorStorage = document.getElementById('vectorStorage').value;
    const graphStorage = document.getElementById('graphStorage').value;

    if (!ragId || !workspace) {
        showNotification('RAG ID 和 Workspace 为必填项', 'warning');
        return;
    }

    try {
        await apiRequest('/admin/rag_instances', {
            method: 'POST',
            body: JSON.stringify({
                rag_id: ragId,
                workspace: workspace,
                working_dir: workingDir || './rag_storage',
                llm_model: llmModel || undefined,
                embedding_model: embeddingModel || undefined,
                vector_storage: vectorStorage || undefined,
                graph_storage: graphStorage || undefined,
            }),
        });

        showNotification(`实例 ${ragId} 创建成功`, 'success');
        e.target.reset();
        loadInstances();
    } catch (error) {
        showNotification(`创建失败: ${error.message}`, 'error');
    }
});

// 上传文档表单
document.getElementById('uploadForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const ragId = document.getElementById('docRagId').value;
    const fileInput = document.getElementById('fileInput');
    const customId = document.getElementById('customDocId').value.trim();

    if (!ragId) {
        showNotification('请先选择 RAG 实例', 'warning');
        return;
    }

    if (!fileInput.files.length) {
        showNotification('请选择文件', 'warning');
        return;
    }

    try {
        const result = await uploadDocument(fileInput.files[0], ragId, customId);
        showNotification('文档上传并索引成功', 'success');
        e.target.reset();
        loadDocStatus();
    } catch (error) {
        showNotification(`上传失败: ${error.message}`, 'error');
    }
});

// 插入文本表单
document.getElementById('insertTextForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const ragId = document.getElementById('docRagId').value;
    const content = document.getElementById('textContent').value.trim();
    const docId = document.getElementById('textDocId').value.trim();
    const filePath = document.getElementById('textFilePath').value.trim();

    if (!ragId) {
        showNotification('请先选择 RAG 实例', 'warning');
        return;
    }

    if (!content) {
        showNotification('请输入文本内容', 'warning');
        return;
    }

    try {
        await insertText(ragId, content, docId, filePath);
        showNotification('文本插入成功', 'success');
        e.target.reset();
        loadDocStatus();
    } catch (error) {
        showNotification(`插入失败: ${error.message}`, 'error');
    }
});

// 查询表单
document.getElementById('queryForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const ragId = document.getElementById('queryRagId').value;
    const question = document.getElementById('queryQuestion').value.trim();
    const mode = document.getElementById('queryMode').value;
    const onlyContext = document.getElementById('onlyContext').checked;
    const topK = document.getElementById('topK').value;
    const chunkTopK = document.getElementById('chunkTopK').value;

    if (!ragId) {
        showNotification('请先选择 RAG 实例', 'warning');
        return;
    }

    if (!question) {
        showNotification('请输入查询问题', 'warning');
        return;
    }

    try {
        const result = await performQuery(ragId, question, {
            mode,
            only_need_context: onlyContext,
            top_k: topK,
            chunk_top_k: chunkTopK,
        });

        const container = document.getElementById('queryResult');
        if (container) {
            container.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        }
        showNotification('查询完成', 'success');
    } catch (error) {
        showNotification(`查询失败: ${error.message}`, 'error');
    }
});

// 创建实体表单
document.getElementById('createEntityForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const ragId = document.getElementById('graphRagId').value;
    const entityName = document.getElementById('entityName').value.trim();
    const entityType = document.getElementById('entityType').value.trim();
    const description = document.getElementById('entityDescription').value.trim();

    if (!ragId || !entityName) {
        showNotification('请选择实例并输入实体名称', 'warning');
        return;
    }

    try {
        await createEntity(ragId, entityName, entityType, description);
        showNotification(`实体 ${entityName} 创建成功`, 'success');
        e.target.reset();
    } catch (error) {
        showNotification(`创建失败: ${error.message}`, 'error');
    }
});

// 查询实体表单
document.getElementById('getEntityForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const ragId = document.getElementById('graphRagId').value;
    const entityName = document.getElementById('getEntityName').value.trim();

    if (!ragId || !entityName) {
        showNotification('请选择实例并输入实体名称', 'warning');
        return;
    }

    try {
        const result = await getEntity(ragId, entityName);
        const container = document.getElementById('entityResult');
        if (container) {
            container.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        }
    } catch (error) {
        showNotification(`查询失败: ${error.message}`, 'error');
    }
});

// 创建关系表单
document.getElementById('createRelationForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const ragId = document.getElementById('graphRagId').value;
    const srcEntity = document.getElementById('srcEntity').value.trim();
    const tgtEntity = document.getElementById('tgtEntity').value.trim();
    const description = document.getElementById('relationDescription').value.trim();

    if (!ragId || !srcEntity || !tgtEntity) {
        showNotification('请选择实例并输入源实体和目标实体', 'warning');
        return;
    }

    try {
        await createRelation(ragId, srcEntity, tgtEntity, description);
        showNotification(`关系创建成功: ${srcEntity} -> ${tgtEntity}`, 'success');
        e.target.reset();
    } catch (error) {
        showNotification(`创建失败: ${error.message}`, 'error');
    }
});

// 查询关系表单
document.getElementById('getRelationForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const ragId = document.getElementById('graphRagId').value;
    const srcEntity = document.getElementById('getSrcEntity').value.trim();
    const tgtEntity = document.getElementById('getTgtEntity').value.trim();

    if (!ragId || !srcEntity || !tgtEntity) {
        showNotification('请选择实例并输入源实体和目标实体', 'warning');
        return;
    }

    try {
        const result = await getRelation(ragId, srcEntity, tgtEntity);
        const container = document.getElementById('relationResult');
        if (container) {
            container.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        }
    } catch (error) {
        showNotification(`查询失败: ${error.message}`, 'error');
    }
});

// ============================================
// 初始化
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // 检查 API 连接
    checkApiStatus();
});
