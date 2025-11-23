# -*- coding: utf-8 -*-
"""
依赖项和 RAG 实例管理 - 并发安全版本
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

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

from .models import RAGInstanceCreate, RAGInstanceInfo

load_dotenv()
nest_asyncio.apply()

logger = logging.getLogger(__name__)


# ==================== xwrag 处理器实现 ====================

class xwragProcessor:
    """xwrag 处理器,用于构建和查询知识图谱"""

    def __init__(
        self,
        working_dir: str,
        workspace: Optional[str] = None,
        # 查询和分块参数（可选）
        top_k: Optional[int] = None,
        chunk_top_k: Optional[int] = None,
        max_entity_tokens: Optional[int] = None,
        max_relation_tokens: Optional[int] = None,
        max_total_tokens: Optional[int] = None,
        cosine_threshold: float = 0.3,
        related_chunk_number: int = 5,
        chunk_token_size: int = 1200,
        chunk_overlap_token_size: int = 100,
        enable_llm_cache: bool = True,
        enable_llm_cache_for_entity_extract: bool = True,
        # NebulaGraph 连接池配置（可选）
        nebula_max_connection_pool_size: Optional[int] = None,
        # 新增高优先级参数（None 表示使用 xwrag 默认值/环境变量）
        language: Optional[str] = None,
        entity_types: Optional[list] = None,
        entity_extract_max_gleaning: Optional[int] = None,
        kg_chunk_pick_method: Optional[str] = None,
        llm_model_max_async: Optional[int] = None,
        embedding_func_max_async: Optional[int] = None,
        max_parallel_insert: Optional[int] = None,
        max_graph_nodes: Optional[int] = None,
    ):
        """
        初始化 xwrag 处理器

        LLM 和 Embedding 配置从环境变量读取（与 xwrag_cli.py 一致）：
        - LLM_MODEL: LLM 模型名称（默认 gpt-4）
        - EMBEDDING_MODEL: Embedding 模型路径（默认 sentence-transformers/all-MiniLM-L6-v2）
        - EMBEDDING_DIM: Embedding 维度（默认 384）
        - EMBEDDING_MAX_TOKEN: 最大 token 数（默认 5000）
        - LITELLM_URL: LiteLLM 服务地址（默认 http://localhost:4000）
        - LITELLM_KEY: LiteLLM API 密钥（默认 sk-1234）

        存储配置固定使用：
        - 图存储: Neo4JStorage
        - 向量存储: FaissVectorDBStorage

        Args:
            working_dir: 工作目录
            workspace: 工作空间（必须唯一）
            top_k: 查询返回的 top k 结果
            chunk_top_k: 分块查询返回的 top k 结果
            max_entity_tokens: 实体的最大 token 数
            max_relation_tokens: 关系的最大 token 数
            max_total_tokens: 总的最大 token 数
            cosine_threshold: 余弦相似度阈值
            related_chunk_number: 相关分块数量
            chunk_token_size: 分块 token 大小
            chunk_overlap_token_size: 分块重叠 token 大小
            enable_llm_cache: 是否启用 LLM 缓存
            enable_llm_cache_for_entity_extract: 是否为实体提取启用 LLM 缓存
        """
        self.working_dir = Path(working_dir)
        self.workspace = workspace

        # 从环境变量获取 LLM 和 Embedding 配置（与 xwrag_cli.py 一致）
        self.llm_model = os.environ.get("LLM_MODEL", "gpt-4")
        self.embedding_model = os.environ.get(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.embedding_dim = int(os.environ.get("EMBEDDING_DIM", "384"))
        self.embedding_max_token = int(os.environ.get("EMBEDDING_MAX_TOKEN", "5000"))
        self.litellm_url = os.environ.get("LITELLM_URL", "http://localhost:4000")
        self.litellm_key = os.environ.get("LITELLM_KEY", "sk-1234")
        self.top_k = top_k
        self.chunk_top_k = chunk_top_k
        self.max_entity_tokens = max_entity_tokens
        self.max_relation_tokens = max_relation_tokens
        self.max_total_tokens = max_total_tokens
        self.cosine_threshold = cosine_threshold
        self.related_chunk_number = related_chunk_number
        self.chunk_token_size = chunk_token_size
        self.chunk_overlap_token_size = chunk_overlap_token_size
        self.enable_llm_cache = enable_llm_cache
        self.enable_llm_cache_for_entity_extract = enable_llm_cache_for_entity_extract
        self.nebula_max_connection_pool_size = nebula_max_connection_pool_size
        # 新增参数
        self.language = language
        self.entity_types = entity_types
        self.entity_extract_max_gleaning = entity_extract_max_gleaning
        self.kg_chunk_pick_method = kg_chunk_pick_method
        self.llm_model_max_async = llm_model_max_async
        self.embedding_func_max_async = embedding_func_max_async
        self.max_parallel_insert = max_parallel_insert
        self.max_graph_nodes = max_graph_nodes

        # 创建工作目录
        self.working_dir.mkdir(exist_ok=True)

        self.rag = None
        self.created_at = datetime.now().isoformat()

        logger.info(f"工作目录: {self.working_dir}")
        logger.info(f"工作空间: {self.workspace}")
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
        logger.info("正在初始化 xwrag 系统...")

        # 如果指定了实例级别的连接池大小，临时设置环境变量
        original_pool_size = os.environ.get("NEBULA_MAX_CONNECTION_POOL_SIZE")
        if self.nebula_max_connection_pool_size is not None:
            os.environ["NEBULA_MAX_CONNECTION_POOL_SIZE"] = str(self.nebula_max_connection_pool_size)
            logger.info(f"设置实例 NebulaGraph 连接池大小: {self.nebula_max_connection_pool_size}")

        try:
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

            # 构建 xwrag 初始化参数
            rag_kwargs = {
                "working_dir": str(self.working_dir),
                "workspace": self.workspace,  # 传递 workspace 实现多租户隔离
                "llm_model_func": self.llm_model_func,
                "embedding_func": EmbeddingFunc(
                    embedding_dim=self.embedding_dim,
                    max_token_size=self.embedding_max_token,
                    func=lambda texts: hf_embed(
                        texts,
                        tokenizer=tokenizer,
                        embed_model=embed_model,
                    ),
                ),
            }

            # 从环境变量读取存储配置（默认使用 NebulaGraph 和 Milvus）
            graph_storage = os.environ.get("GRAPH_STORAGE", "NebulaGraphStorage")
            vector_storage = os.environ.get("VECTOR_STORAGE", "MilvusVectorDBStorage")
            rag_kwargs["graph_storage"] = graph_storage
            rag_kwargs["vector_storage"] = vector_storage
            logger.info(f"使用存储配置: graph={graph_storage}, vector={vector_storage}")

            # 向量数据库配置
            rag_kwargs["vector_db_storage_cls_kwargs"] = {
                "cosine_better_than_threshold": self.cosine_threshold
            }

            # 分块配置
            rag_kwargs["chunk_token_size"] = self.chunk_token_size
            rag_kwargs["chunk_overlap_token_size"] = self.chunk_overlap_token_size

            # 缓存参数（始终传递）
            rag_kwargs["enable_llm_cache"] = self.enable_llm_cache
            rag_kwargs["enable_llm_cache_for_entity_extract"] = self.enable_llm_cache_for_entity_extract

            # 新增参数 - 只有非 None 时才设置（使用 xwrag 默认值/环境变量）
            if self.entity_extract_max_gleaning is not None:
                rag_kwargs["entity_extract_max_gleaning"] = self.entity_extract_max_gleaning
            if self.kg_chunk_pick_method is not None:
                rag_kwargs["kg_chunk_pick_method"] = self.kg_chunk_pick_method
            if self.llm_model_max_async is not None:
                rag_kwargs["llm_model_max_async"] = self.llm_model_max_async
            if self.embedding_func_max_async is not None:
                rag_kwargs["embedding_func_max_async"] = self.embedding_func_max_async
            if self.max_parallel_insert is not None:
                rag_kwargs["max_parallel_insert"] = self.max_parallel_insert
            if self.max_graph_nodes is not None:
                rag_kwargs["max_graph_nodes"] = self.max_graph_nodes

            # 设置 addon_params（语言和实体类型）- 只有非 None 时才设置
            addon_params = {}
            if self.language is not None:
                addon_params["language"] = self.language
            if self.entity_types:
                addon_params["entity_types"] = self.entity_types
            if addon_params:
                rag_kwargs["addon_params"] = addon_params

            # 初始化 RAG
            self.rag = xwrag(**rag_kwargs)

            # 初始化存储
            await self.rag.initialize_storages()
            await initialize_pipeline_status()

            logger.info("xwrag 系统初始化完成")
        finally:
            # 恢复原始环境变量
            if self.nebula_max_connection_pool_size is not None:
                if original_pool_size is not None:
                    os.environ["NEBULA_MAX_CONNECTION_POOL_SIZE"] = original_pool_size
                else:
                    os.environ.pop("NEBULA_MAX_CONNECTION_POOL_SIZE", None)

    def insert_document(self, document_path: str, custom_id: Optional[str] = None):
        """
        插入文档到知识图谱,支持多种格式(PDF、DOCX、TXT等)

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
            # 如果是 TXT 文件,尝试直接读取
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
        # 使用文件名作为 file_path,支持自定义 ID
        file_name = doc_path.name
        if custom_id:
            self.rag.insert(content, ids=[custom_id], file_paths=[file_name])
        else:
            self.rag.insert(content, file_paths=[file_name])
        logger.info(f"文档插入完成: {file_name}")

    def insert_documents_batch(self, documents_data: list):
        """批量插入文档到知识图谱

        Args:
            documents_data: 文档数据列表,每个元素包含:
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

    def query(
        self,
        question: str,
        mode: str = "hybrid",
        only_need_context: bool = True,
        top_k: Optional[int] = None,
        chunk_top_k: Optional[int] = None,
        max_entity_tokens: Optional[int] = None,
        max_relation_tokens: Optional[int] = None,
        max_total_tokens: Optional[int] = None,
        # 新增参数
        stream: bool = False,
        enable_rerank: bool = True,
        response_type: str = "Multiple Paragraphs",
        conversation_history: Optional[list] = None,
        hl_keywords: Optional[list] = None,
        ll_keywords: Optional[list] = None,
        user_prompt: Optional[str] = None,
        include_references: bool = False,
    ) -> str:
        """
        查询知识图谱

        Args:
            question: 查询问题
            mode: 查询模式 (naive/local/global/hybrid)
            only_need_context: 是否只需要上下文
            top_k: 查询返回的 top k 结果
            chunk_top_k: 分块查询返回的 top k 结果
            max_entity_tokens: 实体的最大 token 数
            max_relation_tokens: 关系的最大 token 数
            max_total_tokens: 总的最大 token 数
            stream: 是否启用流式输出
            enable_rerank: 是否启用 Rerank
            response_type: 响应格式
            conversation_history: 对话历史
            hl_keywords: 高优先级关键词
            ll_keywords: 低优先级关键词
            user_prompt: 用户自定义提示词
            include_references: 是否包含引用列表

        Returns:
            查询结果
        """
        if self.rag is None:
            raise ValueError("xwrag 系统未初始化")

        logger.info(f"查询模式: {mode}")
        logger.info(f"查询问题: {question}")

        # 构建 QueryParam
        query_params = {
            "mode": mode,
            "only_need_context": only_need_context,
        }

        # 使用传入参数或实例默认参数
        if top_k is not None:
            query_params["top_k"] = top_k
        elif self.top_k is not None:
            query_params["top_k"] = self.top_k

        if chunk_top_k is not None:
            query_params["chunk_top_k"] = chunk_top_k
        elif self.chunk_top_k is not None:
            query_params["chunk_top_k"] = self.chunk_top_k

        if max_entity_tokens is not None:
            query_params["max_entity_tokens"] = max_entity_tokens
        elif self.max_entity_tokens is not None:
            query_params["max_entity_tokens"] = self.max_entity_tokens

        if max_relation_tokens is not None:
            query_params["max_relation_tokens"] = max_relation_tokens
        elif self.max_relation_tokens is not None:
            query_params["max_relation_tokens"] = self.max_relation_tokens

        if max_total_tokens is not None:
            query_params["max_total_tokens"] = max_total_tokens
        elif self.max_total_tokens is not None:
            query_params["max_total_tokens"] = self.max_total_tokens

        # 新增参数
        query_params["stream"] = stream
        query_params["enable_rerank"] = enable_rerank
        query_params["response_type"] = response_type
        query_params["include_references"] = include_references

        if conversation_history:
            query_params["conversation_history"] = conversation_history
        if hl_keywords:
            query_params["hl_keywords"] = hl_keywords
        if ll_keywords:
            query_params["ll_keywords"] = ll_keywords
        if user_prompt:
            query_params["user_prompt"] = user_prompt

        result = self.rag.query(question, param=QueryParam(**query_params))

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


# ==================== 并发安全的 RAG 实例管理器 ====================

class ConcurrentRAGInstanceManager:
    """
    并发安全的 RAG 实例管理器

    使用 asyncio.Lock 保护关键操作，确保多用户并发访问时的数据一致性
    """

    def __init__(self):
        self.instances: Dict[str, xwragProcessor] = {}
        self._lock = asyncio.Lock()  # 用于保护 instances 字典的锁
        logger.info("并发安全的 RAG 实例管理器已初始化")

    async def create_instance(self, config: RAGInstanceCreate) -> xwragProcessor:
        """
        创建一个新的 RAG 实例（线程安全）

        Args:
            config: RAG 实例配置

        Returns:
            xwragProcessor 实例
        """
        async with self._lock:  # 加锁保护
            if config.rag_id in self.instances:
                raise ValueError(f"RAG 实例 '{config.rag_id}' 已存在")

            # ✅ 验证 workspace 唯一性（避免多实例数据冲突）
            if not config.workspace or config.workspace.strip() == "":
                raise ValueError(
                    "workspace 不能为空。在多实例环境中，必须为每个实例指定唯一的 workspace 以避免数据冲突。\n"
                    "详情请参考: MULTI_INSTANCE_ANALYSIS.md"
                )

            # ✅ 检查 workspace 是否已被其他实例使用
            for existing_id, existing_processor in self.instances.items():
                if existing_processor.workspace == config.workspace:
                    raise ValueError(
                        f"workspace '{config.workspace}' 已被实例 '{existing_id}' 使用。\n"
                        f"同一进程中的多个 xwrag 实例必须使用不同的 workspace，否则会导致数据冲突。\n"
                        f"详情请参考: MULTI_INSTANCE_ANALYSIS.md"
                    )

            logger.info(f"正在创建 RAG 实例: {config.rag_id}")

            # 创建 RAG 处理器（LLM 和 Embedding 配置从环境变量读取）
            processor = xwragProcessor(
                working_dir=config.working_dir,
                workspace=config.workspace,
                top_k=config.top_k,
                chunk_top_k=config.chunk_top_k,
                max_entity_tokens=config.max_entity_tokens,
                max_relation_tokens=config.max_relation_tokens,
                max_total_tokens=config.max_total_tokens,
                cosine_threshold=config.cosine_threshold,
                related_chunk_number=config.related_chunk_number,
                chunk_token_size=config.chunk_token_size,
                chunk_overlap_token_size=config.chunk_overlap_token_size,
                enable_llm_cache=config.enable_llm_cache,
                enable_llm_cache_for_entity_extract=config.enable_llm_cache_for_entity_extract,
                nebula_max_connection_pool_size=config.nebula_max_connection_pool_size,
                # 新增参数
                language=config.language,
                entity_types=config.entity_types,
                entity_extract_max_gleaning=config.entity_extract_max_gleaning,
                kg_chunk_pick_method=config.kg_chunk_pick_method,
                llm_model_max_async=config.llm_model_max_async,
                embedding_func_max_async=config.embedding_func_max_async,
                max_parallel_insert=config.max_parallel_insert,
                max_graph_nodes=config.max_graph_nodes,
            )

            # 初始化 RAG
            await processor.initialize_rag()

            # 存储实例
            self.instances[config.rag_id] = processor

            logger.info(f"RAG 实例创建成功: {config.rag_id}")
            return processor

    def get_instance(self, rag_id: str) -> xwragProcessor:
        """
        获取指定的 RAG 实例（读操作，无需加锁）

        Args:
            rag_id: RAG 实例 ID

        Returns:
            xwragProcessor 实例

        Raises:
            ValueError: 如果实例不存在
        """
        # 读操作通常不需要加锁，因为 Python 的字典读取是原子操作
        if rag_id not in self.instances:
            raise ValueError(f"RAG 实例 '{rag_id}' 不存在")
        return self.instances[rag_id]

    async def list_instances(self) -> list[RAGInstanceInfo]:
        """
        列出所有 RAG 实例（加锁保护）

        Returns:
            RAG 实例信息列表
        """
        async with self._lock:
            instances_info = []
            for rag_id, processor in self.instances.items():
                info = RAGInstanceInfo(
                    rag_id=rag_id,
                    description=getattr(processor, 'workspace', None),
                    working_dir=str(processor.working_dir),
                    workspace=processor.workspace or "",
                    created_at=processor.created_at,
                    llm_model=processor.llm_model,
                    embedding_model=processor.embedding_model,
                )
                instances_info.append(info)
            return instances_info

    async def delete_instance(self, rag_id: str) -> bool:
        """
        删除指定的 RAG 实例（线程安全）

        Args:
            rag_id: RAG 实例 ID

        Returns:
            是否删除成功
        """
        async with self._lock:  # 加锁保护
            if rag_id in self.instances:
                del self.instances[rag_id]
                logger.info(f"RAG 实例已删除: {rag_id}")
                return True
            return False


# 全局 RAG 实例管理器（并发安全版本）
concurrent_rag_manager = ConcurrentRAGInstanceManager()


# ==================== 依赖函数 ====================

def get_concurrent_rag_manager() -> ConcurrentRAGInstanceManager:
    """获取并发安全的 RAG 实例管理器"""
    return concurrent_rag_manager


# 导入 UCD_RAG 建模器
try:
    from UCD_RAG import UCBuilder
except ImportError:
    UCBuilder = None
    logger.warning("未找到 UCD_RAG.py,UCD建模功能将不可用")

# 全局 UCD 建模器
ucd_builder: Optional[UCBuilder] = None


def get_ucd_builder() -> Optional[UCBuilder]:
    """获取 UCD 建模器"""
    return ucd_builder


def set_ucd_builder(builder: UCBuilder):
    """设置 UCD 建模器"""
    global ucd_builder
    ucd_builder = builder
