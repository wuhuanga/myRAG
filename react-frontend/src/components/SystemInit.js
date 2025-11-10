import React, { useState } from 'react';
import { initializeSystem } from '../services/api';
import { Settings, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';

function SystemInit({ onInitSuccess }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const [config, setConfig] = useState({
    working_dir: './rag_working',
    llm_model: '',
    embedding_model: '',
    embedding_dim: '',
    embedding_max_token: '',
    litellm_url: '',
    litellm_key: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      // 构建请求对象,只包含非空字段
      const payload = {
        working_dir: config.working_dir,
      };

      if (config.llm_model) payload.llm_model = config.llm_model;
      if (config.embedding_model) payload.embedding_model = config.embedding_model;
      if (config.embedding_dim) payload.embedding_dim = parseInt(config.embedding_dim);
      if (config.embedding_max_token) payload.embedding_max_token = parseInt(config.embedding_max_token);
      if (config.litellm_url) payload.litellm_url = config.litellm_url;
      if (config.litellm_key) payload.litellm_key = config.litellm_key;

      const result = await initializeSystem(payload);
      setSuccess(true);
      setTimeout(() => {
        if (onInitSuccess) onInitSuccess();
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '初始化失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <Settings className="panel-icon" />
        <h2>系统初始化配置</h2>
      </div>

      <div className="panel-content">
        {success && (
          <div className="alert alert-success">
            <CheckCircle className="alert-icon" />
            <div>
              <strong>初始化成功!</strong>
              <p>系统正在跳转到查询页面...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="alert alert-error">
            <AlertTriangle className="alert-icon" />
            <div>
              <strong>初始化失败</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="form">
          <div className="form-section">
            <h3>基础配置</h3>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="working_dir">
                  工作目录 <span className="required">*</span>
                </label>
                <input
                  type="text"
                  id="working_dir"
                  name="working_dir"
                  value={config.working_dir}
                  onChange={handleChange}
                  className="form-input"
                  required
                  placeholder="./rag_working"
                />
                <span className="form-hint">存储索引和数据的目录</span>
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>模型配置</h3>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="llm_model">LLM 模型</label>
                <input
                  type="text"
                  id="llm_model"
                  name="llm_model"
                  value={config.llm_model}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="gpt-4 (留空使用环境变量或默认值)"
                />
              </div>

              <div className="form-group">
                <label htmlFor="embedding_model">Embedding 模型</label>
                <input
                  type="text"
                  id="embedding_model"
                  name="embedding_model"
                  value={config.embedding_model}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="sentence-transformers/all-MiniLM-L6-v2"
                />
              </div>

              <div className="form-group">
                <label htmlFor="embedding_dim">Embedding 维度</label>
                <input
                  type="number"
                  id="embedding_dim"
                  name="embedding_dim"
                  value={config.embedding_dim}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="384"
                />
              </div>

              <div className="form-group">
                <label htmlFor="embedding_max_token">Embedding 最大 Token</label>
                <input
                  type="number"
                  id="embedding_max_token"
                  name="embedding_max_token"
                  value={config.embedding_max_token}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="5000"
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>LiteLLM 配置</h3>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="litellm_url">LiteLLM URL</label>
                <input
                  type="text"
                  id="litellm_url"
                  name="litellm_url"
                  value={config.litellm_url}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="http://localhost:4000"
                />
              </div>

              <div className="form-group">
                <label htmlFor="litellm_key">LiteLLM API Key</label>
                <input
                  type="password"
                  id="litellm_key"
                  name="litellm_key"
                  value={config.litellm_key}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="sk-1234"
                />
              </div>
            </div>
          </div>

          <div className="info-box">
            <h4>💡 配置说明</h4>
            <ul>
              <li>标有 <span className="required">*</span> 的字段为必填项</li>
              <li>其他字段留空时将使用环境变量或默认值</li>
              <li>请确保已配置好 LiteLLM 服务和 Neo4j 数据库</li>
              <li>初始化过程可能需要几分钟,请耐心等待</li>
            </ul>
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !config.working_dir}
            >
              {loading ? (
                <>
                  <Loader2 className="btn-icon spinning" />
                  初始化中...
                </>
              ) : (
                <>
                  <Settings className="btn-icon" />
                  初始化系统
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default SystemInit;
