#!/usr/bin/env python3
"""
批量重新导入 uploaded_files 目录下的文件到知识库

用法:
    python3 reimport_files.py                          # 导入所有文件
    python3 reimport_files.py 56                       # 只导入 rag_id=56 的文件
    python3 reimport_files.py --dir /path/to/files     # 指定文件目录
    python3 reimport_files.py --api http://host:port   # 指定 API 地址
    python3 reimport_files.py --force                  # 强制模式：先删除已有文档再重新导入
"""
import os
import sys
import argparse
import requests
from pathlib import Path

# 默认配置
DEFAULT_UPLOADED_FILES_DIR = os.environ.get("UPLOADED_FILES_DIR", "./uploaded_files")
DEFAULT_API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def get_active_rag_ids(api_base_url):
    """
    获取当前使用队列中的所有 rag_id

    Returns:
        set: 活跃的 rag_id 集合，如果请求失败返回 None
    """
    try:
        response = requests.get(
            f"{api_base_url}/api/admin/rag_instances/list",
            timeout=30
        )
        if response.status_code == 200:
            instances = response.json()
            return {str(inst.get("rag_id")) for inst in instances}
        else:
            print(f"警告: 获取 RAG 实例列表失败 - {response.status_code}")
            return None
    except Exception as e:
        print(f"警告: 无法连接到 API 服务 - {str(e)}")
        return None


def get_existing_docs(rag_id, api_base_url):
    """
    获取指定 rag_id 的所有文档状态

    Returns:
        dict: {file_name: doc_id} 映射，如果失败返回空字典
    """
    try:
        response = requests.get(
            f"{api_base_url}/api/documents/doc_status/{rag_id}",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            docs = data.get("documents", [])
            # 构建 file_name -> doc_id 的映射
            return {doc.get("file_path", ""): doc.get("doc_id") for doc in docs if doc.get("doc_id")}
        else:
            return {}
    except Exception as e:
        print(f"    警告: 获取文档状态失败 - {str(e)}")
        return {}


def delete_document(rag_id, doc_id, api_base_url):
    """
    删除指定的文档

    Returns:
        bool: 是否删除成功
    """
    try:
        response = requests.delete(
            f"{api_base_url}/api/documents/delete/{rag_id}/{doc_id}",
            timeout=60
        )
        return response.status_code == 200
    except Exception as e:
        print(f"    警告: 删除文档失败 - {str(e)}")
        return False


def reimport_files(target_rag_id=None, files_dir=None, api_base_url=None, force=False):
    """
    重新导入文件

    Args:
        target_rag_id: 指定只导入某个 rag_id 的文件，None 表示导入所有
        files_dir: 文件目录路径
        api_base_url: API 基础地址
        force: 是否强制模式，先删除已有文档再重新导入
    """
    files_dir = files_dir or DEFAULT_UPLOADED_FILES_DIR
    api_base_url = api_base_url or DEFAULT_API_BASE_URL

    if not Path(files_dir).exists():
        print(f"错误: 目录不存在 - {files_dir}")
        return

    files = Path(files_dir).glob("*")

    # 按 rag_id 分组
    rag_files = {}
    for f in files:
        if f.is_file():
            # 文件名格式: {rag_id}_{filename}
            name = f.name
            if "_" in name:
                rag_id = name.split("_")[0]
                if target_rag_id is None or rag_id == str(target_rag_id):
                    if rag_id not in rag_files:
                        rag_files[rag_id] = []
                    rag_files[rag_id].append(f)

    print(f"找到 {sum(len(v) for v in rag_files.values())} 个文件，分布在 {len(rag_files)} 个知识库中")
    print()

    # 获取当前活跃的 RAG 实例
    print("正在检查使用队列中的 RAG 实例...")
    active_rag_ids = get_active_rag_ids(api_base_url)

    if active_rag_ids is None:
        print("无法获取使用队列，终止操作")
        return

    print(f"使用队列中有 {len(active_rag_ids)} 个实例: {sorted(active_rag_ids)}")
    print()

    skipped_count = 0
    imported_count = 0

    for rag_id, files_list in sorted(rag_files.items()):
        # 检查 rag_id 是否在使用队列中
        if rag_id not in active_rag_ids:
            print(f"=== RAG ID: {rag_id} - 跳过（不在使用队列中）===")
            skipped_count += len(files_list)
            print()
            continue

        print(f"=== RAG ID: {rag_id} ({len(files_list)} 个文件) ===")

        # 如果是强制模式，先获取已有文档列表
        existing_docs = {}
        if force:
            print(f"  [强制模式] 获取已有文档列表...")
            existing_docs = get_existing_docs(rag_id, api_base_url)
            if existing_docs:
                print(f"  [强制模式] 找到 {len(existing_docs)} 个已有文档")

        for file_path in files_list:
            print(f"  正在导入: {file_path.name}")

            # 强制模式：先删除已有的同名文档
            if force and file_path.name in existing_docs:
                doc_id = existing_docs[file_path.name]
                print(f"    [强制模式] 删除已有文档: {doc_id}")
                if delete_document(rag_id, doc_id, api_base_url):
                    print(f"    [强制模式] ✅ 删除成功")
                else:
                    print(f"    [强制模式] ⚠️ 删除失败，继续尝试上传")

            try:
                with open(file_path, "rb") as f:
                    files = {"file": (file_path.name, f)}
                    data = {"rag_id": rag_id}

                    response = requests.post(
                        f"{api_base_url}/api/documents/upload",
                        files=files,
                        data=data,
                        timeout=300
                    )

                    if response.status_code == 200:
                        print(f"    ✅ 成功")
                        imported_count += 1
                    else:
                        print(f"    ❌ 失败: {response.text[:100]}")

            except Exception as e:
                print(f"    ❌ 错误: {str(e)}")

        print()

    # 输出统计
    print("=" * 40)
    print(f"导入完成: {imported_count} 个文件成功")
    if skipped_count > 0:
        print(f"跳过: {skipped_count} 个文件（对应的知识库不在使用队列中）")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量重新导入文件到知识库")
    parser.add_argument("rag_id", nargs="?", help="指定只导入某个 rag_id 的文件")
    parser.add_argument("--dir", "-d", dest="files_dir", default=DEFAULT_UPLOADED_FILES_DIR,
                        help=f"文件目录路径 (默认: {DEFAULT_UPLOADED_FILES_DIR})")
    parser.add_argument("--api", "-a", dest="api_base_url", default=DEFAULT_API_BASE_URL,
                        help=f"API 基础地址 (默认: {DEFAULT_API_BASE_URL})")
    parser.add_argument("--force", "-f", action="store_true",
                        help="强制模式：先删除已有文档再重新导入")

    args = parser.parse_args()

    print(f"文件目录: {args.files_dir}")
    print(f"API 地址: {args.api_base_url}")
    if args.force:
        print("模式: 强制重新导入（会删除已有文档）")
    print()

    if args.rag_id:
        print(f"只导入 rag_id={args.rag_id} 的文件\n")
    else:
        print("导入所有文件\n")

    reimport_files(args.rag_id, args.files_dir, args.api_base_url, args.force)
