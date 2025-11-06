# -*- coding: utf-8 -*-
"""
RAG 后端 API 服务 - 完整版
FastAPI + WebSocket 实时通信 + 完整的实体关系管理

依赖安装：
pip install fastapi uvicorn python-multipart aiofiles

运行方式：
uvicorn backend_api_updated:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiofiles

# lightrag 相关导入
from dotenv import load_dotenv
import nest_asyncio
import textract
from lightrag import lightrag, QueryParam
from lightrag.llm.llama_index_impl import llama_index_complete_if_cache
from lightrag.llm.hf import hf_embed
from transformers import AutoModel, AutoTokenizer
from lightrag.utils import EmbeddingFunc
from llama_index.llms.litellm import LiteLLM
from lightrag.kg.shared_storage import initialize_pipeline_status

load_dotenv()
nest_asyncio.apply()

# ========== lightrag 处理器实现 ==========

class lightragProcessor:
    """lightrag 处理器，用于构建和查询知识图谱"""

    def __init__(
        self,
        working_dir: str,
        llm_model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        embedding_dim: Optional[int] = None,
        embedding_max_token: Optional[int] = None,
        litellm_url: Optional[str] = None,
        litellm_key: Optional[str] = None
    ):
        """
        初始化 lightrag 处理器

        Args:
            working_dir: 工作目录
            llm_model: LLM 模型名称
            embedding_model: Embedding 模型名称
            embedding_dim: Embedding 维度
            embedding_max_token: Embedding 最大 token 数
            litellm_url: LiteLLM 服务地址
            litellm_key: LiteLLM API 密钥
        """
        self.working_dir = Path(working_dir)
        
        # 从环境变量获取配置，优先使用传入参数
        self.llm_model = llm_model or os.environ.get("LLM_MODEL", "gpt-4")
        self.embedding_model = embedding_model or os.environ.get(
            "EMBEDDING_MODEL", 
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.embedding_dim = embedding_dim or int(os.environ.get("EMBEDDING_DIM", "384"))
        self.embedding_max_token = embedding_max_token or int(
            os.environ.get("EMBEDDING_MAX_TOKEN", "5000")
        )
        self.litellm_url = litellm_url or os.environ.get(
            "LITELLM_URL", 
            "http://localhost:4000"
        )
        self.litellm_key = litellm_key or os.environ.get("LITELLM_KEY", "sk-1234")

        # 创建工作目录
        self.working_dir.mkdir(exist_ok=True)

        self.rag = None

        logger.info(f"工作目录: {self.working_dir}")
        logger.info(f"LLM 模型: {self.llm_model}")
        logger.info(f"Embedding 模型: {self.embedding_model}")
        logger.info(f"Embedding 维度: {self.embedding_dim}")
        logger.info(f"Embedding 最大 Token: {self.embedding_max_token}")
        logger.info(f"LiteLLM URL: {self.litellm_url}")

    async def llm_model_func(self, prompt, system_prompt=None, history_messages=[], **kwargs):
        """
        LLM 模型调用函数

        Args:
            prompt: 提示词
            system_prompt: 系统提示词
            history_messages: 历史消息
            **kwargs: 其他参数

        Returns:
            模型响应
        """
        try:
            # Initialize LiteLLM if not in kwargs
            if "llm_instance" not in kwargs:
                llm_instance = LiteLLM(
                    model=f"openai/{self.llm_model}",
                    api_base=self.litellm_url,
                    api_key=self.litellm_key,
                    temperature=0.7,
                )
                kwargs["llm_instance"] = llm_instance

            response = await llama_index_complete_if_cache(
                kwargs["llm_instance"],
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
            )
            return response
        except Exception as e:
            logger.error(f"LLM 请求失败: {str(e)}")
            raise

    async def initialize_rag(self):
        """初始化 RAG 系统"""
        logger.info("正在初始化 lightrag 系统...")

        # 加载 Embedding 模型
        logger.info(f"正在加载 Embedding 模型: {self.embedding_model}")
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.embedding_model)
            embed_model = AutoModel.from_pretrained(self.embedding_model)
            logger.info("Embedding 模型加载完成")
        except Exception as e:
            logger.error(f"加载 Embedding 模型失败: {e}")
            logger.info(f"请确保 EMBEDDING_MODEL 环境变量或 --embedding_model 参数配置正确")
            raise

        self.rag = lightrag(
            working_dir=str(self.working_dir),
            llm_model_func=self.llm_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=self.embedding_dim,
                max_token_size=self.embedding_max_token,
                func=lambda texts: hf_embed(
                    texts,
                    tokenizer=tokenizer,
                    embed_model=embed_model,
                ),
            ),
            graph_storage="Neo4JStorage",   # 使用 Neo4j 存储知识图谱
            vector_storage="FaissVectorDBStorage",  # 使用 Faiss 存储向量数据库
            vector_db_storage_cls_kwargs={
                "cosine_better_than_threshold": 0.3  # 您期望的阈值
            },
        )

        await self.rag.initialize_storages()
        await initialize_pipeline_status()

        logger.info("lightrag 系统初始化完成")

    def insert_document(self, document_path: str, custom_id: Optional[str] = None):
        """
        插入文档到知识图谱，支持多种格式（PDF、DOCX、TXT等）

        Args:
            document_path: 文档路径
            custom_id: 可选的自定义文档ID
        """
        doc_path = Path(document_path)
        if not doc_path.exists():
            raise FileNotFoundError(f"文档不存在: {document_path}")

        logger.info(f"正在读取文档: {document_path}")
        
        try:
            # 使用 textract 提取文本内容
            logger.info(f"使用 textract 提取文档内容...")
            text_content = textract.process(str(doc_path))
            content = text_content.decode('utf-8')
            logger.info(f"文档提取成功 (文档长度: {len(content)} 字符)")
        except Exception as e:
            logger.error(f"使用 textract 提取文档失败: {e}")
            # 如果是 TXT 文件，尝试直接读取
            if doc_path.suffix.lower() == '.txt':
                logger.info("尝试直接读取 TXT 文件...")
                try:
                    with open(doc_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    logger.info(f"TXT 文件读取成功 (文档长度: {len(content)} 字符)")
                except Exception as txt_error:
                    logger.error(f"读取 TXT 文件也失败: {txt_error}")
                    raise
            else:
                raise

        if not content.strip():
            logger.warning(f"文档内容为空: {document_path}")
            return

        logger.info(f"正在插入文档到知识图谱...")
        # 使用文件名作为 file_path，支持自定义 ID
        file_name = doc_path.name
        if custom_id:
            self.rag.insert(content, ids=[custom_id], file_paths=[file_name])
        else:
            self.rag.insert(content, file_paths=[file_name])
        logger.info(f"文档插入完成: {file_name}")

    def insert_documents_batch(self, documents_data: List[dict]):
        """批量插入文档到知识图谱
        
        Args:
            documents_data: 文档数据列表，每个元素包含:
                - content: 文档内容
                - file_path: 文件名/路径
                - doc_id: 可选的文档ID
        """
        if not documents_data:
            logger.warning("没有文档需要插入")
            return
        
        contents = []
        file_paths = []
        doc_ids = []
        
        for doc in documents_data:
            contents.append(doc['content'])
            file_paths.append(doc['file_path'])
            if 'doc_id' in doc and doc['doc_id']:
                doc_ids.append(doc['doc_id'])
        
        logger.info(f"正在批量插入 {len(contents)} 个文档到知识图谱...")
        
        # 批量插入
        if doc_ids and len(doc_ids) == len(contents):
            self.rag.insert(contents, ids=doc_ids, file_paths=file_paths)
        else:
            self.rag.insert(contents, file_paths=file_paths)
        
        logger.info(f"批量插入完成: {len(contents)} 个文档")

    def query(self, question: str, mode: str = "hybrid") -> str:
        """
        查询知识图谱

        Args:
            question: 查询问题
            mode: 查询模式 (naive/local/global/hybrid)

        Returns:
            查询结果
        """
        if self.rag is None:
            raise ValueError("lightrag 系统未初始化")

        logger.info(f"查询模式: {mode}")
        logger.info(f"查询问题: {question}")

        result = self.rag.query(
            question,
            param=QueryParam(mode=mode, only_need_context=True)
        )

        # Normalize result to a single string (handle str or iterator/generator of str)
        if isinstance(result, str):
            out_text = result
        else:
            # Try to join iterable of strings; if that fails, fallback to str()
            try:
                out_text = "".join(result)
            except TypeError:
                out_text = str(result)

        return out_text


# 导入 UCD_RAG 建模器
try:
    from UCD_RAG import UCBuilder
except ImportError:
    UCBuilder = None
    logger.warning("未找到 UCD_RAG.py，UCD建模功能将不可用")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 应用
app = FastAPI(
    title="RAG Backend API",
    description="Complete RAG backend with entity/relation management",
    version="2.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
rag_processor: Optional[lightragProcessor] = None
ucd_builder: Optional[UCBuilder] = None
UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)

# ==================== Pydantic 模型定义 ====================

class InitRequest(BaseModel):
    """初始化请求模型"""
    working_dir: str = "./rag_working"
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dim: Optional[int] = None
    embedding_max_token: Optional[int] = None
    litellm_url: Optional[str] = None
    litellm_key: Optional[str] = None

class QueryRequest(BaseModel):
    """查询请求模型"""
    question: str
    mode: str = "hybrid"  # naive, local, global, hybrid

class QueryResponse(BaseModel):
    """查询响应模型"""
    question: str
    answer: str
    mode: str
    timestamp: str

class InsertRequest(BaseModel):
    """文档插入请求模型"""
    content: str
    file_path: str  # 必填：文件路径或文件名称
    doc_id: Optional[str] = None

class BatchInsertRequest(BaseModel):
    """批量插入请求模型"""
    documents: List[InsertRequest]

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

class UCDModelRequest(BaseModel):
    """UCD建模请求模型"""
    question: str
    mode: str = "hybrid"
    out_json: str = "output_uc.json"

# ========== 实体管理相关模型 ==========

class EntityCreateRequest(BaseModel):
    """创建实体请求"""
    entity_name: str
    description: Optional[str] = None
    entity_type: Optional[str] = "UNKNOWN"
    source_id: Optional[str] = "manual_creation"
    file_path: Optional[str] = "manual_creation"

class EntityEditRequest(BaseModel):
    """编辑实体请求"""
    entity_name: str
    updated_data: Dict[str, str]
    allow_rename: bool = True

class EntityDeleteRequest(BaseModel):
    """删除实体请求"""
    entity_name: str

class EntityInfoRequest(BaseModel):
    """获取实体信息请求"""
    entity_name: str
    include_vector_data: bool = False

class EntityMergeRequest(BaseModel):
    """合并实体请求"""
    source_entities: List[str]
    target_entity: str
    merge_strategy: Optional[Dict[str, str]] = None
    target_entity_data: Optional[Dict[str, Any]] = None

# ========== 关系管理相关模型 ==========

class RelationCreateRequest(BaseModel):
    """创建关系请求"""
    source_entity: str
    target_entity: str
    description: Optional[str] = None
    keywords: Optional[str] = None
    weight: Optional[float] = 1.0
    source_id: Optional[str] = "manual_creation"
    file_path: Optional[str] = "manual_creation"

class RelationEditRequest(BaseModel):
    """编辑关系请求"""
    source_entity: str
    target_entity: str
    updated_data: Dict[str, Any]

class RelationDeleteRequest(BaseModel):
    """删除关系请求"""
    source_entity: str
    target_entity: str

class RelationInfoRequest(BaseModel):
    """获取关系信息请求"""
    source_entity: str
    target_entity: str
    include_vector_data: bool = False

# ========== 数据导出相关模型 ==========

class ExportDataRequest(BaseModel):
    """数据导出请求"""
    output_path: str
    file_format: Literal["csv", "excel", "md", "txt"] = "csv"
    include_vector_data: bool = False

# WebSocket 管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket 连接建立，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket 断开连接，剩余连接数: {len(self.active_connections)}")
    
    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")

manager = ConnectionManager()

# ==================== API 端点 ====================

@app.get("/")
async def root():
    """根路由，返回 API 信息"""
    return {
        "service": "RAG Backend API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "system": [
                "/api/init - 初始化系统",
                "/api/health - 健康检查"
            ],
            "documents": [
                "/api/documents/upload - 上传文档",
                "/api/documents/insert - 插入文档内容",
                "/api/documents/batch_insert - 批量插入文档",
                "/api/documents/status - 获取文档状态",
                "/api/documents/list/{status} - 获取指定状态的文档列表"
            ],
            "query": [
                "/api/query - 查询知识库",
                "/api/query_ucd - UCD建模查询"
            ],
            "entities": [
                "/api/entities/create - 创建实体",
                "/api/entities/edit - 编辑实体",
                "/api/entities/delete - 删除实体",
                "/api/entities/info - 获取实体信息",
                "/api/entities/merge - 合并实体"
            ],
            "relations": [
                "/api/relations/create - 创建关系",
                "/api/relations/edit - 编辑关系",
                "/api/relations/delete - 删除关系",
                "/api/relations/info - 获取关系信息"
            ],
            "export": [
                "/api/export - 导出数据"
            ],
            "websocket": [
                "/ws - WebSocket 连接"
            ]
        }
    }

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "rag_initialized": rag_processor is not None,
        "ucd_initialized": ucd_builder is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/init")
async def initialize_system(request: InitRequest):
    """初始化 RAG 系统"""
    global rag_processor, ucd_builder
    
    try:
        logger.info(f"正在初始化 RAG 处理器，工作目录: {request.working_dir}")
        
        # 初始化 RAG 处理器
        rag_processor = lightragProcessor(
            working_dir=request.working_dir,
            llm_model=request.llm_model,
            embedding_model=request.embedding_model,
            embedding_dim=request.embedding_dim,
            embedding_max_token=request.embedding_max_token,
            litellm_url=request.litellm_url,
            litellm_key=request.litellm_key
        )
        
        # 初始化 RAG
        await rag_processor.initialize_rag()
        
        # 初始化 UCD 建模器（如果可用）
        if UCBuilder:
            logger.info("正在初始化 UCD 建模器...")
            ucd_builder = UCBuilder(
                base_url=request.litellm_url or "http://localhost:4000",
                api_key=request.litellm_key or "sk-1234",
                use_case_model_name=request.llm_model or "gpt-4"
            )
            logger.info("UCD 建模器初始化成功")
        else:
            logger.warning("UCD_RAG 模块不可用，跳过 UCD 建模器初始化")
        
        return {
            "status": "success",
            "message": "系统初始化成功",
            "working_dir": str(rag_processor.working_dir),
            "llm_model": rag_processor.llm_model,
            "ucd_available": ucd_builder is not None
        }
    
    except Exception as e:
        logger.error(f"初始化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")

# ========== 文档管理接口 ==========

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), custom_id: Optional[str] = None):
    """上传并处理文档"""
    if rag_processor is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        # 保存上传的文件
        file_path = UPLOAD_DIR / file.filename
        logger.info(f"正在保存文件: {file_path}")
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"文件保存成功，开始处理...")
        
        # 插入到知识图谱
        rag_processor.insert_document(str(file_path), custom_id)
        
        return {
            "status": "success",
            "message": f"文档 {file.filename} 已成功上传并处理",
            "file_path": str(file_path),
            "custom_id": custom_id
        }
    
    except Exception as e:
        logger.error(f"文档上传处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

@app.post("/api/documents/insert")
async def insert_document(request: InsertRequest):
    """直接插入文档内容"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    # 验证文件路径/名称是否提供
    if not request.file_path:
        raise HTTPException(
            status_code=400, 
            detail="必须提供 file_path 参数（文件路径或文件名称）"
        )
    
    try:
        logger.info(f"插入文档内容，文件: {request.file_path}, 长度: {len(request.content)} 字符")
        
        # 插入文档
        if request.doc_id:
            rag_processor.rag.insert(
                request.content,
                ids=[request.doc_id],
                file_paths=[request.file_path]
            )
        else:
            rag_processor.rag.insert(request.content, file_paths=[request.file_path])
        
        return {
            "status": "success",
            "message": f"文档内容已成功插入（文件: {request.file_path}）",
            "file_path": request.file_path,
            "doc_id": request.doc_id,
            "content_length": len(request.content)
        }
    
    except Exception as e:
        logger.error(f"文档插入失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档插入失败: {str(e)}")

