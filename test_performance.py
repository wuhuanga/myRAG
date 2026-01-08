#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试性能统计脚本

统计各个操作的耗时：
- 创建实例
- 插入文档
- 查询
- 删除实例
"""

import time
import sys
import requests
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class PerformanceTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.stats = {
            "create_instance": [],
            "insert_document": [],
            "query": [],
            "delete_instance": []
        }

    def test_create_instance(self, rag_id, workspace):
        """测试创建实例"""
        payload = {
            "rag_id": rag_id,
            "workspace": workspace,
            "working_dir": f"./perf_test_{workspace}",
            "description": f"Performance test {rag_id}",
        }

        start = time.time()
        resp = self.session.post(
            f"{self.base_url}/api/admin/rag_instances/create",
            json=payload,
            timeout=180
        )
        duration = time.time() - start

        resp.raise_for_status()
        self.stats["create_instance"].append(duration)
        return duration

    def test_insert_document(self, rag_id, content, file_path):
        """测试插入文档"""
        payload = {
            "rag_id": rag_id,
            "content": content,
            "file_path": file_path,
        }

        start = time.time()
        resp = self.session.post(
            f"{self.base_url}/api/documents/insert",
            json=payload,
            timeout=120
        )
        duration = time.time() - start

        resp.raise_for_status()
        self.stats["insert_document"].append(duration)
        return duration

    def test_query(self, rag_id, question):
        """测试查询"""
        payload = {
            "rag_id": rag_id,
            "question": question,
            "mode": "hybrid",
            "only_need_context": True,
        }

        start = time.time()
        resp = self.session.post(
            f"{self.base_url}/api/query/",
            json=payload,
            timeout=60
        )
        duration = time.time() - start

        resp.raise_for_status()
        self.stats["query"].append(duration)
        return duration

    def test_delete_instance(self, rag_id):
        """测试删除实例"""
        start = time.time()
        resp = self.session.delete(
            f"{self.base_url}/api/admin/rag_instances/{rag_id}/complete",
            params={"cleanup_storage": True},
            timeout=120
        )
        duration = time.time() - start

        resp.raise_for_status()
        self.stats["delete_instance"].append(duration)
        return duration

    def print_stats(self):
        """打印统计信息"""
        print("\n" + "=" * 80)
        print("性能测试统计结果")
        print("=" * 80)

        for op_name, times in self.stats.items():
            if not times:
                continue

            op_display = {
                "create_instance": "创建实例",
                "insert_document": "插入文档",
                "query": "查询",
                "delete_instance": "删除实例"
            }

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            total_time = sum(times)

            print(f"\n【{op_display.get(op_name, op_name)}】")
            print(f"  执行次数: {len(times)}")
            print(f"  总耗时:   {total_time:.2f} 秒")
            print(f"  平均耗时: {avg_time:.2f} 秒")
            print(f"  最快:     {min_time:.2f} 秒")
            print(f"  最慢:     {max_time:.2f} 秒")

        print("\n" + "=" * 80)


def main():
    print("=" * 80)
    print("RAG 系统性能测试")
    print("=" * 80)
    print()

    # 检查服务器
    print("检查 FastAPI 服务器...", end=" ")
    try:
        resp = requests.get("http://localhost:8000/docs", timeout=5)
        print("✓")
    except:
        print("✗")
        print("\n错误：FastAPI 服务器未运行")
        print("请先启动: python -m xwrag.api.xwrag_server")
        return 1

    print()

    tester = PerformanceTester()

    # 测试参数
    num_instances = 3
    docs_per_instance = 3
    queries_per_instance = 5

    print(f"测试配置:")
    print(f"  - 实例数: {num_instances}")
    print(f"  - 每实例文档数: {docs_per_instance}")
    print(f"  - 每实例查询数: {queries_per_instance}")
    print()

    created_instances = []

    try:
        # 1. 测试创建实例
        print("=" * 80)
        print("阶段 1: 创建实例")
        print("=" * 80)
        for i in range(num_instances):
            rag_id = f"perf_test_{i}"
            workspace = f"perf_ws_{i}"

            print(f"[{i+1}/{num_instances}] 创建 {rag_id}...", end=" ")
            try:
                duration = tester.test_create_instance(rag_id, workspace)
                created_instances.append(rag_id)
                print(f"✓ ({duration:.2f}s)")
            except Exception as e:
                print(f"✗ ({e})")

            time.sleep(1)

        print()

        # 2. 测试插入文档
        print("=" * 80)
        print("阶段 2: 插入文档")
        print("=" * 80)

        test_contents = [
            "Python 是一种高级编程语言，广泛应用于 Web 开发、数据科学、人工智能等领域。",
            "机器学习是人工智能的一个分支，通过数据和算法让计算机自主学习。",
            "RAG (Retrieval-Augmented Generation) 结合了检索和生成技术，提高了 LLM 的准确性。",
        ]

        for i, rag_id in enumerate(created_instances):
            print(f"\n实例 {rag_id}:")
            for j in range(docs_per_instance):
                content = test_contents[j % len(test_contents)]
                file_path = f"perf_doc_{i}_{j}.txt"

                print(f"  [{j+1}/{docs_per_instance}] 插入文档...", end=" ")
                try:
                    duration = tester.test_insert_document(rag_id, content, file_path)
                    print(f"✓ ({duration:.2f}s)")
                except Exception as e:
                    print(f"✗ ({e})")

                time.sleep(0.5)

        # 等待索引
        print("\n等待索引完成...", end=" ")
        time.sleep(10)
        print("✓")
        print()

        # 3. 测试查询
        print("=" * 80)
        print("阶段 3: 查询")
        print("=" * 80)

        test_queries = [
            "Python 有什么用途？",
            "什么是机器学习？",
            "RAG 技术的特点是什么？",
            "如何使用人工智能？",
            "编程语言的应用场景",
        ]

        for i, rag_id in enumerate(created_instances):
            print(f"\n实例 {rag_id}:")
            for j in range(queries_per_instance):
                question = test_queries[j % len(test_queries)]

                print(f"  [{j+1}/{queries_per_instance}] 查询: {question[:20]}...", end=" ")
                try:
                    duration = tester.test_query(rag_id, question)
                    print(f"✓ ({duration:.2f}s)")
                except Exception as e:
                    print(f"✗ ({e})")

                time.sleep(0.3)

        print()

    finally:
        # 4. 清理
        print("=" * 80)
        print("阶段 4: 清理")
        print("=" * 80)
        for i, rag_id in enumerate(created_instances):
            print(f"[{i+1}/{len(created_instances)}] 删除 {rag_id}...", end=" ")
            try:
                duration = tester.test_delete_instance(rag_id)
                print(f"✓ ({duration:.2f}s)")
            except Exception as e:
                print(f"✗ ({e})")

            time.sleep(0.5)

    # 打印统计
    tester.print_stats()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
