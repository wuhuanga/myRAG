# -*- coding: utf-8 -*-
"""
管理功能 - RAG 实例管理、系统健康检查等
"""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from ..dependencies import get_rag_manager, get_ucd_builder, set_ucd_builder, UCBuilder
from ..models import RAGInstanceCreate, RAGInstanceInfo

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/health")
async def health_check():
    """健康检查端点"""
    manager = get_rag_manager()
    ucd_builder = get_ucd_builder()

    return {
        "status": "healthy",
        "rag_instances_count": len(manager.instances),
        "ucd_initialized": ucd_builder is not None,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/rag_instances/create")
async def create_rag_instance(config: RAGInstanceCreate):
    """创建新的 RAG 实例"""
    manager = get_rag_manager()

    try:
        processor = await manager.create_instance(config)

        return {
            "status": "success",
            "message": f"RAG 实例 '{config.rag_id}' 创建成功",
            "rag_id": config.rag_id,
            "working_dir": str(processor.working_dir),
            "workspace": processor.workspace,
            "llm_model": processor.llm_model,
            "embedding_model": processor.embedding_model
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建 RAG 实例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建 RAG 实例失败: {str(e)}")


@router.get("/rag_instances/list", response_model=List[RAGInstanceInfo])
async def list_rag_instances():
    """列出所有 RAG 实例"""
    manager = get_rag_manager()

    try:
        instances = manager.list_instances()
        return instances

    except Exception as e:
        logger.error(f"列出 RAG 实例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"列出 RAG 实例失败: {str(e)}")


@router.get("/rag_instances/{rag_id}")
async def get_rag_instance_info(rag_id: str):
    """获取指定 RAG 实例的详细信息"""
    manager = get_rag_manager()

    try:
        processor = manager.get_instance(rag_id)

        return {
            "status": "success",
            "rag_id": rag_id,
            "working_dir": str(processor.working_dir),
            "workspace": processor.workspace,
            "created_at": processor.created_at,
            "llm_model": processor.llm_model,
            "embedding_model": processor.embedding_model,
            "embedding_dim": processor.embedding_dim,
            "config": {
                "kv_storage": processor.kv_storage,
                "vector_storage": processor.vector_storage,
                "graph_storage": processor.graph_storage,
                "doc_status_storage": processor.doc_status_storage,
                "top_k": processor.top_k,
                "chunk_top_k": processor.chunk_top_k,
                "max_entity_tokens": processor.max_entity_tokens,
                "max_relation_tokens": processor.max_relation_tokens,
                "max_total_tokens": processor.max_total_tokens,
                "cosine_threshold": processor.cosine_threshold,
                "related_chunk_number": processor.related_chunk_number,
                "chunk_token_size": processor.chunk_token_size,
                "chunk_overlap_token_size": processor.chunk_overlap_token_size,
                "enable_llm_cache": processor.enable_llm_cache,
                "enable_llm_cache_for_entity_extract": processor.enable_llm_cache_for_entity_extract,
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取 RAG 实例信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取 RAG 实例信息失败: {str(e)}")


@router.delete("/rag_instances/{rag_id}")
async def delete_rag_instance(rag_id: str):
    """删除指定的 RAG 实例（包括所有知识库数据）"""
    manager = get_rag_manager()

    try:
        success = manager.delete_instance(rag_id)

        if success:
            return {
                "status": "success",
                "message": f"RAG 实例 '{rag_id}' 及其知识库已完全删除",
                "rag_id": rag_id,
                "deleted": {
                    "instance": True,
                    "knowledge_base": True,
                    "working_directory": True
                }
            }
        else:
            raise HTTPException(status_code=404, detail=f"RAG 实例 '{rag_id}' 不存在")

    except Exception as e:
        logger.error(f"删除 RAG 实例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除 RAG 实例失败: {str(e)}")


@router.post("/ucd/init")
async def initialize_ucd_builder(
    base_url: str = "http://localhost:4000",
    api_key: str = "sk-1234",
    model_name: str = "gpt-4"
):
    """初始化 UCD 建模器"""
    if UCBuilder is None:
        raise HTTPException(status_code=400, detail="UCD_RAG 模块不可用")

    try:
        logger.info("正在初始化 UCD 建模器...")
        builder = UCBuilder(
            base_url=base_url,
            api_key=api_key,
            use_case_model_name=model_name
        )
        set_ucd_builder(builder)
        logger.info("UCD 建模器初始化成功")

        return {
            "status": "success",
            "message": "UCD 建模器初始化成功",
            "config": {
                "base_url": base_url,
                "model_name": model_name
            }
        }

    except Exception as e:
        logger.error(f"初始化 UCD 建模器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"初始化 UCD 建模器失败: {str(e)}")