@app.post("/api/documents/batch_insert")
async def batch_insert_documents(request: BatchInsertRequest):
    """批量插入文档"""
    if rag_processor is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        documents_data = []
        for idx, doc in enumerate(request.documents):
            # 验证每个文档都有文件路径
            if not doc.file_path:
                raise HTTPException(
                    status_code=400, 
                    detail=f"文档 {idx + 1} 缺少 file_path 参数（文件路径或文件名称）"
                )
            
            documents_data.append({
                'content': doc.content,
                'file_path': doc.file_path,
                'doc_id': doc.doc_id
            })
        
        logger.info(f"批量插入 {len(documents_data)} 个文档")
        
        # 批量插入
        rag_processor.insert_documents_batch(documents_data)
        
        return {
            "status": "success",
            "message": f"成功批量插入 {len(documents_data)} 个文档",
            "count": len(documents_data),
            "files": [doc['file_path'] for doc in documents_data]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量插入失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量插入失败: {str(e)}")

# ========== 查询接口 ==========

@app.post("/api/query", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest):
    """查询知识库"""
    if rag_processor is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        logger.info(f"查询: {request.question} (模式: {request.mode})")
        
        answer = rag_processor.query(request.question, request.mode)
        
        return QueryResponse(
            question=request.question,
            answer=answer,
            mode=request.mode,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

# ========== 实体管理接口 ==========

@app.post("/api/entities/create")
async def create_entity(request: EntityCreateRequest):
    """创建新实体"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        entity_data = {
            "description": request.description or "",
            "entity_type": request.entity_type,
            "source_id": request.source_id,
            "file_path": request.file_path
        }
        
        result = await rag_processor.rag.acreate_entity(
            request.entity_name,
            entity_data
        )
        
        return {
            "status": "success",
            "message": f"实体 '{request.entity_name}' 创建成功",
            "entity": result
        }
    
    except Exception as e:
        logger.error(f"创建实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建实体失败: {str(e)}")

@app.post("/api/entities/edit")
async def edit_entity(request: EntityEditRequest):
    """编辑实体"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        result = await rag_processor.rag.aedit_entity(
            request.entity_name,
            request.updated_data,
            request.allow_rename
        )
        
        return {
            "status": "success",
            "message": f"实体 '{request.entity_name}' 更新成功",
            "entity": result
        }
    
    except Exception as e:
        logger.error(f"编辑实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"编辑实体失败: {str(e)}")

@app.post("/api/entities/delete")
async def delete_entity(request: EntityDeleteRequest):
    """删除实体"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        result = await rag_processor.rag.adelete_by_entity(request.entity_name)
        
        return {
            "status": result.status,
            "message": result.message,
            "entity_name": request.entity_name
        }
    
    except Exception as e:
        logger.error(f"删除实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除实体失败: {str(e)}")

@app.post("/api/entities/info")
async def get_entity_info(request: EntityInfoRequest):
    """获取实体详细信息"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        info = await rag_processor.rag.get_entity_info(
            request.entity_name,
            request.include_vector_data
        )
        
        return {
            "status": "success",
            "entity_info": info
        }
    
    except Exception as e:
        logger.error(f"获取实体信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实体信息失败: {str(e)}")

@app.post("/api/entities/merge")
async def merge_entities(request: EntityMergeRequest):
    """合并多个实体"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        result = await rag_processor.rag.amerge_entities(
            request.source_entities,
            request.target_entity,
            request.merge_strategy,
            request.target_entity_data
        )
        
        return {
            "status": "success",
            "message": f"成功合并 {len(request.source_entities)} 个实体到 '{request.target_entity}'",
            "merged_entity": result
        }
    
    except Exception as e:
        logger.error(f"合并实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"合并实体失败: {str(e)}")

# ========== 关系管理接口 ==========

@app.post("/api/relations/create")
async def create_relation(request: RelationCreateRequest):
    """创建新关系"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        relation_data = {
            "description": request.description or "",
            "keywords": request.keywords or "",
            "weight": request.weight,
            "source_id": request.source_id,
            "file_path": request.file_path
        }
        
        result = await rag_processor.rag.acreate_relation(
            request.source_entity,
            request.target_entity,
            relation_data
        )
        
        return {
            "status": "success",
            "message": f"关系 '{request.source_entity}' -> '{request.target_entity}' 创建成功",
            "relation": result
        }
    
    except Exception as e:
        logger.error(f"创建关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建关系失败: {str(e)}")

