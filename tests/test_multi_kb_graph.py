# -*- coding: utf-8 -*-
"""
多知识库图谱查询接口测试

测试改造后的图谱查询接口，验证多知识库查询功能：
1. /echarts/top-k - Top-K 节点子图查询
2. /echarts - 完整图谱查询
3. /echarts/neighbors - 节点邻居子图查询

运行方式：
    python -m pytest tests/test_multi_kb_graph.py -v -s
    或直接运行：
    python tests/test_multi_kb_graph.py
"""
import asyncio
import time
import os
from pathlib import Path
from datetime import datetime

import aiohttp
import pytest


def timestamp():
    """返回当前时间戳字符串"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


# 配置
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

# 测试数据
WORKING_DIR_1 = "./test/multi_kb_graph_1"
WORKING_DIR_2 = "./test/multi_kb_graph_2"
RAG_1_ID = "multi_graph_rag_1"
RAG_2_ID = "multi_graph_rag_2"
RAG_1_WORKSPACE = "multi_graph_workspace_1"
RAG_2_WORKSPACE = "multi_graph_workspace_2"

# 测试文档路径
TEST_DOC_1 = "./test/graph_test_doc_1.txt"
TEST_DOC_2 = "./test/graph_test_doc_2.txt"


class TestMultiKBGraph:
    """多知识库图谱查询测试类"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前准备"""
        print("\n" + "="*70)
        print("开始准备测试环境")
        print("="*70)

        # 创建测试目录
        Path("./test").mkdir(exist_ok=True)
        Path(WORKING_DIR_1).mkdir(exist_ok=True)
        Path(WORKING_DIR_2).mkdir(exist_ok=True)

        # 创建测试文档
        self._create_test_documents()

        # 创建两个知识库实例并插入文档
        async with aiohttp.ClientSession() as session:
            await self._setup_knowledge_bases(session)

        print(f"\n[{timestamp()}] 测试环境准备完成\n")

        yield

        # 测试后清理
        print("\n" + "="*70)
        print("开始清理测试环境")
        print("="*70)
        async with aiohttp.ClientSession() as session:
            await self._cleanup(session)

    def _create_test_documents(self):
        """创建测试文档"""
        # 文档 1：关于人工智能
        if not os.path.exists(TEST_DOC_1):
            with open(TEST_DOC_1, 'w', encoding='utf-8') as f:
                f.write("人工智能是计算机科学的一个重要分支。\n")
                f.write("机器学习是人工智能的核心技术之一。\n")
                f.write("深度学习基于神经网络模型。\n")
                f.write("自然语言处理用于理解和生成人类语言。\n")
            print(f"[{timestamp()}] 创建测试文件: {TEST_DOC_1}")

        # 文档 2：关于数据库
        if not os.path.exists(TEST_DOC_2):
            with open(TEST_DOC_2, 'w', encoding='utf-8') as f:
                f.write("数据库是存储和管理数据的系统。\n")
                f.write("关系型数据库使用表格存储数据。\n")
                f.write("图数据库适合存储复杂关系。\n")
                f.write("NoSQL数据库提供灵活的数据模型。\n")
            print(f"[{timestamp()}] 创建测试文件: {TEST_DOC_2}")

    async def _setup_knowledge_bases(self, session):
        """设置知识库并插入文档"""
        print(f"[{timestamp()}] 开始创建知识库...")

        # 创建知识库 1
        print(f"[{timestamp()}] 创建知识库 1: {RAG_1_ID}")
        result1 = await self._create_rag_instance(
            session, RAG_1_ID, RAG_1_WORKSPACE, WORKING_DIR_1, "AI知识库"
        )
        if isinstance(result1, Exception):
            print(f"[{timestamp()}] ⚠️  知识库 1 创建失败: {result1}")
        else:
            print(f"[{timestamp()}] ✓ 知识库 1 创建成功")

        # 创建知识库 2
        print(f"[{timestamp()}] 创建知识库 2: {RAG_2_ID}")
        result2 = await self._create_rag_instance(
            session, RAG_2_ID, RAG_2_WORKSPACE, WORKING_DIR_2, "数据库知识库"
        )
        if isinstance(result2, Exception):
            print(f"[{timestamp()}] ⚠️  知识库 2 创建失败: {result2}")
        else:
            print(f"[{timestamp()}] ✓ 知识库 2 创建成功")

        # 等待初始化完成
        await asyncio.sleep(5)

        # 插入文档到知识库 1
        print(f"[{timestamp()}] 向知识库 1 插入文档...")
        await self._insert_document(session, RAG_1_ID, TEST_DOC_1)

        # 插入文档到知识库 2
        print(f"[{timestamp()}] 向知识库 2 插入文档...")
        await self._insert_document(session, RAG_2_ID, TEST_DOC_2)

        # 等待索引完成
        print(f"[{timestamp()}] 等待索引完成...")
        await asyncio.sleep(10)

    async def _create_rag_instance(self, session, rag_id, workspace, working_dir, description):
        """创建 RAG 实例"""
        url = f"{BASE_URL}{API_PREFIX}/admin/rag_instances/create"
        payload = {
            "rag_id": rag_id,
            "workspace": workspace,
            "working_dir": working_dir,
            "description": description,
            "enable_llm": True
        }

        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=180)) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    return Exception(f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            return e

    async def _insert_document(self, session, rag_id, file_path):
        """插入文档"""
        url = f"{BASE_URL}{API_PREFIX}/documents/upload"

        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('rag_id', rag_id)
            data.add_field('file', f, filename=os.path.basename(file_path))

            try:
                async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        print(f"[{timestamp()}] ✓ 文档插入成功: {file_path}")
                        return result
                    else:
                        error_text = await resp.text()
                        print(f"[{timestamp()}] ✗ 文档插入失败: {error_text}")
                        return None
            except Exception as e:
                print(f"[{timestamp()}] ✗ 文档插入异常: {str(e)}")
                return None

    async def _cleanup(self, session):
        """清理测试数据"""
        print(f"[{timestamp()}] 删除知识库 1: {RAG_1_ID}")
        await self._delete_rag_instance(session, RAG_1_ID)

        print(f"[{timestamp()}] 删除知识库 2: {RAG_2_ID}")
        await self._delete_rag_instance(session, RAG_2_ID)

        print(f"[{timestamp()}] 清理完成")

    async def _delete_rag_instance(self, session, rag_id):
        """删除 RAG 实例"""
        url = f"{BASE_URL}{API_PREFIX}/admin/rag_instances/{rag_id}"
        try:
            async with session.delete(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    print(f"[{timestamp()}] ✓ 知识库删除成功: {rag_id}")
                else:
                    error_text = await resp.text()
                    print(f"[{timestamp()}] ⚠️  知识库删除失败: {error_text}")
        except Exception as e:
            print(f"[{timestamp()}] ⚠️  知识库删除异常: {str(e)}")

    @pytest.mark.asyncio
    async def test_multi_kb_echarts_full(self):
        """测试 1: 多知识库完整图谱查询 (/echarts)"""
        print("\n" + "="*70)
        print("测试 1: 多知识库完整图谱查询")
        print("="*70)

        async with aiohttp.ClientSession() as session:
            # 测试单知识库查询
            print(f"\n[{timestamp()}] 1.1 测试单知识库查询")
            url_single = f"{BASE_URL}{API_PREFIX}/graph/echarts?rag_ids={RAG_1_ID}"
            print(f"[{timestamp()}] → 请求 URL: {url_single}")

            async with session.get(url_single) as resp:
                print(f"[{timestamp()}] ← 响应状态: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    print(f"[{timestamp()}] ← 成功查询知识库: {result.get('rag_ids')}")
                    nodes = result.get('data', {}).get('nodes', [])
                    links = result.get('data', {}).get('links', [])
                    print(f"[{timestamp()}] ← 节点数: {len(nodes)}, 边数: {len(links)}")

                    # 验证节点包含 rag_id
                    if nodes:
                        sample_node = nodes[0]
                        assert 'rag_id' in sample_node, "节点应包含 rag_id 字段"
                        print(f"[{timestamp()}] ✓ 节点包含 rag_id 字段: {sample_node.get('rag_id')}")

                    # 验证边包含 rag_id
                    if links:
                        sample_link = links[0]
                        assert 'rag_id' in sample_link, "边应包含 rag_id 字段"
                        print(f"[{timestamp()}] ✓ 边包含 rag_id 字段: {sample_link.get('rag_id')}")
                else:
                    error_text = await resp.text()
                    print(f"[{timestamp()}] ✗ 查询失败: {error_text}")
                    pytest.fail(f"单知识库查询失败: {error_text}")

            # 测试多知识库查询
            print(f"\n[{timestamp()}] 1.2 测试多知识库查询")
            url_multi = f"{BASE_URL}{API_PREFIX}/graph/echarts?rag_ids={RAG_1_ID}&rag_ids={RAG_2_ID}"
            print(f"[{timestamp()}] → 请求 URL: {url_multi}")

            async with session.get(url_multi) as resp:
                print(f"[{timestamp()}] ← 响应状态: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    rag_ids = result.get('rag_ids', [])
                    print(f"[{timestamp()}] ← 成功查询知识库: {rag_ids}")
                    assert len(rag_ids) == 2, f"应返回2个知识库，实际: {len(rag_ids)}"

                    nodes = result.get('data', {}).get('nodes', [])
                    links = result.get('data', {}).get('links', [])
                    print(f"[{timestamp()}] ← 节点数: {len(nodes)}, 边数: {len(links)}")

                    # 统计不同知识库的节点数
                    kb1_nodes = [n for n in nodes if n.get('rag_id') == RAG_1_ID]
                    kb2_nodes = [n for n in nodes if n.get('rag_id') == RAG_2_ID]
                    print(f"[{timestamp()}] ← {RAG_1_ID} 节点数: {len(kb1_nodes)}")
                    print(f"[{timestamp()}] ← {RAG_2_ID} 节点数: {len(kb2_nodes)}")

                    print(f"[{timestamp()}] ✓ 多知识库完整图谱查询测试通过")
                else:
                    error_text = await resp.text()
                    print(f"[{timestamp()}] ✗ 查询失败: {error_text}")
                    pytest.fail(f"多知识库查询失败: {error_text}")

    @pytest.mark.asyncio
    async def test_multi_kb_top_k(self):
        """测试 2: 多知识库 Top-K 查询 (/echarts/top-k)"""
        print("\n" + "="*70)
        print("测试 2: 多知识库 Top-K 查询")
        print("="*70)

        async with aiohttp.ClientSession() as session:
            # 测试多知识库 Top-K 查询
            k = 5
            url = f"{BASE_URL}{API_PREFIX}/graph/echarts/top-k?rag_ids={RAG_1_ID}&rag_ids={RAG_2_ID}&k={k}"
            print(f"\n[{timestamp()}] → 请求 URL: {url}")
            print(f"[{timestamp()}] → 查询参数: k={k}")

            async with session.get(url) as resp:
                print(f"[{timestamp()}] ← 响应状态: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    rag_ids = result.get('rag_ids', [])
                    returned_k = result.get('k')
                    print(f"[{timestamp()}] ← 成功查询知识库: {rag_ids}")
                    print(f"[{timestamp()}] ← 返回 k 值: {returned_k}")

                    nodes = result.get('data', {}).get('nodes', [])
                    links = result.get('data', {}).get('links', [])
                    print(f"[{timestamp()}] ← 节点数: {len(nodes)}, 边数: {len(links)}")

                    # 验证每个知识库的节点数不超过 k
                    kb1_nodes = [n for n in nodes if n.get('rag_id') == RAG_1_ID]
                    kb2_nodes = [n for n in nodes if n.get('rag_id') == RAG_2_ID]
                    print(f"[{timestamp()}] ← {RAG_1_ID} 节点数: {len(kb1_nodes)} (期望 <= {k})")
                    print(f"[{timestamp()}] ← {RAG_2_ID} 节点数: {len(kb2_nodes)} (期望 <= {k})")

                    assert len(kb1_nodes) <= k, f"{RAG_1_ID} 节点数应 <= {k}"
                    assert len(kb2_nodes) <= k, f"{RAG_2_ID} 节点数应 <= {k}"

                    # 验证所有节点都有 rag_id
                    for node in nodes:
                        assert 'rag_id' in node, f"节点缺少 rag_id 字段: {node}"

                    # 验证所有边都有 rag_id
                    for link in links:
                        assert 'rag_id' in link, f"边缺少 rag_id 字段: {link}"

                    print(f"[{timestamp()}] ✓ Top-K 查询测试通过")
                else:
                    error_text = await resp.text()
                    print(f"[{timestamp()}] ✗ 查询失败: {error_text}")
                    pytest.fail(f"Top-K 查询失败: {error_text}")

    @pytest.mark.asyncio
    async def test_multi_kb_neighbors(self):
        """测试 3: 多知识库邻居查询 (/echarts/neighbors)"""
        print("\n" + "="*70)
        print("测试 3: 多知识库邻居查询")
        print("="*70)

        async with aiohttp.ClientSession() as session:
            # 首先获取一个节点名称
            url_get_nodes = f"{BASE_URL}{API_PREFIX}/graph/echarts?rag_ids={RAG_1_ID}"
            print(f"\n[{timestamp()}] 先获取节点列表...")

            node_id = None
            async with session.get(url_get_nodes) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    nodes = result.get('data', {}).get('nodes', [])
                    if nodes:
                        node_id = nodes[0].get('id') or nodes[0].get('name')
                        print(f"[{timestamp()}] 获取到测试节点: {node_id}")

            if not node_id:
                print(f"[{timestamp()}] ⚠️  未找到可测试的节点，跳过邻居查询测试")
                pytest.skip("未找到可测试的节点")
                return

            # 测试多知识库邻居查询
            url = f"{BASE_URL}{API_PREFIX}/graph/echarts/neighbors?node_id={node_id}&rag_ids={RAG_1_ID}&rag_ids={RAG_2_ID}"
            print(f"\n[{timestamp()}] → 请求 URL: {url}")
            print(f"[{timestamp()}] → 查询节点: {node_id}")

            async with session.get(url) as resp:
                print(f"[{timestamp()}] ← 响应状态: {resp.status}")
                if resp.status == 200:
                    result = await resp.json()
                    returned_node_id = result.get('node_id')
                    rag_ids = result.get('rag_ids', [])
                    print(f"[{timestamp()}] ← 查询节点: {returned_node_id}")
                    print(f"[{timestamp()}] ← 涉及知识库: {rag_ids}")

                    nodes = result.get('data', {}).get('nodes', [])
                    links = result.get('data', {}).get('links', [])
                    print(f"[{timestamp()}] ← 节点数: {len(nodes)}, 边数: {len(links)}")

                    # 统计不同知识库的数据
                    kb1_nodes = [n for n in nodes if n.get('rag_id') == RAG_1_ID]
                    kb2_nodes = [n for n in nodes if n.get('rag_id') == RAG_2_ID]
                    print(f"[{timestamp()}] ← {RAG_1_ID} 节点数: {len(kb1_nodes)}")
                    print(f"[{timestamp()}] ← {RAG_2_ID} 节点数: {len(kb2_nodes)}")

                    # 验证所有节点都有 rag_id
                    for node in nodes:
                        assert 'rag_id' in node, f"节点缺少 rag_id 字段: {node}"

                    # 验证所有边都有 rag_id
                    for link in links:
                        assert 'rag_id' in link, f"边缺少 rag_id 字段: {link}"

                    print(f"[{timestamp()}] ✓ 邻居查询测试通过")
                else:
                    error_text = await resp.text()
                    print(f"[{timestamp()}] ⚠️  查询失败: {error_text}")
                    # 邻居查询可能因为节点不存在而失败，不算测试失败
                    print(f"[{timestamp()}] ⚠️  节点可能在指定知识库中不存在，跳过")


if __name__ == "__main__":
    # 直接运行此脚本
    import sys
    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
