import React, { useState, useEffect } from 'react';
import {
  uploadDocument,
  insertDocument,
  getDocumentsStatus,
  getDocumentsByStatus
} from '../services/api';
import {
  FileText,
  Upload,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  FileUp
} from 'lucide-react';

function DocumentManager() {
  const [activeMode, setActiveMode] = useState('upload');
  const [selectedFile, setSelectedFile] = useState(null);
  const [customId, setCustomId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  // 直接插入相关状态
  const [textContent, setTextContent] = useState('');
  const [filePath, setFilePath] = useState('');
  const [docId, setDocId] = useState('');

  // 文档状态统计
  const [docsStatus, setDocsStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(false);

  // 文档列表
  const [selectedStatus, setSelectedStatus] = useState('PROCESSED');
  const [documentsList, setDocumentsList] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  useEffect(() => {
    fetchDocumentsStatus();
  }, []);

  const fetchDocumentsStatus = async () => {
    setLoadingStatus(true);
    try {
      const status = await getDocumentsStatus();
      setDocsStatus(status);
    } catch (error) {
      console.error('获取文档状态失败:', error);
    } finally {
      setLoadingStatus(false);
    }
  };

  const fetchDocumentsList = async (status) => {
    setLoadingDocs(true);
    try {
      const result = await getDocumentsByStatus(status);
      setDocumentsList(result.documents);
    } catch (error) {
      console.error('获取文档列表失败:', error);
      setDocumentsList([]);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    if (activeMode === 'list') {
      fetchDocumentsList(selectedStatus);
    }
  }, [activeMode, selectedStatus]);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
    setUploadStatus(null);
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadStatus(null);

    try {
      const result = await uploadDocument(selectedFile, customId || null);
      setUploadStatus({
        type: 'success',
        message: `文件上传成功: ${result.message}`,
      });
      setSelectedFile(null);
      setCustomId('');
      fetchDocumentsStatus();
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || error.message || '上传失败',
      });
    } finally {
      setUploading(false);
    }
  };

  const handleTextInsert = async (e) => {
    e.preventDefault();
    if (!textContent.trim() || !filePath.trim()) return;

    setUploading(true);
    setUploadStatus(null);

    try {
      const result = await insertDocument(textContent, filePath, docId || null);
      setUploadStatus({
        type: 'success',
        message: '文档内容插入成功',
      });
      setTextContent('');
      setFilePath('');
      setDocId('');
      fetchDocumentsStatus();
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || error.message || '插入失败',
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <FileText className="panel-icon" />
        <h2>文档管理</h2>
      </div>

      <div className="panel-content">
        {/* 文档状态统计 */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon success">
              <CheckCircle />
            </div>
            <div className="stat-content">
              <div className="stat-value">{docsStatus?.processed || 0}</div>
              <div className="stat-label">已处理</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon warning">
              <AlertCircle />
            </div>
            <div className="stat-content">
              <div className="stat-value">{docsStatus?.pending || 0}</div>
              <div className="stat-label">待处理</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon error">
              <XCircle />
            </div>
            <div className="stat-content">
              <div className="stat-value">{docsStatus?.failed || 0}</div>
              <div className="stat-label">失败</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon primary">
              <FileText />
            </div>
            <div className="stat-content">
              <div className="stat-value">{docsStatus?.total || 0}</div>
              <div className="stat-label">总计</div>
            </div>
          </div>
        </div>

        <button
          onClick={fetchDocumentsStatus}
          className="btn btn-secondary btn-sm"
          disabled={loadingStatus}
        >
          {loadingStatus ? (
            <Loader2 className="btn-icon spinning" />
          ) : (
            <RefreshCw className="btn-icon" />
          )}
          刷新统计
        </button>

        {/* 操作模式选择 */}
        <div className="mode-tabs">
          <button
            onClick={() => setActiveMode('upload')}
            className={`mode-tab ${activeMode === 'upload' ? 'active' : ''}`}
          >
            <Upload className="tab-icon" />
            文件上传
          </button>
          <button
            onClick={() => setActiveMode('insert')}
            className={`mode-tab ${activeMode === 'insert' ? 'active' : ''}`}
          >
            <FileUp className="tab-icon" />
            直接插入
          </button>
          <button
            onClick={() => setActiveMode('list')}
            className={`mode-tab ${activeMode === 'list' ? 'active' : ''}`}
          >
            <FileText className="tab-icon" />
            文档列表
          </button>
        </div>

        {/* 文件上传模式 */}
        {activeMode === 'upload' && (
          <div className="upload-section">
            <div className="upload-area">
              <input
                type="file"
                id="file-input"
                onChange={handleFileSelect}
                accept=".pdf,.doc,.docx,.txt,.rtf"
                className="file-input-hidden"
              />
              <label htmlFor="file-input" className="upload-label">
                <Upload className="upload-icon" />
                <p className="upload-text">
                  {selectedFile ? selectedFile.name : '点击选择文件或拖拽文件到此处'}
                </p>
                <p className="upload-hint">支持 PDF, DOC, DOCX, TXT, RTF</p>
              </label>
            </div>

            {selectedFile && (
              <>
                <div className="form-group">
                  <label htmlFor="custom-id">自定义文档 ID (可选)</label>
                  <input
                    type="text"
                    id="custom-id"
                    value={customId}
                    onChange={(e) => setCustomId(e.target.value)}
                    className="form-input"
                    placeholder="留空自动生成"
                  />
                </div>

                <button
                  onClick={handleFileUpload}
                  className="btn btn-primary"
                  disabled={uploading}
                >
                  {uploading ? (
                    <>
                      <Loader2 className="btn-icon spinning" />
                      上传中...
                    </>
                  ) : (
                    <>
                      <Upload className="btn-icon" />
                      上传文档
                    </>
                  )}
                </button>
              </>
            )}
          </div>
        )}

        {/* 直接插入模式 */}
        {activeMode === 'insert' && (
          <form onSubmit={handleTextInsert} className="form">
            <div className="form-group">
              <label htmlFor="file-path">
                文件路径/名称 <span className="required">*</span>
              </label>
              <input
                type="text"
                id="file-path"
                value={filePath}
                onChange={(e) => setFilePath(e.target.value)}
                className="form-input"
                placeholder="example.txt"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="doc-id">文档 ID (可选)</label>
              <input
                type="text"
                id="doc-id"
                value={docId}
                onChange={(e) => setDocId(e.target.value)}
                className="form-input"
                placeholder="留空自动生成"
              />
            </div>

            <div className="form-group">
              <label htmlFor="text-content">
                文档内容 <span className="required">*</span>
              </label>
              <textarea
                id="text-content"
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                className="form-textarea"
                rows="10"
                placeholder="粘贴或输入文档内容..."
                required
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={uploading}>
              {uploading ? (
                <>
                  <Loader2 className="btn-icon spinning" />
                  插入中...
                </>
              ) : (
                <>
                  <FileUp className="btn-icon" />
                  插入文档
                </>
              )}
            </button>
          </form>
        )}

        {/* 文档列表模式 */}
        {activeMode === 'list' && (
          <div className="documents-list-section">
            <div className="list-header">
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="select-input"
              >
                <option value="PROCESSED">已处理</option>
                <option value="PENDING">待处理</option>
                <option value="FAILED">失败</option>
              </select>

              <button
                onClick={() => fetchDocumentsList(selectedStatus)}
                className="btn btn-secondary btn-sm"
                disabled={loadingDocs}
              >
                {loadingDocs ? (
                  <Loader2 className="btn-icon spinning" />
                ) : (
                  <RefreshCw className="btn-icon" />
                )}
                刷新
              </button>
            </div>

            {loadingDocs ? (
              <div className="loading-state">
                <Loader2 className="spinning" size={32} />
                <p>加载中...</p>
              </div>
            ) : documentsList.length === 0 ? (
              <div className="empty-state">
                <FileText className="empty-icon" />
                <p>暂无文档</p>
              </div>
            ) : (
              <div className="documents-table">
                <table>
                  <thead>
                    <tr>
                      <th>文档 ID</th>
                      <th>文件名</th>
                      <th>状态</th>
                      <th>创建时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documentsList.map((doc) => (
                      <tr key={doc.doc_id}>
                        <td className="doc-id">{doc.doc_id}</td>
                        <td>{doc.file_name}</td>
                        <td>
                          <span className={`status-badge status-${doc.status.toLowerCase()}`}>
                            {doc.status}
                          </span>
                        </td>
                        <td>{doc.created_at ? new Date(doc.created_at).toLocaleString('zh-CN') : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* 状态提示 */}
        {uploadStatus && (
          <div className={`alert alert-${uploadStatus.type}`}>
            {uploadStatus.type === 'success' ? (
              <CheckCircle className="alert-icon" />
            ) : (
              <XCircle className="alert-icon" />
            )}
            <p>{uploadStatus.message}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default DocumentManager;
