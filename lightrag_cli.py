# -*- coding: utf-8 -*-
"""
基于 lightrag 和 LiteLLM 的 RAG 系统命令行工具

支持的文档格式：PDF、DOCX、DOC、TXT、RTF 等（通过 textract 支持）

环境变量配置：
LLM_MODEL: LLM 模型名称，默认 "gpt-4"
EMBEDDING_MODEL: Embedding 模型路径或名称，默认 "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM: Embedding 维度，默认 384
EMBEDDING_MAX_TOKEN: Embedding 最大 token 数，默认 5000
LITELLM_URL: LiteLLM 服务地址，默认 "http://localhost:4000"
LITELLM_KEY: LiteLLM API 密钥，默认 "sk-1234"

命令行参数描述（可选，会覆盖环境变量）：
--working_dir: lightrag 工作目录（必需）
--document_path: 输入文档路径，支持 PDF/DOCX/TXT 等格式（可选）
--llm_model: LLM 模型名称
--embedding_model: Embedding 模型路径或名称
--embedding_dim: Embedding 维度
--embedding_max_token: Embedding 最大 token 数
--litellm_url: LiteLLM 服务地址
--litellm_key: LiteLLM API 密钥

依赖安装：
pip install textract

使用示例：
# 使用环境变量 + PDF 文档
export LLM_MODEL=gpt-4
export EMBEDDING_MODEL=/path/to/model
export LITELLM_URL=http://localhost:4000
export LITELLM_KEY=sk-1234
python lightrag_cli.py --working_dir ./index_default --document_path ./document.pdf

# 使用 DOCX 文档
python lightrag_cli.py \
  --working_dir ./index_default \
  --document_path ./document.docx \
  --llm_model deepseek-chat

# 使用 TXT 文档
python lightrag_cli.py \
  --working_dir ./index_default \
  --document_path ./document.txt
"""

import os
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Optional

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()  # 这会自动加载当前目录的 .env 文件

import nest_asyncio
import textract
from lightrag import lightrag, QueryParam
from lightrag.llm.llama_index_impl import (
    llama_index_complete_if_cache,
    llama_index_embed,
)
from lightrag.llm.hf import hf_model_complete, hf_embed
from transformers import AutoModel, AutoTokenizer
from lightrag.utils import EmbeddingFunc
from llama_index.llms.litellm import LiteLLM
from llama_index.embeddings.litellm import LiteLLMEmbedding
from lightrag.kg.shared_storage import initialize_pipeline_status

