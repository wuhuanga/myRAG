import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==================== 系统管理 ====================

export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

export const initializeSystem = async (config) => {
  const response = await api.post('/api/init', config);
  return response.data;
};

// ==================== 文档管理 ====================

export const uploadDocument = async (file, customId = null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (customId) {
    formData.append('custom_id', customId);
  }

  const response = await api.post('/api/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const insertDocument = async (content, filePath, docId = null) => {
  const response = await api.post('/api/documents/insert', {
    content,
    file_path: filePath,
    doc_id: docId,
  });
  return response.data;
};

export const batchInsertDocuments = async (documents) => {
  const response = await api.post('/api/documents/batch_insert', {
    documents,
  });
  return response.data;
};

export const getDocumentsStatus = async () => {
  const response = await api.get('/api/documents/status');
  return response.data;
};

export const getDocumentsByStatus = async (status) => {
  const response = await api.get(`/api/documents/list/${status}`);
  return response.data;
};

// ==================== 查询 ====================

export const queryKnowledge = async (question, mode = 'hybrid') => {
  const response = await api.post('/api/query', {
    question,
    mode,
  });
  return response.data;
};

export const queryWithUCD = async (question, mode = 'hybrid', outJson = 'output_uc.json') => {
  const response = await api.post('/api/query_ucd', {
    question,
    mode,
    out_json: outJson,
  });
  return response.data;
};

// ==================== 实体管理 ====================

export const createEntity = async (entityName, description, entityType, sourceId, filePath) => {
  const response = await api.post('/api/entities/create', {
    entity_name: entityName,
    description,
    entity_type: entityType,
    source_id: sourceId,
    file_path: filePath,
  });
  return response.data;
};

export const editEntity = async (entityName, updatedData, allowRename = true) => {
  const response = await api.post('/api/entities/edit', {
    entity_name: entityName,
    updated_data: updatedData,
    allow_rename: allowRename,
  });
  return response.data;
};

export const deleteEntity = async (entityName) => {
  const response = await api.post('/api/entities/delete', {
    entity_name: entityName,
  });
  return response.data;
};

export const getEntityInfo = async (entityName, includeVectorData = false) => {
  const response = await api.post('/api/entities/info', {
    entity_name: entityName,
    include_vector_data: includeVectorData,
  });
  return response.data;
};

export const mergeEntities = async (sourceEntities, targetEntity, mergeStrategy = null, targetEntityData = null) => {
  const response = await api.post('/api/entities/merge', {
    source_entities: sourceEntities,
    target_entity: targetEntity,
    merge_strategy: mergeStrategy,
    target_entity_data: targetEntityData,
  });
  return response.data;
};

// ==================== 关系管理 ====================

export const createRelation = async (sourceEntity, targetEntity, description, keywords, weight, sourceId, filePath) => {
  const response = await api.post('/api/relations/create', {
    source_entity: sourceEntity,
    target_entity: targetEntity,
    description,
    keywords,
    weight,
    source_id: sourceId,
    file_path: filePath,
  });
  return response.data;
};

export const editRelation = async (sourceEntity, targetEntity, updatedData) => {
  const response = await api.post('/api/relations/edit', {
    source_entity: sourceEntity,
    target_entity: targetEntity,
    updated_data: updatedData,
  });
  return response.data;
};

export const deleteRelation = async (sourceEntity, targetEntity) => {
  const response = await api.post('/api/relations/delete', {
    source_entity: sourceEntity,
    target_entity: targetEntity,
  });
  return response.data;
};

export const getRelationInfo = async (sourceEntity, targetEntity, includeVectorData = false) => {
  const response = await api.post('/api/relations/info', {
    source_entity: sourceEntity,
    target_entity: targetEntity,
    include_vector_data: includeVectorData,
  });
  return response.data;
};

// ==================== 数据导出 ====================

export const exportData = async (outputPath, fileFormat = 'csv', includeVectorData = false) => {
  const response = await api.post('/api/export', {
    output_path: outputPath,
    file_format: fileFormat,
    include_vector_data: includeVectorData,
  });
  return response.data;
};

export default api;
