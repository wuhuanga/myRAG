# -*- coding: utf-8 -*-
"""
文档操作路由
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException
import aiofiles

from ..dependencies import get_rag_manager
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
    rag_id: str,
    file: UploadFile = File(...),
    custom_id: Optional[str] = None
):
    """上传并处理文档"""
    manager = get_rag_manager()

    try:
        processor = manager.get_instance(rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        # 保存上传的文件
        file_path = UPLOAD_DIR / file.filename
        logger.info(f"正在保存文件: {file_path}")

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        logger.info(f"文件保存成功,开始处理...")

        # 插入到知识图谱
        processor.insert_document(str(file_path), custom_id)

        return {
            "status": "success",
            "message": f"文档 {file.filename} 已成功上传并处理",
            "file_path": str(file_path),
            "custom_id": custom_id,
            "rag_id": rag_id
        }

    except Exception as e:
        logger.error(f"文档上传处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


@router.post("/insert")
async def insert_document(request: InsertRequest):
    """直接插入文档内容"""
    manager = get_rag_manager()

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
        logger.info(f"插入文档内容,文件: {request.file_path}, 长度: {len(request.content)} 字符")

        # 插入文档
        if request.doc_id:
            processor.rag.insert(
                request.content,
                ids=[request.doc_id],
                file_paths=[request.file_path]
            )
        else:
            processor.rag.insert(request.content, file_paths=[request.file_path])

        return {
            "status": "success",
            "message": f"文档内容已成功插入(文件: {request.file_path})",
            "file_path": request.file_path,
            "doc_id": request.doc_id,
            "content_length": len(request.content),
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"文档插入失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档插入失败: {str(e)}")


@router.post("/batch_insert")
async def batch_insert_documents(request: BatchInsertRequest):
    """批量插入文档"""
    manager = get_rag_manager()

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

        logger.info(f"批量插入 {len(documents_data)} 个文档")

        # 批量插入
        processor.insert_documents_batch(documents_data)

        return {
            "status": "success",
            "message": f"成功批量插入 {len(documents_data)} 个文档",
            "count": len(documents_data),
            "files": [doc['file_path'] for doc in documents_data],
            "rag_id": request.rag_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量插入失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量插入失败: {str(e)}")


@router.get("/status/{rag_id}", response_model=DocumentStatusResponse)
async def get_documents_status(rag_id: str):
    """获取所有文档的处理状态统计"""
    manager = get_rag_manager()

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
        failed = status_counts.get('FAILED', 0)

        logger.info(f"文档状态统计: 总计={total}, 已处理={processed}, 待处理={pending}, 失败={failed}")

        return DocumentStatusResponse(
            total=total,
            processed=processed,
            pending=pending,
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
    manager = get_rag_manager()

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
        from lightrag.base import DocStatus

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
