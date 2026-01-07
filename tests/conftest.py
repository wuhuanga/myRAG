#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest 公共配置和 Fixture

提供所有测试共享的 fixture、配置和工具函数
"""

import os
import sys
import asyncio
import pytest
import requests
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================
# 配置 Fixtures
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def initialize_shared_data():
    """初始化共享数据（用于 lock 测试）"""
    from xwrag.kg.shared_storage import initialize_share_data
    # 初始化单进程模式的共享数据
    initialize_share_data(workers=1)
    yield


@pytest.fixture(scope="session")
def base_url():
    """API 基础 URL"""
    return os.getenv("TEST_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        "base_url": os.getenv("TEST_BASE_URL", "http://localhost:8000"),
        "nebula_host": os.getenv("NEBULA_HOST", "localhost"),
        "nebula_port": os.getenv("NEBULA_PORT", "9669"),
        "milvus_host": os.getenv("MILVUS_HOST", "localhost"),
        "milvus_port": os.getenv("MILVUS_PORT", "19530"),
        "test_workspace_prefix": "test_",
        "test_timeout": 120,
    }


# ============================================================
# API Client Fixtures
# ============================================================

@pytest.fixture
def api_client(base_url):
    """API 客户端"""
    class APIClient:
        def __init__(self, base_url: str):
            self.base_url = base_url
            self.session = requests.Session()

        def create_instance(self, rag_id: str, workspace: str, **kwargs) -> Dict[str, Any]:
            """创建 RAG 实例"""
            payload = {
                "rag_id": rag_id,
                "workspace": workspace,
                "working_dir": kwargs.get("working_dir", f"./test_{workspace}"),
                "description": kwargs.get("description", f"Test instance {rag_id}"),
                "top_k": kwargs.get("top_k", 10),
                "chunk_top_k": kwargs.get("chunk_top_k", 5),
                "chunk_token_size": kwargs.get("chunk_token_size", 1200),
                "chunk_overlap_token_size": kwargs.get("chunk_overlap_token_size", 100),
                "enable_llm_cache": kwargs.get("enable_llm_cache", True),
            }
            resp = self.session.post(
                f"{self.base_url}/api/admin/rag_instances/create",
                json=payload,
                timeout=180  # 增加到 3 分钟以支持慢速创建
            )
            resp.raise_for_status()
            return resp.json()

        def list_instances(self) -> List[Dict[str, Any]]:
            """列出所有实例"""
            resp = self.session.get(
                f"{self.base_url}/api/admin/rag_instances/list",
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()

        def delete_instance(self, rag_id: str, cleanup_storage: bool = True) -> Dict[str, Any]:
            """删除实例"""
            resp = self.session.delete(
                f"{self.base_url}/api/admin/rag_instances/{rag_id}/complete",
                params={"cleanup_storage": cleanup_storage},
                timeout=120
            )
            resp.raise_for_status()
            return resp.json()

        def insert_document(self, rag_id: str, content: str, file_path: str, doc_id: str = None) -> Dict[str, Any]:
            """插入文档"""
            payload = {
                "rag_id": rag_id,
                "content": content,
                "file_path": file_path,
            }
            if doc_id:
                payload["doc_id"] = doc_id

            resp = self.session.post(
                f"{self.base_url}/api/documents/insert",
                json=payload,
                timeout=120
            )
            resp.raise_for_status()
            return resp.json()

        def query(self, rag_id: str, question: str, mode: str = "hybrid",
                 only_need_context: bool = True, **kwargs) -> Dict[str, Any]:
            """查询知识库"""
            payload = {
                "rag_id": rag_id,
                "question": question,
                "mode": mode,
                "only_need_context": only_need_context,
                **kwargs
            }
            resp = self.session.post(
                f"{self.base_url}/api/query/",
                json=payload,
                timeout=60
            )
            resp.raise_for_status()
            return resp.json()

        def close(self):
            """关闭会话"""
            self.session.close()

    client = APIClient(base_url)
    yield client
    client.close()


# ============================================================
# RAG Instance Fixtures
# ============================================================

@pytest.fixture
def test_instance(api_client, test_config):
    """创建测试实例（自动清理）"""
    instances = []

    def _create_instance(rag_id: str = None, workspace: str = None, **kwargs):
        """创建实例的工厂函数"""
        if rag_id is None:
            rag_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        if workspace is None:
            workspace = f"{test_config['test_workspace_prefix']}{rag_id}"

        result = api_client.create_instance(rag_id, workspace, **kwargs)
        instances.append(rag_id)
        return result

    yield _create_instance

    # 清理所有创建的实例
    for rag_id in instances:
        try:
            api_client.delete_instance(rag_id, cleanup_storage=True)
        except Exception as e:
            print(f"Warning: Failed to cleanup instance {rag_id}: {e}")


@pytest.fixture
def multiple_test_instances(api_client, test_config):
    """创建多个测试实例（自动清理）"""
    instances = []

    def _create_instances(count: int = 3, prefix: str = "test"):
        """创建多个实例"""
        created = []
        for i in range(count):
            rag_id = f"{prefix}_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            workspace = f"{test_config['test_workspace_prefix']}{rag_id}"
            result = api_client.create_instance(rag_id, workspace)
            instances.append(rag_id)
            created.append(result)
        return created

    yield _create_instances

    # 清理所有创建的实例
    for rag_id in instances:
        try:
            api_client.delete_instance(rag_id, cleanup_storage=True)
        except Exception as e:
            print(f"Warning: Failed to cleanup instance {rag_id}: {e}")


# ============================================================
# Storage Connection Fixtures
# ============================================================

@pytest.fixture
def nebula_connection(test_config):
    """Nebula Graph 连接"""
    try:
        from nebula3.gclient.net import ConnectionPool
        from nebula3.Config import Config

        config = Config()
        config.max_connection_pool_size = 10

        pool = ConnectionPool()
        pool.init(
            [(test_config["nebula_host"], int(test_config["nebula_port"]))],
            config
        )

        yield pool

        pool.close()
    except ImportError:
        pytest.skip("nebula3-python not installed")


@pytest.fixture
def milvus_connection(test_config):
    """Milvus 连接"""
    try:
        from pymilvus import connections

        alias = "test_connection"
        connections.connect(
            alias=alias,
            host=test_config["milvus_host"],
            port=test_config["milvus_port"],
        )

        yield alias

        connections.disconnect(alias)
    except ImportError:
        pytest.skip("pymilvus not installed")


# ============================================================
# Test Data Fixtures
# ============================================================

@pytest.fixture
def sample_documents():
    """测试文档数据"""
    return [
        {
            "content": """Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。
            Python 广泛应用于 Web 开发、数据科学、人工智能和自动化等领域。
            它具有简洁易读的语法，拥有丰富的标准库和第三方库生态系统。
            Python 支持多种编程范式，包括面向对象、函数式和过程式编程。""",
            "file_path": "python_intro.txt",
            "query": "What is Python used for?"
        },
        {
            "content": """机器学习是人工智能的一个子领域，专注于让计算机通过数据学习。
            常见的机器学习算法包括线性回归、决策树、神经网络和支持向量机。
            深度学习是机器学习的一个分支，使用多层神经网络处理复杂数据。
            机器学习应用于图像识别、自然语言处理、推荐系统等众多领域。""",
            "file_path": "ml_intro.txt",
            "query": "What is machine learning?"
        },
        {
            "content": """RAG (Retrieval-Augmented Generation) 是一种结合检索和生成的技术。
            RAG 系统首先从知识库中检索相关信息，然后将其作为上下文传递给 LLM。
            这种方法可以提高生成内容的准确性，减少幻觉问题。
            RAG 特别适合需要专业知识或实时信息的应用场景。""",
            "file_path": "rag_intro.txt",
            "query": "What is RAG?"
        }
    ]


@pytest.fixture
def special_char_documents():
    """包含特殊字符的测试文档"""
    return [
        {
            "content": "单引号测试: It's a beautiful day. O'Brien said 'Hello'.",
            "file_path": "test_single_quote.txt"
        },
        {
            "content": '双引号测试: He said "Hello World" and "Goodbye".',
            "file_path": "test_double_quote.txt"
        },
        {
            "content": r"反斜杠测试: C:\Users\Admin\Documents\ and \\server\share\file.txt",
            "file_path": "test_backslash.txt"
        },
        {
            "content": "混合特殊字符: It's \"awesome\" to use Python! C:\\path\\to\\file",
            "file_path": "test_mixed.txt"
        }
    ]


# ============================================================
# Async Test Support
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================
# Pytest 配置
# ============================================================

def pytest_configure(config):
    """Pytest 配置钩子"""
    # 注册自定义标记
    config.addinivalue_line(
        "markers", "offline: 离线测试，不需要外部服务"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试，需要 Nebula/Milvus 等服务"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试，执行时间较长"
    )
    config.addinivalue_line(
        "markers", "concurrent: 并发测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试集合"""
    # 为所有异步测试添加 asyncio 标记
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# ============================================================
# Helper Functions
# ============================================================

def wait_for_indexing(seconds: int = 10):
    """等待索引完成"""
    import time
    print(f"⏳ 等待 {seconds} 秒让索引完成...")
    time.sleep(seconds)


def assert_response_structure(response: Dict[str, Any], required_fields: List[str]):
    """验证响应结构"""
    for field in required_fields:
        assert field in response, f"Response missing required field: {field}"


def cleanup_test_workspaces(test_config):
    """清理所有测试 workspace"""
    # 这个函数可以在测试会话结束时调用
    pass
