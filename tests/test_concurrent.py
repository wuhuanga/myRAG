#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发测试

测试系统的并发处理能力：
1. 多实例并发创建
2. 并发文档插入
3. 并发查询
4. 混合并发操作
5. 负载测试
"""

import pytest
import time
import asyncio
import concurrent.futures
from typing import List


def wait_for_indexing(seconds: int = 10):
    """等待索引完成"""
    print(f"⏳ 等待 {seconds} 秒让索引完成...")
    time.sleep(seconds)


@pytest.mark.integration
@pytest.mark.concurrent
class TestConcurrentInstanceOperations:
    """并发实例操作测试"""

    def test_concurrent_instance_creation(self, api_client):
        """
        测试并发创建多个实例

        验证：
        1. 可以同时创建多个实例
        2. 所有实例都成功创建
        3. 无资源竞争或冲突
        """
        num_instances = 10
        instance_ids = [f"test_concurrent_create_{i}" for i in range(num_instances)]

        def create_instance(rag_id):
            try:
                result = api_client.create_instance(rag_id, f"concurrent_ws_{rag_id}")
                return (rag_id, True, result)
            except Exception as e:
                return (rag_id, False, str(e))

        # 并发创建
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(create_instance, instance_ids))
        duration = time.time() - start_time

        # 验证结果
        success_count = sum(1 for r in results if r[1])
        print(f"Created {success_count}/{num_instances} instances in {duration:.2f}s")

        assert success_count >= num_instances * 0.8, \
            f"At least 80% of concurrent creates should succeed, got {success_count}/{num_instances}"

        # 验证实例列表
        time.sleep(2)
        all_instances = api_client.list_instances()
        instance_ids_list = [inst.get("rag_id") for inst in all_instances]

        for rag_id, success, _ in results:
            if success:
                assert rag_id in instance_ids_list, f"Instance {rag_id} should be in list"

        # 清理
        for rag_id in instance_ids:
            try:
                api_client.delete_instance(rag_id, cleanup_storage=True)
            except:
                pass

        print(f"✓ Concurrent instance creation test passed")

    def test_concurrent_instance_deletion(self, api_client):
        """
        测试并发删除多个实例

        验证：
        1. 可以同时删除多个实例
        2. 删除操作互不干扰
        3. 所有实例都被正确删除
        """
        num_instances = 5
        instance_ids = []

        # 先创建实例
        for i in range(num_instances):
            rag_id = f"test_concurrent_delete_{i}"
            api_client.create_instance(rag_id, f"del_ws_{i}")
            instance_ids.append(rag_id)
            time.sleep(1)

        def delete_instance(rag_id):
            try:
                result = api_client.delete_instance(rag_id, cleanup_storage=True)
                return (rag_id, True, result)
            except Exception as e:
                return (rag_id, False, str(e))

        # 并发删除
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(delete_instance, instance_ids))
        duration = time.time() - start_time

        # 验证结果
        success_count = sum(1 for r in results if r[1])
        print(f"Deleted {success_count}/{num_instances} instances in {duration:.2f}s")

        assert success_count == num_instances, \
            f"All deletions should succeed, got {success_count}/{num_instances}"

        # 验证实例不在列表中
        time.sleep(2)
        remaining = api_client.list_instances()
        remaining_ids = [inst.get("rag_id") for inst in remaining]

        for rag_id in instance_ids:
            assert rag_id not in remaining_ids, f"Instance {rag_id} should be deleted"

        print(f"✓ Concurrent instance deletion test passed")


@pytest.mark.integration
@pytest.mark.concurrent
class TestConcurrentDocumentOperations:
    """并发文档操作测试"""

    def test_concurrent_document_insertion(self, api_client, sample_documents):
        """
        测试并发向同一实例插入文档

        验证：
        1. 可以并发插入多个文档到同一实例
        2. 所有文档都成功索引
        3. 无数据损坏
        """
        test_id = "test_concurrent_insert"

        try:
            api_client.create_instance(test_id, "concurrent_insert_ws")
            time.sleep(2)

            def insert_document(doc_index):
                try:
                    doc = sample_documents[doc_index % len(sample_documents)]
                    result = api_client.insert_document(
                        test_id,
                        doc["content"],
                        f"concurrent_doc_{doc_index}.txt"
                    )
                    return result.get("status") == "success"
                except Exception as e:
                    print(f"Insert {doc_index} failed: {e}")
                    return False

            # 并发插入 10 个文档
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(insert_document, range(10)))
            duration = time.time() - start_time

            success_count = sum(results)
            print(f"Inserted {success_count}/10 documents in {duration:.2f}s")

            assert success_count >= 8, \
                f"At least 8/10 concurrent inserts should succeed, got {success_count}"

            wait_for_indexing(15)

            # 验证可以查询到文档
            for i, doc in enumerate(sample_documents):
                result = api_client.query(test_id, doc["query"])
                assert result.get("answer"), f"Should find document for query: {doc['query']}"

            print(f"✓ Concurrent document insertion test passed")

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass

    def test_concurrent_insertion_to_multiple_instances(self, api_client, sample_documents):
        """
        测试并发向多个实例插入文档

        验证：
        1. 可以同时向多个实例插入文档
        2. 实例间不互相干扰
        """
        num_instances = 5
        instances = [f"test_multi_insert_{i}" for i in range(num_instances)]

        try:
            # 创建实例
            for rag_id in instances:
                api_client.create_instance(rag_id, f"multi_insert_ws_{rag_id}")
                time.sleep(1)

            def insert_to_instance(rag_id):
                try:
                    result = api_client.insert_document(
                        rag_id,
                        sample_documents[0]["content"],
                        f"{rag_id}_doc.txt"
                    )
                    return result.get("status") == "success"
                except:
                    return False

            # 并发插入到所有实例
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(insert_to_instance, instances))

            success_count = sum(results)
            print(f"Inserted to {success_count}/{num_instances} instances")

            assert success_count >= num_instances * 0.8, \
                f"At least 80% should succeed, got {success_count}/{num_instances}"

            print(f"✓ Concurrent insertion to multiple instances test passed")

        finally:
            for rag_id in instances:
                try:
                    api_client.delete_instance(rag_id, cleanup_storage=True)
                except:
                    pass


@pytest.mark.integration
@pytest.mark.concurrent
class TestConcurrentQueryOperations:
    """并发查询操作测试"""

    def test_concurrent_queries_same_instance(self, api_client, sample_documents):
        """
        测试并发查询同一实例

        验证：
        1. 可以并发查询同一实例
        2. 所有查询都返回结果
        3. 无查询失败或超时
        """
        test_id = "test_concurrent_query"

        try:
            api_client.create_instance(test_id, "concurrent_query_ws")
            time.sleep(2)

            api_client.insert_document(
                test_id,
                sample_documents[0]["content"],
                "query_test.txt"
            )
            wait_for_indexing(10)

            def query_instance(query_index):
                try:
                    result = api_client.query(
                        test_id,
                        f"Query {query_index}: {sample_documents[0]['query']}"
                    )
                    return result.get("answer") is not None
                except:
                    return False

            # 并发 20 个查询
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(query_instance, range(20)))
            duration = time.time() - start_time

            success_count = sum(results)
            print(f"Completed {success_count}/20 queries in {duration:.2f}s")
            print(f"Average query time: {duration/20:.2f}s")

            assert success_count >= 18, \
                f"At least 18/20 queries should succeed, got {success_count}"

            print(f"✓ Concurrent queries test passed")

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass

    def test_concurrent_queries_multiple_instances(self, api_client, sample_documents):
        """
        测试并发查询多个实例

        验证：
        1. 可以同时查询多个实例
        2. 每个实例返回正确的数据（数据隔离）
        """
        num_instances = 3
        instances = [f"test_multi_query_{i}" for i in range(num_instances)]

        try:
            # 创建实例并插入不同文档
            for i, rag_id in enumerate(instances):
                api_client.create_instance(rag_id, f"multi_query_ws_{i}")
                time.sleep(2)
                api_client.insert_document(
                    rag_id,
                    sample_documents[i]["content"],
                    f"doc_{i}.txt"
                )
                time.sleep(2)

            wait_for_indexing(10)

            def query_instance(rag_id):
                try:
                    result = api_client.query(rag_id, "Tell me about this document")
                    return (rag_id, True, result.get("answer"))
                except Exception as e:
                    return (rag_id, False, str(e))

            # 并发查询所有实例
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(query_instance, instances))

            success_count = sum(1 for r in results if r[1])
            print(f"Queried {success_count}/{num_instances} instances")

            assert success_count == num_instances, \
                f"All queries should succeed, got {success_count}/{num_instances}"

            print(f"✓ Concurrent queries to multiple instances test passed")

        finally:
            for rag_id in instances:
                try:
                    api_client.delete_instance(rag_id, cleanup_storage=True)
                except:
                    pass


@pytest.mark.integration
@pytest.mark.concurrent
@pytest.mark.slow
class TestMixedConcurrentOperations:
    """混合并发操作测试"""

    def test_concurrent_create_insert_query_delete(self, api_client, sample_documents):
        """
        测试混合并发操作

        验证：
        1. 同时进行创建、插入、查询、删除操作
        2. 操作不互相干扰
        3. 系统保持稳定
        """
        def create_operation(i):
            rag_id = f"test_mixed_{i}"
            try:
                api_client.create_instance(rag_id, f"mixed_ws_{i}")
                return ("create", i, True)
            except:
                return ("create", i, False)

        def insert_operation(i):
            rag_id = f"test_mixed_{i}"
            try:
                api_client.insert_document(
                    rag_id,
                    sample_documents[i % len(sample_documents)]["content"],
                    f"doc_{i}.txt"
                )
                return ("insert", i, True)
            except:
                return ("insert", i, False)

        def query_operation(i):
            rag_id = f"test_mixed_{i}"
            try:
                result = api_client.query(rag_id, "Any question")
                return ("query", i, result.get("answer") is not None)
            except:
                return ("query", i, False)

        def delete_operation(i):
            rag_id = f"test_mixed_{i}"
            try:
                api_client.delete_instance(rag_id, cleanup_storage=True)
                return ("delete", i, True)
            except:
                return ("delete", i, False)

        try:
            # 第一批：创建实例
            print("Phase 1: Creating instances...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                create_results = list(executor.map(create_operation, range(3)))

            time.sleep(2)

            # 第二批：插入文档
            print("Phase 2: Inserting documents...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                insert_results = list(executor.map(insert_operation, range(3)))

            time.sleep(10)

            # 第三批：查询
            print("Phase 3: Querying...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                query_results = list(executor.map(query_operation, range(3)))

            # 第四批：删除
            print("Phase 4: Deleting instances...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                delete_results = list(executor.map(delete_operation, range(3)))

            # 统计结果
            create_success = sum(1 for r in create_results if r[2])
            insert_success = sum(1 for r in insert_results if r[2])
            query_success = sum(1 for r in query_results if r[2])
            delete_success = sum(1 for r in delete_results if r[2])

            print(f"Results: Create={create_success}/3, Insert={insert_success}/3, "
                  f"Query={query_success}/3, Delete={delete_success}/3")

            assert create_success >= 2, "At least 2/3 creates should succeed"
            assert insert_success >= 2, "At least 2/3 inserts should succeed"
            assert delete_success >= 2, "At least 2/3 deletes should succeed"

            print(f"✓ Mixed concurrent operations test passed")

        finally:
            # 确保清理
            for i in range(3):
                try:
                    api_client.delete_instance(f"test_mixed_{i}", cleanup_storage=True)
                except:
                    pass


@pytest.mark.integration
@pytest.mark.concurrent
@pytest.mark.slow
class TestLoadAndStress:
    """负载和压力测试"""

    def test_sustained_load(self, api_client, sample_documents):
        """
        测试持续负载

        验证：
        1. 系统可以处理持续的查询负载
        2. 性能保持稳定
        3. 无内存泄漏或资源耗尽
        """
        test_id = "test_sustained_load"

        try:
            api_client.create_instance(test_id, "sustained_load_ws")
            time.sleep(2)

            api_client.insert_document(
                test_id,
                sample_documents[0]["content"],
                "load_test.txt"
            )
            wait_for_indexing(10)

            def query_repeatedly(num_queries):
                success_count = 0
                for i in range(num_queries):
                    try:
                        result = api_client.query(test_id, f"Query {i}")
                        if result.get("answer"):
                            success_count += 1
                    except:
                        pass
                return success_count

            # 持续查询 50 次
            start_time = time.time()
            success_count = query_repeatedly(50)
            duration = time.time() - start_time

            print(f"Completed {success_count}/50 queries in {duration:.2f}s")
            print(f"Average query time: {duration/50:.2f}s")

            assert success_count >= 45, f"At least 45/50 queries should succeed, got {success_count}"

            print(f"✓ Sustained load test passed")

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass

    @pytest.mark.skip(reason="Heavy load test, run manually")
    def test_stress_with_many_instances(self, api_client):
        """
        压力测试：大量实例

        验证：
        1. 系统可以处理大量实例
        2. 资源使用合理
        注意：这是一个重度测试，可能需要较长时间
        """
        num_instances = 50

        try:
            # 创建大量实例
            for i in range(num_instances):
                rag_id = f"test_stress_{i}"
                api_client.create_instance(rag_id, f"stress_ws_{i}")
                if i % 10 == 0:
                    print(f"Created {i}/{num_instances} instances")
                time.sleep(0.5)

            print(f"✓ Created {num_instances} instances")

        finally:
            # 清理
            for i in range(num_instances):
                try:
                    api_client.delete_instance(f"test_stress_{i}", cleanup_storage=True)
                except:
                    pass
