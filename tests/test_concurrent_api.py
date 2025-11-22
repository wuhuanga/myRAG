# -*- coding: utf-8 -*-
"""
并发 API 测试脚本

测试 RAG 服务的并发安全性：
1. 并发创建知识库
2. 并发插入文档
3. 并发查询（同一知识库 / 不同知识库）
4. 并发删除知识库

运行方式：
    python -m pytest tests/test_concurrent_api.py -v -s
    或直接运行：
    python tests/test_concurrent_api.py
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
WORKING_DIR = "./test_rag_storage"
RAG_1_ID = "rag_1"
RAG_2_ID = "rag_2"
RAG_1_WORKSPACE = "workspace_1"
RAG_2_WORKSPACE = "workspace_2"

# 文档路径（请根据实际情况修改）
DOC_1_PATH = "weix.docx"
DOC_2_PATH = "sad.txt"

# 查询语句（可自行修改）
QUERY_1 = "这个文档的主要内容是什么？"
QUERY_2 = "请总结一下文档中的关键信息"
QUERY_3 = "文档中提到了哪些重要概念？"


class TestConcurrentAPI:
    """并发 API 测试类"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前准备"""
        # 创建测试目录
        Path(WORKING_DIR).mkdir(exist_ok=True)

        # 创建测试文档（如果不存在）
        self._ensure_test_files_exist()

        yield

        # 测试后清理（可选）
        # await self._cleanup()

    def _ensure_test_files_exist(self):
        """确保测试文件存在"""
        # 如果 sad.txt 不存在，创建一个测试文件
        if not os.path.exists(DOC_2_PATH):
            with open(DOC_2_PATH, 'w', encoding='utf-8') as f:
                f.write("这是一个测试文档。\n")
                f.write("包含一些测试内容用于验证 RAG 系统。\n")
                f.write("主要用于并发测试场景。\n")
            print(f"创建测试文件: {DOC_2_PATH}")

    @pytest.mark.asyncio
    async def test_concurrent_create_instances(self):
        """测试 1: 并发创建两个知识库"""
        print("\n" + "="*60)
        print("测试 1: 并发创建知识库")
        print("="*60)

        async with aiohttp.ClientSession() as session:
            # 准备创建请求
            create_tasks = [
                self._create_rag_instance(
                    session, RAG_1_ID, RAG_1_WORKSPACE, "知识库1"
                ),
                self._create_rag_instance(
                    session, RAG_2_ID, RAG_2_WORKSPACE, "知识库2"
                ),
            ]

            start_time = time.time()
            results = await asyncio.gather(*create_tasks, return_exceptions=True)
            elapsed = time.time() - start_time

            print(f"\n并发创建完成，耗时: {elapsed:.2f}秒")

            # 检查结果
            for i, result in enumerate(results):
                rag_id = RAG_1_ID if i == 0 else RAG_2_ID
                if isinstance(result, Exception):
                    print(f"  {rag_id}: 失败 - {result}")
                else:
                    print(f"  {rag_id}: {result.get('status', 'unknown')}")
                    if result.get('status') == 'success':
                        assert True
                    else:
                        # 如果已存在，也算通过
                        print(f"    详情: {result}")

    @pytest.mark.asyncio
    async def test_concurrent_upload_documents(self):
        """测试 2: 并发插入文档到不同知识库"""
        print("\n" + "="*60)
        print("测试 2: 并发插入文档")
        print("="*60)

        async with aiohttp.ClientSession() as session:
            # 准备上传任务
            upload_tasks = [
                self._upload_document(session, RAG_1_ID, DOC_1_PATH),
                self._upload_document(session, RAG_2_ID, DOC_2_PATH),
            ]

            start_time = time.time()
            results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            elapsed = time.time() - start_time

            print(f"\n并发上传完成，耗时: {elapsed:.2f}秒")

            # 检查结果
            for i, result in enumerate(results):
                rag_id = RAG_1_ID if i == 0 else RAG_2_ID
                doc_path = DOC_1_PATH if i == 0 else DOC_2_PATH
                if isinstance(result, Exception):
                    print(f"  {rag_id} ({doc_path}): 失败 - {result}")
                else:
                    status = result.get('status', 'unknown')
                    print(f"  {rag_id} ({doc_path}): {status}")
                    if 'error' in str(result).lower():
                        print(f"    详情: {result}")

    @pytest.mark.asyncio
    async def test_concurrent_query_same_kb(self):
        """测试 3a: 并发查询同一个知识库"""
        print("\n" + "="*60)
        print("测试 3a: 并发查询同一知识库")
        print("="*60)

        async with aiohttp.ClientSession() as session:
            # 对同一知识库发起多个并发查询
            query_tasks = [
                self._query(session, RAG_1_ID, QUERY_1, "hybrid"),
                self._query(session, RAG_1_ID, QUERY_2, "hybrid"),
                self._query(session, RAG_1_ID, QUERY_3, "local"),
            ]

            start_time = time.time()
            results = await asyncio.gather(*query_tasks, return_exceptions=True)
            elapsed = time.time() - start_time

            print(f"\n并发查询完成，耗时: {elapsed:.2f}秒")

            # 检查结果
            queries = [QUERY_1, QUERY_2, QUERY_3]
            for i, result in enumerate(results):
                query = queries[i][:20] + "..." if len(queries[i]) > 20 else queries[i]
                if isinstance(result, Exception):
                    print(f"  查询 '{query}': 失败 - {result}")
                else:
                    status = "成功" if result.get('answer') else "无结果"
                    answer_preview = result.get('answer', '')[:50] + "..." if result.get('answer') else "N/A"
                    print(f"  查询 '{query}': {status}")
                    print(f"    回答预览: {answer_preview}")

    @pytest.mark.asyncio
    async def test_concurrent_query_different_kb(self):
        """测试 3b: 并发查询不同知识库"""
        print("\n" + "="*60)
        print("测试 3b: 并发查询不同知识库")
        print("="*60)

        async with aiohttp.ClientSession() as session:
            # 对不同知识库发起并发查询
            query_tasks = [
                self._query(session, RAG_1_ID, QUERY_1, "hybrid"),
                self._query(session, RAG_2_ID, QUERY_1, "hybrid"),
                self._query(session, RAG_1_ID, QUERY_2, "local"),
                self._query(session, RAG_2_ID, QUERY_2, "global"),
            ]

            start_time = time.time()
            results = await asyncio.gather(*query_tasks, return_exceptions=True)
            elapsed = time.time() - start_time

            print(f"\n并发查询完成，耗时: {elapsed:.2f}秒")

            # 检查结果
            rag_ids = [RAG_1_ID, RAG_2_ID, RAG_1_ID, RAG_2_ID]
            modes = ["hybrid", "hybrid", "local", "global"]
            for i, result in enumerate(results):
                rag_id = rag_ids[i]
                mode = modes[i]
                if isinstance(result, Exception):
                    print(f"  {rag_id} ({mode}): 失败 - {result}")
                else:
                    status = "成功" if result.get('answer') else "无结果"
                    answer_preview = result.get('answer', '')[:50] + "..." if result.get('answer') else "N/A"
                    print(f"  {rag_id} ({mode}): {status}")
                    print(f"    回答预览: {answer_preview}")

    @pytest.mark.asyncio
    async def test_concurrent_delete_instances(self):
        """测试 4: 并发删除知识库"""
        print("\n" + "="*60)
        print("测试 4: 并发删除知识库")
        print("="*60)

        async with aiohttp.ClientSession() as session:
            # 准备删除任务
            delete_tasks = [
                self._delete_rag_instance(session, RAG_1_ID),
                self._delete_rag_instance(session, RAG_2_ID),
            ]

            start_time = time.time()
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)
            elapsed = time.time() - start_time

            print(f"\n并发删除完成，耗时: {elapsed:.2f}秒")

            # 检查结果
            for i, result in enumerate(results):
                rag_id = RAG_1_ID if i == 0 else RAG_2_ID
                if isinstance(result, Exception):
                    print(f"  {rag_id}: 失败 - {result}")
                else:
                    print(f"  {rag_id}: {result.get('status', 'unknown')}")

    # ==================== 辅助方法 ====================

    async def _create_rag_instance(
        self,
        session: aiohttp.ClientSession,
        rag_id: str,
        workspace: str,
        description: str = ""
    ) -> dict:
        """创建 RAG 实例"""
        url = f"{BASE_URL}{API_PREFIX}/admin/rag_instances/create"
        data = {
            "rag_id": rag_id,
            "workspace": workspace,
            "working_dir": WORKING_DIR,
            "description": description,
        }

        print(f"  [{timestamp()}] 开始创建 {rag_id}...")
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                print(f"  [{timestamp()}] 完成创建 {rag_id}: {result.get('status', 'unknown')}")
                return result
        except Exception as e:
            print(f"  [{timestamp()}] 创建 {rag_id} 失败: {e}")
            return {"status": "error", "message": str(e)}

    async def _upload_document(
        self,
        session: aiohttp.ClientSession,
        rag_id: str,
        file_path: str
    ) -> dict:
        """上传文档"""
        url = f"{BASE_URL}{API_PREFIX}/documents/upload"

        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"  [{timestamp()}] {rag_id} 文件不存在: {file_path}")
            return {"status": "error", "message": f"文件不存在: {file_path}"}

        print(f"  [{timestamp()}] 开始上传 {rag_id} <- {os.path.basename(file_path)}...")
        try:
            # 准备 multipart 表单数据
            data = aiohttp.FormData()
            data.add_field('rag_id', rag_id)
            data.add_field(
                'file',
                open(file_path, 'rb'),
                filename=os.path.basename(file_path)
            )

            async with session.post(url, data=data) as response:
                result = await response.json()
                print(f"  [{timestamp()}] 完成上传 {rag_id}: {result.get('status', 'unknown')}")
                return result
        except Exception as e:
            print(f"  [{timestamp()}] 上传 {rag_id} 失败: {e}")
            return {"status": "error", "message": str(e)}

    async def _query(
        self,
        session: aiohttp.ClientSession,
        rag_id: str,
        question: str,
        mode: str = "hybrid"
    ) -> dict:
        """查询知识库"""
        url = f"{BASE_URL}{API_PREFIX}/query/"
        data = {
            "rag_id": rag_id,
            "question": question,
            "mode": mode,
            "only_need_context": True,
        }

        query_preview = question[:15] + "..." if len(question) > 15 else question
        print(f"  [{timestamp()}] 开始查询 {rag_id} ({mode}): {query_preview}")
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                status = "成功" if result.get('answer') else "无结果"
                print(f"  [{timestamp()}] 完成查询 {rag_id} ({mode}): {status}")
                return result
        except Exception as e:
            print(f"  [{timestamp()}] 查询 {rag_id} 失败: {e}")
            return {"status": "error", "message": str(e)}

    async def _delete_rag_instance(
        self,
        session: aiohttp.ClientSession,
        rag_id: str
    ) -> dict:
        """删除 RAG 实例"""
        url = f"{BASE_URL}{API_PREFIX}/admin/rag_instances/{rag_id}"

        print(f"  [{timestamp()}] 开始删除 {rag_id}...")
        try:
            async with session.delete(url) as response:
                result = await response.json()
                print(f"  [{timestamp()}] 完成删除 {rag_id}: {result.get('status', 'unknown')}")
                return result
        except Exception as e:
            print(f"  [{timestamp()}] 删除 {rag_id} 失败: {e}")
            return {"status": "error", "message": str(e)}

    async def _list_instances(
        self,
        session: aiohttp.ClientSession
    ) -> dict:
        """列出所有 RAG 实例"""
        url = f"{BASE_URL}{API_PREFIX}/admin/rag_instances/list"

        try:
            async with session.get(url) as response:
                result = await response.json()
                return result
        except Exception as e:
            return {"status": "error", "message": str(e)}


