import React, { useState } from 'react';
import {
  createEntity,
  editEntity,
  deleteEntity,
  getEntityInfo,
  mergeEntities,
  createRelation,
  editRelation,
  deleteRelation,
  getRelationInfo,
  exportData
} from '../services/api';
import {
  Network,
  Plus,
  Edit,
  Trash2,
  Info,
  GitMerge,
  Download,
  Loader2,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

function GraphManager() {
  const [activeTab, setActiveTab] = useState('entity');
  const [operation, setOperation] = useState('create');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // 实体表单状态
  const [entityForm, setEntityForm] = useState({
    entityName: '',
    description: '',
    entityType: 'UNKNOWN',
    sourceId: 'manual_creation',
    filePath: 'manual_creation',
  });

  // 实体编辑表单
  const [entityEditForm, setEntityEditForm] = useState({
    entityName: '',
    newName: '',
    description: '',
    allowRename: true,
  });

  // 关系表单状态
  const [relationForm, setRelationForm] = useState({
    sourceEntity: '',
    targetEntity: '',
    description: '',
    keywords: '',
    weight: 1.0,
    sourceId: 'manual_creation',
    filePath: 'manual_creation',
  });

  // 实体合并表单
  const [mergeForm, setMergeForm] = useState({
    sourceEntities: '',
    targetEntity: '',
  });

  // 导出表单
  const [exportForm, setExportForm] = useState({
    outputPath: './exported_data',
    fileFormat: 'csv',
    includeVectorData: false,
  });

  const handleEntityCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const data = await createEntity(
        entityForm.entityName,
        entityForm.description,
        entityForm.entityType,
        entityForm.sourceId,
        entityForm.filePath
      );
      setResult({ type: 'success', message: data.message });
      setEntityForm({
        entityName: '',
        description: '',
        entityType: 'UNKNOWN',
        sourceId: 'manual_creation',
        filePath: 'manual_creation',
      });
    } catch (error) {
      setResult({
        type: 'error',
        message: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEntityEdit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const updatedData = {};
      if (entityEditForm.newName) updatedData.entity_name = entityEditForm.newName;
      if (entityEditForm.description) updatedData.description = entityEditForm.description;

      const data = await editEntity(
        entityEditForm.entityName,
        updatedData,
        entityEditForm.allowRename
      );
      setResult({ type: 'success', message: data.message });
    } catch (error) {
      setResult({
        type: 'error',
        message: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEntityDelete = async (e) => {
    e.preventDefault();
    if (!window.confirm(`确定要删除实体 "${entityEditForm.entityName}" 吗?`)) {
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const data = await deleteEntity(entityEditForm.entityName);
      setResult({ type: 'success', message: data.message });
      setEntityEditForm({ ...entityEditForm, entityName: '' });
    } catch (error) {
      setResult({
        type: 'error',
        message: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEntityInfo = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const data = await getEntityInfo(entityEditForm.entityName, false);
      setResult({
        type: 'info',
        message: '实体信息:',
        data: data.entity_info,
      });
    } catch (error) {
      setResult({
        type: 'error',
        message: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEntityMerge = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const sourceEntities = mergeForm.sourceEntities
        .split(',')
        .map((e) => e.trim())
        .filter((e) => e);

      const data = await mergeEntities(
        sourceEntities,
        mergeForm.targetEntity,
        null,
        null
      );
      setResult({ type: 'success', message: data.message });
      setMergeForm({ sourceEntities: '', targetEntity: '' });
    } catch (error) {
      setResult({
        type: 'error',
        message: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRelationCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const data = await createRelation(
        relationForm.sourceEntity,
        relationForm.targetEntity,
        relationForm.description,
        relationForm.keywords,
        parseFloat(relationForm.weight),
        relationForm.sourceId,
        relationForm.filePath
      );
      setResult({ type: 'success', message: data.message });
      setRelationForm({
        sourceEntity: '',
        targetEntity: '',
        description: '',
        keywords: '',
        weight: 1.0,
        sourceId: 'manual_creation',
        filePath: 'manual_creation',
      });
    } catch (error) {
      setResult({
        type: 'error',
        message: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRelationDelete = async (e) => {
    e.preventDefault();
    if (
      !window.confirm(
        `确定要删除关系 "${relationForm.sourceEntity}" -> "${relationForm.targetEntity}" 吗?`
      )
    ) {
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const data = await deleteRelation(
        relationForm.sourceEntity,
        relationForm.targetEntity
      );
      setResult({ type: 'success', message: data.message });
    } catch (error) {
      setResult({
        type: 'error',
        message: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const data = await exportData(
        exportForm.outputPath,
        exportForm.fileFormat,
        exportForm.includeVectorData
      );
      setResult({ type: 'success', message: data.message });
    } catch (error) {
      setResult({
        type: 'error',
        message: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <Network className="panel-icon" />
        <h2>知识图谱管理</h2>
      </div>

      <div className="panel-content">
        {/* 标签导航 */}
        <div className="mode-tabs">
          <button
            onClick={() => {
              setActiveTab('entity');
              setOperation('create');
              setResult(null);
            }}
            className={`mode-tab ${activeTab === 'entity' ? 'active' : ''}`}
          >
            实体管理
          </button>
          <button
            onClick={() => {
              setActiveTab('relation');
              setOperation('create');
              setResult(null);
            }}
            className={`mode-tab ${activeTab === 'relation' ? 'active' : ''}`}
          >
            关系管理
          </button>
          <button
            onClick={() => {
              setActiveTab('export');
              setResult(null);
            }}
            className={`mode-tab ${activeTab === 'export' ? 'active' : ''}`}
          >
            数据导出
          </button>
        </div>

        {/* 实体管理 */}
        {activeTab === 'entity' && (
          <div className="graph-section">
            {/* 操作选择 */}
            <div className="operation-buttons">
              <button
                onClick={() => {
                  setOperation('create');
                  setResult(null);
                }}
                className={`btn btn-sm ${operation === 'create' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Plus className="btn-icon" />
                创建
              </button>
              <button
                onClick={() => {
                  setOperation('edit');
                  setResult(null);
                }}
                className={`btn btn-sm ${operation === 'edit' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Edit className="btn-icon" />
                编辑
              </button>
              <button
                onClick={() => {
                  setOperation('delete');
                  setResult(null);
                }}
                className={`btn btn-sm ${operation === 'delete' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Trash2 className="btn-icon" />
                删除
              </button>
              <button
                onClick={() => {
                  setOperation('info');
                  setResult(null);
                }}
                className={`btn btn-sm ${operation === 'info' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Info className="btn-icon" />
                查询
              </button>
              <button
                onClick={() => {
                  setOperation('merge');
                  setResult(null);
                }}
                className={`btn btn-sm ${operation === 'merge' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <GitMerge className="btn-icon" />
                合并
              </button>
            </div>

            {/* 创建实体 */}
            {operation === 'create' && (
              <form onSubmit={handleEntityCreate} className="form">
                <div className="form-grid">
                  <div className="form-group">
                    <label>
                      实体名称 <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      value={entityForm.entityName}
                      onChange={(e) =>
                        setEntityForm({ ...entityForm, entityName: e.target.value })
                      }
                      className="form-input"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>实体类型</label>
                    <input
                      type="text"
                      value={entityForm.entityType}
                      onChange={(e) =>
                        setEntityForm({ ...entityForm, entityType: e.target.value })
                      }
                      className="form-input"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>描述</label>
                  <textarea
                    value={entityForm.description}
                    onChange={(e) =>
                      setEntityForm({ ...entityForm, description: e.target.value })
                    }
                    className="form-textarea"
                    rows="3"
                  />
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? <Loader2 className="btn-icon spinning" /> : <Plus className="btn-icon" />}
                  创建实体
                </button>
              </form>
            )}

            {/* 编辑实体 */}
            {operation === 'edit' && (
              <form onSubmit={handleEntityEdit} className="form">
                <div className="form-group">
                  <label>
                    实体名称 <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    value={entityEditForm.entityName}
                    onChange={(e) =>
                      setEntityEditForm({ ...entityEditForm, entityName: e.target.value })
                    }
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>新名称 (可选)</label>
                  <input
                    type="text"
                    value={entityEditForm.newName}
                    onChange={(e) =>
                      setEntityEditForm({ ...entityEditForm, newName: e.target.value })
                    }
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>新描述 (可选)</label>
                  <textarea
                    value={entityEditForm.description}
                    onChange={(e) =>
                      setEntityEditForm({ ...entityEditForm, description: e.target.value })
                    }
                    className="form-textarea"
                    rows="3"
                  />
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? <Loader2 className="btn-icon spinning" /> : <Edit className="btn-icon" />}
                  更新实体
                </button>
              </form>
            )}

            {/* 删除实体 */}
            {operation === 'delete' && (
              <form onSubmit={handleEntityDelete} className="form">
                <div className="form-group">
                  <label>
                    实体名称 <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    value={entityEditForm.entityName}
                    onChange={(e) =>
                      setEntityEditForm({ ...entityEditForm, entityName: e.target.value })
                    }
                    className="form-input"
                    required
                  />
                </div>

                <button type="submit" className="btn btn-danger" disabled={loading}>
                  {loading ? <Loader2 className="btn-icon spinning" /> : <Trash2 className="btn-icon" />}
                  删除实体
                </button>
              </form>
            )}

            {/* 查询实体 */}
            {operation === 'info' && (
              <form onSubmit={handleEntityInfo} className="form">
                <div className="form-group">
                  <label>
                    实体名称 <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    value={entityEditForm.entityName}
                    onChange={(e) =>
                      setEntityEditForm({ ...entityEditForm, entityName: e.target.value })
                    }
                    className="form-input"
                    required
                  />
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? <Loader2 className="btn-icon spinning" /> : <Info className="btn-icon" />}
                  查询实体
                </button>
              </form>
            )}

            {/* 合并实体 */}
            {operation === 'merge' && (
              <form onSubmit={handleEntityMerge} className="form">
                <div className="form-group">
                  <label>
                    源实体 (逗号分隔) <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    value={mergeForm.sourceEntities}
                    onChange={(e) =>
                      setMergeForm({ ...mergeForm, sourceEntities: e.target.value })
                    }
                    className="form-input"
                    placeholder="entity1, entity2, entity3"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>
                    目标实体 <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    value={mergeForm.targetEntity}
                    onChange={(e) =>
                      setMergeForm({ ...mergeForm, targetEntity: e.target.value })
                    }
                    className="form-input"
                    required
                  />
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? <Loader2 className="btn-icon spinning" /> : <GitMerge className="btn-icon" />}
                  合并实体
                </button>
              </form>
            )}
          </div>
        )}

        {/* 关系管理 */}
        {activeTab === 'relation' && (
          <div className="graph-section">
            <div className="operation-buttons">
              <button
                onClick={() => {
                  setOperation('create');
                  setResult(null);
                }}
                className={`btn btn-sm ${operation === 'create' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Plus className="btn-icon" />
                创建
              </button>
              <button
                onClick={() => {
                  setOperation('delete');
                  setResult(null);
                }}
                className={`btn btn-sm ${operation === 'delete' ? 'btn-primary' : 'btn-secondary'}`}
              >
                <Trash2 className="btn-icon" />
                删除
              </button>
            </div>

            {/* 创建关系 */}
            {operation === 'create' && (
              <form onSubmit={handleRelationCreate} className="form">
                <div className="form-grid">
                  <div className="form-group">
                    <label>
                      源实体 <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      value={relationForm.sourceEntity}
                      onChange={(e) =>
                        setRelationForm({ ...relationForm, sourceEntity: e.target.value })
                      }
                      className="form-input"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>
                      目标实体 <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      value={relationForm.targetEntity}
                      onChange={(e) =>
                        setRelationForm({ ...relationForm, targetEntity: e.target.value })
                      }
                      className="form-input"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>描述</label>
                  <textarea
                    value={relationForm.description}
                    onChange={(e) =>
                      setRelationForm({ ...relationForm, description: e.target.value })
                    }
                    className="form-textarea"
                    rows="3"
                  />
                </div>

                <div className="form-grid">
                  <div className="form-group">
                    <label>关键词</label>
                    <input
                      type="text"
                      value={relationForm.keywords}
                      onChange={(e) =>
                        setRelationForm({ ...relationForm, keywords: e.target.value })
                      }
                      className="form-input"
                    />
                  </div>

                  <div className="form-group">
                    <label>权重</label>
                    <input
                      type="number"
                      step="0.1"
                      value={relationForm.weight}
                      onChange={(e) =>
                        setRelationForm({ ...relationForm, weight: e.target.value })
                      }
                      className="form-input"
                    />
                  </div>
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? <Loader2 className="btn-icon spinning" /> : <Plus className="btn-icon" />}
                  创建关系
                </button>
              </form>
            )}

            {/* 删除关系 */}
            {operation === 'delete' && (
              <form onSubmit={handleRelationDelete} className="form">
                <div className="form-grid">
                  <div className="form-group">
                    <label>
                      源实体 <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      value={relationForm.sourceEntity}
                      onChange={(e) =>
                        setRelationForm({ ...relationForm, sourceEntity: e.target.value })
                      }
                      className="form-input"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>
                      目标实体 <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      value={relationForm.targetEntity}
                      onChange={(e) =>
                        setRelationForm({ ...relationForm, targetEntity: e.target.value })
                      }
                      className="form-input"
                      required
                    />
                  </div>
                </div>

                <button type="submit" className="btn btn-danger" disabled={loading}>
                  {loading ? <Loader2 className="btn-icon spinning" /> : <Trash2 className="btn-icon" />}
                  删除关系
                </button>
              </form>
            )}
          </div>
        )}

        {/* 数据导出 */}
        {activeTab === 'export' && (
          <form onSubmit={handleExport} className="form">
            <div className="form-group">
              <label>
                输出路径 <span className="required">*</span>
              </label>
              <input
                type="text"
                value={exportForm.outputPath}
                onChange={(e) =>
                  setExportForm({ ...exportForm, outputPath: e.target.value })
                }
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label>文件格式</label>
              <select
                value={exportForm.fileFormat}
                onChange={(e) =>
                  setExportForm({ ...exportForm, fileFormat: e.target.value })
                }
                className="select-input"
              >
                <option value="csv">CSV</option>
                <option value="excel">Excel</option>
                <option value="md">Markdown</option>
                <option value="txt">Text</option>
              </select>
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={exportForm.includeVectorData}
                  onChange={(e) =>
                    setExportForm({ ...exportForm, includeVectorData: e.target.checked })
                  }
                />
                <span>包含向量数据</span>
              </label>
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? (
                <Loader2 className="btn-icon spinning" />
              ) : (
                <Download className="btn-icon" />
              )}
              导出数据
            </button>
          </form>
        )}

        {/* 结果显示 */}
        {result && (
          <div className={`alert alert-${result.type}`}>
            {result.type === 'success' && <CheckCircle className="alert-icon" />}
            {result.type === 'error' && <AlertTriangle className="alert-icon" />}
            {result.type === 'info' && <Info className="alert-icon" />}
            <div>
              <strong>{result.message}</strong>
              {result.data && (
                <pre className="result-data">{JSON.stringify(result.data, null, 2)}</pre>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default GraphManager;
