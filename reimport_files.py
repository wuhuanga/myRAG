#!/usr/bin/env python3
"""
批量重新导入 uploaded_files 目录下的文件到知识库

用法:
    python3 reimport_files.py                          # 导入所有文件
    python3 reimport_files.py 56                       # 只导入 rag_id=56 的文件
    python3 reimport_files.py --dir /path/to/files     # 指定文件目录
    python3 reimport_files.py --api http://host:port   # 指定 API 地址
"""
import os
import sys
import argparse
import requests
from pathlib import Path

# 默认配置
DEFAULT_UPLOADED_FILES_DIR = os.environ.get("UPLOADED_FILES_DIR", "./uploaded_files")
DEFAULT_API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

def reimport_files(target_rag_id=None, files_dir=None, api_base_url=None):
    """
    重新导入文件

    Args:
        target_rag_id: 指定只导入某个 rag_id 的文件，None 表示导入所有
        files_dir: 文件目录路径
        api_base_url: API 基础地址
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

    for rag_id, files_list in sorted(rag_files.items()):
        print(f"=== RAG ID: {rag_id} ({len(files_list)} 个文件) ===")

        for file_path in files_list:
            print(f"  正在导入: {file_path.name}")

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
                    else:
                        print(f"    ❌ 失败: {response.text[:100]}")

            except Exception as e:
                print(f"    ❌ 错误: {str(e)}")

        print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量重新导入文件到知识库")
    parser.add_argument("rag_id", nargs="?", help="指定只导入某个 rag_id 的文件")
    parser.add_argument("--dir", "-d", dest="files_dir", default=DEFAULT_UPLOADED_FILES_DIR,
                        help=f"文件目录路径 (默认: {DEFAULT_UPLOADED_FILES_DIR})")
    parser.add_argument("--api", "-a", dest="api_base_url", default=DEFAULT_API_BASE_URL,
                        help=f"API 基础地址 (默认: {DEFAULT_API_BASE_URL})")

    args = parser.parse_args()

    print(f"文件目录: {args.files_dir}")
    print(f"API 地址: {args.api_base_url}")
    print()

    if args.rag_id:
        print(f"只导入 rag_id={args.rag_id} 的文件\n")
    else:
        print("导入所有文件\n")

    reimport_files(args.rag_id, args.files_dir, args.api_base_url)