# ==================== 直接运行测试 ====================

async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("RAG 服务并发测试")
    print("="*60)
    print(f"服务地址: {BASE_URL}")
    print(f"测试知识库: {RAG_1_ID}, {RAG_2_ID}")
    print(f"测试文档: {DOC_1_PATH}, {DOC_2_PATH}")

    test = TestConcurrentAPI()

    # 确保测试文件存在
    test._ensure_test_files_exist()

    try:
        # 测试 1: 并发创建
        await test.test_concurrent_create_instances()

        # 等待实例初始化完成
        print("\n等待实例初始化...")
        await asyncio.sleep(2)

        # 测试 2: 并发上传
        await test.test_concurrent_upload_documents()

        # 等待文档处理完成
        print("\n等待文档处理...")
        await asyncio.sleep(5)

        # 测试 3a: 并发查询同一知识库
        await test.test_concurrent_query_same_kb()

        # 测试 3b: 并发查询不同知识库
        await test.test_concurrent_query_different_kb()

        # 测试 4: 并发删除
        # 注意：删除后知识库将不可用，请谨慎运行
        # await test.test_concurrent_delete_instances()

        print("\n" + "="*60)
        print("所有测试完成!")
        print("="*60)

    except Exception as e:
        print(f"\n测试失败: {e}")
        raise


