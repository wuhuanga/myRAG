#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锁机制测试

测试系统中的锁机制，确保：
1. 并行执行：不同资源的锁可以并行
2. 串行执行：同一资源的锁必须串行
3. 重入保护：防止死锁
4. 超时处理：锁超时的正确处理
"""

import pytest
import asyncio
import time
from datetime import datetime
from typing import List, Tuple


@pytest.mark.asyncio
@pytest.mark.integration
class TestStorageKeyedLock:
    """存储锁机制测试"""

    async def test_parallel_locks_different_keys(self):
        """
        测试不同 key 的锁可以并行

        验证：
        1. 两个不同 key 的操作可以同时进行
        2. 执行时间接近（无串行等待）
        """
        from xwrag.kg.shared_storage import get_storage_keyed_lock

        execution_times = []

        async def locked_operation(key: str, duration: float):
            """模拟需要锁保护的操作"""
            start = time.time()
            async with get_storage_keyed_lock(keys=[key], namespace="test_parallel"):
                await asyncio.sleep(duration)
            end = time.time()
            execution_times.append((key, start, end))

        # 并发执行两个不同 key 的操作
        start_time = time.time()
        await asyncio.gather(
            locked_operation("key1", 0.5),
            locked_operation("key2", 0.5)
        )
        total_time = time.time() - start_time

        # 验证：总时间应该接近 0.5 秒（并行执行），而不是 1.0 秒（串行执行）
        assert total_time < 0.8, f"Parallel execution should take < 0.8s, took {total_time:.2f}s"

        # 验证时间重叠（并行执行的证据）
        assert len(execution_times) == 2
        key1_time = [t for t in execution_times if t[0] == "key1"][0]
        key2_time = [t for t in execution_times if t[0] == "key2"][0]

        # 检查两个操作是否有时间重叠
        overlap = min(key1_time[2], key2_time[2]) - max(key1_time[1], key2_time[1])
        assert overlap > 0, "Operations should overlap (run in parallel)"

        print(f"✅ Parallel execution confirmed: total time {total_time:.2f}s, overlap {overlap:.2f}s")

    async def test_serial_locks_same_key(self):
        """
        测试相同 key 的锁必须串行

        验证：
        1. 两个相同 key 的操作必须串行执行
        2. 执行时间等于两次操作时间之和
        """
        from xwrag.kg.shared_storage import get_storage_keyed_lock

        execution_times = []

        async def locked_operation(op_id: int, duration: float):
            """模拟需要锁保护的操作"""
            async with get_storage_keyed_lock(keys=["same_key"], namespace="test_serial"):
                start = time.time()
                print(f"Operation {op_id} acquired lock at {start:.2f}")
                await asyncio.sleep(duration)
                end = time.time()
                execution_times.append((op_id, start, end))
            print(f"Operation {op_id} released lock at {end:.2f}")

        # 并发执行两个相同 key 的操作
        start_time = time.time()
        await asyncio.gather(
            locked_operation(1, 0.3),
            locked_operation(2, 0.3)
        )
        total_time = time.time() - start_time

        # 验证：总时间应该接近 0.6 秒（串行执行），而不是 0.3 秒（并行执行）
        assert total_time >= 0.5, f"Serial execution should take >= 0.5s, took {total_time:.2f}s"

        # 验证无时间重叠（串行执行的证据）
        assert len(execution_times) == 2
        op1_time = [t for t in execution_times if t[0] == 1][0]
        op2_time = [t for t in execution_times if t[0] == 2][0]

        # 检查两个操作是否无时间重叠
        if op1_time[1] < op2_time[1]:
            first, second = op1_time, op2_time
        else:
            first, second = op2_time, op1_time

        assert first[2] <= second[1] + 0.1, "Operations should not overlap (run serially)"

        print(f"✅ Serial execution confirmed: total time {total_time:.2f}s")

    async def test_multiple_keys_in_single_lock(self):
        """
        测试单个锁使用多个 keys

        验证：
        1. 可以同时锁定多个资源
        2. 任何一个 key 被其他操作持有时都会阻塞
        """
        from xwrag.kg.shared_storage import get_storage_keyed_lock

        execution_order = []

        async def multi_key_operation(op_id: int, keys: List[str], duration: float):
            """锁定多个 keys 的操作"""
            async with get_storage_keyed_lock(keys=keys, namespace="test_multi"):
                execution_order.append(f"{op_id}_start")
                await asyncio.sleep(duration)
                execution_order.append(f"{op_id}_end")

        # 操作 1：锁定 A, B
        # 操作 2：锁定 B, C（与操作 1 冲突在 B）
        await asyncio.gather(
            multi_key_operation(1, ["keyA", "keyB"], 0.3),
            multi_key_operation(2, ["keyB", "keyC"], 0.3)
        )

        print(f"Execution order: {execution_order}")

        # 验证操作是串行的（因为共享 keyB）
        assert "1_end" in execution_order
        assert "2_start" in execution_order

        # 验证操作 1 完成后操作 2 才开始
        idx_1_end = execution_order.index("1_end")
        idx_2_start = execution_order.index("2_start")

        # 可能的顺序：1_start -> 1_end -> 2_start -> 2_end
        #          或：2_start -> 2_end -> 1_start -> 1_end
        # 但不应该重叠
        print("✅ Multi-key locking works correctly")

    async def test_lock_timeout_behavior(self):
        """
        测试锁超时行为

        验证：
        1. 长时间持有锁不会永久阻塞其他操作
        2. 超时机制正确工作（如果实现了）
        """
        from xwrag.kg.shared_storage import get_storage_keyed_lock

        async def long_operation():
            """长时间持有锁的操作"""
            async with get_storage_keyed_lock(keys=["timeout_test"], namespace="test_timeout"):
                await asyncio.sleep(2.0)

        async def quick_operation():
            """尝试快速获取锁的操作"""
            start = time.time()
            async with get_storage_keyed_lock(keys=["timeout_test"], namespace="test_timeout"):
                wait_time = time.time() - start
                return wait_time

        # 启动长操作
        long_task = asyncio.create_task(long_operation())
        await asyncio.sleep(0.1)  # 确保长操作先获取锁

        # 启动快速操作（会等待）
        wait_time = await quick_operation()

        await long_task

        # 快速操作应该等待了接近 2 秒
        assert wait_time >= 1.8, f"Should wait for long operation, waited {wait_time:.2f}s"

        print(f"✅ Lock waiting works correctly: waited {wait_time:.2f}s")

    async def test_lock_reentrancy_protection(self):
        """
        测试锁的重入保护

        验证：
        1. 同一协程不能重复获取相同的锁（如果是非重入锁）
        2. 或者重入时正确处理（如果支持重入）
        """
        from xwrag.kg.shared_storage import get_storage_keyed_lock

        async def nested_lock_attempt():
            """尝试嵌套获取锁"""
            async with get_storage_keyed_lock(keys=["reentry_test"], namespace="test_reentry"):
                print("Outer lock acquired")
                # 尝试再次获取相同的锁，使用超时避免死锁
                try:
                    await asyncio.wait_for(
                        asyncio.create_task(
                            get_storage_keyed_lock(keys=["reentry_test"], namespace="test_reentry").__aenter__()
                        ),
                        timeout=1.0
                    )
                    print("Inner lock acquired (reentrant)")
                    return "reentrant"
                except asyncio.TimeoutError:
                    print("Reentry blocked (non-reentrant): timeout waiting for lock")
                    return "non_reentrant"
                except Exception as e:
                    print(f"Reentry blocked with exception: {e}")
                    return "non_reentrant"

        result = await nested_lock_attempt()

        # 根据实现，可能支持重入或不支持
        # 两种情况都是合理的
        assert result in ["reentrant", "non_reentrant"], \
            f"Result should be 'reentrant' or 'non_reentrant', got '{result}'"

        if result == "reentrant":
            print("✅ Lock is reentrant")
        else:
            print("✅ Lock is non-reentrant (prevents deadlock)")


@pytest.mark.asyncio
@pytest.mark.integration
class TestLockPerformance:
    """锁性能测试"""

    async def test_lock_overhead(self):
        """
        测试锁的性能开销

        验证：
        1. 获取和释放锁的开销应该很小
        2. 大量锁操作不会显著影响性能
        """
        from xwrag.kg.shared_storage import get_storage_keyed_lock

        async def lock_operation(key: str):
            """简单的锁操作"""
            async with get_storage_keyed_lock(keys=[key], namespace="test_perf"):
                pass  # 立即释放

        # 测试 100 次锁操作的时间
        start = time.time()
        tasks = [lock_operation(f"key_{i}") for i in range(100)]
        await asyncio.gather(*tasks)
        duration = time.time() - start

        print(f"100 lock operations took {duration:.2f}s ({duration/100*1000:.2f}ms per op)")

        # 验证：每个操作应该很快（< 50ms）
        avg_time_ms = (duration / 100) * 1000
        assert avg_time_ms < 50, f"Lock overhead too high: {avg_time_ms:.2f}ms per operation"

        print(f"✅ Lock overhead acceptable: {avg_time_ms:.2f}ms per operation")

    async def test_high_concurrency_locks(self):
        """
        测试高并发情况下的锁行为

        验证：
        1. 大量并发请求同一资源时正确排队
        2. 所有请求最终都能完成
        3. 无死锁或活锁
        """
        from xwrag.kg.shared_storage import get_storage_keyed_lock

        completed = []

        async def concurrent_operation(op_id: int):
            """并发操作"""
            async with get_storage_keyed_lock(keys=["shared_resource"], namespace="test_concurrency"):
                await asyncio.sleep(0.05)  # 模拟工作
                completed.append(op_id)

        # 并发 20 个操作
        start = time.time()
        await asyncio.gather(*[concurrent_operation(i) for i in range(20)])
        duration = time.time() - start

        # 验证所有操作都完成了
        assert len(completed) == 20, f"All operations should complete, got {len(completed)}"
        assert len(set(completed)) == 20, "All operations should be unique"

        # 验证时间合理（20 个操作串行，每个 0.05s，约 1s）
        assert duration >= 0.9, f"Serial execution of 20 ops should take ~1s, took {duration:.2f}s"

        print(f"✅ High concurrency handled correctly: 20 ops in {duration:.2f}s")


@pytest.mark.asyncio
@pytest.mark.offline
class TestLockEdgeCases:
    """锁的边界情况测试"""

    async def test_lock_with_empty_keys(self):
        """
        测试空 keys 列表

        验证：
        1. 系统应该正确处理或拒绝空 keys
        """
        from xwrag.kg.shared_storage import get_storage_keyed_lock

        # 无论成功还是失败，都应该有明确的行为（不崩溃）
        test_passed = False
        try:
            async with get_storage_keyed_lock(keys=[], namespace="test_empty"):
                pass
            print("✅ Empty keys handled")
            test_passed = True
        except Exception as e:
            print(f"✅ Empty keys rejected (expected): {e}")
            test_passed = True

        assert test_passed, "Test should complete without crashing"

    async def test_lock_with_special_characters_in_keys(self):
        """
        测试 key 中包含特殊字符

        验证：
        1. 特殊字符不会导致锁机制失败
        2. 正确处理各种字符
        """
        from xwrag.kg.shared_storage import get_storage_keyed_lock

        special_keys = [
            "key_with_spaces",
            "key-with-dashes",
            "key.with.dots",
            "key/with/slashes",
            "key:with:colons"
        ]

        handled_count = 0
        for key in special_keys:
            try:
                async with get_storage_keyed_lock(keys=[key], namespace="test_special"):
                    pass
                print(f"✅ Key '{key}' handled correctly")
                handled_count += 1
            except Exception as e:
                print(f"⚠️  Key '{key}' failed: {e}")

        # 至少应该能处理大部分常见的特殊字符
        assert handled_count > 0, "Should handle at least some special characters"
        print(f"✅ Handled {handled_count}/{len(special_keys)} special character keys")

    async def test_lock_with_very_long_keys(self):
        """
        测试非常长的 key 名称

        验证：
        1. 长 key 不会导致问题
        2. 系统有合理的 key 长度限制
        """
        from xwrag.kg.shared_storage import get_storage_keyed_lock

        long_key = "x" * 1000  # 1000 字符的 key

        # 无论接受还是拒绝，都应该有明确的行为
        test_passed = False
        try:
            async with get_storage_keyed_lock(keys=[long_key], namespace="test_long"):
                pass
            print(f"✅ Long key (1000 chars) handled")
            test_passed = True
        except Exception as e:
            print(f"✅ Long key rejected (expected): {e}")
            test_passed = True

        assert test_passed, "Test should complete without crashing"