@app.post("/api/relations/edit")
async def edit_relation(request: RelationEditRequest):
    """编辑关系"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        result = await rag_processor.rag.aedit_relation(
            request.source_entity,
            request.target_entity,
            request.updated_data
        )
        
        return {
            "status": "success",
            "message": f"关系 '{request.source_entity}' -> '{request.target_entity}' 更新成功",
            "relation": result
        }
    
    except Exception as e:
        logger.error(f"编辑关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"编辑关系失败: {str(e)}")

@app.post("/api/relations/delete")
async def delete_relation(request: RelationDeleteRequest):
    """删除关系"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        result = await rag_processor.rag.adelete_by_relation(
            request.source_entity,
            request.target_entity
        )
        
        return {
            "status": result.status,
            "message": result.message,
            "source_entity": request.source_entity,
            "target_entity": request.target_entity
        }
    
    except Exception as e:
        logger.error(f"删除关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除关系失败: {str(e)}")

@app.post("/api/relations/info")
async def get_relation_info(request: RelationInfoRequest):
    """获取关系详细信息"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        info = await rag_processor.rag.get_relation_info(
            request.source_entity,
            request.target_entity,
            request.include_vector_data
        )
        
        return {
            "status": "success",
            "relation_info": info
        }
    
    except Exception as e:
        logger.error(f"获取关系信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取关系信息失败: {str(e)}")

# ========== 数据导出接口 ==========

@app.post("/api/export")
async def export_data(request: ExportDataRequest):
    """导出知识图谱数据"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        await rag_processor.rag.aexport_data(
            request.output_path,
            request.file_format,
            request.include_vector_data
        )
        
        return {
            "status": "success",
            "message": f"数据已成功导出到 {request.output_path}",
            "output_path": request.output_path,
            "format": request.file_format
        }
    
    except Exception as e:
        logger.error(f"导出数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")

