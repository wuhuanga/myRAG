# -*- coding: utf-8 -*-
"""
文档操作路由
"""
import logging
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import aiofiles

from ..dependencies_concurrent import get_concurrent_rag_manager
from ..models import (
    InsertRequest,
    BatchInsertRequest,
    DocumentStatusResponse,
    DocumentListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

# 上传文件目录
UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_document(
    rag_id: str = Form(...),
    file: UploadFile = File(...),
    custom_id: Optional[str] = Form(None)
):
    """上传并处理文档"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        start_time = time.time()
        logger.info(f"⏱️  [上传文档] 开始处理: {file.filename}")

        # 保存上传的文件（添加 rag_id 前缀避免文件名冲突）
        safe_filename = f"{rag_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        logger.info(f"⏱️  [上传文档] 正在保存文件: {file_path}")

        save_start = time.time()
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        save_time = time.time() - save_start

        logger.info(f"⏱️  [上传文档] 文件保存完成，耗时: {save_time:.2f}秒")

        # 插入到知识图谱
        insert_start = time.time()
        await processor.insert_document(str(file_path), custom_id)
        insert_time = time.time() - insert_start

        total_time = time.time() - start_time
        logger.info(f"⏱️  [上传文档] ✅ 完成! 总耗时: {total_time:.2f}秒 (保存: {save_time:.2f}秒, 插入: {insert_time:.2f}秒)")

        return {
            "status": "success",
            "message": f"文档 {file.filename} 已成功上传并处理",
            "file_path": str(file_path),
            "custom_id": custom_id,
            "rag_id": rag_id,
            "time_cost": {
                "total": round(total_time, 2),
                "save": round(save_time, 2),
                "insert": round(insert_time, 2)
            }
        }

    except Exception as e:
        logger.error(f"文档上传处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


@router.post("/insert")
async def insert_document(request: InsertRequest):
    """直接插入文档内容"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    # 验证文件路径/名称是否提供
    if not request.file_path:
        raise HTTPException(
            status_code=400,
            detail="必须提供 file_path 参数(文件路径或文件名称)"
        )

    try:
        start_time = time.time()
        content_length = len(request.content)
        logger.info(f"⏱️  [插入文档] 开始处理: {request.file_path}, 长度: {content_length} 字符")

        # 插入文档
        if request.doc_id:
            processor.rag.insert(
                request.content,
                ids=[request.doc_id],
                file_paths=[request.file_path]
            )
        else:
            processor.rag.insert(request.content, file_paths=[request.file_path])

        total_time = time.time() - start_time
        logger.info(f"⏱️  [插入文档] ✅ 完成! 耗时: {total_time:.2f}秒, 文件: {request.file_path}")

        return {
            "status": "success",
            "message": f"文档内容已成功插入(文件: {request.file_path})",
            "file_path": request.file_path,
            "doc_id": request.doc_id,
            "content_length": content_length,
            "rag_id": request.rag_id,
            "time_cost": round(total_time, 2)
        }

    except Exception as e:
        logger.error(f"文档插入失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档插入失败: {str(e)}")


@router.post("/batch_insert")
async def batch_insert_documents(request: BatchInsertRequest):
    """批量插入文档"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(request.rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        documents_data = []
        for idx, doc in enumerate(request.documents):
            # 验证每个文档都有文件路径
            if 'file_path' not in doc or not doc['file_path']:
                raise HTTPException(
                    status_code=400,
                    detail=f"文档 {idx + 1} 缺少 file_path 参数(文件路径或文件名称)"
                )

            documents_data.append({
                'content': doc['content'],
                'file_path': doc['file_path'],
                'doc_id': doc.get('doc_id')
            })

        start_time = time.time()
        doc_count = len(documents_data)
        total_chars = sum(len(doc['content']) for doc in documents_data)
        logger.info(f"⏱️  [批量插入] 开始处理 {doc_count} 个文档, 总字符数: {total_chars}")

        # 批量插入
        await processor.insert_documents_batch(documents_data)

        total_time = time.time() - start_time
        avg_time = total_time / doc_count if doc_count > 0 else 0
        logger.info(f"⏱️  [批量插入] ✅ 完成! 总耗时: {total_time:.2f}秒, 平均: {avg_time:.2f}秒/文档")

        return {
            "status": "success",
            "message": f"成功批量插入 {doc_count} 个文档",
            "count": doc_count,
            "files": [doc['file_path'] for doc in documents_data],
            "rag_id": request.rag_id,
            "time_cost": {
                "total": round(total_time, 2),
                "average_per_doc": round(avg_time, 2)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量插入失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量插入失败: {str(e)}")


@router.get("/status/{rag_id}", response_model=DocumentStatusResponse)
async def get_documents_status(rag_id: str):
    """获取所有文档的处理状态统计"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        logger.info("获取文档处理状态...")
        status_counts = await processor.rag.get_processing_status()

        total = sum(status_counts.values())
        processed = status_counts.get('PROCESSED', 0)
        pending = status_counts.get('PENDING', 0)
        processing = status_counts.get('PROCESSING', 0)
        failed = status_counts.get('FAILED', 0)

        logger.info(f"文档状态统计: 总计={total}, 已处理={processed}, 待处理={pending}, 处理中={processing}, 失败={failed}")

        return DocumentStatusResponse(
            total=total,
            processed=processed,
            pending=pending,
            processing=processing,
            failed=failed,
            status_counts=status_counts
        )
    except Exception as e:
        logger.error(f"获取文档状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档状态失败: {str(e)}")


@router.get("/list/{rag_id}/{status}")
async def get_documents_by_status(rag_id: str, status: str):
    """根据状态获取文档列表

    参数:
        rag_id: RAG 实例 ID
        status: PROCESSED, PENDING, 或 FAILED
    """
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    # 验证状态参数
    valid_statuses = ['PROCESSED', 'PENDING', 'FAILED']
    status_upper = status.upper()
    if status_upper not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"无效的状态: {status}. 有效值: {', '.join(valid_statuses)}"
        )

    try:
        from xwrag.base import DocStatus

        logger.info(f"获取状态为 {status_upper} 的文档列表...")

        # 将字符串状态转换为 DocStatus 枚举
        doc_status = DocStatus[status_upper]

        # 获取文档字典 {doc_id: DocProcessingStatus}
        docs_dict = await processor.rag.get_docs_by_status(doc_status)

        # 转换为可序列化的格式
        documents = []
        for doc_id, status_info in docs_dict.items():
            # status_info 是 DocProcessingStatus 对象
            file_name = status_info.file_path if hasattr(status_info, 'file_path') else 'N/A'

            # 获取其他可能的属性
            created_at = getattr(status_info, 'created_at', None)
            updated_at = getattr(status_info, 'updated_at', None)
            error_msg = getattr(status_info, 'error_message', None)

            doc_info = {
                "doc_id": doc_id,
                "file_name": file_name,
                "created_at": str(created_at) if created_at else None,
                "updated_at": str(updated_at) if updated_at else None,
                "error_message": error_msg,
                "status": status_upper
            }
            documents.append(doc_info)

        logger.info(f"找到 {len(documents)} 个状态为 {status_upper} 的文档")

        return DocumentListResponse(
            status=status_upper,
            count=len(documents),
            documents=documents
        )
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.delete("/delete/{rag_id}/{doc_id}")
async def delete_document(rag_id: str, doc_id: str):
    """删除指定文档及其所有关联数据

    Args:
        rag_id: RAG 实例 ID
        doc_id: 文档 ID

    Returns:
        删除结果，包括状态和消息
    """
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        logger.info(f"正在删除文档: {doc_id} (RAG ID: {rag_id})")

        # 调用 xwrag 的删除方法
        result = await processor.rag.adelete_by_doc_id(doc_id)

        # 根据删除结果返回相应的 HTTP 状态码
        if result.status == "success":
            logger.info(f"文档删除成功: {doc_id}")
            return {
                "status": "success",
                "doc_id": doc_id,
                "file_path": result.file_path,
                "message": result.message,
                "rag_id": rag_id
            }
        elif result.status == "not_found":
            logger.warning(f"文档未找到: {doc_id}")
            raise HTTPException(status_code=404, detail=result.message)
        else:  # failure
            logger.error(f"文档删除失败: {doc_id} - {result.message}")
            raise HTTPException(status_code=500, detail=result.message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")
