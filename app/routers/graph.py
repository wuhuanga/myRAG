# -*- coding: utf-8 -*-
"""
图操作路由 - 实体和关系管理
"""
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException

from ..dependencies_concurrent import get_concurrent_rag_manager
from ..models import (
    EntityCreateRequest,
    EntityEditRequest,
    EntityDeleteRequest,
    EntityInfoRequest,
    EntityMergeRequest,
    RelationCreateRequest,
    RelationEditRequest,
    RelationDeleteRequest,
    RelationInfoRequest,
    ExportDataRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/graph",
    tags=["graph"],
)


# ==================== 实体管理接口 ====================

@router.post("/entities/create")
async def create_entity(request: EntityCreateRequest):
    """创建新实体"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        entity_data = {
            "description": request.description or "",
            "entity_type": request.entity_type,
            "source_id": request.source_id,
            "file_path": request.file_path
        }

        result = await processor.rag.acreate_entity(
            request.entity_name,
            entity_data
        )

        return {
            "status": "success",
            "message": f"实体 '{request.entity_name}' 创建成功",
            "entity": result,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"创建实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建实体失败: {str(e)}")


@router.post("/entities/edit")
async def edit_entity(request: EntityEditRequest):
    """编辑实体"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        result = await processor.rag.aedit_entity(
            request.entity_name,
            request.updated_data,
            request.allow_rename
        )

        return {
            "status": "success",
            "message": f"实体 '{request.entity_name}' 更新成功",
            "entity": result,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"编辑实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"编辑实体失败: {str(e)}")


@router.post("/entities/delete")
async def delete_entity(request: EntityDeleteRequest):
    """删除实体"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        result = await processor.rag.adelete_by_entity(request.entity_name)

        return {
            "status": result.status,
            "message": result.message,
            "entity_name": request.entity_name,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"删除实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除实体失败: {str(e)}")


@router.post("/entities/info")
async def get_entity_info(request: EntityInfoRequest):
    """获取实体详细信息"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        info = await processor.rag.get_entity_info(
            request.entity_name,
            request.include_vector_data
        )

        return {
            "status": "success",
            "entity_info": info,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"获取实体信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实体信息失败: {str(e)}")


@router.post("/entities/merge")
async def merge_entities(request: EntityMergeRequest):
    """合并多个实体"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        result = await processor.rag.amerge_entities(
            request.source_entities,
            request.target_entity,
            request.merge_strategy,
            request.target_entity_data
        )

        return {
            "status": "success",
            "message": f"成功合并 {len(request.source_entities)} 个实体到 '{request.target_entity}'",
            "merged_entity": result,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"合并实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"合并实体失败: {str(e)}")


# ==================== 关系管理接口 ====================

@router.post("/relations/create")
async def create_relation(request: RelationCreateRequest):
    """创建新关系"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        relation_data = {
            "description": request.description or "",
            "keywords": request.keywords or "",
            "weight": request.weight,
            "source_id": request.source_id,
            "file_path": request.file_path
        }

        result = await processor.rag.acreate_relation(
            request.source_entity,
            request.target_entity,
            relation_data
        )

        return {
            "status": "success",
            "message": f"关系 '{request.source_entity}' -> '{request.target_entity}' 创建成功",
            "relation": result,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"创建关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建关系失败: {str(e)}")


@router.post("/relations/edit")
async def edit_relation(request: RelationEditRequest):
    """编辑关系"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        result = await processor.rag.aedit_relation(
            request.source_entity,
            request.target_entity,
            request.updated_data
        )

        return {
            "status": "success",
            "message": f"关系 '{request.source_entity}' -> '{request.target_entity}' 更新成功",
            "relation": result,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"编辑关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"编辑关系失败: {str(e)}")


@router.post("/relations/delete")
async def delete_relation(request: RelationDeleteRequest):
    """删除关系"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        result = await processor.rag.adelete_by_relation(
            request.source_entity,
            request.target_entity
        )

        return {
            "status": result.status,
            "message": result.message,
            "source_entity": request.source_entity,
            "target_entity": request.target_entity,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"删除关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除关系失败: {str(e)}")


@router.post("/relations/info")
async def get_relation_info(request: RelationInfoRequest):
    """获取关系详细信息"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        info = await processor.rag.get_relation_info(
            request.source_entity,
            request.target_entity,
            request.include_vector_data
        )

        return {
            "status": "success",
            "relation_info": info,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"获取关系信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取关系信息失败: {str(e)}")


# ==================== 数据导出接口 ====================

@router.post("/export")
async def export_data(request: ExportDataRequest):
    """导出知识图谱数据"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        await processor.rag.aexport_data(
            request.output_path,
            request.file_format,
            request.include_vector_data
        )

        return {
            "status": "success",
            "message": f"数据已成功导出到 {request.output_path}",
            "output_path": request.output_path,
            "format": request.file_format,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"导出数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")
