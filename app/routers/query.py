# -*- coding: utf-8 -*-
"""
查询操作路由
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

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
    """查询知识库（支持单知识库和多知识库查询）"""
    manager = get_concurrent_rag_manager()

    try:
        rag_ids = request.get_rag_ids()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 单知识库模式（向后兼容）
    if len(rag_ids) == 1:
        rag_id = rag_ids[0]
        try:
            processor = manager.get_instance(rag_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        try:
            logger.info(f"查询: {request.question} (模式: {request.mode}, RAG ID: {rag_id})")

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
                rag_ids=[rag_id],
                question=request.question,
                answer=answer,
                mode=request.mode,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

    # 多知识库模式
    else:
        async def query_single_kb(rag_id: str) -> Dict[str, Any]:
            """查询单个知识库"""
            try:
                processor = manager.get_instance(rag_id)
                answer = processor.query(
                    question=request.question,
                    mode=request.mode,
                    only_need_context=request.only_need_context,
                    top_k=request.top_k,
                    chunk_top_k=request.chunk_top_k,
                    max_entity_tokens=request.max_entity_tokens,
                    max_relation_tokens=request.max_relation_tokens,
                    max_total_tokens=request.max_total_tokens,
                    stream=request.stream,
                    enable_rerank=request.enable_rerank,
                    response_type=request.response_type,
                    conversation_history=request.conversation_history,
                    hl_keywords=request.hl_keywords,
                    ll_keywords=request.ll_keywords,
                    user_prompt=request.user_prompt,
                    include_references=request.include_references,
                )
                return {
                    "rag_id": rag_id,
                    "answer": answer,
                    "status": "success"
                }
            except Exception as e:
                logger.warning(f"查询知识库 {rag_id} 失败: {str(e)}")
                return {
                    "rag_id": rag_id,
                    "answer": "",
                    "status": "error",
                    "error": str(e)
                }

        try:
            logger.info(f"多知识库查询: {request.question} (模式: {request.mode}, RAG IDs: {rag_ids})")

            # Scatter: 并发查询所有知识库
            tasks = [query_single_kb(rag_id) for rag_id in rag_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Gather: 合并结果
            successful_results = []
            sources = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"查询异常: {result}")
                    continue
                if result.get("status") == "success":
                    successful_results.append(result)
                    sources.append({
                        "rag_id": result["rag_id"],
                        "answer_length": len(result["answer"])
                    })

            if not successful_results:
                raise HTTPException(status_code=500, detail="所有知识库查询均失败")

            # 合并答案（简单拼接，可以根据需求调整合并策略）
            combined_answer = "\n\n".join([
                f"【知识库: {r['rag_id']}】\n{r['answer']}"
                for r in successful_results
            ])

            return QueryResponse(
                rag_ids=rag_ids,
                question=request.question,
                answer=combined_answer,
                mode=request.mode,
                timestamp=datetime.now().isoformat(),
                sources=sources
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"多知识库查询失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"多知识库查询失败: {str(e)}")


@router.post("/keywords", response_model=KeywordsSearchResponse)
async def search_by_keywords(request: KeywordsSearchRequest):
    """使用关键字列表检索知识库（支持单知识库和多知识库查询）"""
    manager = get_concurrent_rag_manager()

    try:
        rag_ids = request.get_rag_ids()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 将关键字列表转换为查询字符串（处理空关键字情况）
    keywords = request.keywords if request.keywords else []
    keywords_str = " ".join(keywords) if keywords else ""

    # 单知识库模式（向后兼容）
    if len(rag_ids) == 1:
        rag_id = rag_ids[0]
        try:
            processor = manager.get_instance(rag_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        try:
            logger.info(f"关键字检索: {keywords} (模式: {request.mode}, RAG ID: {rag_id})")

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
                hl_keywords=keywords if keywords else None,  # 高优先级：搜索关系
                ll_keywords=keywords if keywords else None,  # 低优先级：搜索实体
                enable_rerank=request.enable_rerank,
            )

            return KeywordsSearchResponse(
                rag_ids=[rag_id],
                keywords=keywords if keywords else None,
                context=context,
                mode=request.mode,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"关键字检索失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"关键字检索失败: {str(e)}")

    # 多知识库模式
    else:
        async def search_single_kb(rag_id: str) -> Dict[str, Any]:
            """检索单个知识库"""
            try:
                processor = manager.get_instance(rag_id)
                context = processor.query(
                    question=keywords_str,
                    mode=request.mode,
                    only_need_context=request.only_need_context,
                    top_k=request.top_k,
                    chunk_top_k=request.chunk_top_k,
                    max_entity_tokens=request.max_entity_tokens,
                    max_relation_tokens=request.max_relation_tokens,
                    max_total_tokens=request.max_total_tokens,
                    hl_keywords=keywords if keywords else None,
                    ll_keywords=keywords if keywords else None,
                    enable_rerank=request.enable_rerank,
                )
                return {
                    "rag_id": rag_id,
                    "context": context,
                    "status": "success"
                }
            except Exception as e:
                logger.warning(f"检索知识库 {rag_id} 失败: {str(e)}")
                return {
                    "rag_id": rag_id,
                    "context": "",
                    "status": "error",
                    "error": str(e)
                }

        try:
            logger.info(f"多知识库关键字检索: {keywords} (模式: {request.mode}, RAG IDs: {rag_ids})")

            # Scatter: 并发查询所有知识库
            tasks = [search_single_kb(rag_id) for rag_id in rag_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Gather: 合并结果
            successful_results = []
            sources = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"检索异常: {result}")
                    continue
                if result.get("status") == "success":
                    successful_results.append(result)
                    sources.append({
                        "rag_id": result["rag_id"],
                        "context_length": len(result["context"])
                    })

            if not successful_results:
                raise HTTPException(status_code=500, detail="所有知识库检索均失败")

            # 合并上下文
            combined_context = "\n\n".join([
                f"【知识库: {r['rag_id']}】\n{r['context']}"
                for r in successful_results
            ])

            return KeywordsSearchResponse(
                rag_ids=rag_ids,
                keywords=keywords if keywords else None,
                context=combined_context,
                mode=request.mode,
                timestamp=datetime.now().isoformat(),
                sources=sources
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"多知识库关键字检索失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"多知识库关键字检索失败: {str(e)}")


@router.post("/ucd")
async def query_with_ucd(request: UCDModelRequest):
    """执行查询并进行 UCD 建模（支持单知识库和多知识库查询）"""
    manager = get_concurrent_rag_manager()

    try:
        rag_ids = request.get_rag_ids()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ucd_builder = get_ucd_builder()
    if ucd_builder is None:
        raise HTTPException(status_code=400, detail="UCD 建模器未初始化")

    if request.mode not in ["naive", "local", "global", "hybrid"]:
        raise HTTPException(status_code=400, detail=f"无效的查询模式: {request.mode}")

    # 单知识库模式（向后兼容）
    if len(rag_ids) == 1:
        rag_id = rag_ids[0]
        try:
            processor = manager.get_instance(rag_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        try:
            logger.info(f"[UCD建模流程] 查询问题: {request.question} (模式: {request.mode}, RAG ID: {rag_id})")

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
                "rag_ids": [rag_id],
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

    # 多知识库模式
    else:
        async def query_single_kb(rag_id: str) -> Dict[str, Any]:
            """查询单个知识库"""
            try:
                processor = manager.get_instance(rag_id)
                context = processor.query(request.question, mode=request.mode)
                return {
                    "rag_id": rag_id,
                    "context": context,
                    "status": "success"
                }
            except Exception as e:
                logger.warning(f"查询知识库 {rag_id} 失败: {str(e)}")
                return {
                    "rag_id": rag_id,
                    "context": "",
                    "status": "error",
                    "error": str(e)
                }

        try:
            logger.info(f"[UCD建模流程] 多知识库查询: {request.question} (模式: {request.mode}, RAG IDs: {rag_ids})")

            # 1. 并发查询所有知识库
            logger.info("[UCD建模流程] 步骤1: 并发执行 RAG 检索...")
            tasks = [query_single_kb(rag_id) for rag_id in rag_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 合并上下文
            successful_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"查询异常: {result}")
                    continue
                if result.get("status") == "success":
                    successful_results.append(result)

            if not successful_results:
                raise HTTPException(status_code=500, detail="所有知识库查询均失败")

            combined_context = "\n\n".join([
                f"【知识库: {r['rag_id']}】\n{r['context']}"
                for r in successful_results
            ])
            logger.info(f"[UCD建模流程] 检索到上下文内容 (长度: {len(combined_context)} 字符)")

            # 2. UCD 建模
            logger.info("[UCD建模流程] 步骤2: 开始 UCD 建模...")
            ucd_result = ucd_builder.test_generate(
                question=request.question,
                chunks=combined_context,
                out_json=request.out_json
            )
            logger.info("[UCD建模流程] UCD 建模完成")

            return {
                "status": "success",
                "rag_ids": rag_ids,
                "question": request.question,
                "context": combined_context,
                "ucd_model": ucd_result,
                "output_file": request.out_json,
                "mode": request.mode,
                "timestamp": datetime.now().isoformat(),
                "sources": [{"rag_id": r["rag_id"], "context_length": len(r["context"])} for r in successful_results]
            }

        except HTTPException:
            raise
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
    """使用关键字检索知识图谱，返回清理后的实体和关系（支持单知识库和多知识库查询）"""
    manager = get_concurrent_rag_manager()

    try:
        rag_ids = request.get_rag_ids()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 将关键字列表转换为查询字符串（处理空关键字情况）
    keywords = request.keywords if request.keywords else []
    keywords_str = " ".join(keywords) if keywords else ""

    # 单知识库模式（向后兼容）
    if len(rag_ids) == 1:
        rag_id = rag_ids[0]
        try:
            processor = manager.get_instance(rag_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        try:
            logger.info(f"清理图谱检索: {keywords} (RAG ID: {rag_id})")

            # 调用 aquery_data 获取结构化数据
            from xwrag.base import QueryParam
            param = QueryParam(
                mode="hybrid",
                only_need_context=True,
                top_k=request.top_k,
                chunk_top_k=request.chunk_top_k,
                max_entity_tokens=request.max_entity_tokens,
                max_relation_tokens=request.max_relation_tokens,
                max_total_tokens=request.max_total_tokens,
                hl_keywords=keywords if keywords else None,
                ll_keywords=keywords if keywords else None,
                enable_rerank=request.enable_rerank,
            )

            result = await processor.rag.aquery_data(keywords_str, param)

            # 检查结果是否为空
            if result is None:
                logger.warning(f"知识库 {rag_id} 查询返回 None（可能未插入文档）")
                return GraphCleanResponse(
                    rag_ids=[rag_id],
                    keywords=keywords if keywords else None,
                    entities=[],
                    relationships=[],
                    timestamp=datetime.now().isoformat()
                )

            if result.get("status") != "success":
                raise HTTPException(status_code=500, detail=result.get("message", "查询失败"))

            data = result.get("data", {})
            if data is None:
                data = {}

            # 清理实体数据
            clean_entities = [
                CleanEntity(
                    entity_name=entity.get("entity_name", ""),
                    description=entity.get("description", ""),
                    entity_type=entity.get("entity_type", "")
                )
                for entity in data.get("entities", [])
            ]

            # 清理关系数据
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
                rag_ids=[rag_id],
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

    # 多知识库模式
    else:
        async def query_single_kb(rag_id: str) -> Dict[str, Any]:
            """查询单个知识库的图谱数据"""
            try:
                from xwrag.base import QueryParam
                processor = manager.get_instance(rag_id)

                param = QueryParam(
                    mode="hybrid",
                    only_need_context=True,
                    top_k=request.top_k,
                    chunk_top_k=request.chunk_top_k,
                    max_entity_tokens=request.max_entity_tokens,
                    max_relation_tokens=request.max_relation_tokens,
                    max_total_tokens=request.max_total_tokens,
                    hl_keywords=keywords if keywords else None,
                    ll_keywords=keywords if keywords else None,
                    enable_rerank=request.enable_rerank,
                )

                result = await processor.rag.aquery_data(keywords_str, param)

                # 检查结果是否为空
                if result is None:
                    logger.warning(f"查询知识库 {rag_id} 返回 None（可能未插入文档）")
                    return {
                        "rag_id": rag_id,
                        "data": {},
                        "status": "error"
                    }

                if result.get("status") == "success":
                    data = result.get("data", {})
                    if data is None:
                        data = {}
                    return {
                        "rag_id": rag_id,
                        "data": data,
                        "status": "success"
                    }
                else:
                    logger.warning(f"查询知识库 {rag_id} 失败: {result.get('message', '未知错误')}")
                    return {
                        "rag_id": rag_id,
                        "data": {},
                        "status": "error"
                    }
            except Exception as e:
                logger.warning(f"查询知识库 {rag_id} 异常: {str(e)}")
                return {
                    "rag_id": rag_id,
                    "data": {},
                    "status": "error"
                }

        try:
            logger.info(f"多知识库清理图谱检索: {keywords} (RAG IDs: {rag_ids})")

            # Scatter: 并发查询所有知识库
            tasks = [query_single_kb(rag_id) for rag_id in rag_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Gather: 合并结果
            all_entities = []
            all_relationships = []
            sources = []

            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"查询异常: {result}")
                    continue
                if result.get("status") == "success":
                    data = result.get("data", {})
                    rag_id = result["rag_id"]

                    # 清理并合并实体数据
                    for entity in data.get("entities", []):
                        all_entities.append(
                            CleanEntity(
                                entity_name=entity.get("entity_name", ""),
                                description=entity.get("description", ""),
                                entity_type=entity.get("entity_type", "")
                            )
                        )

                    # 清理并合并关系数据
                    for rel in data.get("relationships", []):
                        all_relationships.append(
                            CleanRelationship(
                                src_id=rel.get("src_id", ""),
                                tgt_id=rel.get("tgt_id", ""),
                                description=rel.get("description", ""),
                                keywords=rel.get("keywords", "")
                            )
                        )

                    sources.append({
                        "rag_id": rag_id,
                        "entities_count": len(data.get("entities", [])),
                        "relationships_count": len(data.get("relationships", []))
                    })

            if not sources:
                logger.warning("所有知识库查询均返回空结果")
                return GraphCleanResponse(
                    rag_ids=rag_ids,
                    keywords=keywords if keywords else None,
                    entities=[],
                    relationships=[],
                    timestamp=datetime.now().isoformat(),
                    sources=[]
                )

            return GraphCleanResponse(
                rag_ids=rag_ids,
                keywords=keywords if keywords else None,
                entities=all_entities,
                relationships=all_relationships,
                timestamp=datetime.now().isoformat(),
                sources=sources
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"多知识库清理图谱检索失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"多知识库清理图谱检索失败: {str(e)}")


@router.post("/chunks-only", response_model=ChunksOnlyResponse)
async def query_chunks_only(request: ChunksOnlyRequest):
    """使用关键字检索，只返回文档chunks（支持单知识库和多知识库查询）"""
    manager = get_concurrent_rag_manager()

    try:
        rag_ids = request.get_rag_ids()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 将关键字列表转换为查询字符串（处理空关键字情况）
    keywords = request.keywords if request.keywords else []
    keywords_str = " ".join(keywords) if keywords else ""

    # 单知识库模式（向后兼容）
    if len(rag_ids) == 1:
        rag_id = rag_ids[0]
        try:
            processor = manager.get_instance(rag_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        try:
            logger.info(f"仅Chunks检索: {keywords} (RAG ID: {rag_id})")

            # 调用 aquery_data 获取结构化数据
            from xwrag.base import QueryParam
            param = QueryParam(
                mode="hybrid",
                only_need_context=True,
                chunk_top_k=request.chunk_top_k,
                max_total_tokens=request.max_total_tokens,
                hl_keywords=keywords if keywords else None,
                ll_keywords=keywords if keywords else None,
                enable_rerank=request.enable_rerank,
            )

            result = await processor.rag.aquery_data(keywords_str, param)

            # 检查结果是否为空
            if result is None:
                logger.warning(f"知识库 {rag_id} 查询返回 None（可能未插入文档）")
                return ChunksOnlyResponse(
                    rag_ids=[rag_id],
                    keywords=keywords if keywords else None,
                    chunks=[],
                    timestamp=datetime.now().isoformat()
                )

            if result.get("status") != "success":
                raise HTTPException(status_code=500, detail=result.get("message", "查询失败"))

            data = result.get("data", {})
            if data is None:
                data = {}

            # 提取 chunks 数据
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
                rag_ids=[rag_id],
                keywords=keywords if keywords else None,
                chunks=chunks,
                timestamp=datetime.now().isoformat()
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"仅Chunks检索失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"仅Chunks检索失败: {str(e)}")

    # 多知识库模式
    else:
        async def query_single_kb(rag_id: str) -> Dict[str, Any]:
            """查询单个知识库的chunks"""
            try:
                from xwrag.base import QueryParam
                processor = manager.get_instance(rag_id)

                param = QueryParam(
                    mode="hybrid",
                    only_need_context=True,
                    chunk_top_k=request.chunk_top_k,
                    max_total_tokens=request.max_total_tokens,
                    hl_keywords=keywords if keywords else None,
                    ll_keywords=keywords if keywords else None,
                    enable_rerank=request.enable_rerank,
                )

                result = await processor.rag.aquery_data(keywords_str, param)

                # 检查结果是否为空
                if result is None:
                    logger.warning(f"查询知识库 {rag_id} 返回 None（可能未插入文档）")
                    return {
                        "rag_id": rag_id,
                        "data": {},
                        "status": "error"
                    }

                if result.get("status") == "success":
                    data = result.get("data", {})
                    if data is None:
                        data = {}
                    return {
                        "rag_id": rag_id,
                        "data": data,
                        "status": "success"
                    }
                else:
                    logger.warning(f"查询知识库 {rag_id} 失败: {result.get('message', '未知错误')}")
                    return {
                        "rag_id": rag_id,
                        "data": {},
                        "status": "error"
                    }
            except Exception as e:
                logger.warning(f"查询知识库 {rag_id} 异常: {str(e)}")
                return {
                    "rag_id": rag_id,
                    "data": {},
                    "status": "error"
                }

        try:
            logger.info(f"多知识库仅Chunks检索: {keywords} (RAG IDs: {rag_ids})")

            # Scatter: 并发查询所有知识库
            tasks = [query_single_kb(rag_id) for rag_id in rag_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Gather: 合并结果
            all_chunks = []
            sources = []

            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"查询异常: {result}")
                    continue
                if result.get("status") == "success":
                    data = result.get("data", {})
                    rag_id = result["rag_id"]

                    # 合并 chunks 数据
                    for chunk in data.get("chunks", []):
                        all_chunks.append(
                            ChunkItem(
                                content=chunk.get("content", ""),
                                file_path=chunk.get("file_path", ""),
                                chunk_id=chunk.get("chunk_id", ""),
                                reference_id=chunk.get("reference_id", "")
                            )
                        )

                    sources.append({
                        "rag_id": rag_id,
                        "chunks_count": len(data.get("chunks", []))
                    })

            if not sources:
                logger.warning("所有知识库查询均返回空结果")
                return ChunksOnlyResponse(
                    rag_ids=rag_ids,
                    keywords=keywords if keywords else None,
                    chunks=[],
                    timestamp=datetime.now().isoformat(),
                    sources=[]
                )

            return ChunksOnlyResponse(
                rag_ids=rag_ids,
                keywords=keywords if keywords else None,
                chunks=all_chunks,
                timestamp=datetime.now().isoformat(),
                sources=sources
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"多知识库仅Chunks检索失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"多知识库仅Chunks检索失败: {str(e)}")
