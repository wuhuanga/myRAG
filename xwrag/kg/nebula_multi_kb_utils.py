# -*- coding: utf-8 -*-
"""
Nebula 多知识库查询辅助函数

提供跨多个 workspace 的并发查询功能（scatter-gather 模式）
"""
import asyncio
from typing import Any, Dict, List
from xwrag.utils import logger


async def multi_workspace_get_nodes_batch(
    kb_list: list[str],
    node_ids: list[str],
    graph_template: Any,  # NebulaGraphStorage
) -> Dict[str, Dict[str, dict]]:
    """
    跨多个 workspace 并发批量获取节点信息

    Args:
        kb_list: workspace 列表
        node_ids: 节点 ID 列表
        graph_template: Nebula 图存储模板实例

    Returns:
        Dict[workspace, Dict[node_id, node_data]]
        每个 workspace 的节点数据都带有 source_workspace 标记
    """
    if not kb_list or not node_ids:
        return {}

    # 按 workspace 分组节点（如果节点已带 source_workspace）
    # 否则对所有节点在所有 workspace 中查询
    grouped_nodes = {}

    # 检查第一个节点是否有 workspace 信息
    if isinstance(node_ids[0], dict) and "source_workspace" in node_ids[0]:
        # 节点已经带 workspace 信息，按 workspace 分组
        for node_info in node_ids:
            ws = node_info.get("source_workspace")
            node_id = node_info.get("entity_name") or node_info.get("id")
            if ws not in grouped_nodes:
                grouped_nodes[ws] = []
            grouped_nodes[ws].append(node_id)
    else:
        # 节点没有 workspace 信息，在所有 workspace 中查询
        for ws in kb_list:
            grouped_nodes[ws] = node_ids

    async def query_workspace(workspace: str, ids: list[str]) -> Dict[str, dict]:
        """查询单个 workspace"""
        try:
            # 创建临时图存储实例（复用连接池）
            from xwrag.kg.nebula_impl import NebulaGraphStorage

            temp_graph = NebulaGraphStorage(
                namespace=graph_template.namespace,
                global_config=graph_template.global_config,
                embedding_func=graph_template.embedding_func,
                workspace=workspace,
            )

            # 初始化（复用连接池，开销低）
            await temp_graph.initialize()

            # 批量查询节点
            nodes_data = await temp_graph.get_nodes_batch(ids)

            # 为每个节点添加 source_workspace 标记
            for node_id, node_info in nodes_data.items():
                if node_info:
                    node_info["source_workspace"] = workspace

            return nodes_data

        except Exception as e:
            logger.warning(
                f"[multi_workspace_nodes] Failed to query workspace '{workspace}': {str(e)}"
            )
            return {}

    # Scatter: 并发查询所有 workspace
    logger.info(
        f"[multi_workspace_nodes] Querying {len(grouped_nodes)} workspaces for {len(node_ids)} nodes"
    )

    scatter_start = asyncio.get_event_loop().time()
    tasks = [query_workspace(ws, ids) for ws, ids in grouped_nodes.items()]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    scatter_time = asyncio.get_event_loop().time() - scatter_start

    logger.info(f"⏱️  [multi_workspace_nodes] Scatter phase: {scatter_time:.3f}s")

    # Gather: 合并结果
    merged_results = {}
    for workspace, result in zip(grouped_nodes.keys(), results_list):
        if isinstance(result, Exception):
            logger.warning(
                f"[multi_workspace_nodes] Exception for workspace '{workspace}': {result}"
            )
            continue

        if result:
            merged_results[workspace] = result

    logger.info(
        f"[multi_workspace_nodes] Retrieved {sum(len(v) for v in merged_results.values())} nodes from {len(merged_results)} workspaces"
    )

    return merged_results


async def multi_workspace_get_relations(
    kb_list: list[str],
    entity_ids: list[str],
    graph_template: Any,
) -> Dict[str, List[tuple]]:
    """
    跨多个 workspace 并发获取关系

    Args:
        kb_list: workspace 列表
        entity_ids: 实体 ID 列表
        graph_template: Nebula 图存储模板实例

    Returns:
        Dict[workspace, List[relations]]
        每个关系元组格式: (src_id, tgt_id, relation_data)
    """
    if not kb_list or not entity_ids:
        return {}

    # 按 workspace 分组实体
    grouped_entities = {}

    if isinstance(entity_ids[0], dict) and "source_workspace" in entity_ids[0]:
        for entity_info in entity_ids:
            ws = entity_info.get("source_workspace")
            entity_id = entity_info.get("entity_name") or entity_info.get("id")
            if ws not in grouped_entities:
                grouped_entities[ws] = []
            grouped_entities[ws].append(entity_id)
    else:
        for ws in kb_list:
            grouped_entities[ws] = entity_ids

    async def query_workspace_relations(workspace: str, ids: list[str]) -> List[tuple]:
        """查询单个 workspace 的关系"""
        try:
            from xwrag.kg.nebula_impl import NebulaGraphStorage

            temp_graph = NebulaGraphStorage(
                namespace=graph_template.namespace,
                global_config=graph_template.global_config,
                embedding_func=graph_template.embedding_func,
                workspace=workspace,
            )

            await temp_graph.initialize()

            # 获取所有相关的边
            # 注意：这里需要根据实际的 Nebula API 调整
            # 假设有一个方法可以批量获取实体的所有关系
            relations = []

            # 为每个关系添加 source_workspace 标记
            for relation in relations:
                if isinstance(relation, dict):
                    relation["source_workspace"] = workspace
                elif isinstance(relation, tuple) and len(relation) == 3:
                    # (src, tgt, data) -> (src, tgt, data_with_workspace)
                    src, tgt, data = relation
                    if isinstance(data, dict):
                        data["source_workspace"] = workspace

            return relations

        except Exception as e:
            logger.warning(
                f"[multi_workspace_relations] Failed to query workspace '{workspace}': {str(e)}"
            )
            return []

    # Scatter: 并发查询
    logger.info(
        f"[multi_workspace_relations] Querying {len(grouped_entities)} workspaces"
    )

    scatter_start = asyncio.get_event_loop().time()
    tasks = [query_workspace_relations(ws, ids) for ws, ids in grouped_entities.items()]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    scatter_time = asyncio.get_event_loop().time() - scatter_start

    logger.info(f"⏱️  [multi_workspace_relations] Scatter phase: {scatter_time:.3f}s")

    # Gather: 合并结果
    merged_results = {}
    for workspace, result in zip(grouped_entities.keys(), results_list):
        if isinstance(result, Exception):
            logger.warning(
                f"[multi_workspace_relations] Exception for workspace '{workspace}': {result}"
            )
            continue

        if result:
            merged_results[workspace] = result

    logger.info(
        f"[multi_workspace_relations] Retrieved {sum(len(v) for v in merged_results.values())} relations from {len(merged_results)} workspaces"
    )

    return merged_results
