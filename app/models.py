# -*- coding: utf-8 -*-
"""
Pydantic 模型定义
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel


# ==================== RAG 实例管理相关模型 ====================

class RAGInstanceCreate(BaseModel):
    """
    创建 RAG 实例请求模型

    注意：LLM 和 Embedding 模型配置从环境变量读取：
    - LLM_MODEL: LLM 模型名称（默认 gpt-4）
    - EMBEDDING_MODEL: Embedding 模型路径（默认 sentence-transformers/all-MiniLM-L6-v2）
    - EMBEDDING_DIM: Embedding 维度（默认 384）
    - EMBEDDING_MAX_TOKEN: 最大 token 数（默认 5000）
    - LITELLM_URL: LiteLLM 服务地址（默认 http://localhost:4000）
    - LITELLM_KEY: LiteLLM API 密钥（默认 sk-1234）

    存储配置固定使用：
    - 图存储: Neo4JStorage
    - 向量存储: FaissVectorDBStorage
    """
    rag_id: str
    description: Optional[str] = None
    working_dir: str = "./rag_storage"
    workspace: str
    # 查询配置（可选）
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
    # NebulaGraph 连接池配置（可选，用于多实例场景）
    nebula_max_connection_pool_size: Optional[int] = None  # 如果不设置，使用环境变量 NEBULA_MAX_CONNECTION_POOL_SIZE（默认 10）
    # 新增高优先级参数（None 表示使用 xwrag 默认值/环境变量）
    language: Optional[str] = None  # 文档处理语言
    entity_types: Optional[List[str]] = None  # 要提取的实体类型
    entity_extract_max_gleaning: Optional[int] = None  # 实体提取最大尝试次数
    kg_chunk_pick_method: Optional[str] = None  # 文本块选择方法（WEIGHT/VECTOR）
    llm_model_max_async: Optional[int] = None  # 最大并发 LLM 调用数
    embedding_func_max_async: Optional[int] = None  # 最大并发 Embedding 调用数
    max_parallel_insert: Optional[int] = None  # 最大并行插入数
    max_graph_nodes: Optional[int] = None  # 知识图谱返回最大节点数
    # LLM 响应处理
    strip_think_tags: bool = False  # 是否去除 LLM 响应中的 <think> 块


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
    """查询请求模型（支持单知识库和多知识库查询）"""
    # 知识库标识（二选一）
    rag_id: Optional[str] = None  # 单知识库模式（向后兼容）
    rag_ids: Optional[List[str]] = None  # 多知识库模式

    question: str
    mode: str = "hybrid"
    only_need_context: bool = True
    # 检索参数（None 表示使用 xwrag 默认值/环境变量）
    top_k: Optional[int] = None  # 检索的实体/关系数量
    chunk_top_k: Optional[int] = None  # 检索的文本块数量
    max_entity_tokens: Optional[int] = None  # 实体最大 token 数
    max_relation_tokens: Optional[int] = None  # 关系最大 token 数
    max_total_tokens: Optional[int] = None  # 总最大 token 数
    # 新增高优先级参数（None 表示使用 xwrag 默认值/环境变量）
    stream: Optional[bool] = None  # 是否启用流式输出
    enable_rerank: Optional[bool] = None  # 是否启用 Rerank
    response_type: Optional[str] = None  # 响应格式
    conversation_history: Optional[List[Dict[str, str]]] = None  # 对话历史
    hl_keywords: Optional[List[str]] = None  # 高优先级关键词
    ll_keywords: Optional[List[str]] = None  # 低优先级关键词
    user_prompt: Optional[str] = None  # 用户自定义提示词
    include_references: Optional[bool] = None  # 是否包含引用列表

    def get_rag_ids(self) -> List[str]:
        """获取知识库 ID 列表（统一处理单库和多库）"""
        if self.rag_ids:
            return self.rag_ids
        elif self.rag_id:
            return [self.rag_id]
        else:
            raise ValueError("必须提供 rag_id 或 rag_ids")


class QueryResponse(BaseModel):
    """查询响应模型"""
    rag_ids: List[str]  # 实际查询的知识库列表
    question: str
    answer: str
    mode: str
    timestamp: str
    # 可选：每个知识库的贡献来源（用于调试和追踪）
    sources: Optional[List[Dict[str, Any]]] = None


class KeywordsSearchRequest(BaseModel):
    """关键字检索请求模型（支持单知识库和多知识库查询）"""
    # 知识库标识（二选一）
    rag_id: Optional[str] = None  # 单知识库模式（向后兼容）
    rag_ids: Optional[List[str]] = None  # 多知识库模式

    keywords: Optional[List[str]] = None  # 关键字列表（可选）
    mode: str = "hybrid"  # 检索模式
    only_need_context: bool = True  # 只返回上下文，不调用 LLM
    # 检索参数
    top_k: Optional[int] = None
    chunk_top_k: Optional[int] = None
    max_entity_tokens: Optional[int] = None
    max_relation_tokens: Optional[int] = None
    max_total_tokens: Optional[int] = None
    enable_rerank: Optional[bool] = None

    def get_rag_ids(self) -> List[str]:
        """获取知识库 ID 列表（统一处理单库和多库）"""
        if self.rag_ids:
            return self.rag_ids
        elif self.rag_id:
            return [self.rag_id]
        else:
            raise ValueError("必须提供 rag_id 或 rag_ids")


class KeywordsSearchResponse(BaseModel):
    """关键字检索响应模型"""
    rag_ids: List[str]  # 实际查询的知识库列表
    keywords: Optional[List[str]] = None
    context: str
    mode: str
    timestamp: str
    # 可选：每个知识库的贡献来源（用于调试和追踪）
    sources: Optional[List[Dict[str, Any]]] = None


class UCDModelRequest(BaseModel):
    """UCD建模请求模型（支持单知识库和多知识库查询）"""
    # 知识库标识（二选一）
    rag_id: Optional[str] = None  # 单知识库模式（向后兼容）
    rag_ids: Optional[List[str]] = None  # 多知识库模式

    question: str
    mode: str = "hybrid"
    out_json: str = "output_uc.json"

    def get_rag_ids(self) -> List[str]:
        """获取知识库 ID 列表（统一处理单库和多库）"""
        if self.rag_ids:
            return self.rag_ids
        elif self.rag_id:
            return [self.rag_id]
        else:
            raise ValueError("必须提供 rag_id 或 rag_ids")


class GraphCleanRequest(BaseModel):
    """清理后的知识图谱检索请求模型（支持单知识库和多知识库查询）"""
    # 知识库标识（二选一）
    rag_id: Optional[str] = None  # 单知识库模式（向后兼容）
    rag_ids: Optional[List[str]] = None  # 多知识库模式

    keywords: Optional[List[str]] = None  # 关键字列表（可选）
    # 检索参数（可选）
    top_k: Optional[int] = None
    chunk_top_k: Optional[int] = None
    max_entity_tokens: Optional[int] = None
    max_relation_tokens: Optional[int] = None
    max_total_tokens: Optional[int] = None
    enable_rerank: Optional[bool] = None

    def get_rag_ids(self) -> List[str]:
        """获取知识库 ID 列表（统一处理单库和多库）"""
        if self.rag_ids:
            return self.rag_ids
        elif self.rag_id:
            return [self.rag_id]
        else:
            raise ValueError("必须提供 rag_id 或 rag_ids")


class CleanEntity(BaseModel):
    """清理后的实体模型"""
    entity_name: str
    description: str
    entity_type: str


class CleanRelationship(BaseModel):
    """清理后的关系模型"""
    src_id: str
    tgt_id: str
    description: str
    keywords: str


class GraphCleanResponse(BaseModel):
    """清理后的知识图谱检索响应模型"""
    rag_ids: List[str]  # 实际查询的知识库列表
    keywords: Optional[List[str]] = None
    entities: List[CleanEntity]
    relationships: List[CleanRelationship]
    timestamp: str
    # 可选：每个知识库的贡献来源（用于调试和追踪）
    sources: Optional[List[Dict[str, Any]]] = None


class ChunksOnlyRequest(BaseModel):
    """仅返回chunks的检索请求模型（支持单知识库和多知识库查询）"""
    # 知识库标识（二选一）
    rag_id: Optional[str] = None  # 单知识库模式（向后兼容）
    rag_ids: Optional[List[str]] = None  # 多知识库模式

    keywords: Optional[List[str]] = None  # 关键字列表（可选）
    # 检索参数（可选）
    chunk_top_k: Optional[int] = None
    max_total_tokens: Optional[int] = None
    enable_rerank: Optional[bool] = None

    def get_rag_ids(self) -> List[str]:
        """获取知识库 ID 列表（统一处理单库和多库）"""
        if self.rag_ids:
            return self.rag_ids
        elif self.rag_id:
            return [self.rag_id]
        else:
            raise ValueError("必须提供 rag_id 或 rag_ids")


class ChunkItem(BaseModel):
    """Chunk 数据模型"""
    content: str
    file_path: str
    chunk_id: str
    reference_id: str


class ChunksOnlyResponse(BaseModel):
    """仅返回chunks的检索响应模型"""
    rag_ids: List[str]  # 实际查询的知识库列表
    keywords: Optional[List[str]] = None
    chunks: List[ChunkItem]
    timestamp: str
    # 可选：每个知识库的贡献来源（用于调试和追踪）
    sources: Optional[List[Dict[str, Any]]] = None


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
    processing: int
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
    file_format: Literal["csv", "excel", "md", "txt", "echarts"] = "csv"
    include_vector_data: bool = False


# ==================== 缓存管理相关模型 ====================

class ClearCacheRequest(BaseModel):
    """清除缓存请求"""
    rag_id: str
    cache_type: Literal["llm_cache", "all"] = "all"


# ==================== 多知识库图谱查询相关模型 ====================

class MultiKnowledgeGraphRequest(BaseModel):
    """
    多知识库图谱查询请求模型

    支持查询单个或多个知识库的图谱数据
    """
    rag_ids: List[str]  # 知识库 ID 列表，支持一个或多个

