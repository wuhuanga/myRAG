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
    GraphCleanRequest,
    GraphCleanResponse,
    CleanEntity,
    CleanRelationship,
    ChunksOnlyRequest,
    ChunksOnlyResponse,
    ChunkItem,
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
        # 将关键字列表转换为查询字符串（处理空关键字情况）
        keywords = request.keywords if request.keywords else []
        keywords_str = " ".join(keywords) if keywords else ""
        logger.info(f"关键字检索: {keywords} (模式: {request.mode}, RAG ID: {request.rag_id})")

        # 执行检索
        # 将关键字同时作为高优先级和低优先级关键词，以便在所有模式下都能检索
        context = processor.query(
            question=keywords_str,
            mode=request.mode,
            only_need_context=request.only_need_context,
            top_k=request.top_k,
            chunk_top_k=request.chunk_top_k,
            max_entity_tokens=request.max_entity_tokens,
            max_relation_tokens=request.max_relation_tokens,
            max_total_tokens=request.max_total_tokens,
            hl_keywords=keywords if keywords else None,  # 高优先级：搜索关系
            ll_keywords=keywords if keywords else None,  # 低优先级：搜索实体
            enable_rerank=request.enable_rerank,
        )

        return KeywordsSearchResponse(
            rag_id=request.rag_id,
            keywords=keywords if keywords else None,
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


@router.post("/graph-clean", response_model=GraphCleanResponse)
async def query_graph_clean(request: GraphCleanRequest):
    """使用关键字检索知识图谱，返回清理后的实体和关系（去除source_id, file_path, created_at等元数据）"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        # 将关键字列表转换为查询字符串（处理空关键字情况）
        keywords = request.keywords if request.keywords else []
        keywords_str = " ".join(keywords) if keywords else ""
        logger.info(f"清理图谱检索: {keywords} (RAG ID: {request.rag_id})")

        # 调用 aquery_data 获取结构化数据（hybrid 模式，同时使用 hl 和 ll 关键字）
        from xwrag.base import QueryParam
        param = QueryParam(
            mode="hybrid",
            only_need_context=True,
            top_k=request.top_k,
            chunk_top_k=request.chunk_top_k,
            max_entity_tokens=request.max_entity_tokens,
            max_relation_tokens=request.max_relation_tokens,
            max_total_tokens=request.max_total_tokens,
            hl_keywords=keywords if keywords else None,  # 高优先级：搜索关系
            ll_keywords=keywords if keywords else None,  # 低优先级：搜索实体
            enable_rerank=request.enable_rerank,
        )

        # 获取结构化数据
        result = await processor.rag.aquery_data(keywords_str, param)

        # 检查结果状态
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "查询失败"))

        data = result.get("data", {})

        # 清理实体数据 - 只保留 entity_name, description, entity_type
        clean_entities = [
            CleanEntity(
                entity_name=entity.get("entity_name", ""),
                description=entity.get("description", ""),
                entity_type=entity.get("entity_type", "")
            )
            for entity in data.get("entities", [])
        ]

        # 清理关系数据 - 只保留 src_id, tgt_id, description, keywords
        clean_relationships = [
            CleanRelationship(
                src_id=rel.get("src_id", ""),
                tgt_id=rel.get("tgt_id", ""),
                description=rel.get("description", ""),
                keywords=rel.get("keywords", "")
            )
            for rel in data.get("relationships", [])
        ]

        return GraphCleanResponse(
            rag_id=request.rag_id,
            keywords=keywords if keywords else None,
            entities=clean_entities,
            relationships=clean_relationships,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理图谱检索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理图谱检索失败: {str(e)}")


@router.post("/chunks-only", response_model=ChunksOnlyResponse)
async def query_chunks_only(request: ChunksOnlyRequest):
    """使用关键字检索，只返回文档chunks（保留顺序和相关性分数）"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        # 将关键字列表转换为查询字符串（处理空关键字情况）
        keywords = request.keywords if request.keywords else []
        keywords_str = " ".join(keywords) if keywords else ""
        logger.info(f"仅Chunks检索: {keywords} (RAG ID: {request.rag_id})")

        # 调用 aquery_data 获取结构化数据（hybrid 模式，同时使用 hl 和 ll 关键字）
        from xwrag.base import QueryParam
        param = QueryParam(
            mode="hybrid",
            only_need_context=True,
            chunk_top_k=request.chunk_top_k,
            max_total_tokens=request.max_total_tokens,
            hl_keywords=keywords if keywords else None,  # 高优先级：搜索关系
            ll_keywords=keywords if keywords else None,  # 低优先级：搜索实体
            enable_rerank=request.enable_rerank,
        )

        # 获取结构化数据
        result = await processor.rag.aquery_data(keywords_str, param)

        # 检查结果状态
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "查询失败"))

        data = result.get("data", {})

        # 提取 chunks 数据，保留顺序和所有信息
        chunks = [
            ChunkItem(
                content=chunk.get("content", ""),
                file_path=chunk.get("file_path", ""),
                chunk_id=chunk.get("chunk_id", ""),
                reference_id=chunk.get("reference_id", "")
            )
            for chunk in data.get("chunks", [])
        ]

        return ChunksOnlyResponse(
            rag_id=request.rag_id,
            keywords=keywords if keywords else None,
            chunks=chunks,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"仅Chunks检索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"仅Chunks检索失败: {str(e)}")
