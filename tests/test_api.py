#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 端点测试

测试所有 FastAPI 端点的功能：
1. Admin 端点（创建、列表、删除实例）
2. Documents 端点（插入文档）
3. Query 端点（查询知识库）
4. 响应格式验证
5. 错误处理
"""

import pytest
import requests
import time
from conftest import wait_for_indexing, assert_response_structure


@pytest.mark.integration
class TestAdminEndpoints:
    """Admin API 端点测试"""

    def test_create_instance_endpoint(self, base_url):
        """
        测试创建实例端点

        验证：
        1. POST /api/admin/rag_instances/create 返回 200
        2. 响应包含必需字段
        3. 创建后实例可以被列出
        """
        payload = {
            "rag_id": "test_api_create",
            "workspace": "test_api_ws",
            "working_dir": "/tmp/test_api",
            "description": "API test instance"
        }

        try:
            # 创建实例
            resp = requests.post(
                f"{base_url}/api/admin/rag_instances/create",
                json=payload,
                timeout=60
            )

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

            data = resp.json()
            assert_response_structure(data, ["message", "rag_id"])
            assert data.get("rag_id") == "test_api_create"

            time.sleep(2)

            # 验证实例在列表中
            list_resp = requests.get(f"{base_url}/api/admin/rag_instances/list", timeout=10)
            assert list_resp.status_code == 200

            instances = list_resp.json()
            instance_ids = [inst.get("rag_id") for inst in instances]
            assert "test_api_create" in instance_ids

        finally:
            # 清理
            requests.delete(
                f"{base_url}/api/admin/rag_instances/test_api_create/complete?cleanup_storage=true",
                timeout=120
            )

    def test_list_instances_endpoint(self, base_url, api_client):
        """
        测试列出实例端点

        验证：
        1. GET /api/admin/rag_instances/list 返回 200
        2. 返回数组格式
        3. 每个实例包含必需字段
        """
        # 创建测试实例
        test_id = "test_api_list"
        try:
            api_client.create_instance(test_id, "test_list_ws")
            time.sleep(2)

            # 列出实例
            resp = requests.get(f"{base_url}/api/admin/rag_instances/list", timeout=10)

            assert resp.status_code == 200
            instances = resp.json()
            assert isinstance(instances, list), "Response should be a list"

            # 验证结构
            if len(instances) > 0:
                instance = instances[0]
                assert "rag_id" in instance
                assert "workspace" in instance

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass

    def test_delete_instance_endpoint(self, base_url, api_client):
        """
        测试删除实例端点

        验证：
        1. DELETE /api/admin/rag_instances/{rag_id}/complete 返回 200
        2. 响应包含清理信息
        3. 删除后实例不在列表中
        """
        test_id = "test_api_delete"

        try:
            # 创建实例
            api_client.create_instance(test_id, "test_delete_ws")
            time.sleep(2)

            # 删除实例
            resp = requests.delete(
                f"{base_url}/api/admin/rag_instances/{test_id}/complete",
                params={"cleanup_storage": True},
                timeout=120
            )

            assert resp.status_code == 200
            data = resp.json()

            assert_response_structure(data, ["status", "message", "cleaned_resources"])
            assert data.get("status") in ["success", "partial"]

            # 验证实例不在列表中
            list_resp = requests.get(f"{base_url}/api/admin/rag_instances/list", timeout=10)
            instances = list_resp.json()
            instance_ids = [inst.get("rag_id") for inst in instances]
            assert test_id not in instance_ids

        except:
            # 确保清理
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass

    def test_delete_nonexistent_instance(self, base_url):
        """
        测试删除不存在的实例

        验证：
        1. 返回 404 或适当的错误状态码
        2. 错误消息清晰
        """
        resp = requests.delete(
            f"{base_url}/api/admin/rag_instances/nonexistent_instance/complete",
            params={"cleanup_storage": True},
            timeout=30
        )

        assert resp.status_code in [404, 400], \
            f"Should return 404 or 400 for nonexistent instance, got {resp.status_code}"


@pytest.mark.integration
class TestDocumentsEndpoints:
    """Documents API 端点测试"""

    def test_insert_document_endpoint(self, base_url, api_client, sample_documents):
        """
        测试插入文档端点

        验证：
        1. POST /api/documents/insert 返回 200
        2. 响应包含插入状态
        3. 文档可以被查询到
        """
        test_id = "test_api_insert"

        try:
            api_client.create_instance(test_id, "test_insert_ws")
            time.sleep(2)

            # 插入文档
            payload = {
                "rag_id": test_id,
                "content": sample_documents[0]["content"],
                "file_path": "api_test.txt"
            }

            resp = requests.post(
                f"{base_url}/api/documents/insert",
                json=payload,
                timeout=120
            )

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

            data = resp.json()
            assert_response_structure(data, ["status", "message", "rag_id"])
            assert data.get("status") == "success"
            assert data.get("rag_id") == test_id

            wait_for_indexing(10)

            # 验证可以查询
            query_result = api_client.query(test_id, sample_documents[0]["query"])
            assert query_result.get("answer"), "Should be able to query inserted document"

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass

    def test_insert_document_invalid_rag_id(self, base_url):
        """
        测试使用无效 rag_id 插入文档

        验证：
        1. 返回 404
        2. 错误消息清晰
        """
        payload = {
            "rag_id": "nonexistent_rag_id",
            "content": "Some content",
            "file_path": "test.txt"
        }

        resp = requests.post(
            f"{base_url}/api/documents/insert",
            json=payload,
            timeout=30
        )

        assert resp.status_code == 404, \
            f"Should return 404 for invalid rag_id, got {resp.status_code}"

    def test_insert_document_missing_fields(self, base_url, api_client):
        """
        测试插入文档时缺少必需字段

        验证：
        1. 返回 422 (Validation Error)
        2. 错误消息指出缺少的字段
        """
        test_id = "test_api_missing_fields"

        try:
            api_client.create_instance(test_id, "test_missing_ws")
            time.sleep(2)

            # 缺少 file_path 字段
            payload = {
                "rag_id": test_id,
                "content": "Some content"
                # Missing "file_path"
            }

            resp = requests.post(
                f"{base_url}/api/documents/insert",
                json=payload,
                timeout=30
            )

            assert resp.status_code == 422, \
                f"Should return 422 for missing fields, got {resp.status_code}"

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass


@pytest.mark.integration
class TestQueryEndpoints:
    """Query API 端点测试"""

    def test_query_endpoint(self, base_url, api_client, sample_documents):
        """
        测试查询端点

        验证：
        1. POST /api/query/ 返回 200
        2. 响应包含 answer 字段
        3. 返回格式正确（QueryResponse）
        """
        test_id = "test_api_query"

        try:
            api_client.create_instance(test_id, "test_query_ws")
            time.sleep(2)

            api_client.insert_document(
                test_id,
                sample_documents[0]["content"],
                "query_test.txt"
            )
            wait_for_indexing(10)

            # 查询
            payload = {
                "rag_id": test_id,
                "question": sample_documents[0]["query"],
                "mode": "hybrid",
                "only_need_context": True
            }

            resp = requests.post(
                f"{base_url}/api/query/",
                json=payload,
                timeout=60
            )

            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

            data = resp.json()
            assert_response_structure(data, ["rag_id", "question", "answer", "mode"])
            assert data.get("rag_id") == test_id
            assert data.get("question") == sample_documents[0]["query"]
            assert "answer" in data

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass

    def test_query_invalid_rag_id(self, base_url):
        """
        测试查询不存在的 rag_id

        验证：
        1. 返回 404
        2. 错误消息清晰
        """
        payload = {
            "rag_id": "nonexistent_query_id",
            "question": "Any question?",
            "mode": "hybrid"
        }

        resp = requests.post(
            f"{base_url}/api/query/",
            json=payload,
            timeout=30
        )

        assert resp.status_code == 404, \
            f"Should return 404 for invalid rag_id, got {resp.status_code}"

    def test_query_different_modes(self, base_url, api_client, sample_documents):
        """
        测试不同的查询模式

        验证：
        1. hybrid 模式
        2. local 模式（如果支持）
        3. global 模式（如果支持）
        """
        test_id = "test_api_modes"

        try:
            api_client.create_instance(test_id, "test_modes_ws")
            time.sleep(2)

            api_client.insert_document(
                test_id,
                sample_documents[0]["content"],
                "modes_test.txt"
            )
            wait_for_indexing(10)

            modes = ["hybrid", "local", "global"]
            for mode in modes:
                payload = {
                    "rag_id": test_id,
                    "question": sample_documents[0]["query"],
                    "mode": mode,
                    "only_need_context": True
                }

                try:
                    resp = requests.post(
                        f"{base_url}/api/query/",
                        json=payload,
                        timeout=60
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        assert data.get("mode") == mode, f"Mode should be {mode}"
                        print(f"Mode {mode} works")
                    else:
                        print(f"Mode {mode} not supported or failed: {resp.status_code}")
                except Exception as e:
                    print(f"Mode {mode} test failed: {e}")

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass


@pytest.mark.integration
class TestAPIErrorHandling:
    """API 错误处理测试"""

    def test_malformed_json(self, base_url):
        """
        测试发送格式错误的 JSON

        验证：
        1. 返回 422 或 400
        2. 错误消息清晰
        """
        resp = requests.post(
            f"{base_url}/api/documents/insert",
            data="not a json",  # 不是 JSON
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        assert resp.status_code in [400, 422], \
            f"Should return 400/422 for malformed JSON, got {resp.status_code}"

    def test_missing_required_headers(self, base_url):
        """
        测试缺少必需的 headers

        验证：
        1. 系统应该能处理缺少 Content-Type 的请求
        2. 或返回适当的错误
        """
        payload = {"rag_id": "test", "content": "test", "file_path": "test.txt"}

        try:
            resp = requests.post(
                f"{base_url}/api/documents/insert",
                json=payload,
                # 正常情况下会自动添加 Content-Type,这里只是测试
                timeout=30
            )
            # 如果成功，说明系统处理得当
            # 如果失败，也可以接受（取决于 FastAPI 配置）
            print(f"Response status: {resp.status_code}")
        except Exception as e:
            print(f"Request failed (expected): {e}")

    def test_concurrent_api_calls(self, base_url, api_client, sample_documents):
        """
        测试并发 API 调用

        验证：
        1. 多个并发请求不会冲突
        2. 每个请求都能正确处理
        """
        import concurrent.futures

        test_id = "test_api_concurrent"

        try:
            api_client.create_instance(test_id, "test_concurrent_ws")
            time.sleep(2)

            api_client.insert_document(
                test_id,
                sample_documents[0]["content"],
                "concurrent_test.txt"
            )
            wait_for_indexing(10)

            def make_query(i):
                """并发查询函数"""
                try:
                    payload = {
                        "rag_id": test_id,
                        "question": f"Query {i}: {sample_documents[0]['query']}",
                        "mode": "hybrid"
                    }
                    resp = requests.post(
                        f"{base_url}/api/query/",
                        json=payload,
                        timeout=60
                    )
                    return resp.status_code == 200
                except Exception as e:
                    print(f"Query {i} failed: {e}")
                    return False

            # 并发发送 5 个查询
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(make_query, range(5)))

            # 验证所有查询都成功
            success_count = sum(results)
            print(f"Successful concurrent queries: {success_count}/5")
            assert success_count >= 4, "At least 4/5 concurrent queries should succeed"

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass


@pytest.mark.integration
class TestAPIResponseFormats:
    """API 响应格式测试"""

    def test_response_content_type(self, base_url, api_client):
        """
        测试响应 Content-Type

        验证：
        1. JSON 端点返回 application/json
        2. Content-Type header 正确
        """
        test_id = "test_api_content_type"

        try:
            api_client.create_instance(test_id, "test_content_type_ws")
            time.sleep(2)

            resp = requests.get(f"{base_url}/api/admin/rag_instances/list", timeout=10)

            assert resp.status_code == 200
            assert "application/json" in resp.headers.get("Content-Type", ""), \
                "Response should be JSON"

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass

    def test_response_timestamps(self, base_url, api_client, sample_documents):
        """
        测试响应中的时间戳

        验证：
        1. QueryResponse 包含 timestamp
        2. 时间戳格式正确（ISO 8601）
        """
        test_id = "test_api_timestamp"

        try:
            api_client.create_instance(test_id, "test_timestamp_ws")
            time.sleep(2)

            api_client.insert_document(
                test_id,
                sample_documents[0]["content"],
                "timestamp_test.txt"
            )
            wait_for_indexing(10)

            result = api_client.query(test_id, sample_documents[0]["query"])

            assert "timestamp" in result, "QueryResponse should include timestamp"

            # 验证时间戳格式（ISO 8601）
            from datetime import datetime
            try:
                datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
                print(f"Timestamp format valid: {result['timestamp']}")
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {result['timestamp']}")

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass
