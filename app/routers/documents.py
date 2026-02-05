# -*- coding: utf-8 -*-
"""
文档操作路由
"""
import logging
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
import aiofiles
import asyncio

from ..dependencies_concurrent import get_concurrent_rag_manager
from ..models import (
    InsertRequest,
    BatchInsertRequest,
    DocumentStatusResponse,
    DocumentListResponse,
    FullDocumentStatusResponse,
    DocumentDetailItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

# 上传文件目录
UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)


# 后台处理函数
async def _process_document_background(rag_id: str, file_path: str, custom_id: Optional[str] = None):
    """后台处理文档"""
    manager = get_concurrent_rag_manager()
    try:
        processor = manager.get_instance(rag_id)
        start_time = time.time()
        logger.info(f"🔄 [后台任务] 开始处理文档: {file_path}")

        await processor.insert_document(file_path, custom_id)

        total_time = time.time() - start_time
        logger.info(f"✅ [后台任务] 文档处理完成: {file_path}, 耗时: {total_time:.2f}秒")
    except Exception as e:
        logger.error(f"❌ [后台任务] 文档处理失败: {file_path}, 错误: {str(e)}")


async def _process_content_background(rag_id: str, content: str, file_path: str, doc_id: Optional[str] = None):
    """后台处理文档内容"""
    manager = get_concurrent_rag_manager()
    try:
        processor = manager.get_instance(rag_id)
        start_time = time.time()
        logger.info(f"🔄 [后台任务] 开始处理内容: {file_path}, 长度: {len(content)} 字符")

        if doc_id:
            processor.rag.insert(content, ids=[doc_id], file_paths=[file_path])
        else:
            processor.rag.insert(content, file_paths=[file_path])

        total_time = time.time() - start_time
        logger.info(f"✅ [后台任务] 内容处理完成: {file_path}, 耗时: {total_time:.2f}秒")
    except Exception as e:
        logger.error(f"❌ [后台任务] 内容处理失败: {file_path}, 错误: {str(e)}")


async def _process_batch_background(rag_id: str, documents_data: list):
    """后台批量处理文档"""
    manager = get_concurrent_rag_manager()
    try:
        processor = manager.get_instance(rag_id)
        start_time = time.time()
        doc_count = len(documents_data)
        logger.info(f"🔄 [后台批量任务] 开始处理 {doc_count} 个文档")

        await processor.insert_documents_batch(documents_data)

        total_time = time.time() - start_time
        avg_time = total_time / doc_count if doc_count > 0 else 0
        logger.info(f"✅ [后台批量任务] 批量处理完成: {doc_count} 个文档, 总耗时: {total_time:.2f}秒, 平均: {avg_time:.2f}秒/文档")
    except Exception as e:
        logger.error(f"❌ [后台批量任务] 批量处理失败: {str(e)}")


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    rag_id: str = Form(...),
    file: UploadFile = File(...),
    custom_id: Optional[str] = Form(None)
):
    """上传文档并后台处理"""
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        start_time = time.time()
        logger.info(f"📤 [上传文档] 接收文件: {file.filename}")

        # 保存上传的文件（添加 rag_id 前缀避免文件名冲突）
        safe_filename = f"{rag_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        save_time = time.time() - start_time
        logger.info(f"💾 [上传文档] 文件已保存: {file_path}, 耗时: {save_time:.2f}秒")

        # 添加后台任务处理文档
        background_tasks.add_task(_process_document_background, rag_id, str(file_path), custom_id)

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
async def insert_document(background_tasks: BackgroundTasks, request: InsertRequest):
    """直接插入文档内容（后台处理）"""
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
        content_length = len(request.content)
        logger.info(f"📝 [插入文档] 接收内容: {request.file_path}, 长度: {content_length} 字符")

        # 添加后台任务处理内容
        background_tasks.add_task(
            _process_content_background,
            request.rag_id,
            request.content,
            request.file_path,
            request.doc_id
        )

        return {
            "status": "success",
            "message": f"文档内容已成功插入(文件: {request.file_path})",
            "file_path": request.file_path,
            "doc_id": request.doc_id,
            "content_length": content_length,
            "rag_id": request.rag_id
        }

    except Exception as e:
        logger.error(f"文档插入失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档插入失败: {str(e)}")


