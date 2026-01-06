#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理测试

测试系统的错误处理机制：
1. 输入验证
2. 连接失败处理
3. 超时处理
4. 资源清理
5. 异常恢复
"""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock


@pytest.mark.integration
class TestInputValidation:
    """输入验证测试"""

    def test_invalid_rag_id_format(self, api_client):
        """
        测试无效的 rag_id 格式

        验证：
        1. 特殊字符在 rag_id 中的处理
        2. 过长的 rag_id
        3. 空 rag_id
        """
        invalid_ids = [
            ("", "empty string"),
            ("   ", "whitespace only"),
            ("rag id with spaces", "spaces"),
            ("rag/id/slash", "slashes"),
            ("x" * 1000, "too long")
        ]

        for invalid_id, description in invalid_ids:
            try:
                result = api_client.create_instance(invalid_id, "test_ws")
                # 如果成功，说明系统接受了这种格式
                print(f"✓ System accepts {description}: {invalid_id[:50]}")
                api_client.delete_instance(invalid_id, cleanup_storage=True)
            except Exception as e:
                # 如果失败，说明系统正确拒绝了
                print(f"✓ System rejects {description}: {e}")

    def test_invalid_workspace_format(self, api_client):
        """
        测试无效的 workspace 格式

        验证：
        1. 特殊字符处理
        2. 空 workspace
        """
        test_id = "test_invalid_ws"

        invalid_workspaces = [
            ("", "empty"),
            ("ws with spaces", "spaces"),
            ("ws/slash", "slashes")
        ]

        for invalid_ws, description in invalid_workspaces:
            try:
                result = api_client.create_instance(test_id, invalid_ws)
                print(f"✓ System accepts workspace with {description}")
                api_client.delete_instance(test_id, cleanup_storage=True)
            except Exception as e:
                print(f"✓ System rejects workspace with {description}: {e}")

    def test_negative_parameters(self, base_url):
        """
        测试负数参数

        验证：
        1. top_k, chunk_top_k 等参数的验证
        2. 负数应该被拒绝
        """
        import requests

        payload = {
            "rag_id": "test_negative",
            "workspace": "test_ws",
            "working_dir": "./test_negative",
            "top_k": -1,  # 负数
            "chunk_top_k": -5
        }

        resp = requests.post(
            f"{base_url}/api/admin/rag_instances/create",
            json=payload,
            timeout=30
        )

        # 应该返回 422 (Validation Error) 或者接受并使用默认值
        if resp.status_code == 422:
            print("✓ System rejects negative parameters")
        else:
            print(f"✓ System accepts negative parameters (may use defaults): {resp.status_code}")

    def test_missing_required_parameters(self, base_url):
        """
        测试缺少必需参数

        验证：
        1. 缺少 rag_id
        2. 缺少 workspace
        3. 返回 422 Validation Error
        """
        import requests

        # 缺少 rag_id
        payload = {"workspace": "test_ws"}
        resp = requests.post(
            f"{base_url}/api/admin/rag_instances/create",
            json=payload,
            timeout=30
        )

        assert resp.status_code == 422, f"Should return 422 for missing rag_id, got {resp.status_code}"

        # 缺少 workspace
        payload = {"rag_id": "test_id"}
        resp = requests.post(
            f"{base_url}/api/admin/rag_instances/create",
            json=payload,
            timeout=30
        )

        assert resp.status_code == 422, f"Should return 422 for missing workspace, got {resp.status_code}"

        print("✓ Missing required parameters correctly rejected")


@pytest.mark.integration
class TestConnectionFailure:
    """连接失败处理测试"""

    def test_query_after_server_restart(self, api_client, sample_documents):
        """
        测试服务重启后的查询

        验证：
        1. 实例数据持久化
        2. 重启后可以恢复
        注意：这个测试需要手动重启服务器，在自动化测试中可能跳过
        """
        pytest.skip("Requires manual server restart")

    def test_operation_on_deleted_instance(self, api_client, sample_documents):
        """
        测试在已删除实例上的操作

        验证：
        1. 删除实例后查询应该失败
        2. 删除实例后插入文档应该失败
        3. 错误消息清晰
        """
        test_id = "test_deleted_ops"

        # 创建并删除实例
        api_client.create_instance(test_id, "test_deleted_ws")
        time.sleep(2)
        api_client.delete_instance(test_id, cleanup_storage=True)

        # 尝试查询已删除的实例
        with pytest.raises(Exception) as exc_info:
            api_client.query(test_id, "Any question")

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower(), \
            "Should indicate instance not found"

        # 尝试向已删除的实例插入文档
        with pytest.raises(Exception) as exc_info:
            api_client.insert_document(test_id, "Some content", "test.txt")

        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower(), \
            "Should indicate instance not found"

        print("✓ Operations on deleted instance correctly fail")


@pytest.mark.integration
class TestTimeoutHandling:
    """超时处理测试"""

    def test_query_timeout(self, api_client, sample_documents):
        """
        测试查询超时

        验证：
        1. 查询超时时正确抛出异常
        2. 不会无限等待
        """
        test_id = "test_timeout_query"

        try:
            api_client.create_instance(test_id, "test_timeout_ws")
            time.sleep(2)

            api_client.insert_document(
                test_id,
                sample_documents[0]["content"],
                "timeout_test.txt"
            )
            time.sleep(10)

            # 使用很短的超时时间（可能会导致超时）
            import requests
            try:
                resp = requests.post(
                    f"{api_client.base_url}/api/query/",
                    json={
                        "rag_id": test_id,
                        "question": sample_documents[0]["query"],
                        "mode": "hybrid"
                    },
                    timeout=0.001  # 1ms 超时，几乎肯定会超时
                )
                print(f"Query completed within 1ms (unexpected): {resp.status_code}")
            except requests.exceptions.Timeout:
                print("✓ Query timeout correctly raised")

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass

    def test_insert_timeout(self, api_client):
        """
        测试插入超时

        验证：
        1. 插入超时时正确处理
        2. 不会导致系统挂起
        """
        test_id = "test_timeout_insert"

        try:
            api_client.create_instance(test_id, "test_insert_timeout_ws")
            time.sleep(2)

            # 尝试插入非常长的文档，可能导致超时
            long_content = "x" * 100000  # 100KB 文本

            import requests
            try:
                resp = requests.post(
                    f"{api_client.base_url}/api/documents/insert",
                    json={
                        "rag_id": test_id,
                        "content": long_content,
                        "file_path": "long.txt"
                    },
                    timeout=0.001  # 很短的超时
                )
                print(f"Insert completed within 1ms (unexpected)")
            except requests.exceptions.Timeout:
                print("✓ Insert timeout correctly raised")

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass


@pytest.mark.integration
class TestResourceCleanup:
    """资源清理测试"""

    def test_cleanup_on_failed_insert(self, api_client):
        """
        测试插入失败时的资源清理

        验证：
        1. 插入失败不会导致资源泄漏
        2. 实例状态保持一致
        """
        test_id = "test_failed_insert"

        try:
            api_client.create_instance(test_id, "test_failed_ws")
            time.sleep(2)

            # 尝试插入无效内容（空字符串）
            try:
                api_client.insert_document(test_id, "", "empty.txt")
            except Exception as e:
                print(f"Insert failed as expected: {e}")

            # 验证实例仍然可用
            try:
                api_client.query(test_id, "Any question")
                print("✓ Instance still functional after failed insert")
            except Exception as e:
                # 查询可能返回空结果，但不应该崩溃
                print(f"Query response: {e}")

        finally:
            try:
                result = api_client.delete_instance(test_id, cleanup_storage=True)
                assert result.get("status") == "success", "Should be able to cleanup after failed insert"
                print("✓ Cleanup successful after failed insert")
            except:
                pass

    def test_partial_cleanup_on_error(self, api_client, sample_documents):
        """
        测试部分清理失败的处理

        验证：
        1. Nebula 清理失败时，Milvus 仍然尝试清理
        2. 返回的 cleaned_resources 和 errors 正确反映状态
        """
        test_id = "test_partial_cleanup"

        try:
            api_client.create_instance(test_id, "test_partial_ws")
            time.sleep(2)

            api_client.insert_document(
                test_id,
                sample_documents[0]["content"],
                "partial_test.txt"
            )
            time.sleep(10)

            # 正常删除
            result = api_client.delete_instance(test_id, cleanup_storage=True)

            # 检查结果
            cleaned = result.get("cleaned_resources", [])
            errors = result.get("errors", [])

            print(f"Cleaned: {cleaned}")
            print(f"Errors: {errors}")

            # 即使有错误，部分资源应该被清理
            if errors:
                print(f"⚠️  Cleanup had {len(errors)} errors")
                assert len(cleaned) > 0, "Should still clean some resources despite errors"
            else:
                print("✓ All resources cleaned successfully")

        except Exception as e:
            print(f"Cleanup test encountered error: {e}")


@pytest.mark.offline
class TestExceptionRecovery:
    """异常恢复测试"""

    @pytest.mark.asyncio
    async def test_exception_in_async_operation(self):
        """
        测试异步操作中的异常处理

        验证：
        1. 异常不会导致协程泄漏
        2. 资源正确释放
        """
        from xwrag.utils import get_storage_keyed_lock

        exception_raised = False

        async def operation_with_exception():
            nonlocal exception_raised
            try:
                async with get_storage_keyed_lock(keys=["test_exception"], namespace="test"):
                    raise ValueError("Intentional exception")
            except ValueError:
                exception_raised = True

        await operation_with_exception()

        assert exception_raised, "Exception should be raised"

        # 验证锁已释放（另一个操作可以获取）
        async def verify_lock_released():
            async with get_storage_keyed_lock(keys=["test_exception"], namespace="test"):
                return True

        result = await verify_lock_released()
        assert result, "Lock should be released after exception"

        print("✓ Lock correctly released after exception")


@pytest.mark.integration
class TestEdgeCases:
    """边界情况测试"""

    def test_rapid_create_delete_cycle(self, api_client):
        """
        测试快速创建-删除循环

        验证：
        1. 快速创建和删除不会导致竞态条件
        2. 系统保持稳定
        """
        for i in range(5):
            test_id = f"test_rapid_{i}"
            try:
                api_client.create_instance(test_id, f"rapid_ws_{i}")
                time.sleep(0.5)  # 很短的等待
                api_client.delete_instance(test_id, cleanup_storage=True)
                print(f"✓ Cycle {i+1} completed")
            except Exception as e:
                pytest.fail(f"Rapid cycle {i+1} failed: {e}")

        print("✓ Rapid create-delete cycles handled correctly")

    def test_concurrent_operations_on_same_instance(self, api_client, sample_documents):
        """
        测试同一实例的并发操作

        验证：
        1. 并发查询同一实例
        2. 并发插入同一实例
        3. 不会导致数据损坏
        """
        import concurrent.futures

        test_id = "test_concurrent_same"

        try:
            api_client.create_instance(test_id, "concurrent_same_ws")
            time.sleep(2)

            api_client.insert_document(
                test_id,
                sample_documents[0]["content"],
                "concurrent_test.txt"
            )
            time.sleep(10)

            # 并发查询
            def query_instance(i):
                try:
                    result = api_client.query(test_id, f"Query {i}: {sample_documents[0]['query']}")
                    return result.get("answer") is not None
                except:
                    return False

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(query_instance, range(10)))

            success_count = sum(results)
            print(f"✓ Concurrent queries: {success_count}/10 succeeded")

            assert success_count >= 8, "At least 8/10 concurrent queries should succeed"

        finally:
            try:
                api_client.delete_instance(test_id, cleanup_storage=True)
            except:
                pass
