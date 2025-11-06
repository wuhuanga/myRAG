import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// API 配置 - 修改这里的 IP 地址为你的服务器 IP
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// 图标组件
const Icon = ({ name }) => {
  const icons = {
    upload: '📤',
    message: '💬',
    settings: '⚙️',
    database: '🗄️',
    send: '📨',
    file: '📄',
    close: '❌',
    check: '✅',
    alert: '⚠️',
    loading: '⏳',
    model: '🎨'
  };
  return <span className="icon">{icons[name]}</span>;
};

function App() {
  // 状态管理
  const [activeTab, setActiveTab] = useState('query');
  const [initialized, setInitialized] = useState(false);
  const [ucdInitialized, setUcdInitialized] = useState(false);
  const [loading, setLoading] = useState(false);
  const [serverOnline, setServerOnline] = useState(false);
  const [status, setStatus] = useState(null);
  
  // 配置
  const [workingDir, setWorkingDir] = useState('./index_default');
  
  // 查询相关
  const [question, setQuestion] = useState('');
  const [queryMode, setQueryMode] = useState('hybrid');
  const [queryType, setQueryType] = useState('normal'); // 'normal' 或 'ucd'
  const [outputJson, setOutputJson] = useState('output_uc.json');
  const [chatHistory, setChatHistory] = useState([]);
  const [querying, setQuerying] = useState(false);
  
  // 上传相关
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  
  // 文档管理相关
  const [docStatus, setDocStatus] = useState(null);
  const [docList, setDocList] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('PROCESSED');
  const [selectedDoc, setSelectedDoc] = useState(null);
  
  const chatEndRef = useRef(null);

  // 检查系统状态
  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // 检查状态
  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/status`);
      const data = await response.json();
      setStatus(data);
      setInitialized(data.initialized);
      setUcdInitialized(data.ucd_initialized);
      setServerOnline(true);
    } catch (error) {
      console.error('检查状态失败:', error);
      setServerOnline(false);
      setStatus(null);
    }
  };

  // 初始化系统
  const handleInitialize = async () => {
    if (!workingDir.trim()) {
      alert('请输入工作目录');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/initialize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ working_dir: workingDir })
      });

      const data = await response.json();
      
      if (response.ok) {
        setInitialized(true);
        setUcdInitialized(data.ucd_enabled);
        alert(`系统初始化成功！\n\n配置信息：\nLLM: ${data.config.llm_model}\nEmbedding: ${data.config.embedding_model}\n维度: ${data.config.embedding_dim}\nUCD建模: ${data.ucd_enabled ? '已启用' : '未启用'}`);
        await checkStatus();
        setActiveTab('query');
      } else {
        alert(`初始化失败: ${data.detail}`);
      }
    } catch (error) {
      alert(`初始化失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 处理文件上传
  const handleFileUpload = async () => {
    if (!uploadFile) {
      alert('请选择文件');
      return;
    }

    if (!initialized) {
      alert('请先初始化系统');
      return;
    }

    setUploading(true);
    setUploadStatus('正在上传...');

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setUploadStatus('✅ 上传成功！');
        setTimeout(() => {
          setUploadFile(null);
          setUploadStatus('');
        }, 2000);
      } else {
        setUploadStatus(`❌ 上传失败: ${data.detail}`);
      }
    } catch (error) {
      setUploadStatus(`❌ 上传失败: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  // 处理查询
  const handleQuery = async () => {
    if (!question.trim()) return;

    if (!initialized) {
      alert('请先初始化系统');
      return;
    }

    if (queryType === 'ucd' && !ucdInitialized) {
      alert('UCD建模功能未启用');
      return;
    }

    const userMessage = {
      type: 'user',
      content: question,
      timestamp: new Date().toLocaleTimeString()
    };

    setChatHistory(prev => [...prev, userMessage]);
    setQuestion('');
    setQuerying(true);

    try {
      let endpoint = queryType === 'ucd' ? '/api/query_ucd' : '/api/query';
      let body = {
        question: question,
        mode: queryMode
      };

      if (queryType === 'ucd') {
        body.out_json = outputJson;
      }

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      let botMessage;
      if (queryType === 'ucd') {
        // UCD 查询结果
        botMessage = {
          type: 'bot',
          content: data.context || '检索内容为空',
          ucdModel: data.ucd_model,
          outputFile: data.output_file,
          mode: data.mode,
          timestamp: new Date().toLocaleTimeString(),
          isUcd: true
        };
      } else {
        // 普通查询结果
        botMessage = {
          type: 'bot',
          content: data.context || '检索内容为空',
          mode: data.mode,
          timestamp: new Date().toLocaleTimeString(),
          isUcd: false
        };
      }

      setChatHistory(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: `查询失败: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setQuerying(false);
    }
  };

  // 键盘事件
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleQuery();
    }
  };

  // 获取文档状态统计
  const fetchDocumentStatus = async () => {
    if (!initialized) return;
    
    setLoadingDocs(true);
    try {
      const response = await fetch(`${API_BASE}/api/documents/status`);
      const data = await response.json();
      setDocStatus(data);
    } catch (error) {
      console.error('获取文档状态失败:', error);
      setDocStatus(null);
    } finally {
      setLoadingDocs(false);
    }
  };

  // 获取指定状态的文档列表
  const fetchDocumentList = async (status) => {
    if (!initialized) return;
    
    setLoadingDocs(true);
    try {
      const response = await fetch(`${API_BASE}/api/documents/list/${status}`);
      const data = await response.json();
      setDocList(data.documents);
    } catch (error) {
      console.error('获取文档列表失败:', error);
      setDocList([]);
    } finally {
      setLoadingDocs(false);
    }
  };

  // 查看文档详情
  const viewDocument = (doc) => {
    setSelectedDoc(doc);
  };

  // 关闭文档详情
  const closeDocumentView = () => {
    setSelectedDoc(null);
  };

  return (
    <div className="App">
      <div className="container">
        {/* Header */}
        <header className="header">
          <h1><Icon name="database" /> lightrag + UCD_RAG 系统</h1>
          <p>基于 Neo4j 和 Faiss 的智能 RAG 系统 + UCD 建模</p>
        </header>

        {/* Status Bar */}
        <div className="status-bar">
          <div className="status-left">
            <div className="status-item">
              <span className={`indicator ${serverOnline ? 'online' : 'offline'}`}></span>
              <span className={serverOnline ? 'text-success' : 'text-error'}>
                {serverOnline ? '服务器在线' : '服务器离线'}
              </span>
            </div>
            <div className="divider"></div>
            <div className="status-item">
              <Icon name={initialized ? 'check' : 'alert'} />
              <span className={initialized ? 'text-success' : 'text-warning'}>
                {initialized ? 'RAG已就绪' : 'RAG未初始化'}
              </span>
            </div>
            <div className="divider"></div>
            <div className="status-item">
              <Icon name={ucdInitialized ? 'check' : 'alert'} />
              <span className={ucdInitialized ? 'text-success' : 'text-warning'}>
                {ucdInitialized ? 'UCD已启用' : 'UCD未启用'}
              </span>
            </div>
          </div>
          <div className="status-right">
            {status?.working_dir && (
              <span className="text-muted">工作目录: {status.working_dir}</span>
            )}
            <button onClick={checkStatus} className="btn-refresh">刷新</button>
          </div>
        </div>

        {!serverOnline && (
          <div className="alert alert-error">
            <p><strong>⚠️ 无法连接到后端服务器</strong></p>
            <p>请确保后端服务已启动：</p>
            <code>uvicorn backend_api:app --host 0.0.0.0 --port 8000 --reload</code>
          </div>
        )}

        {/* Main Content */}
        <div className="main-content">
          {/* Tabs */}
          <div className="tabs">
            <button 
              className={`tab ${activeTab === 'query' ? 'active' : ''}`}
              onClick={() => setActiveTab('query')}
            >
              <Icon name="message" /> 查询
            </button>
            <button 
              className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => setActiveTab('upload')}
            >
              <Icon name="upload" /> 上传文档
            </button>
            <button 
              className={`tab ${activeTab === 'documents' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('documents');
                fetchDocumentStatus();
              }}
            >
              <Icon name="file" /> 文档管理
            </button>
            <button 
              className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              <Icon name="settings" /> 系统配置
            </button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {/* Query Tab */}
            {activeTab === 'query' && (
              <div className="query-container">
                {!initialized ? (
                  <div className="empty-state">
                    <Icon name="alert" />
                    <p>请先在"系统配置"中初始化系统</p>
                    <button onClick={() => setActiveTab('settings')} className="btn-primary">
                      前往配置
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="chat-history">
                      {chatHistory.length === 0 ? (
                        <div className="empty-state">
                          <Icon name="message" />
                          <p>开始提问吧！</p>
                        </div>
                      ) : (
                        chatHistory.map((msg, idx) => (
                          <div key={idx} className={`message message-${msg.type}`}>
                            <div className="message-content">
                              <div className="message-time">{msg.timestamp}</div>
                              <div className="message-text">{msg.content}</div>
                              {msg.mode && (
                                <div className="message-mode">模式: {msg.mode}</div>
                              )}
                              {msg.isUcd && msg.ucdModel && (
                                <div className="ucd-result">
                                  <div className="ucd-badge">
                                    <Icon name="model" /> UCD 建模结果
                                  </div>
                                  <pre className="ucd-json">
                                    {JSON.stringify(msg.ucdModel, null, 2)}
                                  </pre>
                                  <div className="ucd-file">
                                    📁 输出文件: {msg.outputFile}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                      {querying && (
                        <div className="message message-bot">
                          <div className="message-content">
                            <div className="loading">
                              <Icon name="loading" /> {queryType === 'ucd' ? '正在检索并进行UCD建模...' : '正在检索...'}
                            </div>
                          </div>
                        </div>
                      )}
                      <div ref={chatEndRef} />
                    </div>

                    <div className="query-controls">
                      <div className="query-mode">
                        <label>查询类型:</label>
                        <select value={queryType} onChange={(e) => setQueryType(e.target.value)}>
                          <option value="normal">普通查询</option>
                          <option value="ucd" disabled={!ucdInitialized}>
                            UCD建模查询 {!ucdInitialized && '(未启用)'}
                          </option>
                        </select>
                      </div>

                      <div className="query-mode">
                        <label>检索模式:</label>
                        <select value={queryMode} onChange={(e) => setQueryMode(e.target.value)}>
                          <option value="hybrid">混合模式 (Hybrid)</option>
                          <option value="naive">简单模式 (Naive)</option>
                          <option value="local">本地模式 (Local)</option>
                          <option value="global">全局模式 (Global)</option>
                        </select>
                      </div>

                      {queryType === 'ucd' && (
                        <div className="query-mode">
                          <label>输出文件:</label>
                          <input
                            type="text"
                            value={outputJson}
                            onChange={(e) => setOutputJson(e.target.value)}
                            placeholder="output_uc.json"
                            className="output-json-input"
                          />
                        </div>
                      )}
                    </div>

                    <div className="query-input">
                      <textarea
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={handleKeyPress}
                        placeholder="输入您的问题... (Ctrl+Enter 发送)"
                        rows="3"
                      />
                      <button 
                        onClick={handleQuery}
                        disabled={querying || !question.trim()}
                        className="btn-primary"
                      >
                        {querying ? <Icon name="loading" /> : <Icon name="send" />}
                        发送
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Upload Tab */}
            {activeTab === 'upload' && (
              <div className="upload-container">
                {!initialized ? (
                  <div className="empty-state">
                    <Icon name="alert" />
                    <p>请先初始化系统</p>
                  </div>
                ) : (
                  <>
                    <div className="file-drop-zone">
                      <Icon name="file" />
                      <input
                        type="file"
                        onChange={(e) => setUploadFile(e.target.files[0])}
                        accept=".pdf,.docx,.doc,.txt,.rtf"
                        style={{ display: 'none' }}
                        id="file-input"
                      />
                      <label htmlFor="file-input" className="btn-primary">
                        选择文件
                      </label>
                      <p className="text-muted">支持格式: PDF, DOCX, DOC, TXT, RTF</p>
                    </div>

                    {uploadFile && (
                      <div className="file-preview">
                        <div className="file-info">
                          <Icon name="file" />
                          <span>{uploadFile.name}</span>
                          <button onClick={() => setUploadFile(null)} className="btn-close">
                            <Icon name="close" />
                          </button>
                        </div>
                        <button
                          onClick={handleFileUpload}
                          disabled={uploading}
                          className="btn-primary btn-block"
                        >
                          {uploading ? (
                            <>
                              <Icon name="loading" /> 上传中...
                            </>
                          ) : (
                            <>
                              <Icon name="upload" /> 上传文档
                            </>
                          )}
                        </button>
                      </div>
                    )}

                    {uploadStatus && (
                      <div className={`alert ${uploadStatus.includes('成功') ? 'alert-success' : 'alert-error'}`}>
                        {uploadStatus}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Documents Tab */}
            {activeTab === 'documents' && (
              <div className="documents-container">
                {!initialized ? (
                  <div className="empty-state">
                    <Icon name="alert" />
                    <p>请先初始化系统</p>
                  </div>
                ) : (
                  <>
                    {/* 文档状态统计 */}
                    {docStatus && (
                      <div className="doc-stats">
                        <div className="stat-card">
                          <div className="stat-value">{docStatus.total}</div>
                          <div className="stat-label">总文档数</div>
                        </div>
                        <div className="stat-card stat-success">
                          <div className="stat-value">{docStatus.processed}</div>
                          <div className="stat-label">已处理</div>
                        </div>
                        <div className="stat-card stat-warning">
                          <div className="stat-value">{docStatus.pending}</div>
                          <div className="stat-label">待处理</div>
                        </div>
                        <div className="stat-card stat-error">
                          <div className="stat-value">{docStatus.failed}</div>
                          <div className="stat-label">处理失败</div>
                        </div>
                      </div>
                    )}

                    {/* 状态选择器 */}
                    <div className="doc-controls">
                      <div className="doc-filter">
                        <label>查看文档状态:</label>
                        <select 
                          value={selectedStatus} 
                          onChange={(e) => {
                            setSelectedStatus(e.target.value);
                            fetchDocumentList(e.target.value);
                          }}
                        >
                          <option value="PROCESSED">已处理</option>
                          <option value="PENDING">待处理</option>
                          <option value="FAILED">处理失败</option>
                        </select>
                      </div>
                      <button 
                        onClick={() => {
                          fetchDocumentStatus();
                          fetchDocumentList(selectedStatus);
                        }}
                        className="btn-secondary"
                        disabled={loadingDocs}
                      >
                        {loadingDocs ? <Icon name="loading" /> : '刷新'}
                      </button>
                    </div>

                    {/* 文档列表 */}
                    <div className="doc-list">
                      {loadingDocs ? (
                        <div className="loading-state">
                          <Icon name="loading" />
                          <p>加载中...</p>
                        </div>
                      ) : docList.length === 0 ? (
                        <div className="empty-state">
                          <Icon name="file" />
                          <p>没有找到 {selectedStatus === 'PROCESSED' ? '已处理' : selectedStatus === 'PENDING' ? '待处理' : '失败'} 的文档</p>
                        </div>
                      ) : (
                        docList.map((doc, idx) => (
                          <div key={doc.doc_id || idx} className="doc-item">
                            <div className="doc-preview">
                              <div className="doc-header">
                                <div className="doc-id">文档 ID: {doc.doc_id}</div>
                                <div className="doc-filename">📄 {doc.file_name}</div>
                              </div>
                              {doc.created_at && (
                                <div className="doc-meta">
                                  <span className="meta-item">
                                    📅 创建: {new Date(doc.created_at).toLocaleString('zh-CN')}
                                  </span>
                                  {doc.updated_at && (
                                    <span className="meta-item">
                                      🔄 更新: {new Date(doc.updated_at).toLocaleString('zh-CN')}
                                    </span>
                                  )}
                                </div>
                              )}
                              {doc.error_message && (
                                <div className="doc-error">
                                  ❌ 错误: {doc.error_message}
                                </div>
                              )}
                            </div>
                            <button 
                              onClick={() => viewDocument(doc)}
                              className="btn-view"
                            >
                              查看详情
                            </button>
                          </div>
                        ))
                      )}
                    </div>

                    {/* 文档详情弹窗 */}
                    {selectedDoc && (
                      <div className="modal-overlay" onClick={closeDocumentView}>
                        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                          <div className="modal-header">
                            <h3>文档详情</h3>
                            <button onClick={closeDocumentView} className="btn-close-modal">
                              <Icon name="close" />
                            </button>
                          </div>
                          <div className="modal-body">
                            <div className="doc-detail">
                              <div className="detail-label">文档ID:</div>
                              <div className="detail-value">{selectedDoc.doc_id}</div>
                            </div>
                            <div className="doc-detail">
                              <div className="detail-label">文件名:</div>
                              <div className="detail-value">{selectedDoc.file_name}</div>
                            </div>
                            <div className="doc-detail">
                              <div className="detail-label">状态:</div>
                              <div className="detail-value">
                                <span className={`status-badge ${
                                  selectedDoc.status === 'PROCESSED' ? 'status-success' :
                                  selectedDoc.status === 'PENDING' ? 'status-warning' :
                                  'status-error'
                                }`}>
                                  {selectedDoc.status === 'PROCESSED' ? '✅ 已处理' :
                                   selectedDoc.status === 'PENDING' ? '⏳ 待处理' :
                                   '❌ 失败'}
                                </span>
                              </div>
                            </div>
                            {selectedDoc.created_at && (
                              <div className="doc-detail">
                                <div className="detail-label">创建时间:</div>
                                <div className="detail-value">
                                  {new Date(selectedDoc.created_at).toLocaleString('zh-CN')}
                                </div>
                              </div>
                            )}
                            {selectedDoc.updated_at && (
                              <div className="doc-detail">
                                <div className="detail-label">更新时间:</div>
                                <div className="detail-value">
                                  {new Date(selectedDoc.updated_at).toLocaleString('zh-CN')}
                                </div>
                              </div>
                            )}
                            {selectedDoc.error_message && (
                              <div className="doc-detail">
                                <div className="detail-label">错误信息:</div>
                                <div className="detail-content error-content">
                                  {selectedDoc.error_message}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="settings-container">
                <div className="alert alert-info">
                  <p><strong>📋 配置说明</strong></p>
                  <p>系统将自动从 .env 文件读取以下配置：</p>
                  <ul>
                    <li>LLM_MODEL: DeepSeek Chat</li>
                    <li>EMBEDDING_MODEL: 本地 Qwen3 模型</li>
                    <li>NEO4J_URI: Neo4j 连接地址</li>
                  </ul>
                </div>

                <div className="form-group">
                  <label>
                    工作目录 <span className="text-error">*</span>
                  </label>
                  <input
                    type="text"
                    value={workingDir}
                    onChange={(e) => setWorkingDir(e.target.value)}
                    placeholder="./index_default"
                  />
                  <p className="text-muted">💡 用于存储知识图谱数据的目录（自动创建）</p>
                </div>

                <div className="form-actions">
                  <button
                    onClick={handleInitialize}
                    disabled={loading || !workingDir.trim()}
                    className="btn-primary btn-block"
                  >
                    {loading ? (
                      <>
                        <Icon name="loading" /> 初始化中...
                      </>
                    ) : (
                      <>
                        <Icon name="database" /> 初始化系统
                      </>
                    )}
                  </button>
                  <button onClick={checkStatus} className="btn-secondary">
                    刷新状态
                  </button>
                </div>

                {status && status.llm_model && (
                  <div className="config-info">
                    <h3>当前配置信息：</h3>
                    <div className="config-grid">
                      <div className="config-item">
                        <span className="config-label">LLM 模型</span>
                        <span className="config-value">{status.llm_model}</span>
                      </div>
                      <div className="config-item">
                        <span className="config-label">Embedding 模型</span>
                        <span className="config-value config-value-small">{status.embedding_model}</span>
                      </div>
                      <div className="config-item">
                        <span className="config-label">工作目录</span>
                        <span className="config-value config-value-small">{status.working_dir}</span>
                      </div>
                      <div className="config-item">
                        <span className="config-label">Embedding 维度</span>
                        <span className="config-value">{status.embedding_dim || 'N/A'}</span>
                      </div>
                      <div className="config-item">
                        <span className="config-label">UCD 建模</span>
                        <span className="config-value">
                          {status.ucd_initialized ? (
                            <span className="status-badge status-success">✅ 已启用</span>
                          ) : (
                            <span className="status-badge status-warning">⚠️ 未启用</span>
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="alert alert-info">
                  <p><strong>💡 使用提示：</strong></p>
                  <ul>
                    <li>所有配置都从 .env 文件读取，无需手动输入</li>
                    <li>只需指定工作目录即可开始使用</li>
                    <li>不同项目使用不同的工作目录来隔离数据</li>
                    <li>初始化过程可能需要几分钟（首次加载模型）</li>
                    <li>UCD建模功能需要 UCD_RAG.py 文件，自动检测并启用</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="footer">
          <p>基于 lightrag · Neo4j · Faiss · DeepSeek</p>
        </footer>
      </div>
    </div>
  );
}

export default App;