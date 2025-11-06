#!/usr/bin/env python3
"""
简单测试脚本 - 不需要前端，直接测试 API
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_api():
    print("=" * 60)
    print("lightrag API 简单测试")
    print("=" * 60)
    print()
    
    # 1. 测试连接
    print("1️⃣  测试 API 连接...")
    try:
        response = requests.get(f"{API_BASE}/api/status")
        print(f"✅ 连接成功！")
        print(f"   状态: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    print()
    
    # 2. 初始化系统
    print("2️⃣  初始化 RAG 系统...")
    print("   (这可能需要几分钟，请耐心等待...)")
    
    working_dir = input("请输入工作目录 (默认 ./test_index): ").strip()
    if not working_dir:
        working_dir = "./test_index"
    
    try:
        response = requests.post(
            f"{API_BASE}/api/initialize",
            json={"working_dir": working_dir},
            timeout=300  # 5分钟超时
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 初始化成功！")
            print(f"   工作目录: {data['working_dir']}")
            print(f"   LLM 模型: {data['config']['llm_model']}")
            print(f"   Embedding 模型: {data['config']['embedding_model']}")
            print(f"   Embedding 维度: {data['config']['embedding_dim']}")
        else:
            print(f"❌ 初始化失败: {response.text}")
            return
            
    except requests.exceptions.Timeout:
        print("⏱️  请求超时，但初始化可能仍在进行中...")
        print("   请稍后检查状态")
        return
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    print()
    
    # 3. 测试查询
    print("3️⃣  测试查询功能...")
    
    question = input("请输入测试问题 (默认: 你好): ").strip()
    if not question:
        question = "你好"
    
    try:
        response = requests.post(
            f"{API_BASE}/api/query",
            json={
                "question": question,
                "mode": "hybrid"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 查询成功！")
            print(f"   问题: {data['question']}")
            print(f"   回答: {data['answer']}")
            print(f"   模式: {data['mode']}")
        else:
            print(f"❌ 查询失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    
    print()
    print("=" * 60)
    print("测试完成！")
    print()
    print("💡 提示:")
    print("   - 如果初始化成功，你可以访问 http://localhost:8000 使用 Web 界面")
    print("   - API 文档: http://localhost:8000/docs")
    print("=" * 60)

if __name__ == "__main__":
    test_api()