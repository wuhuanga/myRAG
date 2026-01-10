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
    MultiKnowledgeGraphRequest,
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

@router.get("/echarts/top-k/{rag_id}")
async def get_top_k_degree_subgraph(rag_id: str, k: int = 10):
    """
    获取度数最高的 top k 个节点构成的子图（ECharts 格式）

    Args:
        rag_id: RAG 实例 ID
        k: 返回度数最高的 k 个节点（默认 10）

    返回格式：
    {
        "status": "success",
        "rag_id": "...",
        "data": {
            "nodes": [...],
            "links": [...],
            "categories": [...]
        }
    }
    """
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        # 调用 NebulaGraph 的子图查询方法
        chunk_entity_relation_graph = processor.rag.chunk_entity_relation_graph
        echarts_data = await chunk_entity_relation_graph.get_top_k_degree_subgraph_echarts(k)

        return {
            "status": "success",
            "rag_id": rag_id,
            "k": k,
            "data": echarts_data,
        }

    except Exception as e:
        logger.error(f"获取 top {k} 度数子图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取子图失败: {str(e)}")


@router.get("/echarts/neighbors/{rag_id}")
async def get_node_neighbors_subgraph(rag_id: str, node_id: str):
    """
    获取指定节点及其邻居节点构成的子图（ECharts 格式）

    Args:
        rag_id: RAG 实例 ID
        node_id: 中心节点的 ID

    返回格式：
    {
        "status": "success",
        "rag_id": "...",
        "node_id": "...",
        "data": {
            "nodes": [...],
            "links": [...],
            "categories": [...]
        }
    }
    """
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        # 调用 NebulaGraph 的邻居子图查询方法
        chunk_entity_relation_graph = processor.rag.chunk_entity_relation_graph
        echarts_data = await chunk_entity_relation_graph.get_node_neighbors_subgraph_echarts(node_id)

        return {
            "status": "success",
            "rag_id": rag_id,
            "node_id": node_id,
            "data": echarts_data,
        }

    except Exception as e:
        logger.error(f"获取节点 '{node_id}' 邻居子图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取邻居子图失败: {str(e)}")


@router.get("/echarts/{rag_id}")
async def get_echarts_graph(rag_id: str):
    """
    获取 ECharts 格式的知识图谱数据（直接返回 JSON）

    返回格式：
    {
        "nodes": [...],
        "links": [...],
        "categories": [...]
    }
    """
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        # 获取原始数据
        chunk_entity_relation_graph = processor.rag.chunk_entity_relation_graph

        # 获取所有实体和关系（兼容 NebulaGraphStorage）
        nodes_raw = await chunk_entity_relation_graph.get_all_nodes()
        entities_data = []
        for node in nodes_raw:
            entity_name = node.get("id", "")
            # NebulaGraphStorage 将所有属性直接存储在顶层
            graph_data = {k: v for k, v in node.items() if k != "id"}
            entities_data.append({
                "entity_name": entity_name,
                "graph_data": graph_data,
            })

        relations_data_raw = await chunk_entity_relation_graph.get_all_edges()
        relations_data = []
        for edge in relations_data_raw:
            # NebulaGraphStorage 返回 {"source": ..., "target": ..., ...其他属性...}
            src_entity = edge.get("source", "")
            tgt_entity = edge.get("target", "")
            # 其他属性作为 graph_data
            graph_data = {k: v for k, v in edge.items() if k not in ["source", "target"]}
            relations_data.append({
                "src_entity": src_entity,
                "tgt_entity": tgt_entity,
                "graph_data": graph_data,
            })

        # 构建 ECharts 数据结构
        # 1. 构建分类
        entity_types_set = set()
        entity_type_map = {}

        for entity in entities_data:
            graph_data = entity.get("graph_data", {})
            entity_type = graph_data.get("entity_type", "UNKNOWN")
            entity_types_set.add(entity_type)
            entity_type_map[entity["entity_name"]] = entity_type

        categories = [{"name": et} for et in sorted(entity_types_set)]
        category_index = {et: i for i, et in enumerate(sorted(entity_types_set))}

        # 2. 计算节点度数
        node_degrees = {entity["entity_name"]: 0 for entity in entities_data}
        for relation in relations_data:
            src = relation["src_entity"]
            tgt = relation["tgt_entity"]
            node_degrees[src] = node_degrees.get(src, 0) + 1
            node_degrees[tgt] = node_degrees.get(tgt, 0) + 1

        # 3. 构建节点
        nodes = []
        for entity in entities_data:
            entity_name = entity["entity_name"]
            entity_type = entity_type_map.get(entity_name, "UNKNOWN")
            graph_data = entity.get("graph_data", {})

            node = {
                "id": entity_name,
                "name": entity_name,
                "value": node_degrees.get(entity_name, 1),
                "category": category_index.get(entity_type, 0),
                "entity_type": entity_type,
            }

            if graph_data and graph_data.get("description"):
                node["description"] = graph_data.get("description", "")

            nodes.append(node)

        # 4. 构建边
        links = []
        for relation in relations_data:
            graph_data = relation.get("graph_data", {})

            link = {
                "source": relation["src_entity"],
                "target": relation["tgt_entity"],
            }

            if graph_data:
                if graph_data.get("description"):
                    link["description"] = graph_data.get("description", "")
                if graph_data.get("weight"):
                    link["weight"] = graph_data.get("weight", 1.0)
                if graph_data.get("keywords"):
                    link["keywords"] = graph_data.get("keywords", "")

            links.append(link)

        # 返回 ECharts 数据
        echarts_data = {"nodes": nodes, "links": links, "categories": categories}

        return {
            "status": "success",
            "rag_id": rag_id,
            "data": echarts_data,
        }

    except Exception as e:
        logger.error(f"获取 ECharts 图谱数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取图谱数据失败: {str(e)}")


