#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 后端 API 快速测试脚本 - 简化版

快速验证基本功能：
- 健康检查
- 创建实例
- 上传文档
- 查询
"""

import requests
import sys
from pathlib import Path


def test_quick():
    """快速测试"""
    BASE_URL = "http://localhost:8000/api"

    print("\n" + "="*60)
    print("RAG 后端 API 快速测试")
    print("="*60 + "\n")

    # 1. 健康检查
    print("1️⃣  健康检查...")
    try:
        resp = requests.get(f"{BASE_URL}/admin/health", timeout=5)
        if resp.status_code == 200:
            print(f"   ✓ 服务正常: {resp.json()}")
        else:
            print(f"   ✗ 服务异常: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 连接失败: {e}")
        print("\n💡 请确保后端服务正在运行:")
        print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000\n")
        return False

    # 2. 创建实例
    print("\n2️⃣  创建 RAG 实例...")
    rag_id = "quick_test"
    try:
        resp = requests.post(
            f"{BASE_URL}/admin/rag_instances/create",
            json={
                "rag_id": rag_id,
                "workspace": f"{rag_id}_workspace",
                "description": "快速测试实例"
            },
            timeout=30
        )
        if resp.status_code == 200:
            print(f"   ✓ 实例创建成功: {rag_id}")
        else:
            # 可能实例已存在
            if "already exists" in resp.text:
                print(f"   ℹ 实例已存在，继续使用")
            else:
                print(f"   ✗ 创建失败: {resp.text}")
                return False
    except Exception as e:
        print(f"   ✗ 创建失败: {e}")
        return False

    # 3. 上传文档
    print("\n3️⃣  上传文档...")
    doc_file = Path("/root/workplace/lightrag/LightRAG1/docx/卫星工程.docx")

    if not doc_file.exists():
        print(f"   ⚠ 文件不存在: {doc_file}")
        print("   跳过文档上传测试")
    else:
        try:
            with open(doc_file, 'rb') as f:
                files = {'file': (doc_file.name, f, 'application/octet-stream')}
                data = {'rag_id': rag_id}

                resp = requests.post(
                    f"{BASE_URL}/documents/upload",
                    files=files,
                    data=data,
                    timeout=300
                )

            if resp.status_code == 200:
                print(f"   ✓ 文档上传成功: {doc_file.name}")
            else:
                print(f"   ✗ 上传失败: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"   ✗ 上传失败: {e}")

    # 4. 查询
    print("\n4️⃣  执行查询...")
    try:
        resp = requests.post(
            f"{BASE_URL}/query/",
            json={
                "rag_id": rag_id,
                "question": "总结一下主要内容",
                "mode": "hybrid"
            },
            timeout=60
        )

        if resp.status_code == 200:
            result = resp.json()
            answer = result.get('answer', '')
            print(f"   ✓ 查询成功")
            print(f"   回答长度: {len(answer)} 字符")
            if len(answer) > 0:
                preview = answer[:150].replace('\n', ' ')
                print(f"   预览: {preview}...")
        else:
            print(f"   ✗ 查询失败: {resp.status_code}")
    except Exception as e:
        print(f"   ✗ 查询失败: {e}")

    # 5. 查看状态
    print("\n5️⃣  文档状态...")
    try:
        resp = requests.get(f"{BASE_URL}/documents/status/{rag_id}", timeout=10)
        if resp.status_code == 200:
            status = resp.json()
            print(f"   ✓ 总文档数: {status.get('total')}")
            print(f"   ✓ 已处理: {status.get('processed')}")
            print(f"   ✓ 待处理: {status.get('pending')}")
            print(f"   ✓ 失败: {status.get('failed')}")
    except Exception as e:
        print(f"   ✗ 获取状态失败: {e}")

    print("\n" + "="*60)
    print("✅ 快速测试完成")
    print("="*60 + "\n")

    # 询问是否清理
    cleanup = input("是否删除测试实例? (y/N): ").strip().lower()
    if cleanup == 'y':
        try:
            resp = requests.delete(f"{BASE_URL}/admin/rag_instances/{rag_id}", timeout=30)
            if resp.status_code == 200:
                print(f"✓ 实例已删除: {rag_id}\n")
            else:
                print(f"✗ 删除失败: {resp.status_code}\n")
        except Exception as e:
            print(f"✗ 删除失败: {e}\n")
    else:
        print(f"ℹ 保留实例: {rag_id}\n")

    return True


if __name__ == "__main__":
    success = test_quick()
    sys.exit(0 if success else 1)