@router.post("/batch_insert")
async def batch_insert_documents(background_tasks: BackgroundTasks, request: BatchInsertRequest):
    """批量插入文档（后台处理）"""
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

        doc_count = len(documents_data)
        total_chars = sum(len(doc['content']) for doc in documents_data)
        logger.info(f"📦 [批量插入] 接收 {doc_count} 个文档, 总字符数: {total_chars}")

        # 添加后台批量处理任务
        background_tasks.add_task(_process_batch_background, request.rag_id, documents_data)

        return {
            "status": "success",
            "message": f"成功批量插入 {doc_count} 个文档",
            "count": doc_count,
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
        processed = status_counts.get('processed', 0)
        pending = status_counts.get('pending', 0)
        processing = status_counts.get('processing', 0)
        failed = status_counts.get('failed', 0)

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


@router.get("/doc_status/{rag_id}", response_model=FullDocumentStatusResponse)
async def get_full_document_status(rag_id: str):
    """获取全量文档状态列表

    该接口专门用于同步数据，返回指定 rag_id 下所有文档的最新状态。
    字段命名与本地 KV 存储结构完全对齐。

    参数:
        rag_id: RAG 实例 ID

    返回:
        - rag_id: 知识库 ID
        - total: 文档总数
        - doc_status_summary: 状态统计 (PROCESSED, PENDING, PROCESSING, FAILED)
        - doc_status_list: 文档详细列表
    """
    manager = get_concurrent_rag_manager()

    try:
        processor = manager.get_instance(rag_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if processor.rag is None:
        raise HTTPException(status_code=400, detail="RAG 系统未初始化")

    try:
        logger.info(f"获取知识库 {rag_id} 的全量文档状态...")

        # 1. 获取状态统计
        status_counts = await processor.rag.get_processing_status()

        # 2. 获取所有文档的详细信息
        all_docs = await processor.rag.doc_status.get_all()

        # 3. 构建文档列表
        doc_status_list = []
        for doc_id, doc_data in all_docs.items():
            # 处理不同的数据结构（可能是 dict 或 DocProcessingStatus 对象）
            if isinstance(doc_data, dict):
                status = doc_data.get('status', 'unknown')
                file_path = doc_data.get('file_path', 'N/A')
                created_at = doc_data.get('created_at', '')
                updated_at = doc_data.get('updated_at', '')
                error_msg = doc_data.get('error_msg', None)
            else:
                # DocProcessingStatus 对象
                status = doc_data.status if hasattr(doc_data, 'status') else 'unknown'
                file_path = doc_data.file_path if hasattr(doc_data, 'file_path') else 'N/A'
                created_at = doc_data.created_at if hasattr(doc_data, 'created_at') else ''
                updated_at = doc_data.updated_at if hasattr(doc_data, 'updated_at') else ''
                error_msg = doc_data.error_message if hasattr(doc_data, 'error_message') else None

            # 提取文件名（从路径中提取）
            file_name = file_path.split('/')[-1] if file_path else 'N/A'

            doc_item = DocumentDetailItem(
                doc_id=doc_id,
                file_name=file_name,
                status=status if isinstance(status, str) else status.value,
                created_at=str(created_at) if created_at else '',
                updated_at=str(updated_at) if updated_at else '',
                error_message=error_msg
            )
            doc_status_list.append(doc_item)

        # 4. 构建状态摘要（使用大写键名，与示例保持一致）
        doc_status_summary = {
            'PROCESSED': status_counts.get('processed', 0),
            'PENDING': status_counts.get('pending', 0),
            'PROCESSING': status_counts.get('processing', 0),
            'FAILED': status_counts.get('failed', 0)
        }

        total = len(all_docs)

        logger.info(f"知识库 {rag_id} 共有 {total} 个文档")

        return FullDocumentStatusResponse(
            rag_id=rag_id,
            total=total,
            doc_status_summary=doc_status_summary,
            doc_status_list=doc_status_list
        )

    except Exception as e:
        logger.error(f"获取全量文档状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取全量文档状态失败: {str(e)}")


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
            logger.info(f"文档数据库内容删除成功: {doc_id}")

            # 尝试删除原始上传的文件
            file_deleted = False
            file_delete_message = ""
            if result.file_path:
                try:
                    # 构造上传文件的完整路径 (格式: {rag_id}_{filename})
                    safe_filename = f"{rag_id}_{result.file_path}"
                    upload_file_path = UPLOAD_DIR / safe_filename

                    if upload_file_path.exists():
                        upload_file_path.unlink()
                        file_deleted = True
                        file_delete_message = f"原始文件已删除: {safe_filename}"
                        logger.info(f"✅ {file_delete_message}")
                    else:
                        file_delete_message = f"原始文件不存在（可能已被手动删除）: {safe_filename}"
                        logger.warning(file_delete_message)
                except Exception as file_error:
                    file_delete_message = f"删除原始文件失败: {str(file_error)}"
                    logger.error(f"⚠️ {file_delete_message}")
                    # 不抛出异常，因为数据库内容已成功删除

            return {
                "status": "success",
                "doc_id": doc_id,
                "file_path": result.file_path,
                "message": result.message,
                "rag_id": rag_id,
                "file_deleted": file_deleted,
                "file_delete_message": file_delete_message
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
