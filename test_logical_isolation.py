#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逻辑隔离模式测试脚本

测试场景：
1. 创建 3 个 RAG 实例（tech, legal, medical）
2. 为每个实例插入测试文档
3. 验证所有实例的查询功能正常
4. 完全删除 tech 实例
5. 验证 tech 实例被删除，legal 和 medical 实例不受影响
"""

import requests
import time
import sys
from typing import Dict, Any
from datetime import datetime


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class LogicalIsolationTester:
    """逻辑隔离测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_instances = [
            {
                "rag_id": "tech_docs",
                "workspace": "tech",
                "working_dir": "/tmp/rag_test/tech",
                "description": "技术文档知识库"
            },
            {
                "rag_id": "legal_docs",
                "workspace": "legal",
                "working_dir": "/tmp/rag_test/legal",
                "description": "法律文档知识库"
            },
            {
                "rag_id": "medical_docs",
                "workspace": "medical",
                "working_dir": "/tmp/rag_test/medical",
                "description": "医疗文档知识库"
            }
        ]

        self.test_documents = [
            {
                "rag_id": "tech_docs",
                "content": """Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。
                Python 广泛应用于 Web 开发、数据科学、人工智能和自动化等领域。
                它具有简洁易读的语法，拥有丰富的标准库和第三方库生态系统。
                Python 支持多种编程范式，包括面向对象、函数式和过程式编程。""",
                "file_name": "python_intro.txt",
                "query": "What is Python used for?"
            },
            {
                "rag_id": "legal_docs",
                "content": """合同法是规范合同的订立、履行、变更和终止的法律规范。
                有效的合同需要满足要约、承诺和对价三个基本要件。
                合同当事人应当遵循诚实信用原则，全面履行合同义务。
                违反合同义务的一方应当承担继续履行、采取补救措施或者赔偿损失等违约责任。""",
                "file_name": "contract_law.txt",
                "query": "What are the requirements for a valid contract?"
            },
            {
                "rag_id": "medical_docs",
                "content": """糖尿病是一种以高血糖为特征的代谢性疾病。
                糖尿病分为 1 型糖尿病、2 型糖尿病和妊娠糖尿病等类型。
                患者需要通过合理的饮食控制、适当的运动和规范的药物治疗来管理血糖水平。
                长期血糖控制不佳可能导致心血管疾病、肾病、视网膜病变等严重并发症。""",
                "file_name": "diabetes_guide.txt",
                "query": "What are the complications of diabetes?"
            }
        ]

        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    def log(self, message: str, level: str = "INFO"):
        """打印日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": Colors.CYAN,
            "SUCCESS": Colors.GREEN,
            "ERROR": Colors.RED,
            "WARNING": Colors.YELLOW,
            "STEP": Colors.MAGENTA + Colors.BOLD
        }
        color = colors.get(level, Colors.RESET)
        print(f"{color}[{timestamp}] {message}{Colors.RESET}")

    def check(self, condition: bool, description: str) -> bool:
        """检查测试条件"""
        self.results["total"] += 1
        if condition:
            self.results["passed"] += 1
            self.log(f"✅ {description}", "SUCCESS")
            return True
        else:
            self.results["failed"] += 1
            self.results["errors"].append(description)
            self.log(f"❌ {description}", "ERROR")
            return False

    def test_step(self, step_num: int, description: str):
        """打印测试步骤"""
        self.log(f"\n{'='*60}", "STEP")
        self.log(f"步骤 {step_num}: {description}", "STEP")
        self.log(f"{'='*60}", "STEP")

    def create_instance(self, instance: Dict[str, Any]) -> bool:
        """创建 RAG 实例"""
        try:
            payload = {
                **instance,
                "top_k": 10,
                "chunk_top_k": 5,
                "chunk_token_size": 1200,
                "chunk_overlap_token_size": 100,
                "enable_llm_cache": True,
                "enable_llm_cache_for_entity_extract": True
            }

            resp = requests.post(
                f"{self.base_url}/admin/rag_instances/create",
                json=payload,
                timeout=60
            )

            if resp.status_code == 200:
                data = resp.json()
                self.log(f"  创建实例: {instance['rag_id']} (workspace: {instance['workspace']})", "SUCCESS")
                return True
            else:
                self.log(f"  创建失败: {resp.status_code} - {resp.text}", "ERROR")
                return False

        except Exception as e:
            self.log(f"  创建异常: {str(e)}", "ERROR")
            return False

    def list_instances(self) -> list:
        """列出所有实例"""
        try:
            resp = requests.get(f"{self.base_url}/admin/rag_instances/list", timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            self.log(f"  列出实例异常: {str(e)}", "ERROR")
            return []

    def insert_document(self, rag_id: str, content: str, file_name: str) -> bool:
        """插入文档"""
        try:
            # 注意：这里假设你的 API 端点是 /documents/upload_text/{rag_id}
            # 如果实际端点不同，请调整
            resp = requests.post(
                f"{self.base_url}/documents/upload_text/{rag_id}",
                json={"content": content, "file_name": file_name},
                timeout=120
            )

            if resp.status_code == 200:
                self.log(f"  插入文档: {file_name} -> {rag_id}", "SUCCESS")
                return True
            else:
                self.log(f"  插入失败: {resp.status_code} - {resp.text}", "ERROR")
                return False

        except Exception as e:
            self.log(f"  插入异常: {str(e)}", "ERROR")
            return False

    def query_instance(self, rag_id: str, question: str, expect_success: bool = True) -> bool:
        """查询实例"""
        try:
            resp = requests.post(
                f"{self.base_url}/query/{rag_id}",
                json={"question": question, "mode": "hybrid", "only_need_context": True},
                timeout=60
            )

            if expect_success:
                if resp.status_code == 200:
                    result = resp.json()
                    # 检查是否有返回内容
                    if isinstance(result, dict) and result.get("context"):
                        self.log(f"  查询成功: {rag_id} - 返回 {len(result.get('context', ''))} 字符", "SUCCESS")
                        return True
                    elif isinstance(result, str) and len(result) > 0:
                        self.log(f"  查询成功: {rag_id} - 返回 {len(result)} 字符", "SUCCESS")
                        return True
                    else:
                        self.log(f"  查询返回空结果: {rag_id}", "WARNING")
                        return False
                else:
                    self.log(f"  查询失败: {resp.status_code}", "ERROR")
                    return False
            else:
                # 期望失败（实例已删除）
                if resp.status_code == 404:
                    self.log(f"  查询正确失败: {rag_id} (实例不存在)", "SUCCESS")
                    return True
                else:
                    self.log(f"  查询应该失败但返回: {resp.status_code}", "ERROR")
                    return False

        except Exception as e:
            self.log(f"  查询异常: {str(e)}", "ERROR")
            return False

    def delete_instance(self, rag_id: str) -> Dict[str, Any]:
        """删除实例"""
        try:
            resp = requests.delete(
                f"{self.base_url}/admin/rag_instances/{rag_id}/complete?cleanup_storage=true",
                timeout=120
            )

            if resp.status_code == 200:
                result = resp.json()
                self.log(f"  删除成功: {rag_id}", "SUCCESS")
                self.log(f"  清理的资源: {result.get('cleaned_resources', [])}", "INFO")
                return result
            else:
                self.log(f"  删除失败: {resp.status_code} - {resp.text}", "ERROR")
                return {"status": "error", "message": resp.text}

        except Exception as e:
            self.log(f"  删除异常: {str(e)}", "ERROR")
            return {"status": "error", "message": str(e)}

    def run_tests(self):
        """运行完整测试流程"""
        self.log(f"\n{'='*60}", "STEP")
        self.log("🧪 开始逻辑隔离模式测试", "STEP")
        self.log(f"{'='*60}\n", "STEP")

        # ========== 步骤 1: 创建 3 个实例 ==========
        self.test_step(1, "创建 3 个 RAG 实例")

        for instance in self.test_instances:
            success = self.create_instance(instance)
            self.check(success, f"创建实例 {instance['rag_id']}")
            time.sleep(2)  # 等待初始化完成

        # ========== 步骤 2: 验证实例列表 ==========
        self.test_step(2, "验证实例列表")

        instances = self.list_instances()
        instance_ids = [inst.get("rag_id") for inst in instances]

        self.check(len(instances) == 3, f"实例数量正确 (预期: 3, 实际: {len(instances)})")
        self.check("tech_docs" in instance_ids, "tech_docs 实例存在")
        self.check("legal_docs" in instance_ids, "legal_docs 实例存在")
        self.check("medical_docs" in instance_ids, "medical_docs 实例存在")

        # ========== 步骤 3: 插入测试文档 ==========
        self.test_step(3, "插入测试文档")

        for doc in self.test_documents:
            success = self.insert_document(doc["rag_id"], doc["content"], doc["file_name"])
            self.check(success, f"插入文档到 {doc['rag_id']}")
            time.sleep(3)  # 等待索引完成

        self.log("\n⏳ 等待 10 秒让索引完成...", "INFO")
        time.sleep(10)

        # ========== 步骤 4: 验证查询功能（删除前）==========
        self.test_step(4, "验证所有实例的查询功能（删除前）")

        for doc in self.test_documents:
            success = self.query_instance(doc["rag_id"], doc["query"], expect_success=True)
            self.check(success, f"查询 {doc['rag_id']} 正常")

        # ========== 步骤 5: 删除 tech 实例 ==========
        self.test_step(5, "🔥 完全删除 tech 实例")

        delete_result = self.delete_instance("tech_docs")

        self.check(
            delete_result.get("status") == "success",
            "tech_docs 删除成功"
        )

        cleaned = delete_result.get("cleaned_resources", [])
        self.check(
            any("Nebula" in str(item) for item in cleaned),
            "Nebula 图数据已清理"
        )
        self.check(
            any("Milvus" in str(item) for item in cleaned),
            "Milvus 向量数据已清理"
        )
        self.check(
            any("工作目录" in str(item) for item in cleaned),
            "工作目录已清理"
        )

        time.sleep(2)

        # ========== 步骤 6: 验证删除效果 ==========
        self.test_step(6, "验证删除效果")

        # 6.1 验证实例列表（应该只剩 2 个）
        instances = self.list_instances()
        instance_ids = [inst.get("rag_id") for inst in instances]

        self.check(len(instances) == 2, f"实例数量正确 (预期: 2, 实际: {len(instances)})")
        self.check("tech_docs" not in instance_ids, "tech_docs 实例已删除")
        self.check("legal_docs" in instance_ids, "legal_docs 实例仍然存在")
        self.check("medical_docs" in instance_ids, "medical_docs 实例仍然存在")

        # 6.2 验证 tech 查询失败
        self.log("\n  验证 tech_docs 查询失败（预期 404）:", "INFO")
        tech_query_fail = self.query_instance(
            "tech_docs",
            "What is Python?",
            expect_success=False
        )
        self.check(tech_query_fail, "tech_docs 查询正确失败 (404)")

        # 6.3 验证 legal 和 medical 查询仍然正常
        self.log("\n  验证其他实例查询仍然正常:", "INFO")
        legal_query_ok = self.query_instance(
            "legal_docs",
            "What are the requirements for a valid contract?",
            expect_success=True
        )
        self.check(legal_query_ok, "legal_docs 查询仍然正常")

        medical_query_ok = self.query_instance(
            "medical_docs",
            "What are the complications of diabetes?",
            expect_success=True
        )
        self.check(medical_query_ok, "medical_docs 查询仍然正常")

        # ========== 测试总结 ==========
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        self.log(f"\n{'='*60}", "STEP")
        self.log("📊 测试总结", "STEP")
        self.log(f"{'='*60}", "STEP")

        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0

        self.log(f"总测试数: {total}", "INFO")
        self.log(f"通过: {passed}", "SUCCESS")
        self.log(f"失败: {failed}", "ERROR" if failed > 0 else "SUCCESS")
        self.log(f"通过率: {pass_rate:.1f}%", "SUCCESS" if pass_rate == 100 else "WARNING")

        if self.results["errors"]:
            self.log(f"\n失败的测试:", "ERROR")
            for i, error in enumerate(self.results["errors"], 1):
                self.log(f"  {i}. {error}", "ERROR")

        if pass_rate == 100:
            self.log(f"\n{'='*60}", "SUCCESS")
            self.log("🎉 所有测试通过！逻辑隔离模式工作正常！", "SUCCESS")
            self.log(f"{'='*60}\n", "SUCCESS")
        else:
            self.log(f"\n{'='*60}", "ERROR")
            self.log("⚠️  部分测试失败，请检查错误信息", "ERROR")
            self.log(f"{'='*60}\n", "ERROR")

    def cleanup(self):
        """清理测试数据"""
        self.log("\n🧹 清理测试数据...", "INFO")

        instances = self.list_instances()
        for inst in instances:
            rag_id = inst.get("rag_id")
            if rag_id in ["tech_docs", "legal_docs", "medical_docs"]:
                self.log(f"  删除实例: {rag_id}", "INFO")
                self.delete_instance(rag_id)
                time.sleep(1)

        self.log("清理完成", "SUCCESS")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="逻辑隔离模式测试脚本")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API 基础 URL (默认: http://localhost:8000)"
    )
    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="只执行清理操作"
    )

    args = parser.parse_args()

    tester = LogicalIsolationTester(base_url=args.base_url)

    if args.cleanup_only:
        tester.cleanup()
    else:
        try:
            tester.run_tests()
        except KeyboardInterrupt:
            tester.log("\n\n⚠️  测试被中断", "WARNING")
            tester.print_summary()
        except Exception as e:
            tester.log(f"\n\n❌ 测试过程中发生异常: {str(e)}", "ERROR")
            import traceback
            traceback.print_exc()
        finally:
            # 询问是否清理
            try:
                response = input("\n是否清理测试数据？(y/n): ").strip().lower()
                if response == 'y':
                    tester.cleanup()
            except:
                pass


if __name__ == "__main__":
    main()
