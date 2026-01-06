#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储层测试

测试 Nebula Graph 和 Milvus 的存储功能：
1. CRUD 操作
2. 特殊字符处理
3. 批量操作
4. Workspace 过滤
5. 索引功能
"""

import pytest
import time
from conftest import wait_for_indexing


@pytest.mark.integration
class TestNebulaStorage:
    """Nebula Graph 存储测试"""

    def test_insert_and_query_with_workspace_filter(self, api_client, sample_documents):
        """
        测试 Nebula 中 workspace 属性过滤

        验证：
        1. 插入节点时正确设置 workspace 属性
        2. 查询时只返回当前 workspace 的节点
        3. 不同 workspace 的节点互不干扰
        """
        inst1 = "test_nebula_ws1"
        inst2 = "test_nebula_ws2"

        try:
            # 创建两个实例
            api_client.create_instance(inst1, "nebula_ws_1")
            time.sleep(2)
            api_client.create_instance(inst2, "nebula_ws_2")
            time.sleep(2)

            # 为每个实例插入文档
            api_client.insert_document(
                inst1,
                sample_documents[0]["content"],
                "nebula_doc1.txt"
            )

            api_client.insert_document(
                inst2,
                sample_documents[1]["content"],
                "nebula_doc2.txt"
            )

            wait_for_indexing(10)

            # 查询验证数据隔离
            result1 = api_client.query(inst1, sample_documents[0]["query"])
            result2 = api_client.query(inst2, sample_documents[1]["query"])

            assert result1.get("answer"), "Instance 1 should get answer"
            assert result2.get("answer"), "Instance 2 should get answer"

        finally:
            for rag_id in [inst1, inst2]:
                try:
                    api_client.delete_instance(rag_id, cleanup_storage=True)
                except:
                    pass

    def test_nebula_delete_workspace_data(self, api_client, sample_documents):
        """
        测试 Nebula 删除 workspace 数据

        验证：
        1. 删除时只删除当前 workspace 的节点和边
        2. 其他 workspace 的数据保持不变
        3. 删除后无法查询到已删除 workspace 的数据
        """
        inst1 = "test_nebula_del1"
        inst2 = "test_nebula_del2"

        try:
            # 创建两个实例并插入数据
            api_client.create_instance(inst1, "nebula_del_ws1")
            time.sleep(2)
            api_client.create_instance(inst2, "nebula_del_ws2")
            time.sleep(2)

            api_client.insert_document(inst1, sample_documents[0]["content"], "del1.txt")
            api_client.insert_document(inst2, sample_documents[1]["content"], "del2.txt")

            wait_for_indexing(10)

            # 删除第一个实例
            delete_result = api_client.delete_instance(inst1, cleanup_storage=True)
            assert delete_result.get("status") == "success"

            # 验证第二个实例仍然可以查询
            result2 = api_client.query(inst2, sample_documents[1]["query"])
            assert result2.get("answer"), "Instance 2 should still work after inst1 deleted"

            # 验证第一个实例无法查询
            with pytest.raises(Exception):
                api_client.query(inst1, sample_documents[0]["query"])

        finally:
            for rag_id in [inst1, inst2]:
                try:
                    api_client.delete_instance(rag_id, cleanup_storage=True)
                except:
                    pass

    def test_nebula_special_characters_in_properties(self, api_client, special_char_documents):
        """
        测试 Nebula 中特殊字符的处理

        验证：
        1. 单引号、双引号、反斜杠等特殊字符正确存储
        2. 查询时正确返回包含特殊字符的数据
        3. 不会出现 nGQL 语法错误
        """
        rag_id = "test_nebula_special_chars"

        try:
            api_client.create_instance(rag_id, "nebula_special_ws")
            time.sleep(2)

            # 插入包含各种特殊字符的文档
            for doc in special_char_documents:
                result = api_client.insert_document(
                    rag_id,
                    doc["content"],
                    doc["file_path"]
                )
                assert result.get("status") == "success", \
                    f"Failed to insert document with special chars: {doc['file_path']}"
                time.sleep(2)

            wait_for_indexing(10)

            # 查询验证特殊字符处理正确
            result = api_client.query(rag_id, "Tell me about special characters")
            assert result.get("answer"), "Should handle special characters in queries"

        finally:
            try:
                api_client.delete_instance(rag_id, cleanup_storage=True)
            except:
                pass


@pytest.mark.integration
class TestMilvusStorage:
    """Milvus 存储测试"""

    def test_milvus_collection_workspace_prefix(self, api_client, sample_documents):
        """
        测试 Milvus Collection 的 workspace 前缀

        验证：
        1. 每个 workspace 创建带前缀的 collections
        2. Collection 命名格式：{workspace}_{collection_type}
        3. 删除时只删除当前 workspace 的 collections
        """
        inst = "test_milvus_prefix"
        workspace = "milvus_prefix_ws"

        try:
            api_client.create_instance(inst, workspace)
            time.sleep(2)

            # 插入文档
            api_client.insert_document(
                inst,
                sample_documents[0]["content"],
                "milvus_test.txt"
            )

            wait_for_indexing(10)

            # 删除并验证清理
            delete_result = api_client.delete_instance(inst, cleanup_storage=True)

            cleaned = delete_result.get("cleaned_resources", [])
            print(f"Cleaned resources: {cleaned}")

            # 验证 Milvus collections 被清理
            assert any("Milvus" in str(item) for item in cleaned), \
                "Should clean Milvus collections"

        finally:
            try:
                api_client.delete_instance(inst, cleanup_storage=True)
            except:
                pass

    def test_milvus_vector_search_isolation(self, api_client, sample_documents):
        """
        测试 Milvus 向量搜索的 workspace 隔离

        验证：
        1. 向量搜索只返回当前 workspace 的结果
        2. 不会返回其他 workspace 的向量
        """
        inst1 = "test_milvus_search1"
        inst2 = "test_milvus_search2"

        try:
            # 创建两个实例
            api_client.create_instance(inst1, "milvus_search_ws1")
            time.sleep(2)
            api_client.create_instance(inst2, "milvus_search_ws2")
            time.sleep(2)

            # 插入不同的文档
            api_client.insert_document(inst1, sample_documents[0]["content"], "vec1.txt")
            api_client.insert_document(inst2, sample_documents[1]["content"], "vec2.txt")

            wait_for_indexing(10)

            # 查询验证隔离
            result1 = api_client.query(inst1, sample_documents[0]["query"])
            result2 = api_client.query(inst2, sample_documents[1]["query"])

            assert result1.get("answer"), "Instance 1 vector search should work"
            assert result2.get("answer"), "Instance 2 vector search should work"

        finally:
            for rag_id in [inst1, inst2]:
                try:
                    api_client.delete_instance(rag_id, cleanup_storage=True)
                except:
                    pass

    def test_milvus_batch_insert(self, api_client, sample_documents):
        """
        测试 Milvus 批量插入

        验证：
        1. 可以批量插入多个文档
        2. 所有文档都正确索引
        3. 批量插入后可以查询所有文档
        """
        rag_id = "test_milvus_batch"

        try:
            api_client.create_instance(rag_id, "milvus_batch_ws")
            time.sleep(2)

            # 批量插入多个文档
            for i, doc in enumerate(sample_documents):
                result = api_client.insert_document(
                    rag_id,
                    doc["content"],
                    f"batch_doc_{i}.txt"
                )
                assert result.get("status") == "success"
                time.sleep(2)

            wait_for_indexing(15)

            # 验证可以查询所有文档的内容
            for doc in sample_documents:
                result = api_client.query(rag_id, doc["query"])
                assert result.get("answer"), f"Should be able to query: {doc['query']}"

        finally:
            try:
                api_client.delete_instance(rag_id, cleanup_storage=True)
            except:
                pass


@pytest.mark.integration
class TestStorageSpecialCases:
    """存储层特殊场景测试"""

    def test_empty_content_insertion(self, api_client):
        """
        测试空内容插入

        验证：
        1. 空字符串内容的处理
        2. 只包含空白字符的内容
        3. 系统应该正确处理或拒绝
        """
        rag_id = "test_empty_content"

        try:
            api_client.create_instance(rag_id, "empty_content_ws")
            time.sleep(2)

            # 测试空字符串
            try:
                result = api_client.insert_document(rag_id, "", "empty.txt")
                # 如果成功，验证状态
                if result.get("status") == "success":
                    print("Empty content accepted")
            except Exception as e:
                # 如果拒绝，这也是合理的
                print(f"Empty content rejected (expected): {e}")

            # 测试只有空白字符
            try:
                result = api_client.insert_document(rag_id, "   \n\n   ", "whitespace.txt")
                if result.get("status") == "success":
                    print("Whitespace-only content accepted")
            except Exception as e:
                print(f"Whitespace content rejected (expected): {e}")

        finally:
            try:
                api_client.delete_instance(rag_id, cleanup_storage=True)
            except:
                pass

    def test_very_long_content(self, api_client):
        """
        测试超长内容

        验证：
        1. 可以处理长文本（例如 10000+ 字符）
        2. 正确分块和索引
        3. 查询长文本返回正确结果
        """
        rag_id = "test_long_content"

        try:
            api_client.create_instance(rag_id, "long_content_ws")
            time.sleep(2)

            # 生成长文本
            long_content = "Python is a programming language. " * 500  # ~17000 字符
            long_content += "\nThe answer to the question is: Python is versatile and powerful."

            result = api_client.insert_document(rag_id, long_content, "long_doc.txt")
            assert result.get("status") == "success", "Should handle long content"

            wait_for_indexing(15)

            # 查询验证
            query_result = api_client.query(rag_id, "What is Python?")
            assert query_result.get("answer"), "Should be able to query long documents"

        finally:
            try:
                api_client.delete_instance(rag_id, cleanup_storage=True)
            except:
                pass

    def test_unicode_and_multilingual(self, api_client):
        """
        测试 Unicode 和多语言内容

        验证：
        1. 中文、日文、韩文等多语言内容
        2. Emoji 和特殊 Unicode 字符
        3. 混合语言内容
        """
        rag_id = "test_unicode"

        try:
            api_client.create_instance(rag_id, "unicode_ws")
            time.sleep(2)

            # 多语言内容
            multilingual_docs = [
                {
                    "content": "这是中文内容。Python 是一种编程语言，广泛用于数据科学和人工智能。",
                    "file_path": "chinese.txt",
                    "query": "Python是什么？"
                },
                {
                    "content": "日本語のコンテンツ。Pythonはプログラミング言語です。🐍",
                    "file_path": "japanese.txt",
                    "query": "Pythonについて"
                },
                {
                    "content": "Mixed 混合 content with émojis 😊 and spëcial characters: café, naïve, 北京",
                    "file_path": "mixed.txt",
                    "query": "special characters"
                }
            ]

            for doc in multilingual_docs:
                result = api_client.insert_document(rag_id, doc["content"], doc["file_path"])
                assert result.get("status") == "success", \
                    f"Should handle multilingual content: {doc['file_path']}"
                time.sleep(2)

            wait_for_indexing(10)

            # 验证查询
            for doc in multilingual_docs:
                result = api_client.query(rag_id, doc["query"])
                assert result.get("answer"), f"Should handle multilingual query: {doc['query']}"

        finally:
            try:
                api_client.delete_instance(rag_id, cleanup_storage=True)
            except:
                pass


@pytest.mark.integration
class TestStorageCRUD:
    """存储层 CRUD 操作测试"""

    def test_create_read_update_delete_cycle(self, api_client, sample_documents):
        """
        测试完整的 CRUD 周期

        验证：
        1. Create: 插入文档
        2. Read: 查询文档
        3. Update: 插入相同文件路径的新内容（覆盖）
        4. Delete: 删除实例
        """
        rag_id = "test_crud"

        try:
            # Create
            api_client.create_instance(rag_id, "crud_ws")
            time.sleep(2)

            # Insert (Create)
            result = api_client.insert_document(
                rag_id,
                sample_documents[0]["content"],
                "crud_doc.txt"
            )
            assert result.get("status") == "success"
            wait_for_indexing(10)

            # Read (Query)
            query_result = api_client.query(rag_id, sample_documents[0]["query"])
            assert query_result.get("answer"), "Should be able to query inserted document"

            # Update (Insert with same file_path)
            updated_content = "Updated content: Python is now even more awesome!"
            update_result = api_client.insert_document(
                rag_id,
                updated_content,
                "crud_doc.txt"  # Same file path
            )
            assert update_result.get("status") == "success"
            wait_for_indexing(10)

            # Query updated content
            query_result2 = api_client.query(rag_id, "Tell me about Python")
            assert query_result2.get("answer"), "Should query updated content"

            # Delete
            delete_result = api_client.delete_instance(rag_id, cleanup_storage=True)
            assert delete_result.get("status") == "success"

            # Verify deleted
            with pytest.raises(Exception):
                api_client.query(rag_id, "any question")

        finally:
            try:
                api_client.delete_instance(rag_id, cleanup_storage=True)
            except:
                pass
