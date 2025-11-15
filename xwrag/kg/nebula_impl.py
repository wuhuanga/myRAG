import os
import re
import asyncio
from dataclasses import dataclass
from typing import final, Optional, Dict, Any, List
import configparser
import logging

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..utils import logger
from ..base import BaseGraphStorage
from ..types import KnowledgeGraph, KnowledgeGraphNode, KnowledgeGraphEdge
from ..constants import GRAPH_FIELD_SEP
from ..kg.shared_storage import get_data_init_lock, get_graph_db_lock
import pipmaster as pm

if not pm.is_installed("nebula3-python"):
    pm.install("nebula3-python")

from nebula3.gclient.net import ConnectionPool  # type: ignore
from nebula3.Config import Config  # type: ignore
from nebula3.common import ttypes  # type: ignore
from nebula3.Exception import (  # type: ignore
    IOErrorException,
    NotValidConnectionException,
    AuthFailedException,
)

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=False)
config = configparser.ConfigParser()
config.read("config.ini", "utf-8")

logging.getLogger("nebula3").setLevel(logging.ERROR)


@final
@dataclass
class NebulaGraphStorage(BaseGraphStorage):
    """
    改进版 NebulaGraph 实现 - 真正的多租户隔离:
    
    架构:
      workspace → Space (完全隔离,每个 workspace 独立的 NebulaGraph Space)
      固定 Tag → "entity" (统一的节点类型)
      
    优势:
      - 完全隔离: 每个 workspace 有独立的 Space
      - 性能更好: 查询只在自己的 Space 中
      - 管理简单: 删除 workspace 直接 DROP SPACE
      - namespace 不再使用,简化架构
    """

    # 🔥 修复1: 必需参数(无默认值)必须在可选参数(有默认值)之前
    namespace: str
    global_config: Dict[str, Any]
    embedding_func: Any
    workspace: Optional[str]  # 有默认值,放在最后

    def __post_init__(self):
        # 读取环境变量中的 workspace 配置
        nebula_workspace = os.environ.get("NEBULA_WORKSPACE")
        if nebula_workspace and nebula_workspace.strip():
            self.workspace = nebula_workspace

        # 默认使用 "base" workspace
        if not self.workspace or not str(self.workspace).strip():
            self.workspace = "base"

        super().__init__(
            namespace=self.namespace,
            workspace=self.workspace,
            global_config=self.global_config,
            embedding_func=self.embedding_func,
        )

        self._connection_pool: Optional[ConnectionPool] = None
        # 注意：不再维护持久的 self._session，每次查询创建独立 session 以避免泄漏
        
        # 使用 workspace 作为 Space 名称
        self._space_name = re.sub(r"[^a-zA-Z0-9_]", "_", self.workspace)
        
        # 使用固定的 Tag 名称
        self._tag_name = "entity"
        
        self._user = os.environ.get("NEBULA_USER", config.get("nebula", "user", fallback="root"))
        self._password = os.environ.get("NEBULA_PASSWORD", config.get("nebula", "password", fallback="nebula"))

        # 类型映射
        self._TYPE_MAP = [
            ("is_map", "as_map"),  # Map 类型必须在前面，因为 properties(vertex) 返回 Map
            ("is_list", "as_list"),
            ("is_set", "as_set"),
            ("is_string", "as_string"),
            ("is_int", "as_int"),
            ("is_double", "as_double"),
            ("is_bool", "as_bool"),
            ("is_date", "as_date"),
            ("is_time", "as_time"),
            ("is_datetime", "as_datetime"),
        ]

    def _get_workspace_label(self) -> str:
        """返回固定的 tag 名称"""
        return self._tag_name

    def _is_chinese_text(self, text: str) -> bool:
        """检查是否包含中文字符"""
        chinese_pattern = re.compile(r"[\u4e00-\u9fff]+")
        return bool(chinese_pattern.search(text))

    async def initialize(self):
        """初始化 NebulaGraph 连接和 Schema"""
        async with get_data_init_lock():
            NEBULA_HOSTS = os.environ.get(
                "NEBULA_HOSTS", config.get("nebula", "hosts", fallback="127.0.0.1:9669")
            )
            if not NEBULA_HOSTS:
                raise ValueError("NEBULA_HOSTS is required")

            # 解析 hosts
            hosts = []
            for host_str in NEBULA_HOSTS.split(","):
                host_str = host_str.strip()
                if ":" in host_str:
                    host, port = host_str.split(":")
                    hosts.append((host, int(port)))
                else:
                    hosts.append((host_str, 9669))

            # 配置连接池
            nebula_config = Config()
            nebula_config.max_connection_pool_size = int(
                os.environ.get("NEBULA_MAX_CONNECTION_POOL_SIZE", 10)
            )
            nebula_config.timeout = int(os.environ.get("NEBULA_TIMEOUT", 30000))

            # 初始化连接池
            self._connection_pool = ConnectionPool()
            if not self._connection_pool.init(hosts, nebula_config):
                raise ConnectionError("Failed to initialize NebulaGraph connection pool")

            # 使用临时 session 进行初始化（完成后立即释放）
            init_session = None
            try:
                # 创建临时 session 用于初始化
                init_session = self._connection_pool.get_session(self._user, self._password)
                
                # 使用 workspace 创建独立的 Space
                logger.info(
                    f"[{self.workspace}] Creating/Using Space: {self._space_name} "
                    f"(workspace-based isolation)"
                )

                # 先检查 space 是否存在
                check_space_query = f"SHOW SPACES"
                check_res = init_session.execute(check_space_query)
                space_exists = False
                
                if check_res.is_succeeded():
                    for row_index in range(check_res.row_size()):
                        row = check_res.row_values(row_index)
                        if row and len(row) > 0:
                            space_name_value = row[0]
                            # 转换值为字符串
                            if hasattr(space_name_value, 'as_string'):
                                space_name = space_name_value.as_string()
                            else:
                                space_name = str(space_name_value)
                            
                            if space_name.strip() == self._space_name:
                                space_exists = True
                                logger.info(f"[{self.workspace}] ✅ Space '{self._space_name}' already exists")
                                break
                
                # 如果 space 不存在,创建它
                if not space_exists:
                    logger.info(f"[{self.workspace}] 🔨 Creating new Space: {self._space_name}")
                    create_space_q = (
                        f"CREATE SPACE IF NOT EXISTS {self._space_name} "
                        f"(partition_num=10, replica_factor=1, vid_type=FIXED_STRING(256))"
                    )
                    res = init_session.execute(create_space_q)
                    if not res.is_succeeded():
                        error_msg = res.error_msg()
                        # 如果错误不是"space已存在",则记录警告
                        if "existed" not in error_msg.lower():
                            logger.warning(f"[{self.workspace}] Space creation message: {error_msg}")
                        else:
                            logger.info(f"[{self.workspace}] Space already exists (concurrent creation)")
                    else:
                        logger.info(f"[{self.workspace}] ✅ Successfully created Space: {self._space_name}")
                    
                    # 等待 Space 传播到集群(新建的 space 需要更长时间)
                    logger.info(f"[{self.workspace}] ⏳ Waiting for Space to be ready...")
                    await asyncio.sleep(5)

                # 切换到该 workspace 的 Space,带重试机制
                max_retries = 3
                retry_delay = 2
                use_success = False
                
                for retry in range(max_retries):
                    use_res = init_session.execute(f"USE {self._space_name}")
                    if use_res.is_succeeded():
                        use_success = True
                        logger.info(f"[{self.workspace}] ✅ Successfully switched to Space: {self._space_name}")
                        break
                    else:
                        error_msg = use_res.error_msg()
                        if retry < max_retries - 1:
                            logger.warning(
                                f"[{self.workspace}] Failed to USE space (attempt {retry + 1}/{max_retries}): "
                                f"{error_msg}, retrying in {retry_delay}s..."
                            )
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # 指数退避
                        else:
                            raise RuntimeError(
                                f"[{self.workspace}] Failed to USE space {self._space_name} after "
                                f"{max_retries} attempts: {error_msg}"
                            )
                
                if not use_success:
                    raise RuntimeError(f"[{self.workspace}] Could not USE space {self._space_name}")

                # 创建固定的 Tag "entity"
                tag_name = self._tag_name
                logger.info(
                    f"[{self.workspace}] Creating Tag: {tag_name} in Space: {self._space_name}"
                )
                
                create_tag_q = (
                    f"CREATE TAG IF NOT EXISTS {tag_name} "
                    f"(entity_id string, entity_type string, description string, source_id string, "
                    f"file_path string, created_at int)"
                )
                tag_res = init_session.execute(create_tag_q)
                if not tag_res.is_succeeded():
                    logger.warning(f"[{self.workspace}] Tag creation message: {tag_res.error_msg()}")

                # 创建 Edge type "relationship"
                create_edge_q = (
                    "CREATE EDGE IF NOT EXISTS relationship "
                    "(weight double, description string, keywords string, source_id string)"
                )
                edge_res = init_session.execute(create_edge_q)
                if not edge_res.is_succeeded():
                    logger.warning(f"[{self.workspace}] Edge creation message: {edge_res.error_msg()}")

                # 创建索引
                try:
                    # 创建entity_id索引（用于主键查询）
                    index_q = f"CREATE TAG INDEX IF NOT EXISTS idx_entity_id ON {tag_name}(entity_id(256))"
                    index_res = init_session.execute(index_q)
                    if index_res.is_succeeded():
                        logger.info(f"[{self.workspace}] Created index on {tag_name}.entity_id")
                    else:
                        logger.warning(f"[{self.workspace}] Index creation message: {index_res.error_msg()}")

                    # 创建source_id索引（用于按chunk_id过滤查询）
                    source_index_q = f"CREATE TAG INDEX IF NOT EXISTS idx_source_id ON {tag_name}(source_id(256))"
                    source_index_res = init_session.execute(source_index_q)
                    if source_index_res.is_succeeded():
                        logger.info(f"[{self.workspace}] Created index on {tag_name}.source_id")
                    else:
                        logger.warning(f"[{self.workspace}] source_id index message: {source_index_res.error_msg()}")
                except Exception as e:
                    logger.warning(f"[{self.workspace}] Index creation warning: {e}")

                # 等待 schema 传播（Tag和Edge需要2个心跳周期才能完全传播，每个周期默认10秒）
                # 对于新创建的space，需要等待更长时间确保schema可用
                wait_time = 15 if not space_exists else 10
                logger.info(f"[{self.workspace}] ⏳ Waiting {wait_time}s for schema propagation...")
                await asyncio.sleep(wait_time)

                logger.info(
                    f"[{self.workspace}] ✅ NebulaGraph initialized successfully:\n"
                    f"  Space: {self._space_name} (isolated per workspace)\n"
                    f"  Tag: {tag_name} (fixed)\n"
                    f"  Edge: relationship\n"
                    f"  Namespace: {self.namespace} (not used for isolation)"
                )

            except Exception as e:
                logger.error(f"[{self.workspace}] Failed to initialize NebulaGraph: {e}")
                if self._connection_pool:
                    self._connection_pool.close()
                raise
            finally:
                # 确保初始化 session 被释放（防止泄漏）
                if init_session:
                    try:
                        init_session.release()
                        logger.debug(f"[{self.workspace}] Released initialization session")
                    except Exception as release_error:
                        logger.warning(f"[{self.workspace}] Failed to release init session: {release_error}")

    async def finalize(self):
        """关闭连接"""
        if self._connection_pool:
            try:
                self._connection_pool.close()
            finally:
                self._connection_pool = None
                logger.info(f"[{self.workspace}] NebulaGraph connection pool closed")

    async def index_done_callback(self) -> None:
        """索引完成回调"""
        return None

    async def _execute_query(self, query: str):
        """执行查询 - 每次创建独立的 session 以避免泄漏"""
        if not self._connection_pool:
            raise RuntimeError("Connection pool not initialized")

        session = None
        max_retries = 5
        retry_delay = 0.5

        for attempt in range(max_retries):
            try:
                # 为每个查询创建独立的 session（避免并发竞争和 session 泄漏）
                # 如果连接池满，这里会抛出异常，我们需要重试
                session = self._connection_pool.get_session(self._user, self._password)
                break  # 成功获取 session，跳出重试循环
            except Exception as e:
                if attempt < max_retries - 1:
                    # 连接池可能已满，等待后重试
                    error_str = str(e).lower()
                    if "no available connection" in error_str or "connection" in error_str:
                        logger.warning(
                            f"[{self.workspace}] Connection pool exhausted (attempt {attempt + 1}/{max_retries}), "
                            f"waiting {retry_delay}s..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 5)  # 指数退避，最多等待 5 秒
                        continue
                # 最后一次重试失败或其他错误
                logger.error(f"[{self.workspace}] Failed to get session after {max_retries} attempts: {e}")
                raise

        if session is None:
            raise RuntimeError(f"[{self.workspace}] Could not acquire session from pool after {max_retries} attempts")

        try:

            # 切换到正确的 Space（带重试）
            use_success = False
            for use_attempt in range(3):
                try:
                    use_query = f"USE {self._space_name}"
                    logger.info(f"[{self.workspace}] Executing: {use_query}")
                    use_res = session.execute(use_query)
                    if use_res.is_succeeded():
                        use_success = True
                        logger.info(f"[{self.workspace}] ✓ Successfully switched to Space: {self._space_name}")
                        break
                    else:
                        if use_attempt < 2:
                            logger.warning(
                                f"[{self.workspace}] Failed to USE space (attempt {use_attempt + 1}/3): "
                                f"{use_res.error_msg()}"
                            )
                            await asyncio.sleep(0.5)
                        else:
                            raise RuntimeError(f"Failed to USE space {self._space_name}: {use_res.error_msg()}")
                except Exception as use_error:
                    if use_attempt < 2:
                        logger.warning(f"[{self.workspace}] Error using space (attempt {use_attempt + 1}/3): {use_error}")
                        await asyncio.sleep(0.5)
                    else:
                        raise

            if not use_success:
                raise RuntimeError(f"Could not USE space {self._space_name} after 3 attempts")

            # 打印要执行的查询语句（用于调试NebulaGraph语法）
            logger.info(f"[{self.workspace}] Executing NebulaGraph query: {query}")

            # 执行查询（带重试）
            def run_query():
                return session.execute(query)

            result = await asyncio.to_thread(run_query)
            if not result.is_succeeded():
                logger.error(
                    f"[{self.workspace}] Query failed in Space {self._space_name}: "
                    f"{result.error_msg()}\nQuery: {query}"
                )
                raise RuntimeError(f"Query execution failed: {result.error_msg()}")
            return result
        except Exception as e:
            logger.error(f"[{self.workspace}] Execute query error: {e}")
            raise
        finally:
            # 确保 session 总是被释放（防止泄漏）
            if session:
                try:
                    session.release()
                except Exception as release_error:
                    logger.warning(f"[{self.workspace}] Failed to release session: {release_error}")

    def _escape_string(self, s: Optional[str]) -> str:
        """转义字符串 - 处理所有 NebulaGraph 需要的特殊字符"""
        if s is None:
            return ""
        s = str(s)
        # 必须先转义反斜杠，再转义其他字符
        s = s.replace("\\", "\\\\")
        s = s.replace('"', '\\"')
        s = s.replace("'", "\\'")
        # 转义换行符和其他控制字符
        s = s.replace("\n", "\\n")
        s = s.replace("\r", "\\r")
        s = s.replace("\t", "\\t")
        return s

    def _format_properties(self, properties: Dict[str, Any]) -> str:
        """格式化属性 - 按照 Tag 定义的字段顺序"""
        # 定义字段顺序(与 Tag 定义一致)
        field_order = ["entity_id", "entity_type", "description", "source_id", "file_path", "created_at"]
        
        props = []
        for key in field_order:
            value = properties.get(key, "")  # 如果字段不存在,使用空字符串或默认值
            
            # 特殊处理 created_at,确保是整数
            if key == "created_at":
                if isinstance(value, (int, float)):
                    props.append(str(int(value)))
                else:
                    props.append("0")  # 默认值
            elif isinstance(value, str):
                props.append(f'"{self._escape_string(value)}"')
            elif isinstance(value, bool):
                props.append(str(value).lower())
            elif isinstance(value, (int, float)):
                props.append(str(value))
            else:
                props.append(f'"{self._escape_string(str(value))}"')
        
        return ", ".join(props)

    def _value_to_python(self, value):
        """将 Nebula value 转换为 Python 类型"""
        # 🔥 修复3: 安全地访问 properties 属性
        for check, getter in self._TYPE_MAP:
            if hasattr(value, check) and getattr(value, check)():
                result = getattr(value, getter)()

                # 递归处理嵌套类型
                if isinstance(result, dict):
                    # Map 类型: 递归转换字典中的值
                    return {k: self._value_to_python(v) for k, v in result.items()}
                elif isinstance(result, (list, set)):
                    # List/Set 类型: 递归转换列表/集合中的元素
                    return [self._value_to_python(item) for item in result]
                else:
                    return result

        if hasattr(value, "is_null") and value.is_null():
            return None
        return str(value)

    # ==================== 核心 API 方法 ====================

    async def has_node(self, node_id: str) -> bool:
        """检查节点是否存在"""
        # ✅ 移除全局锁以提高读性能（读操作不需要全局锁）
        try:
            tag = self._tag_name
            safe_id = self._escape_string(node_id)
            # 使用id()函数匹配VID，与其他查询保持一致
            query = f'MATCH (n:{tag}) WHERE id(n) == "{safe_id}" RETURN n LIMIT 1'
            result = await self._execute_query(query)
            return result.row_size() > 0
        except Exception as e:
            logger.error(f"[{self.workspace}] Error checking node existence: {e}")
            return False

    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        """检查边是否存在"""
        # ✅ 移除全局锁以提高读性能（读操作不需要全局锁）
        try:
            tag = self._tag_name
            src = self._escape_string(source_node_id)
            tgt = self._escape_string(target_node_id)
            # 修复：使用id()函数而不是entity_id属性
            query = (
                f'MATCH (a:{tag})-[r:relationship]-(b:{tag}) '
                f'WHERE id(a) == "{src}" AND id(b) == "{tgt}" RETURN r LIMIT 1'
            )
            result = await self._execute_query(query)
            return result.row_size() > 0
        except Exception as e:
            logger.error(f"[{self.workspace}] Error checking edge existence: {e}")
            return False

    async def node_degree(self, node_id: str) -> int:
        """获取节点度数"""
        # ✅ 移除全局锁以提高读性能（读操作不需要全局锁）
        try:
            tag = self._tag_name
            safe_id = self._escape_string(node_id)
            # 修复：使用id()函数而不是entity_id属性
            query = (
                f'MATCH (n:{tag})-[r:relationship]-(m:{tag}) '
                f'WHERE id(n) == "{safe_id}" RETURN count(r) AS degree'
            )
            result = await self._execute_query(query)
            if result.row_size() > 0:
                return int(result.row_values(0)[0].as_int())
            return 0
        except Exception as e:
            logger.error(f"[{self.workspace}] Error getting node degree: {e}")
            return 0

    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        """获取边度数"""
        src_degree = await self.node_degree(src_id)
        tgt_degree = await self.node_degree(tgt_id)
        return src_degree + tgt_degree

    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点数据"""
        # ✅ 移除全局锁以提高读性能（读操作不需要全局锁）
        try:
            tag = self._tag_name
            safe_id = self._escape_string(node_id)
            # 修复：使用FETCH PROP ON直接通过VID查询
            query = f'FETCH PROP ON {tag} "{safe_id}" YIELD properties(vertex)'
            result = await self._execute_query(query)

            # Debug logging
            logger.info(f"[{self.workspace}] get_node result row_size: {result.row_size()}")
            if result.row_size() == 0:
                logger.warning(f"[{self.workspace}] get_node returned 0 rows for node_id: {node_id}")
                return None

            # YIELD properties(vertex) 返回Map类型
            row = result.row_values(0)
            logger.info(f"[{self.workspace}] get_node row: len={len(row) if row else 0}, type={type(row)}")

            if row and len(row) > 0:
                props_value = row[0]
                logger.info(f"[{self.workspace}] get_node props_value type: {type(props_value)}")
                logger.info(f"[{self.workspace}] get_node props_value: {props_value}")

                # _value_to_python 现在可以直接处理 Map 类型并返回 Python 字典
                properties = self._value_to_python(props_value)
                logger.info(f"[{self.workspace}] get_node extracted properties: {properties}")

                if isinstance(properties, dict):
                    return properties
                else:
                    logger.warning(f"[{self.workspace}] Expected dict but got {type(properties)}: {properties}")
                    return None
            return None
        except Exception as e:
            logger.error(f"[{self.workspace}] Error getting node: {e}")
            return None

    async def get_nodes_batch(self, node_ids: list[str]) -> dict[str, dict]:
        """批量获取节点数据

        Args:
            node_ids: 要查询的节点ID列表

        Returns:
            字典，键为node_id，值为节点数据字典；未找到的节点不在返回字典中
        """
        if not node_ids:
            return {}

        try:
            tag = self._tag_name
            # 使用FETCH PROP ON直接通过VID批量查询（VID就是node_id）
            # NebulaGraph语法：FETCH PROP ON tag "vid1", "vid2" YIELD properties(vertex)
            escaped_ids = [f'"{self._escape_string(nid)}"' for nid in node_ids]
            ids_str = ", ".join(escaped_ids)
            query = f'FETCH PROP ON {tag} {ids_str} YIELD properties(vertex)'

            result = await self._execute_query(query)
            nodes = {}

            # Debug: Log result structure
            logger.info(f"[{self.workspace}] FETCH result row_size: {result.row_size()}")
            logger.info(f"[{self.workspace}] FETCH result columns: {result.keys()}")

            for i in range(result.row_size()):
                row = result.row_values(i)
                logger.info(f"[{self.workspace}] Row {i}: len={len(row) if row else 0}, type={type(row)}")

                if row and len(row) > 0:
                    # YIELD properties(vertex) 返回一个Map类型的值
                    props_value = row[0]
                    logger.info(f"[{self.workspace}] props_value type: {type(props_value)}, value: {props_value}")

                    # _value_to_python 现在可以直接处理 Map 类型并返回 Python 字典
                    properties = self._value_to_python(props_value)
                    logger.info(f"[{self.workspace}] Extracted properties: {properties}")

                    # 使用entity_id作为key
                    if isinstance(properties, dict) and 'entity_id' in properties:
                        nodes[properties['entity_id']] = properties
                        logger.info(f"[{self.workspace}] Added node with entity_id: {properties['entity_id']}")
                    else:
                        logger.warning(f"[{self.workspace}] Invalid properties or missing entity_id: {properties}")

            # 记录未找到的节点
            found_ids = set(nodes.keys())
            missing_ids = set(node_ids) - found_ids
            if missing_ids:
                logger.warning(
                    f"[{self.workspace}] get_nodes_batch: {len(missing_ids)} nodes not found: {list(missing_ids)[:5]}..."
                )

            return nodes

        except Exception as e:
            logger.error(f"[{self.workspace}] Error in get_nodes_batch: {e}")
            logger.error(f"[{self.workspace}] Query was: FETCH PROP ON {tag} ... YIELD properties(vertex)")
            # 降级到逐个查询
            logger.info(f"[{self.workspace}] Falling back to individual queries")
            result = {}
            for node_id in node_ids:
                node = await self.get_node(node_id)
                if node is not None:
                    result[node_id] = node
            return result

    async def get_edge(self, source_node_id: str, target_node_id: str) -> Optional[Dict[str, Any]]:
        """获取边数据"""
        # ✅ 移除全局锁以提高读性能（读操作不需要全局锁）
        try:
            tag = self._tag_name
            src = self._escape_string(source_node_id)
            tgt = self._escape_string(target_node_id)
            # 修复：使用MATCH ... RETURN properties(r)来获取边属性
            query = (
                f'MATCH (a:{tag})-[r:relationship]-(b:{tag}) '
                f'WHERE id(a) == "{src}" AND id(b) == "{tgt}" '
                f'RETURN properties(r) LIMIT 1'
            )
            result = await self._execute_query(query)
            if result.row_size() == 0:
                logger.warning(f"[{self.workspace}] get_edge: no edge found between {source_node_id} and {target_node_id}")
                return None

            # properties(r) 返回Map类型，与properties(vertex)类似
            row = result.row_values(0)
            if row and len(row) > 0:
                props_value = row[0]
                logger.info(f"[{self.workspace}] get_edge props_value type: {type(props_value)}")

                # _value_to_python 可以直接处理 Map 类型并返回 Python 字典
                properties = self._value_to_python(props_value)
                logger.info(f"[{self.workspace}] get_edge extracted properties: {properties}")

                if isinstance(properties, dict):
                    return properties
                else:
                    logger.warning(f"[{self.workspace}] Expected dict but got {type(properties)}")
                    return None
            return None
        except Exception as e:
            logger.error(f"[{self.workspace}] Error getting edge: {e}")
            return None

    async def get_node_edges(self, source_node_id: str) -> Optional[List[tuple]]:
        """获取节点的所有边"""
        # ✅ 移除全局锁以提高读性能（读操作不需要全局锁）
        try:
            tag = self._tag_name
            src = self._escape_string(source_node_id)
            # 修复：使用id()函数而不是entity_id属性，并返回id()
            query = (
                f'MATCH (a:{tag})-[r:relationship]-(b:{tag}) '
                f'WHERE id(a) == "{src}" RETURN id(a) AS src, id(b) AS tgt'
            )
            result = await self._execute_query(query)
            if result.row_size() == 0:
                return []
            edges = []
            for i in range(result.row_size()):
                row = result.row_values(i)
                src_val = self._value_to_python(row[0])
                tgt_val = self._value_to_python(row[1])
                edges.append((src_val, tgt_val))
            return edges
        except Exception as e:
            logger.error(f"[{self.workspace}] Error getting node edges: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((IOErrorException,)),
    )
    async def upsert_node(self, node_id: str, node_data: Dict[str, Any]) -> None:
        """插入或更新节点"""
        async with get_graph_db_lock():
            try:
                if "entity_id" not in node_data:
                    node_data["entity_id"] = node_id
                props_str = self._format_properties(node_data)
                tag = self._tag_name
                query = (
                    f'INSERT VERTEX IF NOT EXISTS {tag}(entity_id, entity_type, description, source_id, file_path, created_at) '
                    f'VALUES "{self._escape_string(node_id)}": ({props_str})'
                )
                # 添加调试日志（仅首次）
                if not hasattr(self, '_logged_first_insert'):
                    logger.info(f"[{self.workspace}] First node insert query: {query[:200]}...")
                    self._logged_first_insert = True

                await self._execute_query(query)
            except Exception as e:
                logger.error(f"[{self.workspace}] Error upserting node {node_id}: {e}")
                logger.error(f"[{self.workspace}] Failed query: {query[:300]}...")
                raise

    async def upsert_nodes(self, nodes: List[tuple]):
        """批量插入或更新节点"""
        async with get_graph_db_lock():
            if not nodes:
                return
            try:
                tag = self._tag_name
                batch_values = []
                for node_id, node_data in nodes:
                    if "entity_id" not in node_data:
                        node_data["entity_id"] = node_id
                    props_str = self._format_properties(node_data)
                    batch_values.append(f'"{self._escape_string(node_id)}": ({props_str})')
                
                query = (
                    f'INSERT VERTEX IF NOT EXISTS {tag}(entity_id, entity_type, description, source_id, file_path, created_at) '
                    f'VALUES {", ".join(batch_values)}'
                )
                await self._execute_query(query)
            except Exception as e:
                logger.error(f"[{self.workspace}] Error upserting nodes batch: {e}")
                raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((IOErrorException,)),
    )
    async def upsert_edge(self, source_node_id: str, target_node_id: str, edge_data: Dict[str, Any]) -> None:
        """插入或更新边

        注意：此方法假设调用者已经确保节点存在（由 operate.py 保证）
        不再重复检查节点存在性，以提高性能
        """
        # 移除全局锁，使用 INSERT EDGE 的原子性
        # NebulaGraph 的 INSERT EDGE 是原子操作，不需要全局锁保护
        try:
            weight = edge_data.get("weight", 1.0)
            description = self._escape_string(edge_data.get("description", ""))
            keywords = self._escape_string(edge_data.get("keywords", ""))
            source_id = self._escape_string(edge_data.get("source_id", ""))

            # INSERT EDGE 是幂等的，重复插入会更新
            query = (
                f'INSERT EDGE relationship(weight, description, keywords, source_id) VALUES '
                f'"{self._escape_string(source_node_id)}" -> "{self._escape_string(target_node_id)}": '
                f'({weight}, "{description}", "{keywords}", "{source_id}")'
            )
            await self._execute_query(query)
        except Exception as e:
            logger.error(f"[{self.workspace}] Error upserting edge {source_node_id}->{target_node_id}: {e}")
            raise

    async def upsert_edges(self, edges: List[tuple]):
        """批量插入或更新边"""
        async with get_graph_db_lock():
            if not edges:
                return
            try:
                for src_id, tgt_id, edge_data in edges:
                    await self.upsert_edge(src_id, tgt_id, edge_data)
            except Exception as e:
                logger.error(f"[{self.workspace}] Error upserting edges batch: {e}")
                raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((IOErrorException,)),
    )
    async def delete_node(self, node_id: str) -> None:
        """删除节点"""
        async with get_graph_db_lock():
            try:
                query = f'DELETE VERTEX "{self._escape_string(node_id)}" WITH EDGE'
                await self._execute_query(query)
            except Exception as e:
                logger.error(f"[{self.workspace}] Error deleting node {node_id}: {e}")
                raise

    async def remove_nodes(self, nodes: List[str]):
        """批量删除节点"""
        async with get_graph_db_lock():
            if not nodes:
                return
            try:
                node_list = ", ".join(f'"{self._escape_string(n)}"' for n in nodes)
                query = f'DELETE VERTEX {node_list} WITH EDGE'
                await self._execute_query(query)
            except Exception as e:
                logger.error(f"[{self.workspace}] Error removing nodes: {e}")
                raise

    async def remove_edges(self, edges: List[tuple]):
        """批量删除边"""
        async with get_graph_db_lock():
            try:
                if not edges:
                    return
                for src_id, tgt_id in edges:
                    q = (
                        f'DELETE EDGE relationship "{self._escape_string(src_id)}" -> '
                        f'"{self._escape_string(tgt_id)}"'
                    )
                    await self._execute_query(q)
            except Exception as e:
                logger.error(f"[{self.workspace}] Error removing edges: {e}")
                raise

    async def get_all_labels(self) -> List[str]:
        """获取所有节点标签"""
        async with get_graph_db_lock():
            try:
                tag = self._tag_name
                query = f'MATCH (n:{tag}) RETURN DISTINCT n.entity_id AS label'
                result = await self._execute_query(query)
                labels: List[str] = []
                for i in range(result.row_size()):
                    val = self._value_to_python(result.row_values(i)[0])
                    if isinstance(val, str):
                        labels.append(val)
                return sorted(labels)
            except Exception as e:
                logger.error(f"[{self.workspace}] Error getting all labels: {e}")
                return []

    async def get_all_nodes(self) -> List[Dict[str, Any]]:
        """获取所有节点"""
        async with get_graph_db_lock():
            try:
                tag = self._tag_name
                # 修复：使用id(n)和properties(n)
                query = f'MATCH (n:{tag}) RETURN id(n) AS id, properties(n)'
                result = await self._execute_query(query)
                nodes = []
                for i in range(result.row_size()):
                    row = result.row_values(i)
                    node_id = self._value_to_python(row[0])
                    props_value = row[1]

                    node_data = {"id": node_id}
                    # _value_to_python 可以直接处理 Map 类型
                    props = self._value_to_python(props_value)
                    if isinstance(props, dict):
                        node_data.update(props)

                    nodes.append(node_data)
                return nodes
            except Exception as e:
                logger.error(f"[{self.workspace}] Error getting all nodes: {e}")
                return []

    async def get_all_edges(self) -> List[Dict[str, Any]]:
        """获取所有边"""
        async with get_graph_db_lock():
            try:
                tag = self._tag_name
                # 修复：使用properties(r)来获取边属性
                query = f'MATCH (a:{tag})-[r:relationship]-(b:{tag}) RETURN id(a) AS src, id(b) AS tgt, properties(r)'
                result = await self._execute_query(query)
                edges = []
                for i in range(result.row_size()):
                    row = result.row_values(i)
                    src = self._value_to_python(row[0])
                    tgt = self._value_to_python(row[1])
                    props_value = row[2]

                    edge_data = {"source": src, "target": tgt}
                    # _value_to_python 可以直接处理 Map 类型
                    props = self._value_to_python(props_value)
                    if isinstance(props, dict):
                        edge_data.update(props)

                    edges.append(edge_data)
                return edges
            except Exception as e:
                logger.error(f"[{self.workspace}] Error getting all edges: {e}")
                return []

    # 🔥 修复6: 实现缺失的抽象方法
    async def get_nodes_by_chunk_ids(self, chunk_ids: list[str]) -> list[dict]:
        """根据 chunk_ids 获取相关节点"""
        async with get_graph_db_lock():
            try:
                if not chunk_ids:
                    return []

                tag = self._tag_name
                # 转义并构建查询
                safe_chunk_ids = [f'"{self._escape_string(cid)}"' for cid in chunk_ids]
                chunk_ids_str = ", ".join(safe_chunk_ids)

                # 使用LOOKUP ON来利用source_id索引进行高效查询
                query = (
                    f'LOOKUP ON {tag} '
                    f'WHERE {tag}.source_id IN [{chunk_ids_str}] '
                    f'YIELD properties(vertex) AS props'
                )
                result = await self._execute_query(query)

                nodes = []
                for i in range(result.row_size()):
                    props_value = result.row_values(i)[0]

                    # _value_to_python 可以直接处理 Map 类型
                    node_data = self._value_to_python(props_value)
                    if isinstance(node_data, dict):
                        nodes.append(node_data)

                return nodes
            except Exception as e:
                logger.error(f"[{self.workspace}] Error getting nodes by chunk_ids: {e}")
                return []

    async def get_edges_by_chunk_ids(self, chunk_ids: list[str]) -> list[dict]:
        """根据 chunk_ids 获取相关边"""
        async with get_graph_db_lock():
            try:
                if not chunk_ids:
                    return []

                tag = self._tag_name
                # 转义并构建查询
                safe_chunk_ids = [f'"{self._escape_string(cid)}"' for cid in chunk_ids]
                chunk_ids_str = ", ".join(safe_chunk_ids)

                # 修复：使用properties(r)来获取边属性，使用id()来获取节点ID
                query = (
                    f'MATCH (a:{tag})-[r:relationship]-(b:{tag}) '
                    f'WHERE r.source_id IN [{chunk_ids_str}] '
                    f'RETURN id(a) AS src, id(b) AS tgt, properties(r)'
                )
                result = await self._execute_query(query)

                edges = []
                for i in range(result.row_size()):
                    row = result.row_values(i)
                    src = self._value_to_python(row[0])
                    tgt = self._value_to_python(row[1])
                    props_value = row[2]

                    edge_data = {"source": src, "target": tgt}
                    # _value_to_python 可以直接处理 Map 类型
                    props = self._value_to_python(props_value)
                    if isinstance(props, dict):
                        edge_data.update(props)

                    edges.append(edge_data)

                return edges
            except Exception as e:
                logger.error(f"[{self.workspace}] Error getting edges by chunk_ids: {e}")
                return []

    async def get_popular_labels(self, limit: int = 300) -> List[str]:
        """获取热门标签"""
        async with get_graph_db_lock():
            try:
                tag = self._tag_name
                # 修复：使用id(n)并添加GROUP BY子句用于聚合
                query = (
                    f'MATCH (n:{tag})-[r:relationship]-(m:{tag}) '
                    f'RETURN id(n) AS label, count(r) AS degree '
                    f'ORDER BY degree DESC LIMIT {limit}'
                )
                result = await self._execute_query(query)
                labels: List[str] = []
                for i in range(result.row_size()):
                    val = self._value_to_python(result.row_values(i)[0])
                    if isinstance(val, str):
                        labels.append(val)
                return labels
            except Exception as e:
                logger.error(f"[{self.workspace}] Error getting popular labels: {e}")
                return []

    async def search_labels(self, query: str, limit: int = 50) -> List[str]:
        """搜索标签"""
        tag = self._tag_name
        query_strip = query.strip()
        if not query_strip:
            return []

        query_lower = query_strip.lower()
        is_chinese = self._is_chinese_text(query_strip)

        async with get_graph_db_lock():
            try:
                if is_chinese:
                    nql = (
                        f'MATCH (n:{tag}) '
                        f'WHERE n.entity_id CONTAINS "{self._escape_string(query_strip)}" '
                        f'RETURN n.entity_id AS label LIMIT {limit * 2}'
                    )
                    result = await self._execute_query(nql)
                    
                    labels = []
                    for i in range(result.row_size()):
                        label = self._value_to_python(result.row_values(i)[0])
                        if isinstance(label, str):
                            labels.append(label)
                    
                    def chinese_score(label):
                        if label == query_strip:
                            return 1000
                        elif label.startswith(query_strip):
                            return 500
                        else:
                            return 100 - len(label)
                    
                    labels.sort(key=chinese_score, reverse=True)
                    return labels[:limit]
                    
                else:
                    nql = (
                        f'MATCH (n:{tag}) '
                        f'WHERE n.entity_id IS NOT NULL '
                        f'RETURN n.entity_id AS label LIMIT {limit * 3}'
                    )
                    result = await self._execute_query(nql)
                    
                    labels = []
                    for i in range(result.row_size()):
                        label = self._value_to_python(result.row_values(i)[0])
                        if not isinstance(label, str):
                            continue
                        label_lower = label.lower()
                        if query_lower in label_lower:
                            labels.append(label)
                    
                    def latin_score(label):
                        label_lower = label.lower()
                        if label_lower == query_lower:
                            return 1000
                        elif label_lower.startswith(query_lower):
                            return 500
                        elif ' ' + query_lower in label_lower or '_' + query_lower in label_lower:
                            return 50
                        else:
                            return 100 - len(label)
                    
                    labels.sort(key=latin_score, reverse=True)
                    return labels[:limit]
                    
            except Exception as e:
                logger.error(f"[{self.workspace}] Error searching labels: {e}")
                return []

    async def get_knowledge_graph(self, node_label: str, max_depth: int = 3, max_nodes: int = 1000) -> KnowledgeGraph:
        """获取知识图谱"""
        async with get_graph_db_lock():
            try:
                tag = self._tag_name
                nodes = []
                node_ids = set()

                if node_label == "*":
                    nodes_query = f'MATCH (n:{tag}) RETURN n.entity_id AS id, n LIMIT {max_nodes}'
                else:
                    nodes_query = (
                        f'MATCH (n:{tag}) WHERE n.entity_id CONTAINS "{self._escape_string(node_label)}" '
                        f'RETURN n.entity_id AS id, n LIMIT {max_nodes}'
                    )

                nodes_result = await self._execute_query(nodes_query)
                for i in range(nodes_result.row_size()):
                    row = nodes_result.row_values(i)
                    node_id = self._value_to_python(row[0])
                    node_value = row[1]
                    node_data = {}
                    if hasattr(node_value, 'properties') and node_value.properties:
                        for key, value in node_value.properties.items():
                            node_data[key] = self._value_to_python(value)
                    nodes.append(KnowledgeGraphNode(id=node_id, **node_data))
                    node_ids.add(node_id)

                edges = []
                if node_ids:
                    node_list = ", ".join(f'"{self._escape_string(nid)}"' for nid in node_ids)
                    edges_query = (
                        f'MATCH (a:{tag})-[r:relationship]-(b:{tag}) '
                        f'WHERE a.entity_id IN [{node_list}] AND b.entity_id IN [{node_list}] '
                        f'RETURN a.entity_id AS src, b.entity_id AS tgt, r'
                    )
                    edges_result = await self._execute_query(edges_query)
                    for i in range(edges_result.row_size()):
                        row = edges_result.row_values(i)
                        src = self._value_to_python(row[0])
                        tgt = self._value_to_python(row[1])
                        edge_value = row[2]
                        edge_data = {}
                        if hasattr(edge_value, 'properties') and edge_value.properties:
                            for key, value in edge_value.properties.items():
                                edge_data[key] = self._value_to_python(value)
                        edges.append(KnowledgeGraphEdge(source_id=src, target_id=tgt, **edge_data))

                return KnowledgeGraph(nodes=nodes, edges=edges)
            except Exception as e:
                logger.error(f"[{self.workspace}] Error getting knowledge graph: {e}")
                return KnowledgeGraph(nodes=[], edges=[])

    async def embed_nodes(self, algorithm: str) -> tuple[KnowledgeGraph, dict]:
        """对节点进行嵌入"""
        kg = await self.get_knowledge_graph("*", max_nodes=10000)
        embeddings = {}
        for node in kg.nodes:
            embeddings[node.id] = [0.0] * 128
        return kg, embeddings

    async def drop(self):
        """删除整个 workspace 的数据"""
        async with get_graph_db_lock():
            try:
                logger.warning(
                    f"[{self.workspace}] Dropping entire Space: {self._space_name}"
                )

                if self._connection_pool:
                    temp_session = self._connection_pool.get_session(self._user, self._password)
                    try:
                        drop_query = f"DROP SPACE IF EXISTS {self._space_name}"
                        result = temp_session.execute(drop_query)
                        if result.is_succeeded():
                            logger.info(f"[{self.workspace}] ✅ Dropped Space: {self._space_name}")
                        else:
                            logger.error(
                                f"[{self.workspace}] Failed to drop Space {self._space_name}: "
                                f"{result.error_msg()}"
                            )
                    finally:
                        temp_session.release()
                    
            except Exception as e:
                logger.error(f"[{self.workspace}] Error dropping Space {self._space_name}: {e}")
                raise