# ========== UCD 建模接口 ==========

@app.post("/api/query_ucd")
async def query_with_ucd(request: UCDModelRequest):
    """执行查询并进行 UCD 建模"""
    if rag_processor is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    if ucd_builder is None:
        raise HTTPException(status_code=400, detail="UCD 建模器未初始化")
    
    if request.mode not in ["naive", "local", "global", "hybrid"]:
        raise HTTPException(status_code=400, detail=f"无效的查询模式: {request.mode}")
    
    try:
        logger.info(f"[UCD建模流程] 查询问题: {request.question} (模式: {request.mode})")
        
        # 1. RAG 检索
        logger.info("[UCD建模流程] 步骤1: 执行 RAG 检索...")
        context = rag_processor.query(request.question, mode=request.mode)
        logger.info(f"[UCD建模流程] 检索到上下文内容 (长度: {len(context)} 字符)")
        
        # 2. UCD 建模
        logger.info("[UCD建模流程] 步骤2: 开始 UCD 建模...")
        ucd_result = ucd_builder.test_generate(
            question=request.question,
            chunks=context,
            out_json=request.out_json
        )
        logger.info("[UCD建模流程] UCD 建模完成")
        
        return {
            "status": "success",
            "question": request.question,
            "context": context,
            "ucd_model": ucd_result,
            "output_file": request.out_json,
            "mode": request.mode,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"[UCD建模流程] 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"UCD 建模失败: {str(e)}")

# ========== 文档状态管理接口 ==========

@app.get("/api/documents/status", response_model=DocumentStatusResponse)
async def get_documents_status():
    """获取所有文档的处理状态统计"""
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        logger.info("获取文档处理状态...")
        status_counts = await rag_processor.rag.get_processing_status()
        
        total = sum(status_counts.values())
        processed = status_counts.get('PROCESSED', 0)
        pending = status_counts.get('PENDING', 0)
        failed = status_counts.get('FAILED', 0)
        
        logger.info(f"文档状态统计: 总计={total}, 已处理={processed}, 待处理={pending}, 失败={failed}")
        
        return DocumentStatusResponse(
            total=total,
            processed=processed,
            pending=pending,
            failed=failed,
            status_counts=status_counts
        )
    except Exception as e:
        logger.error(f"获取文档状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档状态失败: {str(e)}")

@app.get("/api/documents/list/{status}")
async def get_documents_by_status(status: str):
    """根据状态获取文档列表
    
    参数:
        status: PROCESSED, PENDING, 或 FAILED
    """
    if rag_processor is None or rag_processor.rag is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    # 验证状态参数
    valid_statuses = ['PROCESSED', 'PENDING', 'FAILED']
    status_upper = status.upper()
    if status_upper not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的状态: {status}. 有效值: {', '.join(valid_statuses)}"
        )
    
    try:
        from lightrag.base import DocStatus
        
        logger.info(f"获取状态为 {status_upper} 的文档列表...")
        
        # 将字符串状态转换为 DocStatus 枚举
        doc_status = DocStatus[status_upper]
        
        # 获取文档字典 {doc_id: DocProcessingStatus}
        docs_dict = await rag_processor.rag.get_docs_by_status(doc_status)
        
        # 转换为可序列化的格式
        documents = []
        for doc_id, status_info in docs_dict.items():
            # status_info 是 DocProcessingStatus 对象
            file_name = status_info.file_path if hasattr(status_info, 'file_path') else 'N/A'
            
            # 获取其他可能的属性
            created_at = getattr(status_info, 'created_at', None)
            updated_at = getattr(status_info, 'updated_at', None)
            error_msg = getattr(status_info, 'error_message', None)
            
            doc_info = {
                "doc_id": doc_id,
                "file_name": file_name,
                "created_at": str(created_at) if created_at else None,
                "updated_at": str(updated_at) if updated_at else None,
                "error_message": error_msg,
                "status": status_upper
            }
            documents.append(doc_info)
        
        logger.info(f"找到 {len(documents)} 个状态为 {status_upper} 的文档")
        
        return DocumentListResponse(
            status=status_upper,
            count=len(documents),
            documents=documents
        )
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

