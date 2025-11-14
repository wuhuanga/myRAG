import React, { useState, useRef, useEffect } from 'react';
import { queryKnowledge, queryWithUCD } from '../services/api';
import { MessageSquare, Send, Loader2, User, Bot, Sparkles } from 'lucide-react';

function QueryPanel() {
  const [question, setQuestion] = useState('');
  const [mode, setMode] = useState('hybrid');
  const [useUCD, setUseUCD] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userMessage = {
      type: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    setChatHistory(prev => [...prev, userMessage]);
    setQuestion('');
    setLoading(true);

    try {
      let result;
      if (useUCD) {
        result = await queryWithUCD(question, mode);
        const botMessage = {
          type: 'bot',
          content: result.context,
          ucdModel: result.ucd_model,
          mode: result.mode,
          timestamp: new Date().toISOString(),
        };
        setChatHistory(prev => [...prev, botMessage]);
      } else {
        result = await queryKnowledge(question, mode);
        const botMessage = {
          type: 'bot',
          content: result.answer,
          mode: result.mode,
          timestamp: new Date().toISOString(),
        };
        setChatHistory(prev => [...prev, botMessage]);
      }
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: error.response?.data?.detail || error.message || '查询失败',
        timestamp: new Date().toISOString(),
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery(e);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <MessageSquare className="panel-icon" />
        <h2>知识查询</h2>
      </div>

      <div className="panel-content query-panel">
        <div className="chat-container">
          <div className="chat-messages">
            {chatHistory.length === 0 ? (
              <div className="empty-state">
                <MessageSquare className="empty-icon" />
                <h3>开始对话</h3>
                <p>输入您的问题,我将从知识库中为您查找答案</p>
              </div>
            ) : (
              <>
                {chatHistory.map((message, index) => (
                  <div key={index} className={`message message-${message.type}`}>
                    <div className="message-avatar">
                      {message.type === 'user' ? (
                        <User className="avatar-icon" />
                      ) : message.type === 'error' ? (
                        <span className="avatar-icon error">!</span>
                      ) : (
                        <Bot className="avatar-icon" />
                      )}
                    </div>
                    <div className="message-content">
                      <div className="message-header">
                        <span className="message-sender">
                          {message.type === 'user' ? '您' : message.type === 'error' ? '错误' : 'AI 助手'}
                        </span>
                        <span className="message-time">{formatTimestamp(message.timestamp)}</span>
                      </div>
                      <div className="message-text">{message.content}</div>
                      {message.mode && (
                        <div className="message-meta">
                          <span className="mode-badge">{message.mode}</span>
                        </div>
                      )}
                      {message.ucdModel && (
                        <div className="ucd-result">
                          <Sparkles className="ucd-icon" />
                          <span>UCD 建模已生成</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="message message-bot">
                    <div className="message-avatar">
                      <Bot className="avatar-icon" />
                    </div>
                    <div className="message-content">
                      <div className="message-loading">
                        <Loader2 className="spinning" />
                        <span>正在思考...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </>
            )}
          </div>

          <div className="chat-input-container">
            <div className="query-options">
              <div className="option-group">
                <label>查询模式:</label>
                <select
                  value={mode}
                  onChange={(e) => setMode(e.target.value)}
                  className="select-input"
                >
                  <option value="hybrid">混合模式 (Hybrid)</option>
                  <option value="naive">简单模式 (Naive)</option>
                  <option value="local">本地模式 (Local)</option>
                  <option value="global">全局模式 (Global)</option>
                </select>
              </div>

              <div className="option-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={useUCD}
                    onChange={(e) => setUseUCD(e.target.checked)}
                  />
                  <span>使用 UCD 建模</span>
                </label>
              </div>
            </div>

            <form onSubmit={handleQuery} className="chat-input-form">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入您的问题... (Enter 发送, Shift+Enter 换行)"
                className="chat-input"
                rows="3"
              />
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || !question.trim()}
              >
                {loading ? (
                  <Loader2 className="btn-icon spinning" />
                ) : (
                  <Send className="btn-icon" />
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QueryPanel;
