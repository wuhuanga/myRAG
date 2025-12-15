# -*- coding: utf-8 -*-
"""
查询操作路由
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..dependencies_concurrent import get_concurrent_rag_manager, get_ucd_builder
from ..models import (
    QueryRequest,
    QueryResponse,
    KeywordsSearchRequest,
    KeywordsSearchResponse,
    UCDModelRequest,
    ClearCacheRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/query",
    tags=["query"],
)


@router.post("/", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest):
    """查询知识库"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        logger.info(f"查询: {request.question} (模式: {request.mode}, RAG ID: {request.rag_id})")

        answer = processor.query(
            question=request.question,
            mode=request.mode,
            only_need_context=request.only_need_context,
            top_k=request.top_k,
            chunk_top_k=request.chunk_top_k,
            max_entity_tokens=request.max_entity_tokens,
            max_relation_tokens=request.max_relation_tokens,
            max_total_tokens=request.max_total_tokens,
            # 新增参数
            stream=request.stream,
            enable_rerank=request.enable_rerank,
            response_type=request.response_type,
            conversation_history=request.conversation_history,
            hl_keywords=request.hl_keywords,
            ll_keywords=request.ll_keywords,
            user_prompt=request.user_prompt,
            include_references=request.include_references,
        )

        return QueryResponse(
            rag_id=request.rag_id,
            question=request.question,
            answer=answer,
            mode=request.mode,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/keywords", response_model=KeywordsSearchResponse)
async def search_by_keywords(request: KeywordsSearchRequest):
    """使用关键字列表检索知识库"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        # 将关键字列表转换为查询字符串
        keywords_str = " ".join(request.keywords)
        logger.info(f"关键字检索: {request.keywords} (模式: {request.mode}, RAG ID: {request.rag_id})")

        # 执行检索
        context = processor.query(
            question=keywords_str,
            mode=request.mode,
            only_need_context=request.only_need_context,
            top_k=request.top_k,
            chunk_top_k=request.chunk_top_k,
            max_entity_tokens=request.max_entity_tokens,
            max_relation_tokens=request.max_relation_tokens,
            max_total_tokens=request.max_total_tokens,
            hl_keywords=request.keywords,  # 将关键字作为高优先级关键词
            enable_rerank=request.enable_rerank,
        )

        return KeywordsSearchResponse(
            rag_id=request.rag_id,
            keywords=request.keywords,
            context=context,
            mode=request.mode,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"关键字检索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"关键字检索失败: {str(e)}")


@router.post("/ucd")
async def query_with_ucd(request: UCDModelRequest):
    """执行查询并进行 UCD 建模"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    ucd_builder = get_ucd_builder()
    if ucd_builder is None:
        raise HTTPException(status_code=400, detail="UCD 建模器未初始化")

    if request.mode not in ["naive", "local", "global", "hybrid"]:
        raise HTTPException(status_code=400, detail=f"无效的查询模式: {request.mode}")

    try:
        logger.info(f"[UCD建模流程] 查询问题: {request.question} (模式: {request.mode}, RAG ID: {request.rag_id})")

        # 1. RAG 检索
        logger.info("[UCD建模流程] 步骤1: 执行 RAG 检索...")
        context = processor.query(request.question, mode=request.mode)
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
            "rag_id": request.rag_id,
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


@router.post("/clear_cache")
async def clear_cache(request: ClearCacheRequest):
    """清除 LLM 缓存"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        if request.cache_type == "llm_cache":
            # 清除 LLM 缓存
            logger.info(f"正在清除 RAG 实例 {request.rag_id} 的 LLM 缓存...")
            # 调用 xwrag 的缓存清除函数
            if hasattr(processor.rag, 'clear_llm_cache'):
                await processor.rag.clear_llm_cache()
            else:
                # 如果没有专门的清除缓存方法,尝试调用通用方法
                from xwrag.llm.llama_index_impl import clear_cache
                clear_cache()

            return {
                "status": "success",
                "message": f"RAG 实例 {request.rag_id} 的 LLM 缓存已清除",
                "rag_id": request.rag_id,
                "cache_type": request.cache_type
            }

        elif request.cache_type == "all":
            # 清除所有缓存
            logger.info(f"正在清除 RAG 实例 {request.rag_id} 的所有缓存...")
            # 清除 LLM 缓存
            if hasattr(processor.rag, 'clear_llm_cache'):
                await processor.rag.clear_llm_cache()
            else:
                from xwrag.llm.llama_index_impl import clear_cache
                clear_cache()

            # 可以在这里添加其他缓存清除逻辑

            return {
                "status": "success",
                "message": f"RAG 实例 {request.rag_id} 的所有缓存已清除",
                "rag_id": request.rag_id,
                "cache_type": request.cache_type
            }

    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")