# ========== WebSocket 端点 ==========

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点，用于实时通信"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "query":
                if rag_processor is None:
                    await manager.send_message({
                        "type": "error",
                        "message": "请先初始化 RAG 系统"
                    }, websocket)
                    continue
                
                try:
                    question = data["question"]
                    mode = data.get("mode", "hybrid")
                    
                    await manager.send_message({
                        "type": "status",
                        "message": "正在查询..."
                    }, websocket)
                    
                    context = rag_processor.query(question, mode=mode)
                    
                    await manager.send_message({
                        "type": "answer",
                        "question": question,
                        "context": context,
                        "mode": mode
                    }, websocket)
                
                except Exception as e:
                    await manager.send_message({
                        "type": "error",
                        "message": str(e)
                    }, websocket)
            
            elif data["type"] == "entity_operation":
                # 处理实体相关操作
                operation = data.get("operation")
                
                if operation == "create":
                    entity_name = data.get("entity_name")
                    entity_data = data.get("entity_data", {})
                    result = await rag_processor.rag.acreate_entity(entity_name, entity_data)
                    
                    await manager.send_message({
                        "type": "entity_created",
                        "result": result
                    }, websocket)
                
                elif operation == "delete":
                    entity_name = data.get("entity_name")
                    result = await rag_processor.rag.adelete_by_entity(entity_name)
                    
                    await manager.send_message({
                        "type": "entity_deleted",
                        "result": {"status": result.status, "message": result.message}
                    }, websocket)
            
            elif data["type"] == "query_ucd":
                if rag_processor is None or ucd_builder is None:
                    await manager.send_message({
                        "type": "error",
                        "message": "请先初始化系统"
                    }, websocket)
                    continue
                
                try:
                    question = data["question"]
                    mode = data.get("mode", "hybrid")
                    out_json = data.get("out_json", "output_uc.json")
                    
                    await manager.send_message({
                        "type": "status",
                        "message": "正在检索知识..."
                    }, websocket)
                    
                    context = rag_processor.query(question, mode=mode)
                    
                    await manager.send_message({
                        "type": "status",
                        "message": "正在进行 UCD 建模..."
                    }, websocket)
                    
                    ucd_result = ucd_builder.test_generate(
                        question=question,
                        chunks=context,
                        out_json=out_json
                    )
                    
                    await manager.send_message({
                        "type": "ucd_result",
                        "question": question,
                        "context": context,
                        "ucd_model": ucd_result,
                        "output_file": out_json
                    }, websocket)
                
                except Exception as e:
                    await manager.send_message({
                        "type": "error",
                        "message": str(e)
                    }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)