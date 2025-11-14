# -*- coding: utf-8 -*-
"""
xwrag 后端 API 服务 + UCD_RAG 建模
FastAPI + WebSocket 实时通信

依赖安装：
pip install fastapi uvicorn python-multipart aiofiles

运行方式：
uvicorn backend_api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiofiles

# 导入 xwrag 处理器
try:
    from xwrag_cli import xwragProcessor
except ImportError:
    import os
    from pathlib import Path
    from typing import Optional
    from dotenv import load_dotenv
    import nest_asyncio
    import textract
    from xwrag import xwrag, QueryParam
    from xwrag.llm.llama_index_impl import llama_index_complete_if_cache
    from xwrag.llm.hf import hf_embed
    from transformers import AutoModel, AutoTokenizer
    from xwrag.utils import EmbeddingFunc
    from llama_index.llms.litellm import LiteLLM
    from xwrag.kg.shared_storage import initialize_pipeline_status
    
    load_dotenv()
    nest_asyncio.apply()
    
    class xwragProcessor:
        """xwrag 处理器，用于构建和查询知识图谱"""

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
            self.working_dir = Path(working_dir)
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
            self.working_dir.mkdir(exist_ok=True)
            self.rag = None
            logger.info(f"工作目录: {self.working_dir}")
            logger.info(f"LLM 模型: {self.llm_model}")

        async def llm_model_func(self, prompt, system_prompt=None, history_messages=[], **kwargs):
            try:
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
            logger.info("正在初始化 xwrag 系统...")
            try:
                tokenizer = AutoTokenizer.from_pretrained(self.embedding_model)
                embed_model = AutoModel.from_pretrained(self.embedding_model)
                logger.info("Embedding 模型加载完成")
            except Exception as e:
                logger.error(f"加载 Embedding 模型失败: {e}")
                raise

            self.rag = xwrag(
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
                graph_storage="Neo4JStorage",
                vector_storage="FaissVectorDBStorage",
                vector_db_storage_cls_kwargs={
                    "cosine_better_than_threshold": 0.3
                },
            )
            await self.rag.initialize_storages()
            await initialize_pipeline_status()
            logger.info("xwrag 系统初始化完成")

        def insert_document(self, document_path: str, custom_id: Optional[str] = None):
            """插入单个文档到知识图谱"""
            doc_path = Path(document_path)
            if not doc_path.exists():
                raise FileNotFoundError(f"文档不存在: {document_path}")
            logger.info(f"正在读取文档: {document_path}")
            try:
                text_content = textract.process(str(doc_path))
                content = text_content.decode('utf-8')
                logger.info(f"文档提取成功 (文档长度: {len(content)} 字符)")
            except Exception as e:
                logger.error(f"使用 textract 提取文档失败: {e}")
                if doc_path.suffix.lower() == '.txt':
                    with open(doc_path, "r", encoding="utf-8") as f:
                        content = f.read()
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
            """查询并返回检索到的上下文内容"""
            if self.rag is None:
                raise ValueError("RAG 系统未初始化")
            logger.info(f"查询模式: {mode}")
            logger.info(f"查询问题: {question}")
            result = self.rag.query(question, param=QueryParam(mode=mode))
            return result
        
        def query_with_llm(self, question: str, mode: str = "hybrid") -> str:
            """查询并返回RAG大模型生成的完整答案"""
            if self.rag is None:
                raise ValueError("RAG 系统未初始化")
            logger.info(f"查询模式: {mode} (带LLM生成)")
            logger.info(f"查询问题: {question}")
            result = self.rag.query(question, param=QueryParam(mode=mode, only_need_context=False))
            return result

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
    title="XWrag + UCD_RAG API",
    description="基于 XWrag 的知识图谱 RAG 系统 + UCD 建模",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 RAG 处理器和 UCD 建模器
rag_processor: Optional[xwragProcessor] = None
ucd_builder: Optional[UCBuilder] = None
temp_dir = Path("./temp_uploads")
temp_dir.mkdir(exist_ok=True)

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# Pydantic 模型
class InitRequest(BaseModel):
    working_dir: str  # 必需参数

class QueryRequest(BaseModel):
    question: str
    mode: str = "hybrid"

class UCDQueryRequest(BaseModel):
    question: str
    mode: str = "hybrid"
    out_json: Optional[str] = "output_uc.json"

class DocumentStatusResponse(BaseModel):
    total: int
    processed: int
    pending: int
    failed: int
    status_counts: dict

class DocumentListResponse(BaseModel):
    status: str
    count: int
    documents: List[dict]

class StatusResponse(BaseModel):
    initialized: bool
    ucd_initialized: bool
    working_dir: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dim: Optional[int] = None
    litellm_url: Optional[str] = None

# API 端点

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "XWrag + UCD_RAG API Server",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """获取系统状态"""
    if rag_processor is None:
        return StatusResponse(
            initialized=False,
            ucd_initialized=(ucd_builder is not None)
        )
    
    return StatusResponse(
        initialized=True,
        ucd_initialized=(ucd_builder is not None),
        working_dir=str(rag_processor.working_dir),
        llm_model=rag_processor.llm_model,
        embedding_model=rag_processor.embedding_model,
        embedding_dim=rag_processor.embedding_dim,
        litellm_url=rag_processor.litellm_url
    )

@app.post("/api/initialize")
async def initialize_system(request: InitRequest):
    """初始化 RAG 系统和 UCD 建模器"""
    global rag_processor, ucd_builder
    
    try:
        logger.info(f"开始初始化 RAG 系统: {request.working_dir}")
        logger.info("使用 .env 文件中的配置")
        
        # 初始化 RAG 处理器
        rag_processor = xwragProcessor(
            working_dir=request.working_dir
        )
        await rag_processor.initialize_rag()
        
        # 初始化 UCD 建模器（使用后端的 LLM 配置）
        if UCBuilder is not None:
            logger.info("正在初始化 UCD 建模器...")
            ucd_builder = UCBuilder()
            # 将后端的 LLM 配置传递给 UCD 建模器
            ucd_builder.llm_model = rag_processor.llm_model
            ucd_builder.litellm_url = rag_processor.litellm_url
            ucd_builder.litellm_key = rag_processor.litellm_key
            # 重新初始化 UCD 的 LLM 客户端
            from openai import OpenAI
            ucd_builder.client = OpenAI(
                api_key=rag_processor.litellm_key,
                base_url=rag_processor.litellm_url
            )
            ucd_builder.chat_model = rag_processor.llm_model
            logger.info("UCD 建模器初始化成功")
        
        logger.info("系统初始化成功")
        return {
            "status": "success",
            "message": "系统初始化成功",
            "working_dir": str(rag_processor.working_dir),
            "config": {
                "llm_model": rag_processor.llm_model,
                "embedding_model": rag_processor.embedding_model,
                "embedding_dim": rag_processor.embedding_dim,
                "litellm_url": rag_processor.litellm_url
            },
            "ucd_enabled": (ucd_builder is not None)
        }
    
    except Exception as e:
        logger.error(f"初始化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档"""
    if rag_processor is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    try:
        # 保存上传的文件
        file_path = temp_dir / file.filename
        logger.info(f"保存上传文件: {file_path}")
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # 插入文档到知识图谱
        logger.info(f"开始处理文档: {file.filename}")
        rag_processor.insert_document(str(file_path))
        
        # 删除临时文件
        file_path.unlink()
        
        logger.info(f"文档处理完成: {file.filename}")
        return {
            "status": "success",
            "message": f"文档 {file.filename} 上传并处理成功",
            "filename": file.filename
        }
    
    except Exception as e:
        logger.error(f"文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")

