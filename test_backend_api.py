#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 后端 API 全面测试脚本

测试内容：
1. 健康检查
2. 创建两个 RAG 实例
3. 上传文档（同步）
4. 查询文档状态
5. 执行查询
6. 并发测试
7. 清理资源
"""

import requests
import time
import json
import sys
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


class Colors:
    """终端颜色输出"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class APITester:
    """API 测试类"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.test_results = []

    def log(self, message: str, level: str = "INFO"):
        """输出日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "INFO": Colors.OKBLUE,
            "SUCCESS": Colors.OKGREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL,
            "HEADER": Colors.HEADER
        }.get(level, Colors.ENDC)

        print(f"{color}[{timestamp}] [{level}] {message}{Colors.ENDC}")

    def log_separator(self, title: str = ""):
        """输出分隔线"""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
        if title:
            print(f"{Colors.BOLD}{Colors.HEADER}{title.center(80)}{Colors.ENDC}")
            print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

    def record_result(self, test_name: str, success: bool, duration: float, details: str = ""):
        """记录测试结果"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "duration": duration,
            "details": details
        })

    def print_summary(self):
        """打印测试摘要"""
        self.log_separator("测试摘要")

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed

        print(f"{Colors.BOLD}总测试数: {total}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ 通过: {passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}✗ 失败: {failed}{Colors.ENDC}")
        print()

        # 打印详细结果
        for result in self.test_results:
            status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if result["success"] else f"{Colors.FAIL}✗{Colors.ENDC}"
            duration = f"{result['duration']:.2f}s"
            print(f"{status} {result['test']:<50} {duration:>10}")
            if result["details"]:
                print(f"  {Colors.WARNING}{result['details']}{Colors.ENDC}")

        print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

    def test_health_check(self):
        """测试健康检查"""
        self.log_separator("测试 1: 健康检查")
        start = time.time()

        try:
            response = self.session.get(f"{self.api_url}/admin/health", timeout=10)
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                self.log(f"服务状态: {data.get('status')}", "SUCCESS")
                self.log(f"RAG 实例数: {data.get('rag_instances_count')}", "INFO")
                self.log(f"UCD 初始化: {data.get('ucd_initialized')}", "INFO")
                self.log(f"响应时间: {duration:.2f}s", "INFO")
                self.record_result("健康检查", True, duration)
                return True
            else:
                self.log(f"健康检查失败: {response.status_code} - {response.text}", "ERROR")
                self.record_result("健康检查", False, duration, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            duration = time.time() - start
            self.log(f"健康检查异常: {str(e)}", "ERROR")
            self.record_result("健康检查", False, duration, str(e))
            return False

    def create_rag_instance(self, rag_id: str, workspace: str, description: str = "") -> bool:
        """创建 RAG 实例"""
        self.log(f"创建 RAG 实例: {rag_id} (workspace: {workspace})", "INFO")
        start = time.time()

        try:
            payload = {
                "rag_id": rag_id,
                "workspace": workspace,
                "description": description,
                "working_dir": "./rag_storage"
            }

            response = self.session.post(
                f"{self.api_url}/admin/rag_instances/create",
                json=payload,
                timeout=30
            )
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                self.log(f"✓ 实例创建成功: {rag_id}", "SUCCESS")
                self.log(f"  工作目录: {data.get('working_dir')}", "INFO")
                self.log(f"  LLM 模型: {data.get('llm_model')}", "INFO")
                self.log(f"  Embedding 模型: {data.get('embedding_model')}", "INFO")
                self.log(f"  耗时: {duration:.2f}s", "INFO")
                self.record_result(f"创建实例 - {rag_id}", True, duration)
                return True
            else:
                self.log(f"✗ 创建实例失败: {response.status_code} - {response.text}", "ERROR")
                self.record_result(f"创建实例 - {rag_id}", False, duration, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            duration = time.time() - start
            self.log(f"✗ 创建实例异常: {str(e)}", "ERROR")
            self.record_result(f"创建实例 - {rag_id}", False, duration, str(e))
            return False

    def list_rag_instances(self) -> List[Dict]:
        """列出所有 RAG 实例"""
        self.log("获取 RAG 实例列表", "INFO")
        start = time.time()

        try:
            response = self.session.get(f"{self.api_url}/admin/rag_instances/list", timeout=10)
            duration = time.time() - start

            if response.status_code == 200:
                instances = response.json()
                self.log(f"✓ 找到 {len(instances)} 个实例", "SUCCESS")
                for inst in instances:
                    self.log(f"  - {inst.get('rag_id')}: {inst.get('description', 'N/A')}", "INFO")
                self.record_result("列出实例", True, duration)
                return instances
            else:
                self.log(f"✗ 获取实例列表失败: {response.status_code}", "ERROR")
                self.record_result("列出实例", False, duration, f"HTTP {response.status_code}")
                return []

        except Exception as e:
            duration = time.time() - start
            self.log(f"✗ 获取实例列表异常: {str(e)}", "ERROR")
            self.record_result("列出实例", False, duration, str(e))
            return []

    def upload_document(self, rag_id: str, file_path: str, custom_id: str = None) -> bool:
        """上传文档"""
        file_path_obj = Path(file_path)
        self.log(f"上传文档: {file_path_obj.name} -> {rag_id}", "INFO")
        start = time.time()

        try:
            if not file_path_obj.exists():
                self.log(f"✗ 文件不存在: {file_path}", "ERROR")
                self.record_result(f"上传文档 - {file_path_obj.name}", False, 0, "文件不存在")
                return False

            # 准备文件和表单数据
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_path_obj.name, f, 'application/octet-stream')
                }
                data = {
                    'rag_id': rag_id
                }
                if custom_id:
                    data['custom_id'] = custom_id

                response = self.session.post(
                    f"{self.api_url}/documents/upload",
                    files=files,
                    data=data,
                    timeout=300  # 5分钟超时，文档处理可能较慢
                )

            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                self.log(f"✓ 文档上传成功: {file_path_obj.name}", "SUCCESS")
                self.log(f"  状态: {data.get('status')}", "INFO")
                self.log(f"  消息: {data.get('message')}", "INFO")
                self.log(f"  耗时: {duration:.2f}s", "INFO")
                self.record_result(f"上传文档 - {file_path_obj.name}", True, duration)
                return True
            else:
                self.log(f"✗ 文档上传失败: {response.status_code} - {response.text}", "ERROR")
                self.record_result(f"上传文档 - {file_path_obj.name}", False, duration, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            duration = time.time() - start
            self.log(f"✗ 文档上传异常: {str(e)}", "ERROR")
            self.record_result(f"上传文档 - {file_path_obj.name}", False, duration, str(e))
            return False

    def get_document_status(self, rag_id: str) -> Dict:
        """获取文档状态"""
        self.log(f"获取文档状态: {rag_id}", "INFO")
        start = time.time()

        try:
            response = self.session.get(f"{self.api_url}/documents/status/{rag_id}", timeout=10)
            duration = time.time() - start

            if response.status_code == 200:
                status = response.json()
                self.log(f"✓ 文档状态获取成功", "SUCCESS")
                self.log(f"  总数: {status.get('total')}", "INFO")
                self.log(f"  已处理: {status.get('processed')}", "INFO")
                self.log(f"  待处理: {status.get('pending')}", "INFO")
                self.log(f"  失败: {status.get('failed')}", "INFO")
                self.record_result(f"文档状态 - {rag_id}", True, duration)
                return status
            else:
                self.log(f"✗ 获取文档状态失败: {response.status_code}", "ERROR")
                self.record_result(f"文档状态 - {rag_id}", False, duration, f"HTTP {response.status_code}")
                return {}

        except Exception as e:
            duration = time.time() - start
            self.log(f"✗ 获取文档状态异常: {str(e)}", "ERROR")
            self.record_result(f"文档状态 - {rag_id}", False, duration, str(e))
            return {}

    def query_knowledge(self, rag_id: str, question: str, mode: str = "hybrid") -> Dict:
        """查询知识库"""
        self.log(f"查询知识库: {question[:50]}...", "INFO")
        start = time.time()

        try:
            payload = {
                "rag_id": rag_id,
                "question": question,
                "mode": mode,
                "only_need_context": False
            }

            response = self.session.post(
                f"{self.api_url}/query/",
                json=payload,
                timeout=60
            )
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                self.log(f"✓ 查询成功", "SUCCESS")
                self.log(f"  问题: {question}", "INFO")
                self.log(f"  模式: {mode}", "INFO")
                self.log(f"  回答长度: {len(answer)} 字符", "INFO")
                self.log(f"  耗时: {duration:.2f}s", "INFO")
                if len(answer) > 0:
                    preview = answer[:200].replace('\n', ' ')
                    self.log(f"  回答预览: {preview}...", "INFO")
                self.record_result(f"查询 - {rag_id}", True, duration)
                return data
            else:
                self.log(f"✗ 查询失败: {response.status_code} - {response.text}", "ERROR")
                self.record_result(f"查询 - {rag_id}", False, duration, f"HTTP {response.status_code}")
                return {}

        except Exception as e:
            duration = time.time() - start
            self.log(f"✗ 查询异常: {str(e)}", "ERROR")
            self.record_result(f"查询 - {rag_id}", False, duration, str(e))
            return {}

    def delete_rag_instance(self, rag_id: str) -> bool:
        """删除 RAG 实例"""
        self.log(f"删除 RAG 实例: {rag_id}", "INFO")
        start = time.time()

        try:
            response = self.session.delete(
                f"{self.api_url}/admin/rag_instances/{rag_id}",
                timeout=30
            )
            duration = time.time() - start

            if response.status_code == 200:
                self.log(f"✓ 实例删除成功: {rag_id}", "SUCCESS")
                self.record_result(f"删除实例 - {rag_id}", True, duration)
                return True
            else:
                self.log(f"✗ 删除实例失败: {response.status_code}", "ERROR")
                self.record_result(f"删除实例 - {rag_id}", False, duration, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            duration = time.time() - start
            self.log(f"✗ 删除实例异常: {str(e)}", "ERROR")
            self.record_result(f"删除实例 - {rag_id}", False, duration, str(e))
            return False

    def concurrent_upload_test(self, rag_id: str, file_paths: List[str]):
        """并发上传测试"""
        self.log_separator("并发上传测试")
        self.log(f"并发上传 {len(file_paths)} 个文件到 {rag_id}", "INFO")
        start = time.time()

        def upload_file(file_path):
            return self.upload_document(rag_id, file_path)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(upload_file, fp): fp for fp in file_paths}

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    self.log(f"✗ 并发上传失败 {file_path}: {str(e)}", "ERROR")

        duration = time.time() - start
        self.log(f"并发上传完成，总耗时: {duration:.2f}s", "SUCCESS")

    def concurrent_query_test(self, rag_id: str, questions: List[str]):
        """并发查询测试"""
        self.log_separator("并发查询测试")
        self.log(f"并发查询 {len(questions)} 个问题", "INFO")
        start = time.time()

        def query_single(question):
            return self.query_knowledge(rag_id, question)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(query_single, q): q for q in questions}

            results = []
            for future in as_completed(futures):
                question = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.log(f"✗ 并发查询失败 {question}: {str(e)}", "ERROR")

        duration = time.time() - start
        self.log(f"并发查询完成，总耗时: {duration:.2f}s", "SUCCESS")
        self.log(f"成功查询数: {len(results)}/{len(questions)}", "INFO")


def main():
    """主测试流程"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("RAG 后端 API 全面测试")
    print("=" * 80)
    print(f"{Colors.ENDC}\n")

    # 配置
    BASE_URL = "http://localhost:8000"

    # 文件路径配置
    DOC_DIR = Path("/root/workplace/lightrag/LightRAG1/docx")

    INSTANCE_1_ID = "satellite_project"
    INSTANCE_1_FILES = [DOC_DIR / "卫星工程.docx"]

    INSTANCE_2_ID = "tender_docs"
    INSTANCE_2_FILES = [
        DOC_DIR / "子标书01.docx",
        DOC_DIR / "子标书02.docx"
    ]

    # 初始化测试器
    tester = APITester(BASE_URL)

    try:
        # ==================== 第1步：健康检查 ====================
        if not tester.test_health_check():
            tester.log("健康检查失败，请确保后端服务正在运行", "ERROR")
            tester.log(f"命令：python -m uvicorn app.main:app --host 0.0.0.0 --port 8000", "INFO")
            sys.exit(1)

        # ==================== 第2步：创建 RAG 实例 ====================
        tester.log_separator("测试 2: 创建 RAG 实例")

        # 创建实例1：卫星工程
        success1 = tester.create_rag_instance(
            rag_id=INSTANCE_1_ID,
            workspace=f"{INSTANCE_1_ID}_workspace",
            description="卫星工程项目知识库"
        )

        time.sleep(1)

        # 创建实例2：标书文档
        success2 = tester.create_rag_instance(
            rag_id=INSTANCE_2_ID,
            workspace=f"{INSTANCE_2_ID}_workspace",
            description="标书文档知识库"
        )

        if not (success1 and success2):
            tester.log("部分实例创建失败", "WARNING")

        # ==================== 第3步：列出所有实例 ====================
        tester.log_separator("测试 3: 列出所有 RAG 实例")
        instances = tester.list_rag_instances()

        # ==================== 第4步：上传文档（同步） ====================
        tester.log_separator("测试 4: 同步上传文档")

        # 上传到实例1
        tester.log(f"\n>>> 上传文档到实例: {INSTANCE_1_ID}", "HEADER")
        for file_path in INSTANCE_1_FILES:
            if file_path.exists():
                tester.upload_document(INSTANCE_1_ID, str(file_path))
                time.sleep(2)  # 给予处理时间
            else:
                tester.log(f"文件不存在，跳过: {file_path}", "WARNING")

        # 上传到实例2
        tester.log(f"\n>>> 上传文档到实例: {INSTANCE_2_ID}", "HEADER")
        for file_path in INSTANCE_2_FILES:
            if file_path.exists():
                tester.upload_document(INSTANCE_2_ID, str(file_path))
                time.sleep(2)  # 给予处理时间
            else:
                tester.log(f"文件不存在，跳过: {file_path}", "WARNING")

        # ==================== 第5步：查看文档状态 ====================
        tester.log_separator("测试 5: 查看文档处理状态")

        tester.log(f"\n>>> 实例 {INSTANCE_1_ID} 的文档状态:", "HEADER")
        tester.get_document_status(INSTANCE_1_ID)

        time.sleep(1)

        tester.log(f"\n>>> 实例 {INSTANCE_2_ID} 的文档状态:", "HEADER")
        tester.get_document_status(INSTANCE_2_ID)

        # ==================== 第6步：执行查询 ====================
        tester.log_separator("测试 6: 执行知识库查询")

        # 查询实例1
        tester.log(f"\n>>> 查询实例: {INSTANCE_1_ID}", "HEADER")
        tester.query_knowledge(
            rag_id=INSTANCE_1_ID,
            question="卫星工程的主要内容是什么？",
            mode="hybrid"
        )

        time.sleep(2)

        # 查询实例2
        tester.log(f"\n>>> 查询实例: {INSTANCE_2_ID}", "HEADER")
        tester.query_knowledge(
            rag_id=INSTANCE_2_ID,
            question="标书中的主要技术要求有哪些？",
            mode="hybrid"
        )

        # ==================== 第7步：并发上传测试 ====================
        if len(INSTANCE_2_FILES) > 1:
            # 使用实例2测试并发上传（如果有多个文件）
            existing_files = [str(f) for f in INSTANCE_2_FILES if f.exists()]
            if len(existing_files) >= 2:
                # 创建一个临时实例用于并发测试
                test_instance_id = "concurrent_test"
                tester.log_separator("测试 7: 并发上传")

                if tester.create_rag_instance(
                    rag_id=test_instance_id,
                    workspace=f"{test_instance_id}_workspace",
                    description="并发测试实例"
                ):
                    tester.concurrent_upload_test(test_instance_id, existing_files[:2])
                    time.sleep(3)
                    tester.get_document_status(test_instance_id)

        # ==================== 第8步：并发查询测试 ====================
        tester.log_separator("测试 8: 并发查询")

        test_questions = [
            "总结一下主要内容",
            "有哪些关键技术？",
            "项目的目标是什么？",
        ]

        tester.concurrent_query_test(INSTANCE_1_ID, test_questions)

        # ==================== 第9步：清理（可选） ====================
        tester.log_separator("测试完成")

        cleanup = input(f"\n{Colors.WARNING}是否删除测试创建的实例？(y/N): {Colors.ENDC}").strip().lower()

        if cleanup == 'y':
            tester.log_separator("清理测试数据")
            tester.delete_rag_instance(INSTANCE_1_ID)
            time.sleep(1)
            tester.delete_rag_instance(INSTANCE_2_ID)
            if 'test_instance_id' in locals():
                time.sleep(1)
                tester.delete_rag_instance(test_instance_id)
        else:
            tester.log("保留测试实例，可稍后手动清理", "INFO")

    except KeyboardInterrupt:
        tester.log("\n测试被用户中断", "WARNING")
    except Exception as e:
        tester.log(f"\n测试过程中发生异常: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
    finally:
        # 打印测试摘要
        tester.print_summary()


if __name__ == "__main__":
    main()
