# -*- coding: utf-8 -*-
"""
RAG 后端 API 服务 - 主应用入口

依赖安装:
pip install fastapi uvicorn python-multipart aiofiles

运行方式:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
import logging
from typing import List
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .routers import documents, graph, query
from .internal import admin

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 应用
app = FastAPI(
    title="RAG Backend API",
    description="Modular RAG backend with multi-instance support",
    version="3.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(admin.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(query.router, prefix="/api")


# ==================== 根路由 ====================

@app.get("/")
async def root():
    """根路由,返回 API 信息"""
    return {
        "service": "RAG Backend API",
        "version": "3.0.0",
        "status": "running",
        "description": "模块化 RAG 后端,支持多实例管理",
        "endpoints": {
            "admin": [
                "/api/admin/health - 健康检查",
                "/api/admin/rag_instances/create - 创建 RAG 实例",
                "/api/admin/rag_instances/list - 列出所有 RAG 实例",
                "/api/admin/rag_instances/{rag_id} - 获取/删除 RAG 实例",
                "/api/admin/ucd/init - 初始化 UCD 建模器"
            ],
            "documents": [
                "/api/documents/upload - 上传文档",
                "/api/documents/insert - 插入文档内容",
                "/api/documents/batch_insert - 批量插入文档",
                "/api/documents/status/{rag_id} - 获取文档状态",
                "/api/documents/list/{rag_id}/{status} - 获取指定状态的文档列表"
            ],
            "query": [
                "/api/query/ - 查询知识库",
                "/api/query/ucd - UCD 建模查询",
                "/api/query/clear_cache - 清除缓存"
            ],
            "graph": [
                "/api/graph/entities/create - 创建实体",
                "/api/graph/entities/edit - 编辑实体",
                "/api/graph/entities/delete - 删除实体",
                "/api/graph/entities/info - 获取实体信息",
                "/api/graph/entities/merge - 合并实体",
                "/api/graph/relations/create - 创建关系",
                "/api/graph/relations/edit - 编辑关系",
                "/api/graph/relations/delete - 删除关系",
                "/api/graph/relations/info - 获取关系信息",
                "/api/graph/export - 导出数据"
            ],
            "websocket": [
                "/ws - WebSocket 连接"
            ]
        }
    }


# ==================== WebSocket 支持 ====================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket 连接建立,当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket 断开连接,剩余连接数: {len(self.active_connections)}")

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点,用于实时通信"""
    from .dependencies_concurrent import get_concurrent_rag_manager, get_ucd_builder

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            rag_manager = get_concurrent_rag_manager()

            if data["type"] == "query":
                rag_id = data.get("rag_id")
                if not rag_id:
                    await manager.send_message({
                        "type": "error",
                        "message": "必须指定 rag_id"
                    }, websocket)
                    continue

                try:
                    processor = rag_manager.get_instance(rag_id)
                except ValueError as e:
                    await manager.send_message({
                        "type": "error",
                        "message": str(e)
                    }, websocket)
                    continue

                try:
                    question = data["question"]
                    mode = data.get("mode", "hybrid")

                    await manager.send_message({
                        "type": "status",
                        "message": "正在查询..."
                    }, websocket)

                    context = processor.query(question, mode=mode)

                    await manager.send_message({
                        "type": "answer",
                        "rag_id": rag_id,
                        "question": question,
                        "context": context,
                        "mode": mode
                    }, websocket)

                except Exception as e:
                    await manager.send_message({
                        "type": "error",
                        "message": str(e)
                    }, websocket)

            elif data["type"] == "entity_operation":
                rag_id = data.get("rag_id")
                if not rag_id:
                    await manager.send_message({
                        "type": "error",
                        "message": "必须指定 rag_id"
                    }, websocket)
                    continue

                try:
                    processor = rag_manager.get_instance(rag_id)
                except ValueError as e:
                    await manager.send_message({
                        "type": "error",
                        "message": str(e)
                    }, websocket)
                    continue

                # 处理实体相关操作
                operation = data.get("operation")

                if operation == "create":
                    entity_name = data.get("entity_name")
                    entity_data = data.get("entity_data", {})
                    result = await processor.rag.acreate_entity(entity_name, entity_data)

                    await manager.send_message({
                        "type": "entity_created",
                        "rag_id": rag_id,
                        "result": result
                    }, websocket)

                elif operation == "delete":
                    entity_name = data.get("entity_name")
                    result = await processor.rag.adelete_by_entity(entity_name)

                    await manager.send_message({
                        "type": "entity_deleted",
                        "rag_id": rag_id,
                        "result": {"status": result.status, "message": result.message}
                    }, websocket)

            elif data["type"] == "query_ucd":
                rag_id = data.get("rag_id")
                if not rag_id:
                    await manager.send_message({
                        "type": "error",
                        "message": "必须指定 rag_id"
                    }, websocket)
                    continue

                try:
                    processor = rag_manager.get_instance(rag_id)
                except ValueError as e:
                    await manager.send_message({
                        "type": "error",
                        "message": str(e)
                    }, websocket)
                    continue

                ucd_builder = get_ucd_builder()
                if ucd_builder is None:
                    await manager.send_message({
                        "type": "error",
                        "message": "UCD 建模器未初始化"
                    }, websocket)
                    continue

                try:
                    question = data["question"]
                    mode = data.get("mode", "hybrid")
                    out_json = data.get("out_json", "output_uc.json")

                    await manager.send_message({
                        "type": "status",
                        "message": "正在检索知识..."
                    }, websocket)

                    context = processor.query(question, mode=mode)

                    await manager.send_message({
                        "type": "status",
                        "message": "正在进行 UCD 建模..."
                    }, websocket)

                    ucd_result = ucd_builder.test_generate(
                        question=question,
                        chunks=context,
                        out_json=out_json
                    )

                    await manager.send_message({
                        "type": "ucd_result",
                        "rag_id": rag_id,
                        "question": question,
                        "context": context,
                        "ucd_model": ucd_result,
                        "output_file": out_json
                    }, websocket)

                except Exception as e:
                    await manager.send_message({
                        "type": "error",
                        "message": str(e)
                    }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