@router.post("/export")
async def export_data(request: ExportDataRequest):
    """导出知识图谱数据到文件"""
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


# ==================== 多知识库图谱查询接口 ====================

@router.post("/echarts/multi")
async def get_multi_knowledge_graph(request: MultiKnowledgeGraphRequest):
    """
    获取多个知识库的 ECharts 格式图谱数据

    支持查询单个或多个知识库，返回合并后的图谱数据，
    节点和边都带有 rag_id 标识来源。

    请求示例:
    {
        "rag_ids": ["kb1", "kb2", "kb3"]
    }

    返回格式：
    {
        "status": "success",
        "rag_ids": ["kb1", "kb2"],
        "data": {
            "nodes": [
                {"id": "...", "name": "...", "rag_id": "kb1", ...},
                {"id": "...", "name": "...", "rag_id": "kb2", ...}
            ],
            "links": [
                {"source": "...", "target": "...", "rag_id": "kb1", ...},
                {"source": "...", "target": "...", "rag_id": "kb2", ...}
            ],
            "categories": [...]
        }
    }
    """
    manager = get_concurrent_rag_manager()

    if not request.rag_ids:
        raise HTTPException(status_code=400, detail="rag_ids 不能为空")

    # 收集所有知识库的数据
    all_nodes = []
    all_links = []
    all_categories_set = set()
    entity_type_map = {}
    node_degrees = {}
    valid_rag_ids = []

    for rag_id in request.rag_ids:
        try:
            processor = manager.get_instance(rag_id)
        except ValueError:
            logger.warning(f"知识库 {rag_id} 不存在，跳过")
            continue

        if processor.rag is None:
            logger.warning(f"知识库 {rag_id} 未初始化，跳过")
            continue

        valid_rag_ids.append(rag_id)

        try:
            # 获取该知识库的图谱数据
            chunk_entity_relation_graph = processor.rag.chunk_entity_relation_graph

            # 获取所有节点
            nodes_raw = await chunk_entity_relation_graph.get_all_nodes()
            for node in nodes_raw:
                entity_name = node.get("id", "")
                graph_data = {k: v for k, v in node.items() if k != "id"}
                entity_type = graph_data.get("entity_type", "UNKNOWN")

                # 记录实体类型
                all_categories_set.add(entity_type)
                # 使用 (entity_name, rag_id) 作为唯一键
                entity_key = (entity_name, rag_id)
                entity_type_map[entity_key] = entity_type

                # 初始化度数
                if entity_key not in node_degrees:
                    node_degrees[entity_key] = 0

                # 存储节点（添加 rag_id）
                node_data = {
                    "entity_name": entity_name,
                    "graph_data": graph_data,
                    "rag_id": rag_id  # 添加 rag_id 标识
                }
                all_nodes.append(node_data)

            # 获取所有边
            relations_raw = await chunk_entity_relation_graph.get_all_edges()
            for edge in relations_raw:
                src_entity = edge.get("source", "")
                tgt_entity = edge.get("target", "")
                graph_data = {k: v for k, v in edge.items() if k not in ["source", "target"]}

                # 计算度数（同一知识库内的边）
                src_key = (src_entity, rag_id)
                tgt_key = (tgt_entity, rag_id)
                node_degrees[src_key] = node_degrees.get(src_key, 0) + 1
                node_degrees[tgt_key] = node_degrees.get(tgt_key, 0) + 1

                # 存储边（添加 rag_id）
                link_data = {
                    "src_entity": src_entity,
                    "tgt_entity": tgt_entity,
                    "graph_data": graph_data,
                    "rag_id": rag_id  # 添加 rag_id 标识
                }
                all_links.append(link_data)

        except Exception as e:
            logger.error(f"获取知识库 {rag_id} 的图谱数据失败: {str(e)}")
            continue

    if not valid_rag_ids:
        raise HTTPException(status_code=404, detail="没有找到有效的知识库")

    # 构建 ECharts 数据结构
    # 1. 构建分类
    categories = [{"name": et} for et in sorted(all_categories_set)]
    category_index = {et: i for i, et in enumerate(sorted(all_categories_set))}

    # 2. 构建节点
    echarts_nodes = []
    for node_data in all_nodes:
        entity_name = node_data["entity_name"]
        rag_id = node_data["rag_id"]
        entity_key = (entity_name, rag_id)
        entity_type = entity_type_map.get(entity_key, "UNKNOWN")
        graph_data = node_data.get("graph_data", {})

        # 生成唯一 ID：entity_name@rag_id
        unique_id = f"{entity_name}@{rag_id}"

        echarts_node = {
            "id": unique_id,
            "name": entity_name,
            "value": node_degrees.get(entity_key, 1),
            "category": category_index.get(entity_type, 0),
            "entity_type": entity_type,
            "rag_id": rag_id  # 标识来源
        }

        if graph_data and graph_data.get("description"):
            echarts_node["description"] = graph_data.get("description", "")

        echarts_nodes.append(echarts_node)

    # 3. 构建边
    echarts_links = []
    for link_data in all_links:
        src_entity = link_data["src_entity"]
        tgt_entity = link_data["tgt_entity"]
        rag_id = link_data["rag_id"]
        graph_data = link_data.get("graph_data", {})

        # 生成唯一 ID
        src_unique_id = f"{src_entity}@{rag_id}"
        tgt_unique_id = f"{tgt_entity}@{rag_id}"

        echarts_link = {
            "source": src_unique_id,
            "target": tgt_unique_id,
            "rag_id": rag_id  # 标识来源
        }

        if graph_data:
            if graph_data.get("description"):
                echarts_link["description"] = graph_data.get("description", "")
            if graph_data.get("weight"):
                echarts_link["weight"] = graph_data.get("weight", 1.0)
            if graph_data.get("keywords"):
                echarts_link["keywords"] = graph_data.get("keywords", "")

        echarts_links.append(echarts_link)

    # 返回 ECharts 数据
    echarts_data = {
        "nodes": echarts_nodes,
        "links": echarts_links,
        "categories": categories
    }

    return {
        "status": "success",
        "rag_ids": valid_rag_ids,
        "data": echarts_data,
    }
