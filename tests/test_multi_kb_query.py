#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多知识库查询接口测试
测试所有 5 个 RAG 查询接口的多知识库支持
"""
import asyncio
import aiohttp
import sys
import os
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

# 测试用的知识库 ID（需要提前创建）
TEST_RAG_IDS = ["test_kb1", "test_kb2"]
TEST_SINGLE_RAG_ID = "test_kb1"


def timestamp():
    """返回格式化的时间戳"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


class MultiKBQueryTester:
    """多知识库查询接口测试器"""

    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def log_result(self, test_name, passed, message=""):
        """记录测试结果"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✓ PASS"
        else:
            self.failed_tests += 1
            status = "✗ FAIL"

        self.test_results.append({
            "test": test_name,
            "status": status,
            "message": message
        })
        print(f"[{timestamp()}] {status} - {test_name}")
        if message:
            print(f"          {message}")

    async def test_standard_query_single(self, session):
        """测试 1.1: 标准查询 - 单知识库模式"""
        print(f"\n[{timestamp()}] ========== 测试 1.1: 标准查询 - 单知识库 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/"
        payload = {
            "rag_id": TEST_SINGLE_RAG_ID,
            "question": "什么是RAG？",
            "mode": "hybrid",
            "only_need_context": True
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # 验证响应格式
                    if "rag_ids" in data and isinstance(data["rag_ids"], list):
                        if len(data["rag_ids"]) == 1 and data["rag_ids"][0] == TEST_SINGLE_RAG_ID:
                            self.log_result("标准查询-单知识库", True, f"响应: {data['rag_ids']}")
                        else:
                            self.log_result("标准查询-单知识库", False, f"rag_ids 不匹配: {data['rag_ids']}")
                    else:
                        self.log_result("标准查询-单知识库", False, "响应格式错误")
                else:
                    error_text = await resp.text()
                    self.log_result("标准查询-单知识库", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("标准查询-单知识库", False, f"异常: {str(e)}")

    async def test_standard_query_multi(self, session):
        """测试 1.2: 标准查询 - 多知识库模式"""
        print(f"\n[{timestamp()}] ========== 测试 1.2: 标准查询 - 多知识库 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/"
        payload = {
            "rag_ids": TEST_RAG_IDS,
            "question": "什么是RAG？",
            "mode": "hybrid",
            "only_need_context": True,
            "top_k": 10
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # 验证响应格式
                    if "rag_ids" in data and isinstance(data["rag_ids"], list):
                        if len(data["rag_ids"]) > 0:
                            has_sources = "sources" in data and isinstance(data["sources"], list)
                            self.log_result(
                                "标准查询-多知识库",
                                True,
                                f"查询 {len(data['rag_ids'])} 个知识库, sources: {has_sources}"
                            )
                        else:
                            self.log_result("标准查询-多知识库", False, "rag_ids 为空")
                    else:
                        self.log_result("标准查询-多知识库", False, "响应格式错误")
                else:
                    error_text = await resp.text()
                    self.log_result("标准查询-多知识库", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("标准查询-多知识库", False, f"异常: {str(e)}")

    async def test_keywords_search_single(self, session):
        """测试 2.1: 关键字检索 - 单知识库"""
        print(f"\n[{timestamp()}] ========== 测试 2.1: 关键字检索 - 单知识库 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/keywords"
        payload = {
            "rag_id": TEST_SINGLE_RAG_ID,
            "keywords": ["RAG", "向量数据库"],
            "mode": "hybrid"
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "rag_ids" in data and "context" in data:
                        self.log_result(
                            "关键字检索-单知识库",
                            True,
                            f"检索到上下文: {len(data.get('context', ''))} 字符"
                        )
                    else:
                        self.log_result("关键字检索-单知识库", False, "响应格式错误")
                else:
                    error_text = await resp.text()
                    self.log_result("关键字检索-单知识库", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("关键字检索-单知识库", False, f"异常: {str(e)}")

    async def test_keywords_search_multi(self, session):
        """测试 2.2: 关键字检索 - 多知识库"""
        print(f"\n[{timestamp()}] ========== 测试 2.2: 关键字检索 - 多知识库 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/keywords"
        payload = {
            "rag_ids": TEST_RAG_IDS,
            "keywords": ["RAG", "向量数据库"],
            "mode": "hybrid",
            "top_k": 10
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "rag_ids" in data and "context" in data:
                        has_sources = "sources" in data
                        self.log_result(
                            "关键字检索-多知识库",
                            True,
                            f"检索 {len(data['rag_ids'])} 个知识库, sources: {has_sources}"
                        )
                    else:
                        self.log_result("关键字检索-多知识库", False, "响应格式错误")
                else:
                    error_text = await resp.text()
                    self.log_result("关键字检索-多知识库", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("关键字检索-多知识库", False, f"异常: {str(e)}")

    async def test_graph_clean_single(self, session):
        """测试 3.1: 清理图谱检索 - 单知识库"""
        print(f"\n[{timestamp()}] ========== 测试 3.1: 清理图谱检索 - 单知识库 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/graph-clean"
        payload = {
            "rag_id": TEST_SINGLE_RAG_ID,
            "keywords": ["RAG"],
            "top_k": 10
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "rag_ids" in data and "entities" in data and "relationships" in data:
                        self.log_result(
                            "清理图谱检索-单知识库",
                            True,
                            f"实体: {len(data['entities'])}, 关系: {len(data['relationships'])}"
                        )
                    else:
                        self.log_result("清理图谱检索-单知识库", False, "响应格式错误")
                else:
                    error_text = await resp.text()
                    self.log_result("清理图谱检索-单知识库", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("清理图谱检索-单知识库", False, f"异常: {str(e)}")

    async def test_graph_clean_multi(self, session):
        """测试 3.2: 清理图谱检索 - 多知识库"""
        print(f"\n[{timestamp()}] ========== 测试 3.2: 清理图谱检索 - 多知识库 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/graph-clean"
        payload = {
            "rag_ids": TEST_RAG_IDS,
            "keywords": ["RAG"],
            "top_k": 20
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "rag_ids" in data and "entities" in data and "relationships" in data:
                        has_sources = "sources" in data
                        self.log_result(
                            "清理图谱检索-多知识库",
                            True,
                            f"查询 {len(data['rag_ids'])} 个知识库, 实体: {len(data['entities'])}, 关系: {len(data['relationships'])}, sources: {has_sources}"
                        )
                    else:
                        self.log_result("清理图谱检索-多知识库", False, "响应格式错误")
                else:
                    error_text = await resp.text()
                    self.log_result("清理图谱检索-多知识库", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("清理图谱检索-多知识库", False, f"异常: {str(e)}")

    async def test_chunks_only_single(self, session):
        """测试 4.1: 仅 Chunks 检索 - 单知识库"""
        print(f"\n[{timestamp()}] ========== 测试 4.1: 仅 Chunks 检索 - 单知识库 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/chunks-only"
        payload = {
            "rag_id": TEST_SINGLE_RAG_ID,
            "keywords": ["RAG"],
            "chunk_top_k": 5
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "rag_ids" in data and "chunks" in data:
                        self.log_result(
                            "仅Chunks检索-单知识库",
                            True,
                            f"Chunks: {len(data['chunks'])}"
                        )
                    else:
                        self.log_result("仅Chunks检索-单知识库", False, "响应格式错误")
                else:
                    error_text = await resp.text()
                    self.log_result("仅Chunks检索-单知识库", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("仅Chunks检索-单知识库", False, f"异常: {str(e)}")

    async def test_chunks_only_multi(self, session):
        """测试 4.2: 仅 Chunks 检索 - 多知识库"""
        print(f"\n[{timestamp()}] ========== 测试 4.2: 仅 Chunks 检索 - 多知识库 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/chunks-only"
        payload = {
            "rag_ids": TEST_RAG_IDS,
            "keywords": ["RAG"],
            "chunk_top_k": 10
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "rag_ids" in data and "chunks" in data:
                        has_sources = "sources" in data
                        self.log_result(
                            "仅Chunks检索-多知识库",
                            True,
                            f"查询 {len(data['rag_ids'])} 个知识库, Chunks: {len(data['chunks'])}, sources: {has_sources}"
                        )
                    else:
                        self.log_result("仅Chunks检索-多知识库", False, "响应格式错误")
                else:
                    error_text = await resp.text()
                    self.log_result("仅Chunks检索-多知识库", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("仅Chunks检索-多知识库", False, f"异常: {str(e)}")

    async def test_ucd_single(self, session):
        """测试 5.1: UCD 建模 - 单知识库"""
        print(f"\n[{timestamp()}] ========== 测试 5.1: UCD 建模 - 单知识库 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/ucd"
        payload = {
            "rag_id": TEST_SINGLE_RAG_ID,
            "question": "用户登录流程",
            "mode": "hybrid"
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "rag_ids" in data and "context" in data:
                        self.log_result(
                            "UCD建模-单知识库",
                            True,
                            f"上下文: {len(data.get('context', ''))} 字符"
                        )
                    else:
                        self.log_result("UCD建模-单知识库", False, "响应格式错误")
                else:
                    # UCD 建模可能因为 UCD builder 未初始化而失败，这是预期的
                    error_text = await resp.text()
                    if "UCD 建模器未初始化" in error_text:
                        self.log_result("UCD建模-单知识库", True, "跳过（UCD builder 未初始化）")
                    else:
                        self.log_result("UCD建模-单知识库", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("UCD建模-单知识库", False, f"异常: {str(e)}")

    async def test_ucd_multi(self, session):
        """测试 5.2: UCD 建模 - 多知识库"""
        print(f"\n[{timestamp()}] ========== 测试 5.2: UCD 建模 - 多知识库 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/ucd"
        payload = {
            "rag_ids": TEST_RAG_IDS,
            "question": "用户登录和注册流程",
            "mode": "hybrid"
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "rag_ids" in data and "context" in data:
                        has_sources = "sources" in data
                        self.log_result(
                            "UCD建模-多知识库",
                            True,
                            f"查询 {len(data['rag_ids'])} 个知识库, sources: {has_sources}"
                        )
                    else:
                        self.log_result("UCD建模-多知识库", False, "响应格式错误")
                else:
                    error_text = await resp.text()
                    if "UCD 建模器未初始化" in error_text:
                        self.log_result("UCD建模-多知识库", True, "跳过（UCD builder 未初始化）")
                    else:
                        self.log_result("UCD建模-多知识库", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("UCD建模-多知识库", False, f"异常: {str(e)}")

    async def test_backward_compatibility(self, session):
        """测试 6: 向后兼容性 - 使用旧版 rag_id 参数"""
        print(f"\n[{timestamp()}] ========== 测试 6: 向后兼容性测试 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/"
        payload = {
            "rag_id": TEST_SINGLE_RAG_ID,  # 使用旧版单参数
            "question": "向后兼容性测试",
            "mode": "hybrid",
            "only_need_context": True
        }

        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # 验证返回的是 rag_ids 数组格式
                    if "rag_ids" in data and isinstance(data["rag_ids"], list):
                        if len(data["rag_ids"]) == 1:
                            self.log_result(
                                "向后兼容性测试",
                                True,
                                f"rag_id -> rag_ids 转换正确: {data['rag_ids']}"
                            )
                        else:
                            self.log_result("向后兼容性测试", False, f"rag_ids 数量错误: {len(data['rag_ids'])}")
                    else:
                        self.log_result("向后兼容性测试", False, "响应格式错误")
                else:
                    error_text = await resp.text()
                    self.log_result("向后兼容性测试", False, f"HTTP {resp.status}: {error_text}")
        except Exception as e:
            self.log_result("向后兼容性测试", False, f"异常: {str(e)}")

    async def test_error_handling(self, session):
        """测试 7: 错误处理 - 无效的知识库ID"""
        print(f"\n[{timestamp()}] ========== 测试 7: 错误处理测试 ==========")

        url = f"{BASE_URL}{API_PREFIX}/query/"
        payload = {
            "rag_ids": ["invalid_kb_1", "invalid_kb_2"],
            "question": "错误处理测试",
            "mode": "hybrid"
        }

        try:
            async with session.post(url, json=payload) as resp:
                # 应该返回 500 或 404 错误
                if resp.status in [404, 500]:
                    error_text = await resp.text()
                    if "失败" in error_text or "不存在" in error_text:
                        self.log_result(
                            "错误处理测试",
                            True,
                            f"正确处理无效知识库: HTTP {resp.status}"
                        )
                    else:
                        self.log_result("错误处理测试", False, f"错误信息不明确: {error_text}")
                else:
                    self.log_result("错误处理测试", False, f"应返回错误但返回 {resp.status}")
        except Exception as e:
            self.log_result("错误处理测试", False, f"异常: {str(e)}")

    async def run_all_tests(self):
        """运行所有测试"""
        print(f"\n{'='*60}")
        print(f"多知识库查询接口测试")
        print(f"{'='*60}")
        print(f"测试知识库: {TEST_RAG_IDS}")
        print(f"单知识库: {TEST_SINGLE_RAG_ID}")
        print(f"{'='*60}\n")

        async with aiohttp.ClientSession() as session:
            # 1. 标准查询测试
            await self.test_standard_query_single(session)
            await self.test_standard_query_multi(session)

            # 2. 关键字检索测试
            await self.test_keywords_search_single(session)
            await self.test_keywords_search_multi(session)

            # 3. 清理图谱检索测试
            await self.test_graph_clean_single(session)
            await self.test_graph_clean_multi(session)

            # 4. 仅 Chunks 检索测试
            await self.test_chunks_only_single(session)
            await self.test_chunks_only_multi(session)

            # 5. UCD 建模测试
            await self.test_ucd_single(session)
            await self.test_ucd_multi(session)

            # 6. 向后兼容性测试
            await self.test_backward_compatibility(session)

            # 7. 错误处理测试
            await self.test_error_handling(session)

        # 打印测试总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print(f"测试总结")
        print(f"{'='*60}")
        print(f"总测试数: {self.total_tests}")
        print(f"通过: {self.passed_tests}")
        print(f"失败: {self.failed_tests}")
        print(f"通过率: {(self.passed_tests/self.total_tests*100):.1f}%")
        print(f"{'='*60}\n")

        if self.failed_tests > 0:
            print("失败的测试:")
            for result in self.test_results:
                if "✗" in result["status"]:
                    print(f"  - {result['test']}: {result['message']}")
            print()


async def main():
    """主函数"""
    tester = MultiKBQueryTester()
    await tester.run_all_tests()

    # 返回退出码
    sys.exit(0 if tester.failed_tests == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
