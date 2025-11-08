#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 后端 API 并发测试脚本

测试场景：
1. 同一个 RAG 实例的并发文档上传
2. 不同 RAG 实例的并发文档上传
3. 同一个 RAG 实例的并发查询
4. 不同 RAG 实例的并发查询
"""

import requests
import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import threading


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


class ConcurrentAPITester:
    """并发 API 测试类"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.test_results = []
        self.lock = threading.Lock()

    def log(self, message: str, level: str = "INFO"):
        """线程安全的日志输出"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        thread_id = threading.current_thread().name
        color = {
            "INFO": Colors.OKBLUE,
            "SUCCESS": Colors.OKGREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL,
            "HEADER": Colors.HEADER
        }.get(level, Colors.ENDC)

        with self.lock:
            print(f"{color}[{timestamp}] [{thread_id}] [{level}] {message}{Colors.ENDC}")

    def log_separator(self, title: str = ""):
        """输出分隔线"""
        print(f"\n{Colors.BOLD}{'='*100}{Colors.ENDC}")
        if title:
            print(f"{Colors.BOLD}{Colors.HEADER}{title.center(100)}{Colors.ENDC}")
            print(f"{Colors.BOLD}{'='*100}{Colors.ENDC}\n")

    def record_result(self, test_name: str, success: bool, duration: float, details: str = ""):
        """记录测试结果"""
        with self.lock:
            self.test_results.append({
                "test": test_name,
                "success": success,
                "duration": duration,
                "details": details
            })

    def health_check(self) -> bool:
        """健康检查"""
        try:
            response = requests.get(f"{self.api_url}/admin/health", timeout=10)
            return response.status_code == 200
        except:
            return False

    def create_rag_instance(self, rag_id: str, workspace: str, description: str = "") -> Tuple[bool, float]:
        """创建 RAG 实例"""
        start = time.time()
        try:
            payload = {
                "rag_id": rag_id,
                "workspace": workspace,
                "description": description,
                "working_dir": "./rag_storage"
            }

            response = requests.post(
                f"{self.api_url}/admin/rag_instances/create",
                json=payload,
                timeout=30
            )
            duration = time.time() - start

            if response.status_code == 200:
                self.log(f"✓ 实例创建成功: {rag_id} ({duration:.2f}s)", "SUCCESS")
                return True, duration
            else:
                self.log(f"✗ 创建实例失败: {rag_id} - {response.status_code}", "ERROR")
                return False, duration

        except Exception as e:
            duration = time.time() - start
            self.log(f"✗ 创建实例异常: {rag_id} - {str(e)}", "ERROR")
            return False, duration

    def upload_document_thread(self, rag_id: str, file_path: str, thread_name: str) -> Dict:
        """线程安全的文档上传"""
        file_path_obj = Path(file_path)
        start = time.time()

        self.log(f"开始上传: {file_path_obj.name} -> {rag_id}", "INFO")

        try:
            if not file_path_obj.exists():
                duration = time.time() - start
                self.log(f"✗ 文件不存在: {file_path}", "ERROR")
                return {
                    "success": False,
                    "rag_id": rag_id,
                    "file": file_path_obj.name,
                    "duration": duration,
                    "error": "文件不存在"
                }

            # 每个线程使用独立的 session
            session = requests.Session()

            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_path_obj.name, f, 'application/octet-stream')
                }
                data = {
                    'rag_id': rag_id
                }

                response = session.post(
                    f"{self.api_url}/documents/upload",
                    files=files,
                    data=data,
                    timeout=300
                )

            duration = time.time() - start

            if response.status_code == 200:
                self.log(f"✓ 上传成功: {file_path_obj.name} -> {rag_id} ({duration:.2f}s)", "SUCCESS")
                return {
                    "success": True,
                    "rag_id": rag_id,
                    "file": file_path_obj.name,
                    "duration": duration,
                    "response": response.json()
                }
            else:
                self.log(f"✗ 上传失败: {file_path_obj.name} -> {rag_id} - HTTP {response.status_code}", "ERROR")
                return {
                    "success": False,
                    "rag_id": rag_id,
                    "file": file_path_obj.name,
                    "duration": duration,
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            duration = time.time() - start
            self.log(f"✗ 上传异常: {file_path_obj.name} -> {rag_id} - {str(e)}", "ERROR")
            return {
                "success": False,
                "rag_id": rag_id,
                "file": file_path_obj.name,
                "duration": duration,
                "error": str(e)
            }

    def query_thread(self, rag_id: str, question: str, mode: str = "hybrid") -> Dict:
        """线程安全的查询"""
        start = time.time()
        question_preview = question[:30] + "..." if len(question) > 30 else question

        self.log(f"开始查询: [{rag_id}] {question_preview}", "INFO")

        try:
            session = requests.Session()

            payload = {
                "rag_id": rag_id,
                "question": question,
                "mode": mode,
                "only_need_context": False
            }

            response = session.post(
                f"{self.api_url}/query/",
                json=payload,
                timeout=60
            )
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                answer_len = len(data.get('answer', ''))
                self.log(f"✓ 查询成功: [{rag_id}] {question_preview} ({duration:.2f}s, {answer_len}字符)", "SUCCESS")
                return {
                    "success": True,
                    "rag_id": rag_id,
                    "question": question,
                    "duration": duration,
                    "answer_length": answer_len,
                    "response": data
                }
            else:
                self.log(f"✗ 查询失败: [{rag_id}] {question_preview} - HTTP {response.status_code}", "ERROR")
                return {
                    "success": False,
                    "rag_id": rag_id,
                    "question": question,
                    "duration": duration,
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            duration = time.time() - start
            self.log(f"✗ 查询异常: [{rag_id}] {question_preview} - {str(e)}", "ERROR")
            return {
                "success": False,
                "rag_id": rag_id,
                "question": question,
                "duration": duration,
                "error": str(e)
            }

    def test_concurrent_upload_same_instance(self, rag_id: str, file_paths: List[str], max_workers: int = 3):
        """测试：同一个实例的并发上传"""
        self.log_separator(f"测试：同一个实例并发上传 ({rag_id})")
        self.log(f"并发上传 {len(file_paths)} 个文件，线程数: {max_workers}", "HEADER")

        overall_start = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Upload") as executor:
            futures = {
                executor.submit(self.upload_document_thread, rag_id, fp, f"Thread-{i}"): fp
                for i, fp in enumerate(file_paths)
            }

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.log(f"✗ 线程异常: {file_path} - {str(e)}", "ERROR")

        overall_duration = time.time() - overall_start

        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count
        avg_duration = sum(r["duration"] for r in results) / len(results) if results else 0

        self.log_separator("并发上传结果统计")
        print(f"{Colors.BOLD}总文件数: {len(file_paths)}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ 成功: {success_count}{Colors.ENDC}")
        print(f"{Colors.FAIL}✗ 失败: {failed_count}{Colors.ENDC}")
        print(f"{Colors.BOLD}总耗时: {overall_duration:.2f}s{Colors.ENDC}")
        print(f"{Colors.BOLD}平均耗时: {avg_duration:.2f}s{Colors.ENDC}")
        print(f"{Colors.BOLD}并发效率: {(sum(r['duration'] for r in results) / overall_duration):.2f}x{Colors.ENDC}\n")

        self.record_result(f"并发上传-同实例-{rag_id}", success_count == len(file_paths), overall_duration)
        return results

    def test_concurrent_upload_different_instances(self, upload_tasks: List[Tuple[str, str]], max_workers: int = 5):
        """测试：不同实例的并发上传

        Args:
            upload_tasks: List of (rag_id, file_path) tuples
        """
        self.log_separator(f"测试：不同实例并发上传")
        self.log(f"并发上传 {len(upload_tasks)} 个文件到不同实例，线程数: {max_workers}", "HEADER")

        overall_start = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="CrossUpload") as executor:
            futures = {
                executor.submit(self.upload_document_thread, rag_id, fp, f"Thread-{i}"): (rag_id, fp)
                for i, (rag_id, fp) in enumerate(upload_tasks)
            }

            for future in as_completed(futures):
                rag_id, file_path = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.log(f"✗ 线程异常: {rag_id}/{file_path} - {str(e)}", "ERROR")

        overall_duration = time.time() - overall_start

        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count
        avg_duration = sum(r["duration"] for r in results) / len(results) if results else 0

        # 按实例分组统计
        instance_stats = {}
        for r in results:
            rag_id = r["rag_id"]
            if rag_id not in instance_stats:
                instance_stats[rag_id] = {"success": 0, "failed": 0}
            if r["success"]:
                instance_stats[rag_id]["success"] += 1
            else:
                instance_stats[rag_id]["failed"] += 1

        self.log_separator("不同实例并发上传结果统计")
        print(f"{Colors.BOLD}总文件数: {len(upload_tasks)}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ 成功: {success_count}{Colors.ENDC}")
        print(f"{Colors.FAIL}✗ 失败: {failed_count}{Colors.ENDC}")
        print(f"{Colors.BOLD}总耗时: {overall_duration:.2f}s{Colors.ENDC}")
        print(f"{Colors.BOLD}平均耗时: {avg_duration:.2f}s{Colors.ENDC}")
        print(f"{Colors.BOLD}并发效率: {(sum(r['duration'] for r in results) / overall_duration):.2f}x{Colors.ENDC}\n")

        print(f"{Colors.BOLD}各实例统计:{Colors.ENDC}")
        for rag_id, stats in instance_stats.items():
            print(f"  {rag_id}: ✓ {stats['success']} / ✗ {stats['failed']}")
        print()

        self.record_result(f"并发上传-跨实例", success_count == len(upload_tasks), overall_duration)
        return results

    def test_concurrent_query_same_instance(self, rag_id: str, questions: List[str], max_workers: int = 5):
        """测试：同一个实例的并发查询"""
        self.log_separator(f"测试：同一个实例并发查询 ({rag_id})")
        self.log(f"并发查询 {len(questions)} 个问题，线程数: {max_workers}", "HEADER")

        overall_start = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Query") as executor:
            futures = {
                executor.submit(self.query_thread, rag_id, q): q
                for q in questions
            }

            for future in as_completed(futures):
                question = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.log(f"✗ 查询线程异常: {question} - {str(e)}", "ERROR")

        overall_duration = time.time() - overall_start

        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count
        avg_duration = sum(r["duration"] for r in results) / len(results) if results else 0

        self.log_separator("并发查询结果统计")
        print(f"{Colors.BOLD}总查询数: {len(questions)}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ 成功: {success_count}{Colors.ENDC}")
        print(f"{Colors.FAIL}✗ 失败: {failed_count}{Colors.ENDC}")
        print(f"{Colors.BOLD}总耗时: {overall_duration:.2f}s{Colors.ENDC}")
        print(f"{Colors.BOLD}平均耗时: {avg_duration:.2f}s{Colors.ENDC}")
        print(f"{Colors.BOLD}并发效率: {(sum(r['duration'] for r in results) / overall_duration):.2f}x{Colors.ENDC}\n")

        self.record_result(f"并发查询-同实例-{rag_id}", success_count == len(questions), overall_duration)
        return results

    def test_concurrent_query_different_instances(self, query_tasks: List[Tuple[str, str]], max_workers: int = 10):
        """测试：不同实例的并发查询

        Args:
            query_tasks: List of (rag_id, question) tuples
        """
        self.log_separator(f"测试：不同实例并发查询")
        self.log(f"并发查询 {len(query_tasks)} 个问题到不同实例，线程数: {max_workers}", "HEADER")

        overall_start = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="CrossQuery") as executor:
            futures = {
                executor.submit(self.query_thread, rag_id, q): (rag_id, q)
                for rag_id, q in query_tasks
            }

            for future in as_completed(futures):
                rag_id, question = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.log(f"✗ 查询线程异常: {rag_id}/{question} - {str(e)}", "ERROR")

        overall_duration = time.time() - overall_start

        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count
        avg_duration = sum(r["duration"] for r in results) / len(results) if results else 0

        # 按实例分组统计
        instance_stats = {}
        for r in results:
            rag_id = r["rag_id"]
            if rag_id not in instance_stats:
                instance_stats[rag_id] = {"success": 0, "failed": 0}
            if r["success"]:
                instance_stats[rag_id]["success"] += 1
            else:
                instance_stats[rag_id]["failed"] += 1

        self.log_separator("不同实例并发查询结果统计")
        print(f"{Colors.BOLD}总查询数: {len(query_tasks)}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ 成功: {success_count}{Colors.ENDC}")
        print(f"{Colors.FAIL}✗ 失败: {failed_count}{Colors.ENDC}")
        print(f"{Colors.BOLD}总耗时: {overall_duration:.2f}s{Colors.ENDC}")
        print(f"{Colors.BOLD}平均耗时: {avg_duration:.2f}s{Colors.ENDC}")
        print(f"{Colors.BOLD}并发效率: {(sum(r['duration'] for r in results) / overall_duration):.2f}x{Colors.ENDC}\n")

        print(f"{Colors.BOLD}各实例统计:{Colors.ENDC}")
        for rag_id, stats in instance_stats.items():
            print(f"  {rag_id}: ✓ {stats['success']} / ✗ {stats['failed']}")
        print()

        self.record_result(f"并发查询-跨实例", success_count == len(query_tasks), overall_duration)
        return results

    def get_document_status(self, rag_id: str) -> Dict:
        """获取文档状态"""
        try:
            response = requests.get(f"{self.api_url}/documents/status/{rag_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}

    def delete_rag_instance(self, rag_id: str) -> bool:
        """删除 RAG 实例"""
        try:
            response = requests.delete(f"{self.api_url}/admin/rag_instances/{rag_id}", timeout=30)
            return response.status_code == 200
        except:
            return False

    def print_summary(self):
        """打印测试摘要"""
        self.log_separator("测试总结")

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed

        print(f"{Colors.BOLD}总测试场景: {total}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ 通过: {passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}✗ 失败: {failed}{Colors.ENDC}")
        print()

        for result in self.test_results:
            status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if result["success"] else f"{Colors.FAIL}✗{Colors.ENDC}"
            duration = f"{result['duration']:.2f}s"
            print(f"{status} {result['test']:<60} {duration:>10}")

        print(f"\n{Colors.BOLD}{'='*100}{Colors.ENDC}\n")


def main():
    """主测试流程"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 100)
    print("RAG 后端 API 并发测试")
    print("=" * 100)
    print(f"{Colors.ENDC}\n")

    # 配置
    BASE_URL = "http://localhost:8000"
    DOC_DIR = Path("/root/workplace/lightrag/LightRAG1/docx")

    # 文件路径
    FILE_SATELLITE = DOC_DIR / "卫星工程.docx"
    FILE_TENDER_01 = DOC_DIR / "子标书01.docx"
    FILE_TENDER_02 = DOC_DIR / "子标书02.docx"

    # 实例配置
    INSTANCE_1 = "satellite_project"
    INSTANCE_2 = "tender_docs"

    # 初始化测试器
    tester = ConcurrentAPITester(BASE_URL)

    try:
        # ==================== 前置检查 ====================
        tester.log_separator("前置检查")

        if not tester.health_check():
            tester.log("❌ 后端服务未运行", "ERROR")
            tester.log("请先启动后端: ./start_backend.sh", "INFO")
            sys.exit(1)

        tester.log("✓ 后端服务正常", "SUCCESS")

        # 检查文件
        files_to_check = [FILE_SATELLITE, FILE_TENDER_01, FILE_TENDER_02]
        missing_files = [f for f in files_to_check if not f.exists()]

        if missing_files:
            tester.log(f"⚠ 以下文件不存在:", "WARNING")
            for f in missing_files:
                tester.log(f"  - {f}", "WARNING")
            tester.log("测试将使用已存在的文件", "INFO")

        existing_files = [str(f) for f in files_to_check if f.exists()]
        if not existing_files:
            tester.log("❌ 没有可用的测试文件", "ERROR")
            sys.exit(1)

        # ==================== 创建实例 ====================
        tester.log_separator("创建测试实例")

        success1, dur1 = tester.create_rag_instance(
            INSTANCE_1,
            f"{INSTANCE_1}_workspace",
            "卫星工程项目知识库"
        )

        time.sleep(0.5)

        success2, dur2 = tester.create_rag_instance(
            INSTANCE_2,
            f"{INSTANCE_2}_workspace",
            "标书文档知识库"
        )

        if not (success1 and success2):
            tester.log("⚠ 部分实例创建失败，但继续测试", "WARNING")

        time.sleep(2)

        # ==================== 测试1：同一实例并发上传 ====================
        if len(existing_files) >= 2:
            tester.test_concurrent_upload_same_instance(
                INSTANCE_1,
                existing_files[:2],  # 取前2个文件
                max_workers=2
            )

            time.sleep(3)

            # 查看状态
            tester.log(f"\n查看 {INSTANCE_1} 的文档状态:", "HEADER")
            status = tester.get_document_status(INSTANCE_1)
            if status:
                print(f"  总文档数: {status.get('total')}")
                print(f"  已处理: {status.get('processed')}")
                print(f"  待处理: {status.get('pending')}")
                print(f"  失败: {status.get('failed')}\n")

        # ==================== 测试2：不同实例并发上传 ====================
        if FILE_SATELLITE.exists() and FILE_TENDER_01.exists() and FILE_TENDER_02.exists():
            upload_tasks = [
                (INSTANCE_1, str(FILE_SATELLITE)),
                (INSTANCE_2, str(FILE_TENDER_01)),
                (INSTANCE_2, str(FILE_TENDER_02)),
            ]

            tester.test_concurrent_upload_different_instances(
                upload_tasks,
                max_workers=3
            )

            time.sleep(3)

            # 查看两个实例的状态
            for inst_id in [INSTANCE_1, INSTANCE_2]:
                tester.log(f"\n查看 {inst_id} 的文档状态:", "HEADER")
                status = tester.get_document_status(inst_id)
                if status:
                    print(f"  总文档数: {status.get('total')}")
                    print(f"  已处理: {status.get('processed')}")
                    print(f"  待处理: {status.get('pending')}")
                    print(f"  失败: {status.get('failed')}\n")

        # ==================== 等待文档处理完成 ====================
        tester.log_separator("等待文档处理完成")
        tester.log("等待 10 秒让文档处理...", "INFO")
        time.sleep(10)

        # ==================== 测试3：同一实例并发查询 ====================
        questions_instance1 = [
            "卫星工程的主要内容是什么？",
            "总结一下核心技术",
            "项目的目标是什么？",
            "有哪些关键挑战？",
            "预期成果有哪些？",
        ]

        tester.test_concurrent_query_same_instance(
            INSTANCE_1,
            questions_instance1,
            max_workers=5
        )

        time.sleep(2)

        # ==================== 测试4：不同实例并发查询 ====================
        query_tasks = [
            (INSTANCE_1, "卫星工程的主要内容是什么？"),
            (INSTANCE_1, "总结一下核心技术"),
            (INSTANCE_2, "标书中的主要技术要求有哪些？"),
            (INSTANCE_2, "项目预算是多少？"),
            (INSTANCE_1, "项目的时间安排"),
            (INSTANCE_2, "投标人资格要求"),
            (INSTANCE_1, "技术路线是什么？"),
            (INSTANCE_2, "评分标准"),
        ]

        tester.test_concurrent_query_different_instances(
            query_tasks,
            max_workers=8
        )

        # ==================== 清理 ====================
        tester.log_separator("测试完成")

        cleanup = input(f"\n{Colors.WARNING}是否删除测试创建的实例？(y/N): {Colors.ENDC}").strip().lower()

        if cleanup == 'y':
            tester.log_separator("清理测试数据")
            for inst_id in [INSTANCE_1, INSTANCE_2]:
                if tester.delete_rag_instance(inst_id):
                    tester.log(f"✓ 已删除实例: {inst_id}", "SUCCESS")
                else:
                    tester.log(f"✗ 删除失败: {inst_id}", "ERROR")
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