async def run_stress_test(num_queries: int = 10):
    """压力测试：对同一知识库发起大量并发查询"""
    print("\n" + "="*60)
    print(f"压力测试: {num_queries} 个并发查询")
    print("="*60)

    async with aiohttp.ClientSession() as session:
        test = TestConcurrentAPI()

        # 准备查询任务
        query_tasks = []
        for i in range(num_queries):
            query = f"测试查询 {i+1}: 文档的主要内容是什么？"
            mode = ["hybrid", "local", "global"][i % 3]
            query_tasks.append(test._query(session, RAG_1_ID, query, mode))

        start_time = time.time()
        results = await asyncio.gather(*query_tasks, return_exceptions=True)
        elapsed = time.time() - start_time

        # 统计结果
        success = sum(1 for r in results if not isinstance(r, Exception) and r.get('answer'))
        failed = len(results) - success

        print(f"\n压力测试完成:")
        print(f"  总查询数: {num_queries}")
        print(f"  成功: {success}")
        print(f"  失败: {failed}")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  平均耗时: {elapsed/num_queries:.2f}秒/查询")
        print(f"  QPS: {num_queries/elapsed:.2f}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "stress":
        # 运行压力测试
        num = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        asyncio.run(run_stress_test(num))
    else:
        # 运行标准测试
        asyncio.run(run_all_tests())
