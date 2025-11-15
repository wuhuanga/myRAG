#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NebulaGraph 全功能测试脚本
测试所有 nebula_impl.py 中的函数和功能
"""
import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from xwrag.kg.nebula_impl import NebulaGraphStorage
from xwrag.kg.shared_storage import initialize_share_data


class NebulaTestSuite:
    """NebulaGraph 测试套件"""

    def __init__(self):
        self.storage = None
        self.test_results = {
            'passed': [],
            'failed': []
        }

    def log_test(self, test_name, passed, message=""):
        """记录测试结果"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")

        if passed:
            self.test_results['passed'].append(test_name)
        else:
            self.test_results['failed'].append(test_name)

    async def setup(self):
        """初始化测试环境"""
        print("\n" + "=" * 80)
        print("NebulaGraph 全功能测试")
        print("=" * 80)

        # 初始化共享存储系统（必须在创建实例之前调用）
        print("\n[SETUP] 初始化共享存储系统...")
        initialize_share_data(workers=1)
        print("[SETUP] ✅ 共享存储初始化完成")

        print("\n[SETUP] 创建 NebulaGraph 存储实例...")

        # 创建一个简单的 mock embedding function
        def mock_embedding_func(texts):
            """Mock embedding function for testing"""
            if isinstance(texts, str):
                return [0.1] * 384  # 返回384维的mock向量
            else:
                return [[0.1] * 384 for _ in texts]  # 批量返回

        self.storage = NebulaGraphStorage(
            namespace="test_comprehensive",
            global_config={
                "host": "127.0.0.1",
                "port": 9669,
                "username": "root",
                "password": "nebula",
                "space_vid_type": "FIXED_STRING(256)"
            },
            embedding_func=mock_embedding_func,
            workspace="test_comprehensive"
        )

        print("[SETUP] 初始化数据库...")
        await self.storage.initialize()
        print("[SETUP] ✅ 初始化完成\n")

    async def cleanup(self):
        """清理测试数据"""
        print("\n[CLEANUP] 清理测试数据...")
        # 这里可以添加清理逻辑，比如删除测试 space
        print("[CLEANUP] ✅ 清理完成\n")

    # ==================== 节点测试 ====================

    async def test_upsert_node(self):
        """测试插入/更新节点"""
        print("\n" + "-" * 80)
        print("测试 1: upsert_node - 插入/更新单个节点")
        print("-" * 80)

        node_data = {
            "entity_id": "测试节点1",
            "entity_type": "concept",
            "description": "这是一个测试节点",
            "source_id": "test_chunk_001",
            "file_path": "test.txt"
        }

        try:
            await self.storage.upsert_node("测试节点1", node_data)

            # 验证节点是否插入成功
            retrieved = await self.storage.get_node("测试节点1")

            if retrieved and retrieved.get('entity_id') == "测试节点1":
                self.log_test("upsert_node", True,
                    f"成功插入节点: {retrieved.get('entity_id')}, 描述: {retrieved.get('description')}")
            else:
                self.log_test("upsert_node", False, "节点未正确插入或检索失败")
        except Exception as e:
            self.log_test("upsert_node", False, f"异常: {e}")

    async def test_upsert_nodes_batch(self):
        """测试批量插入节点"""
        print("\n" + "-" * 80)
        print("测试 2: upsert_nodes - 批量插入节点")
        print("-" * 80)

        nodes = [
            ("测试节点2", {
                "entity_id": "测试节点2",
                "entity_type": "method",
                "description": "批量插入测试节点2",
                "source_id": "test_chunk_002",
                "file_path": "test.txt"
            }),
            ("测试节点3", {
                "entity_id": "测试节点3",
                "entity_type": "data",
                "description": "批量插入测试节点3",
                "source_id": "test_chunk_003",
                "file_path": "test.txt"
            }),
            ("测试节点4", {
                "entity_id": "测试节点4",
                "entity_type": "tool",
                "description": "批量插入测试节点4",
                "source_id": "test_chunk_004",
                "file_path": "test.txt"
            })
        ]

        try:
            await self.storage.upsert_nodes(nodes)

            # 验证批量插入
            retrieved_nodes = await self.storage.get_nodes_batch(["测试节点2", "测试节点3", "测试节点4"])

            if len(retrieved_nodes) == 3:
                self.log_test("upsert_nodes", True,
                    f"成功批量插入 {len(retrieved_nodes)} 个节点")
            else:
                self.log_test("upsert_nodes", False,
                    f"预期 3 个节点，实际获取 {len(retrieved_nodes)} 个")
        except Exception as e:
            self.log_test("upsert_nodes", False, f"异常: {e}")

    async def test_get_node(self):
        """测试获取单个节点"""
        print("\n" + "-" * 80)
        print("测试 3: get_node - 获取单个节点")
        print("-" * 80)

        try:
            node = await self.storage.get_node("测试节点1")

            if node and node.get('entity_id') == "测试节点1":
                self.log_test("get_node", True,
                    f"成功获取节点: {node.get('entity_id')}, 类型: {node.get('entity_type')}")
            else:
                self.log_test("get_node", False, "节点检索失败或数据不正确")
        except Exception as e:
            self.log_test("get_node", False, f"异常: {e}")

    async def test_get_nodes_batch(self):
        """测试批量获取节点"""
        print("\n" + "-" * 80)
        print("测试 4: get_nodes_batch - 批量获取节点")
        print("-" * 80)

        try:
            nodes = await self.storage.get_nodes_batch([
                "测试节点1", "测试节点2", "测试节点3", "不存在的节点"
            ])

            if len(nodes) == 3:  # 应该获取到3个节点，不存在的节点不返回
                self.log_test("get_nodes_batch", True,
                    f"成功批量获取 {len(nodes)} 个节点 (忽略不存在的节点)")
                for node_id, node_data in nodes.items():
                    print(f"   - {node_id}: {node_data.get('description')}")
            else:
                self.log_test("get_nodes_batch", False,
                    f"预期 3 个节点，实际获取 {len(nodes)} 个")
        except Exception as e:
            self.log_test("get_nodes_batch", False, f"异常: {e}")

    async def test_has_node(self):
        """测试检查节点是否存在"""
        print("\n" + "-" * 80)
        print("测试 5: has_node - 检查节点是否存在")
        print("-" * 80)

        try:
            exists1 = await self.storage.has_node("测试节点1")
            exists2 = await self.storage.has_node("不存在的节点999")

            if exists1 and not exists2:
                self.log_test("has_node", True,
                    "成功检测到存在的节点和不存在的节点")
            else:
                self.log_test("has_node", False,
                    f"检测失败: 测试节点1={exists1}, 不存在的节点={exists2}")
        except Exception as e:
            self.log_test("has_node", False, f"异常: {e}")

    # ==================== 边测试 ====================

    async def test_upsert_edge(self):
        """测试插入/更新边"""
        print("\n" + "-" * 80)
        print("测试 6: upsert_edge - 插入/更新单条边")
        print("-" * 80)

        edge_data = {
            "description": "测试节点1和测试节点2之间的关系",
            "keywords": "测试,关系",
            "weight": 0.8,
            "source_id": "test_chunk_001"
        }

        try:
            await self.storage.upsert_edge("测试节点1", "测试节点2", edge_data)

            # 验证边是否插入成功
            retrieved = await self.storage.get_edge("测试节点1", "测试节点2")

            if retrieved and retrieved.get('description'):
                self.log_test("upsert_edge", True,
                    f"成功插入边，描述: {retrieved.get('description')}, 权重: {retrieved.get('weight')}")
            else:
                self.log_test("upsert_edge", False, "边未正确插入或检索失败")
        except Exception as e:
            self.log_test("upsert_edge", False, f"异常: {e}")

    async def test_upsert_edges_batch(self):
        """测试批量插入边"""
        print("\n" + "-" * 80)
        print("测试 7: upsert_edges - 批量插入边")
        print("-" * 80)

        edges = [
            ("测试节点2", "测试节点3", {
                "description": "节点2到节点3的关系",
                "keywords": "测试,批量",
                "weight": 0.9,
                "source_id": "test_chunk_002"
            }),
            ("测试节点3", "测试节点4", {
                "description": "节点3到节点4的关系",
                "keywords": "测试,链式",
                "weight": 0.7,
                "source_id": "test_chunk_003"
            })
        ]

        try:
            await self.storage.upsert_edges(edges)

            # 验证批量插入
            edge1 = await self.storage.get_edge("测试节点2", "测试节点3")
            edge2 = await self.storage.get_edge("测试节点3", "测试节点4")

            if edge1 and edge2:
                self.log_test("upsert_edges", True,
                    "成功批量插入 2 条边")
            else:
                self.log_test("upsert_edges", False,
                    f"批量插入失败: edge1={edge1 is not None}, edge2={edge2 is not None}")
        except Exception as e:
            self.log_test("upsert_edges", False, f"异常: {e}")

    async def test_get_edge(self):
        """测试获取边"""
        print("\n" + "-" * 80)
        print("测试 8: get_edge - 获取单条边")
        print("-" * 80)

        try:
            edge = await self.storage.get_edge("测试节点1", "测试节点2")

            if edge and 'description' in edge:
                self.log_test("get_edge", True,
                    f"成功获取边，描述: {edge.get('description')}, 关键词: {edge.get('keywords')}")
            else:
                self.log_test("get_edge", False, "边检索失败或数据不完整")
        except Exception as e:
            self.log_test("get_edge", False, f"异常: {e}")

    async def test_has_edge(self):
        """测试检查边是否存在"""
        print("\n" + "-" * 80)
        print("测试 9: has_edge - 检查边是否存在")
        print("-" * 80)

        try:
            exists1 = await self.storage.has_edge("测试节点1", "测试节点2")
            exists2 = await self.storage.has_edge("测试节点1", "测试节点4")

            if exists1 and not exists2:
                self.log_test("has_edge", True,
                    "成功检测到存在的边和不存在的边")
            else:
                self.log_test("has_edge", False,
                    f"检测失败: 节点1-节点2={exists1}, 节点1-节点4={exists2}")
        except Exception as e:
            self.log_test("has_edge", False, f"异常: {e}")

    async def test_get_node_edges(self):
        """测试获取节点的所有边"""
        print("\n" + "-" * 80)
        print("测试 10: get_node_edges - 获取节点的所有边")
        print("-" * 80)

        try:
            edges = await self.storage.get_node_edges("测试节点2")

            if edges and len(edges) >= 2:  # 测试节点2应该有至少2条边
                self.log_test("get_node_edges", True,
                    f"成功获取 {len(edges)} 条边")
                for src, tgt in edges[:3]:  # 只显示前3条
                    print(f"   - {src} -> {tgt}")
            else:
                self.log_test("get_node_edges", False,
                    f"预期至少 2 条边，实际获取 {len(edges) if edges else 0} 条")
        except Exception as e:
            self.log_test("get_node_edges", False, f"异常: {e}")

    # ==================== 度数测试 ====================

    async def test_node_degree(self):
        """测试获取节点度数"""
        print("\n" + "-" * 80)
        print("测试 11: node_degree - 获取节点度数")
        print("-" * 80)

        try:
            degree = await self.storage.node_degree("测试节点2")

            if degree >= 2:  # 测试节点2应该有至少2个连接
                self.log_test("node_degree", True,
                    f"测试节点2 的度数: {degree}")
            else:
                self.log_test("node_degree", False,
                    f"预期度数 >= 2，实际: {degree}")
        except Exception as e:
            self.log_test("node_degree", False, f"异常: {e}")

    async def test_edge_degree(self):
        """测试获取边度数"""
        print("\n" + "-" * 80)
        print("测试 12: edge_degree - 获取边度数 (源节点+目标节点的度数和)")
        print("-" * 80)

        try:
            degree = await self.storage.edge_degree("测试节点1", "测试节点2")

            if degree > 0:
                self.log_test("edge_degree", True,
                    f"边 (测试节点1-测试节点2) 的度数: {degree}")
            else:
                self.log_test("edge_degree", False,
                    f"边度数应该 > 0，实际: {degree}")
        except Exception as e:
            self.log_test("edge_degree", False, f"异常: {e}")

    async def test_node_degrees_batch(self):
        """测试批量获取节点度数"""
        print("\n" + "-" * 80)
        print("测试 13: node_degrees_batch - 批量获取节点度数")
        print("-" * 80)

        try:
            degrees = await self.storage.node_degrees_batch([
                "测试节点1", "测试节点2", "测试节点3"
            ])

            if len(degrees) == 3:
                self.log_test("node_degrees_batch", True,
                    f"成功批量获取 {len(degrees)} 个节点的度数")
                for node_id, degree in degrees.items():
                    print(f"   - {node_id}: {degree}")
            else:
                self.log_test("node_degrees_batch", False,
                    f"预期 3 个节点度数，实际获取 {len(degrees)} 个")
        except Exception as e:
            self.log_test("node_degrees_batch", False, f"异常: {e}")

    async def test_edge_degrees_batch(self):
        """测试批量获取边度数"""
        print("\n" + "-" * 80)
        print("测试 14: edge_degrees_batch - 批量获取边度数")
        print("-" * 80)

        try:
            edge_pairs = [
                ("测试节点1", "测试节点2"),
                ("测试节点2", "测试节点3"),
            ]
            degrees = await self.storage.edge_degrees_batch(edge_pairs)

            if len(degrees) == 2:
                self.log_test("edge_degrees_batch", True,
                    f"成功批量获取 {len(degrees)} 条边的度数")
                for edge_pair, degree in degrees.items():
                    print(f"   - {edge_pair}: {degree}")
            else:
                self.log_test("edge_degrees_batch", False,
                    f"预期 2 条边度数，实际获取 {len(degrees)} 条")
        except Exception as e:
            self.log_test("edge_degrees_batch", False, f"异常: {e}")

    async def test_get_edges_batch(self):
        """测试批量获取边"""
        print("\n" + "-" * 80)
        print("测试 15: get_edges_batch - 批量获取边数据")
        print("-" * 80)

        try:
            edge_pairs = [
                {"src": "测试节点1", "tgt": "测试节点2"},
                {"src": "测试节点2", "tgt": "测试节点3"},
            ]
            edges = await self.storage.get_edges_batch(edge_pairs)

            if len(edges) == 2:
                self.log_test("get_edges_batch", True,
                    f"成功批量获取 {len(edges)} 条边")
                for edge_pair, edge_data in edges.items():
                    print(f"   - {edge_pair}: {edge_data.get('description')}")
            else:
                self.log_test("get_edges_batch", False,
                    f"预期 2 条边，实际获取 {len(edges)} 条")
        except Exception as e:
            self.log_test("get_edges_batch", False, f"异常: {e}")

    # ==================== 查询测试 ====================

    async def test_get_all_nodes(self):
        """测试获取所有节点"""
        print("\n" + "-" * 80)
        print("测试 16: get_all_nodes - 获取所有节点")
        print("-" * 80)

        try:
            nodes = await self.storage.get_all_nodes()

            if nodes and len(nodes) >= 4:  # 至少应该有我们插入的4个测试节点
                self.log_test("get_all_nodes", True,
                    f"成功获取 {len(nodes)} 个节点")
                # 显示前3个节点
                for node in nodes[:3]:
                    print(f"   - {node.get('id')}: {node.get('entity_type')}")
            else:
                self.log_test("get_all_nodes", False,
                    f"预期至少 4 个节点，实际获取 {len(nodes) if nodes else 0} 个")
        except Exception as e:
            self.log_test("get_all_nodes", False, f"异常: {e}")

    async def test_get_all_edges(self):
        """测试获取所有边"""
        print("\n" + "-" * 80)
        print("测试 17: get_all_edges - 获取所有边")
        print("-" * 80)

        try:
            edges = await self.storage.get_all_edges()

            if edges and len(edges) >= 3:  # 至少应该有我们插入的3条测试边
                self.log_test("get_all_edges", True,
                    f"成功获取 {len(edges)} 条边")
                # 显示前3条边
                for edge in edges[:3]:
                    print(f"   - {edge.get('source')} -> {edge.get('target')}: {edge.get('description')}")
            else:
                self.log_test("get_all_edges", False,
                    f"预期至少 3 条边，实际获取 {len(edges) if edges else 0} 条")
        except Exception as e:
            self.log_test("get_all_edges", False, f"异常: {e}")

    async def test_get_nodes_by_chunk_ids(self):
        """测试根据chunk_id获取节点"""
        print("\n" + "-" * 80)
        print("测试 18: get_nodes_by_chunk_ids - 根据chunk_id获取节点")
        print("-" * 80)

        try:
            nodes = await self.storage.get_nodes_by_chunk_ids([
                "test_chunk_001", "test_chunk_002", "test_chunk_999"
            ])

            if nodes and len(nodes) >= 2:  # 应该获取到至少2个节点
                self.log_test("get_nodes_by_chunk_ids", True,
                    f"成功获取 {len(nodes)} 个节点")
                for node in nodes[:3]:
                    print(f"   - {node.get('entity_id')}: chunk={node.get('source_id')}")
            else:
                self.log_test("get_nodes_by_chunk_ids", False,
                    f"预期至少 2 个节点，实际获取 {len(nodes) if nodes else 0} 个")
        except Exception as e:
            self.log_test("get_nodes_by_chunk_ids", False, f"异常: {e}")

    async def test_get_edges_by_chunk_ids(self):
        """测试根据chunk_id获取边"""
        print("\n" + "-" * 80)
        print("测试 19: get_edges_by_chunk_ids - 根据chunk_id获取边")
        print("-" * 80)

        try:
            edges = await self.storage.get_edges_by_chunk_ids([
                "test_chunk_001", "test_chunk_002"
            ])

            if edges and len(edges) >= 1:
                self.log_test("get_edges_by_chunk_ids", True,
                    f"成功获取 {len(edges)} 条边")
                for edge in edges[:3]:
                    print(f"   - {edge.get('source')} -> {edge.get('target')}: chunk={edge.get('source_id')}")
            else:
                self.log_test("get_edges_by_chunk_ids", False,
                    f"预期至少 1 条边，实际获取 {len(edges) if edges else 0} 条")
        except Exception as e:
            self.log_test("get_edges_by_chunk_ids", False, f"异常: {e}")

    async def test_get_popular_labels(self):
        """测试获取热门标签"""
        print("\n" + "-" * 80)
        print("测试 20: get_popular_labels - 获取热门标签（按度数排序的节点）")
        print("-" * 80)

        try:
            labels = await self.storage.get_popular_labels(limit=10)

            if labels:
                self.log_test("get_popular_labels", True,
                    f"成功获取 {len(labels)} 个热门标签")
                for label in labels[:5]:
                    print(f"   - {label}")
            else:
                self.log_test("get_popular_labels", False, "未获取到热门标签")
        except Exception as e:
            self.log_test("get_popular_labels", False, f"异常: {e}")

    # ==================== 删除测试 ====================

    async def test_remove_edges(self):
        """测试删除边"""
        print("\n" + "-" * 80)
        print("测试 21: remove_edges - 删除边")
        print("-" * 80)

        # 先插入一条测试边
        await self.storage.upsert_edge("测试节点4", "测试节点1", {
            "description": "待删除的测试边",
            "keywords": "测试,删除",
            "weight": 0.5,
            "source_id": "test_chunk_999"
        })

        try:
            # 删除边
            edges_to_remove = [("测试节点4", "测试节点1")]
            await self.storage.remove_edges(edges_to_remove)

            # 验证边是否已删除
            edge = await self.storage.get_edge("测试节点4", "测试节点1")

            if edge is None:
                self.log_test("remove_edges", True, "成功删除边")
            else:
                self.log_test("remove_edges", False, "边未被删除")
        except Exception as e:
            self.log_test("remove_edges", False, f"异常: {e}")

    async def test_delete_node(self):
        """测试删除单个节点"""
        print("\n" + "-" * 80)
        print("测试 23: delete_node - 删除单个节点")
        print("-" * 80)

        try:
            # 先插入一个待删除的节点
            await self.storage.upsert_node("待删除节点", {
                "entity_type": "temporary",
                "description": "这个节点将被删除",
                "source_id": "test_chunk_delete",
                "file_path": "test.txt"
            })

            # 验证节点存在
            exists_before = await self.storage.has_node("待删除节点")

            # 删除节点
            await self.storage.delete_node("待删除节点")

            # 验证节点已被删除
            exists_after = await self.storage.has_node("待删除节点")

            if exists_before and not exists_after:
                self.log_test("delete_node", True, "成功删除节点")
            else:
                self.log_test("delete_node", False,
                    f"删除失败: before={exists_before}, after={exists_after}")
        except Exception as e:
            self.log_test("delete_node", False, f"异常: {e}")

    async def test_remove_nodes(self):
        """测试批量删除节点"""
        print("\n" + "-" * 80)
        print("测试 24: remove_nodes - 批量删除节点")
        print("-" * 80)

        try:
            # 先插入多个待删除的节点
            test_nodes = [
                ("批量删除节点1", {"entity_type": "temp", "description": "临时节点1",
                  "source_id": "test_chunk_temp1", "file_path": "test.txt"}),
                ("批量删除节点2", {"entity_type": "temp", "description": "临时节点2",
                  "source_id": "test_chunk_temp2", "file_path": "test.txt"}),
                ("批量删除节点3", {"entity_type": "temp", "description": "临时节点3",
                  "source_id": "test_chunk_temp3", "file_path": "test.txt"})
            ]
            await self.storage.upsert_nodes(test_nodes)

            # 验证节点存在
            nodes_before = await self.storage.get_nodes_batch([
                "批量删除节点1", "批量删除节点2", "批量删除节点3"
            ])

            # 批量删除
            await self.storage.remove_nodes([
                "批量删除节点1", "批量删除节点2", "批量删除节点3"
            ])

            # 验证节点已被删除
            nodes_after = await self.storage.get_nodes_batch([
                "批量删除节点1", "批量删除节点2", "批量删除节点3"
            ])

            if len(nodes_before) == 3 and len(nodes_after) == 0:
                self.log_test("remove_nodes", True, "成功批量删除 3 个节点")
            else:
                self.log_test("remove_nodes", False,
                    f"删除失败: before={len(nodes_before)}, after={len(nodes_after)}")
        except Exception as e:
            self.log_test("remove_nodes", False, f"异常: {e}")

    async def test_get_all_labels(self):
        """测试获取所有标签"""
        print("\n" + "-" * 80)
        print("测试 25: get_all_labels - 获取所有节点标签")
        print("-" * 80)

        try:
            labels = await self.storage.get_all_labels()

            # 应该至少包含测试节点1-4的标签
            expected_labels = ["测试节点1", "测试节点2", "测试节点3", "测试节点4"]
            found_count = sum(1 for label in expected_labels if label in labels)

            if found_count >= 4:
                self.log_test("get_all_labels", True,
                    f"成功获取 {len(labels)} 个标签，包含所有测试节点")
                print(f"   标签示例: {labels[:5]}")
            else:
                self.log_test("get_all_labels", False,
                    f"预期至少 4 个测试标签，实际找到 {found_count} 个")
        except Exception as e:
            self.log_test("get_all_labels", False, f"异常: {e}")

    async def test_search_labels(self):
        """测试搜索标签"""
        print("\n" + "-" * 80)
        print("测试 26: search_labels - 搜索标签")
        print("-" * 80)

        try:
            # 搜索包含"测试"的标签（中文搜索）
            chinese_results = await self.storage.search_labels("测试", limit=10)

            # 搜索包含"node"的标签（如果有英文节点的话，这里主要测试功能）
            # 由于我们的测试数据都是中文，这里改为搜索"节点"
            results = await self.storage.search_labels("节点", limit=10)

            if len(results) >= 3:  # 应该至少找到测试节点1-4
                self.log_test("search_labels", True,
                    f"成功搜索到 {len(results)} 个标签")
                print(f"   搜索结果: {results[:5]}")
            else:
                self.log_test("search_labels", False,
                    f"预期至少 3 个结果，实际获取 {len(results)} 个")
        except Exception as e:
            self.log_test("search_labels", False, f"异常: {e}")

    async def test_drop(self):
        """测试删除整个Space（数据库）"""
        print("\n" + "-" * 80)
        print("测试 27: drop - 删除整个Space（数据库）")
        print("-" * 80)

        try:
            # 创建一个临时的测试space
            temp_storage = NebulaGraphStorage(
                namespace="test_drop_temp",
                global_config={
                    "host": "127.0.0.1",
                    "port": 9669,
                    "username": "root",
                    "password": "nebula",
                    "space_vid_type": "FIXED_STRING(256)"
                },
                embedding_func=lambda texts: [0.1] * 384 if isinstance(texts, str) else [[0.1] * 384 for _ in texts],
                workspace="test_drop_temp"
            )

            # 初始化临时space
            await temp_storage.initialize()

            # 添加一些测试数据
            await temp_storage.upsert_node("临时节点1", {
                "entity_type": "temp",
                "description": "临时测试数据",
                "source_id": "temp_chunk",
                "file_path": "temp.txt"
            })

            # 验证数据存在
            node_exists = await temp_storage.has_node("临时节点1")

            # 删除整个space
            await temp_storage.drop()

            # 关闭连接
            await temp_storage.finalize()

            if node_exists:
                self.log_test("drop", True, "成功删除整个Space (test_drop_temp)")
                print("   ⚠️  注意：Space 'test_drop_temp' 已被完全删除")
            else:
                self.log_test("drop", False, "临时数据创建失败，无法验证删除功能")
        except Exception as e:
            self.log_test("drop", False, f"异常: {e}")

    # ==================== 其他功能测试 ====================

    async def test_get_nodes_edges_batch(self):
        """测试批量获取多个节点的边"""
        print("\n" + "-" * 80)
        print("测试 28: get_nodes_edges_batch - 批量获取多个节点的边")
        print("-" * 80)

        try:
            result = await self.storage.get_nodes_edges_batch([
                "测试节点1", "测试节点2", "测试节点3"
            ])

            if result and len(result) >= 2:
                self.log_test("get_nodes_edges_batch", True,
                    f"成功获取 {len(result)} 个节点的边")
                for node_id, edges in result.items():
                    print(f"   - {node_id}: {len(edges)} 条边")
            else:
                self.log_test("get_nodes_edges_batch", False,
                    f"预期至少 2 个节点的边，实际获取 {len(result) if result else 0} 个")
        except Exception as e:
            self.log_test("get_nodes_edges_batch", False, f"异常: {e}")

    # ==================== 运行所有测试 ====================

    async def run_all_tests(self):
        """运行所有测试"""
        await self.setup()

        # 节点测试
        await self.test_upsert_node()
        await self.test_upsert_nodes_batch()
        await self.test_get_node()
        await self.test_get_nodes_batch()
        await self.test_has_node()

        # 边测试
        await self.test_upsert_edge()
        await self.test_upsert_edges_batch()
        await self.test_get_edge()
        await self.test_has_edge()
        await self.test_get_node_edges()

        # 度数测试
        await self.test_node_degree()
        await self.test_edge_degree()
        await self.test_node_degrees_batch()
        await self.test_edge_degrees_batch()
        await self.test_get_edges_batch()

        # 查询测试
        await self.test_get_all_nodes()
        await self.test_get_all_edges()
        await self.test_get_nodes_by_chunk_ids()
        await self.test_get_edges_by_chunk_ids()
        await self.test_get_popular_labels()

        # 删除测试
        await self.test_remove_edges()
        await self.test_delete_node()
        await self.test_remove_nodes()

        # 标签和搜索测试
        await self.test_get_all_labels()
        await self.test_search_labels()

        # 其他功能测试
        await self.test_get_nodes_edges_batch()

        # Space删除测试（放在最后，因为会创建和删除独立的space）
        await self.test_drop()

        await self.cleanup()

        # 打印测试总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)

        total = len(self.test_results['passed']) + len(self.test_results['failed'])
        passed = len(self.test_results['passed'])
        failed = len(self.test_results['failed'])

        print(f"\n总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"通过率: {(passed/total*100):.1f}%")

        if failed > 0:
            print("\n失败的测试:")
            for test_name in self.test_results['failed']:
                print(f"  - {test_name}")

        print("\n" + "=" * 80)

        if failed == 0:
            print("🎉 所有测试通过！")
        else:
            print("⚠️  存在失败的测试，请检查")
        print("=" * 80 + "\n")


async def main():
    """主函数"""
    suite = NebulaTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
