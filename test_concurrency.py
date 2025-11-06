#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发性能测试脚本

用法:
    python test_concurrency.py --test query --concurrent 50
    python test_concurrency.py --test mixed --concurrent 100
    python test_concurrency.py --test stress
"""

import asyncio
import aiohttp
import time
import argparse
from typing import List, Tuple
import statistics


BASE_URL = "http://localhost:8000"


async def test_concurrent_queries(num_requests: int = 100, rag_id: str = "test_kb"):
    """测试并发查询性能"""

    print(f"\n{'='*60}")
    print(f"并发查询测试 - {num_requests} 个并发请求")
    print(f"{'='*60}\n")

    async def single_query(session, query_id):
        start = time.time()
        try:
            async with session.post(
                f"{BASE_URL}/api/query/",
                json={
                    "rag_id": rag_id,
                    "question": f"测试问题 {query_id}",
                    "mode": "hybrid",
                    "top_k": 10
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                result = await response.json()
                duration = time.time() - start
                return {
                    'query_id': query_id,
                    'duration': duration,
                    'status': response.status,
                    'success': response.status == 200
                }
        except Exception as e:
            duration = time.time() - start
            return {
                'query_id': query_id,
                'duration': duration,
                'status': 0,
                'success': False,
                'error': str(e)
            }

    start_time = time.time()

    # 创建连接池
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [single_query(session, i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    # 统计结果
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    if successful:
        durations = [r['duration'] for r in successful]
        avg_time = statistics.mean(durations)
        median_time = statistics.median(durations)
        min_time = min(durations)
        max_time = max(durations)
        qps = len(successful) / total_time
    else:
        avg_time = median_time = min_time = max_time = qps = 0

    # 打印结果
    print(f"📊 测试结果:")
    print(f"  总请求数:     {num_requests}")
    print(f"  成功:         {len(successful)} ✅")
    print(f"  失败:         {len(failed)} ❌")
    print(f"\n⏱️  性能指标:")
    print(f"  总耗时:       {total_time:.2f}s")
    print(f"  平均响应时间: {avg_time:.2f}s")
    print(f"  中位数时间:   {median_time:.2f}s")
    print(f"  最快:         {min_time:.2f}s")
    print(f"  最慢:         {max_time:.2f}s")
    print(f"  QPS:          {qps:.2f} 请求/秒")

    if failed:
        print(f"\n❌ 失败请求:")
        for r in failed[:5]:  # 只显示前5个
            error = r.get('error', 'Unknown error')
            print(f"  - 查询 {r['query_id']}: {error[:50]}...")

    return {
        'total': num_requests,
        'successful': len(successful),
        'failed': len(failed),
        'total_time': total_time,
        'qps': qps,
        'avg_time': avg_time
    }


async def test_concurrent_inserts(num_requests: int = 10, rag_id: str = "test_kb"):
    """测试并发插入性能"""

    print(f"\n{'='*60}")
    print(f"并发插入测试 - {num_requests} 个并发请求")
    print(f"{'='*60}\n")

    async def single_insert(session, doc_id):
        start = time.time()
        try:
            async with session.post(
                f"{BASE_URL}/api/documents/insert",
                json={
                    "rag_id": rag_id,
                    "content": f"测试文档内容 {doc_id} " * 100,  # 模拟较长的文档
                    "file_path": f"test_doc_{doc_id}.txt"
                },
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                result = await response.json()
                duration = time.time() - start
                return {
                    'doc_id': doc_id,
                    'duration': duration,
                    'status': response.status,
                    'success': response.status == 200
                }
        except Exception as e:
            duration = time.time() - start
            return {
                'doc_id': doc_id,
                'duration': duration,
                'status': 0,
                'success': False,
                'error': str(e)
            }

    start_time = time.time()

    connector = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(connector=connector) as session:
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(5)  # 最多5个并发插入

        async def controlled_insert(doc_id):
            async with semaphore:
                return await single_insert(session, doc_id)

        tasks = [controlled_insert(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    # 统计
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"📊 测试结果:")
    print(f"  总请求数:     {num_requests}")
    print(f"  成功:         {len(successful)} ✅")
    print(f"  失败:         {len(failed)} ❌")
    print(f"  总耗时:       {total_time:.2f}s")

    if successful:
        avg_time = statistics.mean([r['duration'] for r in successful])
        print(f"  平均时间:     {avg_time:.2f}s")
        print(f"  吞吐量:       {len(successful) / total_time:.2f} 文档/秒")


async def test_mixed_operations(num_operations: int = 100, rag_id: str = "test_kb"):
    """测试混合读写操作"""

    print(f"\n{'='*60}")
    print(f"混合操作测试 - {num_operations} 个操作 (90% 读, 10% 写)")
    print(f"{'='*60}\n")

    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        # 90% 读操作
        read_count = int(num_operations * 0.9)
        read_tasks = []
        for i in range(read_count):
            async def query():
                async with session.post(
                    f"{BASE_URL}/api/query/",
                    json={
                        "rag_id": rag_id,
                        "question": f"问题 {i}",
                        "mode": "naive"  # 使用 naive 模式加快速度
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    return await resp.json()
            read_tasks.append(query())

        # 10% 写操作
        write_count = num_operations - read_count
        write_tasks = []
        for i in range(write_count):
            async def insert():
                async with session.post(
                    f"{BASE_URL}/api/graph/entities/create",
                    json={
                        "rag_id": rag_id,
                        "entity_name": f"Entity_{i}",
                        "description": "测试实体"
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    return await resp.json()
            write_tasks.append(insert())

        # 混合执行
        all_tasks = read_tasks + write_tasks
        start = time.time()
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        duration = time.time() - start

        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful

        print(f"📊 测试结果:")
        print(f"  读操作:       {read_count}")
        print(f"  写操作:       {write_count}")
        print(f"  成功:         {successful} ✅")
        print(f"  失败:         {failed} ❌")
        print(f"  总耗时:       {duration:.2f}s")
        print(f"  吞吐量:       {successful / duration:.2f} ops/s")


async def stress_test(rag_id: str = "test_kb"):
    """压力测试: 逐步增加并发数"""

    print(f"\n{'='*60}")
    print(f"压力测试 - 逐步增加并发级别")
    print(f"{'='*60}\n")

    concurrent_levels = [10, 25, 50, 100, 200]
    results = []

    for level in concurrent_levels:
        print(f"\n🔄 测试并发级别: {level}")
        result = await test_concurrent_queries(level, rag_id)
        results.append((level, result))
        await asyncio.sleep(2)  # 休息2秒

    # 汇总报告
    print(f"\n{'='*60}")
    print("压力测试汇总报告")
    print(f"{'='*60}\n")
    print(f"{'并发数':<10} {'QPS':<10} {'平均时间':<12} {'成功率':<10}")
    print("-" * 45)

    for level, result in results:
        success_rate = (result['successful'] / result['total']) * 100
        print(f"{level:<10} {result['qps']:<10.2f} {result['avg_time']:<12.2f} {success_rate:<10.1f}%")


async def check_server():
    """检查服务器是否可用"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/admin/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return True
    except:
        pass
    return False


