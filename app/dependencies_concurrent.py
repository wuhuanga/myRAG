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
from lightrag import lightrag, QueryParam
from lightrag.llm.llama_index_impl import llama_index_complete_if_cache
from lightrag.llm.hf import hf_embed
from transformers import AutoModel, AutoTokenizer
from lightrag.utils import EmbeddingFunc
from llama_index.llms.litellm import LiteLLM
from lightrag.kg.shared_storage import initialize_pipeline_status

from .models import RAGInstanceCreate, RAGInstanceInfo

load_dotenv()
nest_asyncio.apply()

logger = logging.getLogger(__name__)


# ==================== lightrag 处理器实现（与原版相同）====================
# ... (lightragProcessor 类的代码与原版完全相同，此处省略)


# ==================== 并发安全的 RAG 实例管理器 ====================

class ConcurrentRAGInstanceManager:
    """
    并发安全的 RAG 实例管理器

    使用 asyncio.Lock 保护关键操作，确保多用户并发访问时的数据一致性
    """

    def __init__(self):
        self.instances: Dict[str, lightragProcessor] = {}
        self._lock = asyncio.Lock()  # 用于保护 instances 字典的锁
        logger.info("并发安全的 RAG 实例管理器已初始化")

    async def create_instance(self, config: RAGInstanceCreate) -> lightragProcessor:
        """
        创建一个新的 RAG 实例（线程安全）

        Args:
            config: RAG 实例配置

        Returns:
            lightragProcessor 实例
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
                        f"同一进程中的多个 lightrag 实例必须使用不同的 workspace，否则会导致数据冲突。\n"
                        f"详情请参考: MULTI_INSTANCE_ANALYSIS.md"
                    )

            logger.info(f"正在创建 RAG 实例: {config.rag_id}")

            # 创建 RAG 处理器（LLM 和 Embedding 配置从环境变量读取）
            processor = lightragProcessor(
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
            )

            # 初始化 RAG
            await processor.initialize_rag()

            # 存储实例
            self.instances[config.rag_id] = processor

            logger.info(f"RAG 实例创建成功: {config.rag_id}")
            return processor

    def get_instance(self, rag_id: str) -> lightragProcessor:
        """
        获取指定的 RAG 实例（读操作，无需加锁）

        Args:
            rag_id: RAG 实例 ID

        Returns:
            lightragProcessor 实例

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