nest_asyncio.apply()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class lightragProcessor:
    """lightrag 处理器，用于构建和查询知识图谱"""

    def __init__(
        self,
        working_dir: str,
        llm_model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        embedding_dim: Optional[int] = None,
        embedding_max_token: Optional[int] = None,
        litellm_url: Optional[str] = None,
        litellm_key: Optional[str] = None
    ):
        """
        初始化 lightrag 处理器

        Args:
            working_dir: 工作目录
            llm_model: LLM 模型名称
            embedding_model: Embedding 模型名称
            embedding_dim: Embedding 维度
            embedding_max_token: Embedding 最大 token 数
            litellm_url: LiteLLM 服务地址
            litellm_key: LiteLLM API 密钥
        """
        self.working_dir = Path(working_dir)
        
        # 从环境变量获取配置，优先使用传入参数
        self.llm_model = llm_model or os.environ.get("LLM_MODEL", "gpt-4")
        self.embedding_model = embedding_model or os.environ.get(
            "EMBEDDING_MODEL", 
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.embedding_dim = embedding_dim or int(os.environ.get("EMBEDDING_DIM", "384"))
        self.embedding_max_token = embedding_max_token or int(
            os.environ.get("EMBEDDING_MAX_TOKEN", "5000")
        )
        self.litellm_url = litellm_url or os.environ.get(
            "LITELLM_URL", 
            "http://localhost:4000"
        )
        self.litellm_key = litellm_key or os.environ.get("LITELLM_KEY", "sk-1234")

        # 创建工作目录
        self.working_dir.mkdir(exist_ok=True)

        self.rag = None

        logger.info(f"工作目录: {self.working_dir}")
        logger.info(f"LLM 模型: {self.llm_model}")
        logger.info(f"Embedding 模型: {self.embedding_model}")
        logger.info(f"Embedding 维度: {self.embedding_dim}")
        logger.info(f"Embedding 最大 Token: {self.embedding_max_token}")
        logger.info(f"LiteLLM URL: {self.litellm_url}")

    async def llm_model_func(self, prompt, system_prompt=None, history_messages=[], **kwargs):
        """
        LLM 模型调用函数

        Args:
            prompt: 提示词
            system_prompt: 系统提示词
            history_messages: 历史消息
            **kwargs: 其他参数

        Returns:
            模型响应
        """
        try:
            # Initialize LiteLLM if not in kwargs
            if "llm_instance" not in kwargs:
                llm_instance = LiteLLM(
                    model=f"openai/{self.llm_model}",
                    api_base=self.litellm_url,
                    api_key=self.litellm_key,
                    temperature=0.7,
                )
                kwargs["llm_instance"] = llm_instance

            response = await llama_index_complete_if_cache(
                kwargs["llm_instance"],
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
            )
            return response
        except Exception as e:
            logger.error(f"LLM 请求失败: {str(e)}")
            raise

    async def initialize_rag(self):
        """初始化 RAG 系统"""
        logger.info("正在初始化 lightrag 系统...")

        # 加载 Embedding 模型
        logger.info(f"正在加载 Embedding 模型: {self.embedding_model}")
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.embedding_model)
            embed_model = AutoModel.from_pretrained(self.embedding_model)
            logger.info("Embedding 模型加载完成")
        except Exception as e:
            logger.error(f"加载 Embedding 模型失败: {e}")
            logger.info(f"请确保 EMBEDDING_MODEL 环境变量或 --embedding_model 参数配置正确")
            raise

        self.rag = lightrag(
            working_dir=str(self.working_dir),
            llm_model_func=self.llm_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=self.embedding_dim,
                max_token_size=self.embedding_max_token,
                func=lambda texts: hf_embed(
                    texts,
                    tokenizer=tokenizer,
                    embed_model=embed_model,
                ),
            ),
            graph_storage="Neo4JStorage",   # 使用 Neo4j 存储知识图谱
            vector_storage="FaissVectorDBStorage",  # 使用 Faiss 存储向量数据库
            vector_db_storage_cls_kwargs={
                "cosine_better_than_threshold": 0.3  # 您期望的阈值
            },
        )

        await self.rag.initialize_storages()
        await initialize_pipeline_status()

        logger.info("lightrag 系统初始化完成")

    def insert_document(self, document_path: str):
        """
        插入文档到知识图谱，支持多种格式（PDF、DOCX、TXT等）

        Args:
            document_path: 文档路径
        """
        doc_path = Path(document_path)
        if not doc_path.exists():
            raise FileNotFoundError(f"文档不存在: {document_path}")

        logger.info(f"正在读取文档: {document_path}")
        
        try:
            # 使用 textract 提取文本内容
            logger.info(f"使用 textract 提取文档内容...")
            text_content = textract.process(str(doc_path))
            content = text_content.decode('utf-8')
            logger.info(f"文档提取成功 (文档长度: {len(content)} 字符)")
        except Exception as e:
            logger.error(f"使用 textract 提取文档失败: {e}")
            # 如果是 TXT 文件，尝试直接读取
            if doc_path.suffix.lower() == '.txt':
                logger.info("尝试直接读取 TXT 文件...")
                try:
                    with open(doc_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    logger.info(f"TXT 文件读取成功 (文档长度: {len(content)} 字符)")
                except Exception as txt_error:
                    logger.error(f"读取 TXT 文件也失败: {txt_error}")
                    raise
            else:
                raise

        if not content.strip():
            logger.warning(f"文档内容为空: {document_path}")
            return

        logger.info(f"正在插入文档到知识图谱...")
        self.rag.insert(content)
        logger.info("文档插入完成")

    def query(self, question: str, mode: str = "hybrid") -> str:
        """
        查询知识图谱

        Args:
            question: 查询问题
            mode: 查询模式 (naive/local/global/hybrid)

        Returns:
            查询结果
        """
        if self.rag is None:
            raise ValueError("RAG 系统未初始化")

        logger.info(f"查询模式: {mode}")
        logger.info(f"查询问题: {question}")

        result = self.rag.query(
            question,
            param=QueryParam(mode=mode, only_need_context=True)
        )##only_need_prompt,only_need_context

        # Normalize result to a single string (handle str or iterator/generator of str)
        if isinstance(result, str):
            out_text = result
        else:
            # Try to join iterable of strings; if that fails, fallback to str()
            try:
                out_text = "".join(result)
            except TypeError:
                out_text = str(result)

        with open('output2.txt', 'w', encoding='utf-8') as f:
            f.write(out_text)

        return result


def main():
    """命令行接口入口"""

    parser = argparse.ArgumentParser(
        description="lightrag 知识图谱构建和查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--working_dir",
        type=str,
        required=True,
        help="lightrag 工作目录"
    )
    parser.add_argument(
        "--document_path",
        type=str,
        default=None,
        help="输入文档路径，支持 PDF、DOCX、TXT 等格式（可选）"
    )
    parser.add_argument(
        "--llm_model",
        type=str,
        default=None,
        help="LLM 模型名称（默认从环境变量 LLM_MODEL 读取，否则为 gpt-4）"
    )
    parser.add_argument(
        "--embedding_model",
        type=str,
        default=None,
        help="Embedding 模型路径或名称（默认从环境变量 EMBEDDING_MODEL 读取，否则为 sentence-transformers/all-MiniLM-L6-v2）"
    )
    parser.add_argument(
        "--embedding_dim",
        type=int,
        default=None,
        help="Embedding 维度（默认从环境变量 EMBEDDING_DIM 读取，否则为 384）"
    )
    parser.add_argument(
        "--embedding_max_token",
        type=int,
        default=None,
        help="Embedding 最大 token 数（默认从环境变量 EMBEDDING_MAX_TOKEN 读取，否则为 5000）"
    )
    parser.add_argument(
        "--litellm_url",
        type=str,
        default=None,
        help="LiteLLM 服务地址（默认从环境变量 LITELLM_URL 读取）"
    )
    parser.add_argument(
        "--litellm_key",
        type=str,
        default=None,
        help="LiteLLM API 密钥（默认从环境变量 LITELLM_KEY 读取）"
    )

    args = parser.parse_args()

    # 创建处理器
    processor = lightragProcessor(
        working_dir=args.working_dir,
        llm_model=args.llm_model,
        embedding_model=args.embedding_model,
        embedding_dim=args.embedding_dim,
        embedding_max_token=args.embedding_max_token,
        litellm_url=args.litellm_url,
        litellm_key=args.litellm_key
    )

    try:
        # 初始化 RAG 系统
        asyncio.run(processor.initialize_rag())

        # 如果提供了文档路径，则插入文档
        if args.document_path:
            processor.insert_document(args.document_path)

        # 进入交互式查询模式
        print("\n=== lightrag 系统就绪 ===")
        print("支持的查询模式: naive, local, global, hybrid")
        print("输入 'quit' 或 'exit' 退出\n")

        while True:
            question = input("请输入您的问题: ").strip()
            if question.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break
            if not question:
                continue

            # 询问查询模式
            mode = input("请选择查询模式 [naive/local/global/hybrid] (默认 hybrid): ").strip()
            if not mode:
                mode = "hybrid"
            if mode not in ["naive", "local", "global", "hybrid"]:
                print(f"无效的查询模式: {mode}，使用默认模式 hybrid")
                mode = "hybrid"

            try:
                print(f"\n正在查询...")
                answer = processor.query(question, mode=mode)
                print(f"\n答案:\n{answer}\n")
                print("-" * 50)
            except Exception as e:
                logger.error(f"查询时出错: {e}")
                print(f"查询失败: {e}")

    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        print(f"\n错误: {e}")


if __name__ == "__main__":
    main()