async def main():
    parser = argparse.ArgumentParser(description='RAG API 并发性能测试')
    parser.add_argument('--test', choices=['query', 'insert', 'mixed', 'stress'],
                        default='query', help='测试类型')
    parser.add_argument('--concurrent', type=int, default=50,
                        help='并发数')
    parser.add_argument('--rag-id', type=str, default='test_kb',
                        help='RAG 实例 ID')

    args = parser.parse_args()

    print(f"\n🚀 RAG API 并发性能测试")
    print(f"服务器: {BASE_URL}")
    print(f"RAG ID: {args.rag_id}")

    # 检查服务器
    print(f"\n检查服务器连接...")
    if not await check_server():
        print(f"❌ 无法连接到服务器 {BASE_URL}")
        print(f"请确保服务已启动: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return

    print(f"✅ 服务器连接正常\n")

    # 执行测试
    if args.test == 'query':
        await test_concurrent_queries(args.concurrent, args.rag_id)
    elif args.test == 'insert':
        await test_concurrent_inserts(args.concurrent, args.rag_id)
    elif args.test == 'mixed':
        await test_mixed_operations(args.concurrent, args.rag_id)
    elif args.test == 'stress':
        await stress_test(args.rag_id)

    print(f"\n✅ 测试完成!\n")


if __name__ == "__main__":
    asyncio.run(main())
