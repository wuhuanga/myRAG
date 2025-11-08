# -*- coding: utf-8 -*-
"""
RAG 后端 API 服务 - 入口文件

此文件已重构为模块化架构。
请使用新的入口点运行服务。

新的运行方式：
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

或者使用此向后兼容的入口点：
    uvicorn backend_api:app --host 0.0.0.0 --port 8000 --reload
"""

# 导入新的模块化 API
from app.main import app

# 向后兼容：导出 app
__all__ = ["app"]

# 打印迁移提示
print("=" * 60)
print("注意：backend_api.py 已迁移到模块化架构")
print("建议使用新的入口点运行：")
print("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
print("")
print("API 结构变化：")
print("  旧：单实例，需要先调用 /api/init 初始化")
print("  新：多实例管理，支持动态创建/删除 RAG 实例")
print("")
print("主要端点变化：")
print("  /api/init → /api/admin/rag_instances/create")
print("  /api/health → /api/admin/health")
print("  /api/query → /api/query/ (需要 rag_id)")
print("  /api/documents/upload → /api/documents/upload (需要 rag_id)")
print("=" * 60)
