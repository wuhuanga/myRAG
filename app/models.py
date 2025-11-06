# -*- coding: utf-8 -*-
"""
Pydantic 模型定义
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel


# ==================== RAG 实例管理相关模型 ====================

class RAGInstanceCreate(BaseModel):
    """创建 RAG 实例请求模型"""
    rag_id: str
    description: Optional[str] = None
    working_dir: str
    workspace: str
    # 存储配置
    kv_storage: Optional[str] = None
    vector_storage: Optional[str] = None
    graph_storage: Optional[str] = None
    doc_status_storage: Optional[str] = None
    # 查询配置
    top_k: Optional[int] = None
    chunk_top_k: Optional[int] = None
    max_entity_tokens: Optional[int] = None
    max_relation_tokens: Optional[int] = None
    max_total_tokens: Optional[int] = None
    cosine_threshold: float = 0.3
    related_chunk_number: int = 5
    chunk_token_size: int = 1200
    chunk_overlap_token_size: int = 100
    enable_llm_cache: bool = True
    enable_llm_cache_for_entity_extract: bool = True
    # LLM 配置 (可选)
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dim: Optional[int] = None
    embedding_max_token: Optional[int] = None
    litellm_url: Optional[str] = None
    litellm_key: Optional[str] = None


class RAGInstanceInfo(BaseModel):
    """RAG 实例信息"""
    rag_id: str
    description: Optional[str] = None
    working_dir: str
    workspace: str
    created_at: str
    llm_model: str
    embedding_model: str


# ==================== 查询相关模型 ====================

class QueryRequest(BaseModel):
    """查询请求模型"""
    rag_id: str  # 指定使用的 RAG 实例 ID
    question: str
    mode: str = "hybrid"
    only_need_context: bool = True
    top_k: int = 20
    chunk_top_k: int = 10
    max_entity_tokens: int = 6000
    max_relation_tokens: int = 8000
    max_total_tokens: int = 16300


class QueryResponse(BaseModel):
    """查询响应模型"""
    rag_id: str
    question: str
    answer: str
    mode: str
    timestamp: str


class UCDModelRequest(BaseModel):
    """UCD建模请求模型"""
    rag_id: str
    question: str
    mode: str = "hybrid"
    out_json: str = "output_uc.json"


# ==================== 文档管理相关模型 ====================

class InsertRequest(BaseModel):
    """文档插入请求模型"""
    rag_id: str  # 指定使用的 RAG 实例 ID
    content: str
    file_path: str  # 必填:文件路径或文件名称
    doc_id: Optional[str] = None


class BatchInsertRequest(BaseModel):
    """批量插入请求模型"""
    rag_id: str
    documents: List[Dict[str, str]]  # [{content, file_path, doc_id?}, ...]


class DocumentUploadRequest(BaseModel):
    """文档上传请求 (用于查询参数)"""
    rag_id: str
    custom_id: Optional[str] = None


class DocumentStatusResponse(BaseModel):
    """文档状态响应模型"""
    total: int
    processed: int
    pending: int
    failed: int
    status_counts: dict


class DocumentListResponse(BaseModel):
    """文档列表响应模型"""
    status: str
    count: int
    documents: List[dict]


# ==================== 实体管理相关模型 ====================

class EntityCreateRequest(BaseModel):
    """创建实体请求"""
    rag_id: str
    entity_name: str
    description: Optional[str] = None
    entity_type: Optional[str] = "UNKNOWN"
    source_id: Optional[str] = "manual_creation"
    file_path: Optional[str] = "manual_creation"


class EntityEditRequest(BaseModel):
    """编辑实体请求"""
    rag_id: str
    entity_name: str
    updated_data: Dict[str, str]
    allow_rename: bool = True


class EntityDeleteRequest(BaseModel):
    """删除实体请求"""
    rag_id: str
    entity_name: str


class EntityInfoRequest(BaseModel):
    """获取实体信息请求"""
    rag_id: str
    entity_name: str
    include_vector_data: bool = False


class EntityMergeRequest(BaseModel):
    """合并实体请求"""
    rag_id: str
    source_entities: List[str]
    target_entity: str
    merge_strategy: Optional[Dict[str, str]] = None
    target_entity_data: Optional[Dict[str, Any]] = None


# ==================== 关系管理相关模型 ====================

class RelationCreateRequest(BaseModel):
    """创建关系请求"""
    rag_id: str
    source_entity: str
    target_entity: str
    description: Optional[str] = None
    keywords: Optional[str] = None
    weight: Optional[float] = 1.0
    source_id: Optional[str] = "manual_creation"
    file_path: Optional[str] = "manual_creation"


class RelationEditRequest(BaseModel):
    """编辑关系请求"""
    rag_id: str
    source_entity: str
    target_entity: str
    updated_data: Dict[str, Any]


class RelationDeleteRequest(BaseModel):
    """删除关系请求"""
    rag_id: str
    source_entity: str
    target_entity: str


class RelationInfoRequest(BaseModel):
    """获取关系信息请求"""
    rag_id: str
    source_entity: str
    target_entity: str
    include_vector_data: bool = False


# ==================== 数据导出相关模型 ====================

class ExportDataRequest(BaseModel):
    """数据导出请求"""
    rag_id: str
    output_path: str
    file_format: Literal["csv", "excel", "md", "txt"] = "csv"
    include_vector_data: bool = False


# ==================== 缓存管理相关模型 ====================

class ClearCacheRequest(BaseModel):
    """清除缓存请求"""
    rag_id: str
    cache_type: Literal["llm_cache", "all"] = "all"
