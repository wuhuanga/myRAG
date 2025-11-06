import React, { useState, useEffect, useRef } from 'react';
import { Upload, MessageSquare, Settings, Database, Send, FileText, Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export default function lightragApp() {
  const [activeTab, setActiveTab] = useState('query');
  const [initialized, setInitialized] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  
  // 初始化配置
  const [config, setConfig] = useState({
    working_dir: './index_default',
    llm_model: '',
    embedding_model: '',
    embedding_dim: '',
    embedding_max_token: '',
    litellm_url: '',
    litellm_key: ''
  });
  
  // 查询相关
  const [question, setQuestion] = useState('');
  const [queryMode, setQueryMode] = useState('hybrid');
  const [chatHistory, setChatHistory] = useState([]);
  const [querying, setQuerying] = useState(false);
  
  // 上传相关
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  
  const chatEndRef = useRef(null);
  const API_BASE = 'http://localhost:8000';

  // 检查系统状态
  useEffect(() => {
    checkStatus();
  }, []);

  // 自动滚动到聊天底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/status`);
      const data = await response.json();
      setStatus(data);
      setInitialized(data.initialized);
    } catch (error) {
      console.error('检查状态失败:', error);
    }
  };

  const handleInitialize = async () => {
    setLoading(true);
    try {
      const payload = {
        working_dir: config.working_dir,
        ...(config.llm_model && { llm_model: config.llm_model }),
        ...(config.embedding_model && { embedding_model: config.embedding_model }),
        ...(config.embedding_dim && { embedding_dim: parseInt(config.embedding_dim) }),
        ...(config.embedding_max_token && { embedding_max_token: parseInt(config.embedding_max_token) }),
        ...(config.litellm_url && { litellm_url: config.litellm_url }),
        ...(config.litellm_key && { litellm_key: config.litellm_key })
      };

      const response = await fetch(`${API_BASE}/api/initialize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      
      if (response.ok) {
        setInitialized(true);
        alert('系统初始化成功！');
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

  const handleFileUpload = async () => {
    if (!uploadFile) {
      alert('请选择文件');
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
        setUploadStatus('上传成功！');
        setTimeout(() => {
          setUploadFile(null);
          setUploadStatus('');
        }, 2000);
      } else {
        setUploadStatus(`上传失败: ${data.detail}`);
      }
    } catch (error) {
      setUploadStatus(`上传失败: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleQuery = async () => {
    if (!question.trim()) return;

    const userMessage = {
      type: 'user',
      content: question,
      timestamp: new Date().toLocaleTimeString()
    };

    setChatHistory(prev => [...prev, userMessage]);
    setQuestion('');
    setQuerying(true);

    try {
      const response = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question,
          mode: queryMode
        })
      });

      const data = await response.json();

      const botMessage = {
        type: 'bot',
        content: data.answer,
        mode: data.mode,
        timestamp: new Date().toLocaleTimeString()
      };

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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <Database className="w-10 h-10 text-purple-400" />
            lightrag 知识图谱系统
          </h1>
          <p className="text-purple-200">基于 Neo4j 和 Faiss 的智能 RAG 系统</p>
        </div>

        {/* Status Bar */}
        <div className="mb-6 bg-slate-800/50 backdrop-blur-sm rounded-lg p-4 border border-purple-500/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {initialized ? (
                <>
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-green-400 font-medium">系统已就绪</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-5 h-5 text-yellow-400" />
                  <span className="text-yellow-400 font-medium">系统未初始化</span>
                </>
              )}
            </div>
            {status?.working_dir && (
              <div className="text-sm text-purple-200">
                工作目录: {status.working_dir}
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-2xl border border-purple-500/20 overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-purple-500/20">
            <button
              onClick={() => setActiveTab('query')}
              className={`flex-1 px-6 py-4 flex items-center justify-center gap-2 transition-all ${
                activeTab === 'query'
                  ? 'bg-purple-600 text-white'
                  : 'text-purple-200 hover:bg-slate-700/50'
              }`}
            >
              <MessageSquare className="w-5 h-5" />
              查询
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex-1 px-6 py-4 flex items-center justify-center gap-2 transition-all ${
                activeTab === 'upload'
                  ? 'bg-purple-600 text-white'
                  : 'text-purple-200 hover:bg-slate-700/50'
              }`}
            >
              <Upload className="w-5 h-5" />
              上传文档
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`flex-1 px-6 py-4 flex items-center justify-center gap-2 transition-all ${
                activeTab === 'settings'
                  ? 'bg-purple-600 text-white'
                  : 'text-purple-200 hover:bg-slate-700/50'
              }`}
            >
              <Settings className="w-5 h-5" />
              系统配置
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* Query Tab */}
            {activeTab === 'query' && (
              <div className="space-y-4">
                {!initialized ? (
                  <div className="text-center py-12">
                    <AlertCircle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
                    <p className="text-purple-200 mb-4">请先在"系统配置"中初始化系统</p>
                    <button
                      onClick={() => setActiveTab('settings')}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      前往配置
                    </button>
                  </div>
                ) : (
                  <>
                    {/* Chat History */}
                    <div className="bg-slate-900/50 rounded-lg p-4 h-96 overflow-y-auto space-y-4">
                      {chatHistory.length === 0 ? (
                        <div className="text-center text-purple-300 py-12">
                          <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                          <p>开始提问吧！</p>
                        </div>
                      ) : (
                        chatHistory.map((msg, idx) => (
                          <div
                            key={idx}
                            className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                          >
                            <div
                              className={`max-w-2xl rounded-lg p-4 ${
                                msg.type === 'user'
                                  ? 'bg-purple-600 text-white'
                                  : msg.type === 'error'
                                  ? 'bg-red-600/20 text-red-200 border border-red-500/30'
                                  : 'bg-slate-700 text-purple-100'
                              }`}
                            >
                              <div className="text-sm mb-1 opacity-75">{msg.timestamp}</div>
                              <div className="whitespace-pre-wrap">{msg.content}</div>
                              {msg.mode && (
                                <div className="text-xs mt-2 opacity-75">模式: {msg.mode}</div>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                      {querying && (
                        <div className="flex justify-start">
                          <div className="bg-slate-700 rounded-lg p-4">
                            <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
                          </div>
                        </div>
                      )}
                      <div ref={chatEndRef} />
                    </div>

                    {/* Query Mode Selector */}
                    <div className="flex items-center gap-4">
                      <label className="text-purple-200">查询模式:</label>
                      <select
                        value={queryMode}
                        onChange={(e) => setQueryMode(e.target.value)}
                        className="px-4 py-2 bg-slate-700 text-white rounded-lg border border-purple-500/30 focus:outline-none focus:border-purple-500"
                      >
                        <option value="hybrid">混合模式 (Hybrid)</option>
                        <option value="naive">简单模式 (Naive)</option>
                        <option value="local">本地模式 (Local)</option>
                        <option value="global">全局模式 (Global)</option>
                      </select>
                    </div>

                    {/* Query Input */}
                    <div className="flex gap-2">
                      <textarea
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="输入您的问题... (Enter 发送)"
                        className="flex-1 px-4 py-3 bg-slate-700 text-white rounded-lg border border-purple-500/30 focus:outline-none focus:border-purple-500 resize-none"
                        rows="3"
                      />
                      <button
                        onClick={handleQuery}
                        disabled={querying || !question.trim()}
                        className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                      >
                        {querying ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Upload Tab */}
            {activeTab === 'upload' && (
              <div className="space-y-6">
                {!initialized ? (
                  <div className="text-center py-12">
                    <AlertCircle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
                    <p className="text-purple-200">请先初始化系统</p>
                  </div>
                ) : (
                  <>
                    <div className="border-2 border-dashed border-purple-500/30 rounded-lg p-12 text-center hover:border-purple-500/50 transition-colors">
                      <FileText className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                      <input
                        type="file"
                        onChange={(e) => setUploadFile(e.target.files[0])}
                        accept=".pdf,.docx,.doc,.txt,.rtf"
                        className="hidden"
                        id="file-upload"
                      />
                      <label
                        htmlFor="file-upload"
                        className="cursor-pointer px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors inline-block"
                      >
                        选择文件
                      </label>
                      <p className="text-purple-300 mt-4 text-sm">
                        支持格式: PDF, DOCX, DOC, TXT, RTF
                      </p>
                    </div>

                    {uploadFile && (
                      <div className="bg-slate-700/50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <FileText className="w-6 h-6 text-purple-400" />
                            <span className="text-white">{uploadFile.name}</span>
                          </div>
                          <button
                            onClick={() => setUploadFile(null)}
                            className="text-red-400 hover:text-red-300"
                          >
                            <XCircle className="w-5 h-5" />
                          </button>
                        </div>
                        <button
                          onClick={handleFileUpload}
                          disabled={uploading}
                          className="w-full px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                        >
                          {uploading ? (
                            <>
                              <Loader2 className="w-5 h-5 animate-spin" />
                              上传中...
                            </>
                          ) : (
                            <>
                              <Upload className="w-5 h-5" />
                              上传文档
                            </>
                          )}
                        </button>
                      </div>
                    )}

                    {uploadStatus && (
                      <div className={`p-4 rounded-lg ${
                        uploadStatus.includes('成功') 
                          ? 'bg-green-600/20 text-green-200 border border-green-500/30' 
                          : 'bg-red-600/20 text-red-200 border border-red-500/30'
                      }`}>
                        {uploadStatus}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-purple-200 mb-2">工作目录 *</label>
                    <input
                      type="text"
                      value={config.working_dir}
                      onChange={(e) => setConfig({ ...config, working_dir: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-purple-500/30 focus:outline-none focus:border-purple-500"
                      placeholder="./index_default"
                    />
                  </div>
                  <div>
                    <label className="block text-purple-200 mb-2">LLM 模型</label>
                    <input
                      type="text"
                      value={config.llm_model}
                      onChange={(e) => setConfig({ ...config, llm_model: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-purple-500/30 focus:outline-none focus:border-purple-500"
                      placeholder="gpt-4 (默认)"
                    />
                  </div>
                  <div>
                    <label className="block text-purple-200 mb-2">Embedding 模型</label>
                    <input
                      type="text"
                      value={config.embedding_model}
                      onChange={(e) => setConfig({ ...config, embedding_model: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-purple-500/30 focus:outline-none focus:border-purple-500"
                      placeholder="sentence-transformers/all-MiniLM-L6-v2"
                    />
                  </div>
                  <div>
                    <label className="block text-purple-200 mb-2">Embedding 维度</label>
                    <input
                      type="number"
                      value={config.embedding_dim}
                      onChange={(e) => setConfig({ ...config, embedding_dim: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-purple-500/30 focus:outline-none focus:border-purple-500"
                      placeholder="384 (默认)"
                    />
                  </div>
                  <div>
                    <label className="block text-purple-200 mb-2">Embedding 最大 Token</label>
                    <input
                      type="number"
                      value={config.embedding_max_token}
                      onChange={(e) => setConfig({ ...config, embedding_max_token: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-purple-500/30 focus:outline-none focus:border-purple-500"
                      placeholder="5000 (默认)"
                    />
                  </div>
                  <div>
                    <label className="block text-purple-200 mb-2">LiteLLM URL</label>
                    <input
                      type="text"
                      value={config.litellm_url}
                      onChange={(e) => setConfig({ ...config, litellm_url: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-purple-500/30 focus:outline-none focus:border-purple-500"
                      placeholder="http://localhost:4000"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-purple-200 mb-2">LiteLLM API Key</label>
                    <input
                      type="password"
                      value={config.litellm_key}
                      onChange={(e) => setConfig({ ...config, litellm_key: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-purple-500/30 focus:outline-none focus:border-purple-500"
                      placeholder="sk-1234"
                    />
                  </div>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={handleInitialize}
                    disabled={loading || !config.working_dir}
                    className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        初始化中...
                      </>
                    ) : (
                      <>
                        <Database className="w-5 h-5" />
                        初始化系统
                      </>
                    )}
                  </button>
                  <button
                    onClick={checkStatus}
                    className="px-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                  >
                    刷新状态
                  </button>
                </div>

                <div className="bg-slate-700/50 rounded-lg p-4 text-sm text-purple-200">
                  <p className="font-medium mb-2">💡 提示:</p>
                  <ul className="space-y-1 list-disc list-inside">
                    <li>标有 * 的字段为必填项</li>
                    <li>其他字段为空时将使用环境变量或默认值</li>
                    <li>需要先配置好 LiteLLM 服务和 Neo4j 数据库</li>
                    <li>初始化可能需要一些时间，请耐心等待</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-purple-300 text-sm">
          <p>基于 lightrag · Neo4j · Faiss · LiteLLM</p>
        </div>
      </div>
    </div>
  );
}