@app.post("/api/query")
async def query_knowledge(request: QueryRequest):
    """查询知识图谱(仅返回检索内容)"""
    if rag_processor is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    if request.mode not in ["naive", "local", "global", "hybrid"]:
        raise HTTPException(status_code=400, detail=f"无效的查询模式: {request.mode}")
    
    try:
        logger.info(f"查询问题: {request.question} (模式: {request.mode})")
        
        # 获取检索内容
        context = rag_processor.query(request.question, mode=request.mode)
        
        logger.info("查询完成")
        return {
            "status": "success",
            "question": request.question,
            "context": context,
            "mode": request.mode,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.post("/api/query_llm")
async def query_knowledge_with_llm(request: QueryRequest):
    """查询知识图谱并返回RAG大模型生成的完整答案"""
    if rag_processor is None:
        raise HTTPException(status_code=400, detail="请先初始化 RAG 系统")
    
    if request.mode not in ["naive", "local", "global", "hybrid"]:
        raise HTTPException(status_code=400, detail=f"无效的查询模式: {request.mode}")
    
    try:
        logger.info(f"查询问题(带LLM生成): {request.question} (模式: {request.mode})")
        
        # 获取LLM生成的完整答案
        answer = rag_processor.query_with_llm(request.question, mode=request.mode)
        
        logger.info("LLM查询完成")
        return {
            "status": "success",
            "question": request.question,
            "answer": answer,
            "mode": request.mode,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"LLM查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM查询失败: {str(e)}")

@app.post("/api/query_ucd")
async def query_and_model_ucd(request: UCDQueryRequest):
    """查询知识图谱 + UCD 建模（集成流程）"""
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
        from xwrag.base import DocStatus
        
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
            
            elif data["type"] == "query_llm":
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
                        "message": "正在查询并生成答案..."
                    }, websocket)
                    
                    answer = rag_processor.query_with_llm(question, mode=mode)
                    
                    await manager.send_message({
                        "type": "answer_llm",
                        "question": question,
                        "answer": answer,
                        "mode": mode
                    }, websocket)
                
                except Exception as e:
                    await manager.send_message({
                        "type": "error",
                        "message": str(e)
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