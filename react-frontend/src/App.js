import React, { useState, useEffect } from 'react';
import './App.css';
import SystemInit from './components/SystemInit';
import QueryPanel from './components/QueryPanel';
import DocumentManager from './components/DocumentManager';
import GraphManager from './components/GraphManager';
import { healthCheck } from './services/api';
import {
  Database,
  MessageSquare,
  FileText,
  Network,
  Activity,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('init');
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSystemHealth();
    // 每30秒检查一次系统状态
    const interval = setInterval(checkSystemHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkSystemHealth = async () => {
    try {
      const status = await healthCheck();
      setSystemStatus(status);
      if (status.rag_initialized && activeTab === 'init') {
        setActiveTab('query');
      }
    } catch (error) {
      console.error('健康检查失败:', error);
      setSystemStatus({ status: 'error', rag_initialized: false });
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'init', name: '系统初始化', icon: Database, disabled: false },
    { id: 'query', name: '知识查询', icon: MessageSquare, disabled: !systemStatus?.rag_initialized },
    { id: 'documents', name: '文档管理', icon: FileText, disabled: !systemStatus?.rag_initialized },
    { id: 'graph', name: '图谱管理', icon: Network, disabled: !systemStatus?.rag_initialized },
  ];

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <Database className="logo-icon" />
            <div>
              <h1>RAG 知识图谱系统</h1>
              <p className="subtitle">基于 Neo4j + Faiss 的智能 RAG 系统</p>
            </div>
          </div>

          <div className="header-status">
            <Activity className="status-icon" />
            <div className="status-info">
              {loading ? (
                <span className="status-text loading">检查中...</span>
              ) : systemStatus?.status === 'healthy' ? (
                <>
                  <CheckCircle className="status-indicator success" />
                  <span className="status-text success">
                    {systemStatus.rag_initialized ? '系统已就绪' : '系统在线 (未初始化)'}
                  </span>
                </>
              ) : (
                <>
                  <AlertCircle className="status-indicator error" />
                  <span className="status-text error">系统异常</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="app-container">
        <nav className="tab-nav">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => !tab.disabled && setActiveTab(tab.id)}
                className={`tab-button ${activeTab === tab.id ? 'active' : ''} ${tab.disabled ? 'disabled' : ''}`}
                disabled={tab.disabled}
              >
                <Icon className="tab-icon" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>

        <main className="main-content">
          {activeTab === 'init' && (
            <SystemInit
              onInitSuccess={() => {
                checkSystemHealth();
                setActiveTab('query');
              }}
            />
          )}
          {activeTab === 'query' && <QueryPanel />}
          {activeTab === 'documents' && <DocumentManager />}
          {activeTab === 'graph' && <GraphManager />}
        </main>
      </div>

      <footer className="app-footer">
        <p>Powered by LightRAG • Neo4j • Faiss • FastAPI</p>
      </footer>
    </div>
  );
}

export default App;
