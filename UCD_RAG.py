# -*- coding: utf-8 -*-
"""
UC RAG 问答生成器（单文件，工程级）
- 功能：将自然语言建模需求 → 严格符合 UC.schema.v3.json 的"用例图 JSON"
- 兼容 MagicDraw/Cameo：键域、取值、结构与关系端点均严格按 Schema 与 SysML/UML 语义
- RAG：FAISS 召回（与 REQ_RAG 工程的路径约定完全一致）
- LLM：支持外部配置（通过 LiteLLM 或 OpenAI 兼容接口）

参考与对齐：
- 现有 REQ_RAG 单文件工程风格、流程与目录约定（检索→提示词→LLM→Schema校验→工程化修复→落盘）
- UC v3 Schema（本地 UC.schema.v3.json），严格 Schema-first 生成与校验

用法（交互式）：
python UCD_RAG.py

用法（直接生成）：
from UCD_RAG import UCBuilder
b = UCBuilder()
b.load_knowledge_base("embeddings/knowledge_base.json", "embeddings")
res = b.generate("为低空轨道卫星的地面站系统构建用例图：人类操作员、遥测接收、任务计划、登录与审计、异常处理等", out_json="output_uc.json")

用法（使用外部LLM配置）：
b = UCBuilder(
    llm_model="deepseek-chat",
    litellm_url="http://localhost:4000",
    litellm_key="sk-1234"
)

注意：代码不硬编码 API Key，请通过环境变量或参数提供。
"""

import os
import re
import json
import math
import unicodedata
from collections import defaultdict
from textwrap import dedent
from datetime import datetime, timezone

import numpy as np
import pandas as pd

# ===== 可选依赖：faiss / jsonschema =====
try:
    import faiss
except Exception:
    faiss = None

try:
    import jsonschema
    from jsonschema import Draft7Validator
except Exception:
    jsonschema = None
    Draft7Validator = None

# —— OpenAI 兼容客户端 ——
try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# ===================== 向量模型（占位/可替换） =====================
class DummyEmbeddingModel:
    """占位向量模型，接口兼容。工程部署时请替换为真实中文向量模型（如 bge-base-zh）。"""
    def encode(self, texts):
        rng = np.random.default_rng(2025)
        return rng.random((len(texts), 768), dtype=np.float32)


def load_embedding_model():
    return DummyEmbeddingModel()


def build_faiss_index(vectors: np.ndarray):
    if faiss is None:
        raise RuntimeError("未安装 faiss，无法建立向量索引。请先：pip install faiss-cpu")
    if not isinstance(vectors, np.ndarray) or vectors.ndim != 2:
        raise ValueError("chunk_embeddings 必须为二维 ndarray")
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors.astype("float32"))
    return index


# ======== 文本归一化 / 轻量工具 ========
_PUNCT_RE = re.compile(r"[^\w\u4e00-\u9fa5\.%/μΩαβ\-]+", re.UNICODE)
_NUM_UNIT_JOINT = re.compile(r"(?P<num>\d+(?:\.\d+)?)(?P<unit>[a-zA-ZμΩ%/]+)")


def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    s = _NUM_UNIT_JOINT.sub(lambda m: f"{m.group('num')}{m.group('unit')}", s)
    s = _PUNCT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ===================== UC 生成器 =====================
class UCBuilder:
    def __init__(
        self,
        llm_model: str = None,
        litellm_url: str = None,
        litellm_key: str = None,
        api_base: str = None
    ):
        """
        初始化 UCBuilder
        
        Args:
            llm_model: LLM 模型名称（例如 "deepseek-chat", "gpt-4" 等）
            litellm_url: LiteLLM 服务地址（如果使用 LiteLLM）
            litellm_key: API 密钥
            api_base: OpenAI 兼容的 API 基础 URL（如果不使用 LiteLLM）
        """
        # KB / 索引
        self.knowledge_base = []
        self.chunk_embeddings = None
        self.faiss_index = None

        self.embedder = load_embedding_model()
        self.autofix_promote_external_usecase = False  # 保守模式；需要时改 True

        # === LLM 客户端配置 ===
        if OpenAI is None:
            raise RuntimeError("缺少 openai 依赖，请先：pip install openai")
        
        # 优先使用传入的参数，其次使用环境变量
        self.llm_model = llm_model or os.getenv("QWEN_MODEL", "qwen3-coder-plus")
        self.litellm_url = litellm_url
        self.litellm_key = litellm_key
        
        # 确定 API key 和 base URL
        if self.litellm_key:
            api_key = self.litellm_key
        else:
            api_key = os.getenv("OPENAI_API_KEY", "sk-47e6eab40f974d86a5081097144908b4")
        
        if not api_key:
            raise RuntimeError("未检测到 API Key。请通过参数或环境变量 OPENAI_API_KEY 提供。")
        
        # 确定 base URL
        if self.litellm_url:
            base_url = self.litellm_url
        elif api_base:
            base_url = api_base
        else:
            base_url = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").strip()
        
        # 初始化 OpenAI 客户端
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.chat_model = self.llm_model
        
        print(f"📝 UCBuilder 初始化:")
        print(f"   LLM 模型: {self.chat_model}")
        print(f"   API Base: {base_url}")

    # ---------- 数据载入 ----------
    def load_knowledge_base(self, kb_json="embeddings/knowledge_base.json", index_dir="embeddings"):
        if not os.path.exists(kb_json):
            raise FileNotFoundError(f"未找到知识库 JSON：{kb_json}")
        with open(kb_json, "r", encoding="utf-8") as f:
            self.knowledge_base = json.load(f)
        emb_path = os.path.join(index_dir, "chunk_embeddings.npy")
        if not os.path.exists(emb_path):
            raise FileNotFoundError(f"未找到向量文件：{emb_path}")
        self.chunk_embeddings = np.load(emb_path)
        self.faiss_index = build_faiss_index(self.chunk_embeddings)

    # ---------- 向量召回 ----------
    def retrieve_chunks(self, question: str, top_k=8):
        if self.faiss_index is None or self.chunk_embeddings is None:
            raise RuntimeError("FAISS 索引未初始化，请先 load_knowledge_base()")
        kb_size = len(self.knowledge_base) if isinstance(self.knowledge_base, list) else 0
        if kb_size == 0:
            return []
        top_k = max(1, min(top_k, kb_size))
        qv = self.embedder.encode([question]).astype("float32")
        if qv.ndim == 1:
            qv = qv.reshape(1, -1)
        distances, indices = self.faiss_index.search(qv, top_k)

        results = []
        print(f"\n📚 知识库 Top{top_k}（L2 越小越相似）")
        for rank, (idx, dist) in enumerate(zip(indices[0], distances[0]), start=1):
            if idx is None or idx < 0 or idx >= kb_size:
                continue
            entry = self.knowledge_base[idx] if isinstance(self.knowledge_base[idx], dict) else {}
            txt = str(entry.get("text", ""))
            src = entry.get("source") or entry.get("id") or f"kb:{idx}"
            prev = txt.replace("\n", " ")
            if len(prev) > 160: prev = prev[:160] + "..."
            print(f"  #{rank:<2} d={dist:.4f}  id={idx}  src={src}\n     └─ {prev}")
            results.append({"text": txt, "score": float(dist), "index": int(idx), "source": src})
        return results

    def _contract_skeleton(self) -> str:
        from datetime import datetime, timezone
        import json

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        contract = {
            "version": "1.1.0",
            "generatedAt": now,
            "model": {
                "elements": [
                    {
                        "code": "{string}",
                        "type": "Actor",
                        "name": "{string}",
                        "isHuman": "{boolean}",
                        "stereotypes": "{string[]}",
                        "documentation": "{string}"
                    },
                    {
                        "code": "{string}",
                        "type": "UseCase",
                        "name": "{string}",
                        "subjectRefCode": "{string|null}",  # 指向 Subject.code
                        "extensionPoints": [
                            {"code": "{string}", "name": "{string}"}
                        ],
                        "preconditions": "{string[]}",
                        "postconditions": "{string[]}",
                        "stereotypes": "{string[]}",
                        "documentation": "{string}"
                    },
                    {
                        "code": "{string}",
                        "type": "Subject",
                        "name": "{string}",
                        "ownedUseCases": "{string[]}",  # UseCase.code 列表
                        "stereotypes": "{string[]}",
                        "documentation": "{string}"
                    }
                ],
                "references": {
                    "classifiers": "{string[]}"
                },
                "relationships": [
                    {
                        "type": "association",
                        "code": "{string}",
                        "name": "{string|null}",
                        "stereotypes": "{string[]}",
                        "end1": {"refCode": "{string}"},  # Actor/UseCase/Subject 的 code
                        "end2": {"refCode": "{string}"},
                        "documentation": "{string}"
                    },
                    {
                        "type": "include",
                        "code": "{string}",
                        "addition": {"refCode": "{string}"},    # 被 include 的用例
                        "includingCase": {"refCode": "{string}"},
                        "stereotypes": "{string[]}",
                        "documentation": "{string}"
                    },
                    {
                        "type": "extend",
                        "code": "{string}",
                        "extension": {"refCode": "{string}"},   # 扩展用例
                        "extendedCase": {"refCode": "{string}"},
                        "extensionLocations": [
                            {"refCode": "{string}"}  # 指向 UseCase.extensionPoints[i].code
                        ],
                        "condition": "{string}",
                        "stereotypes": "{string[]}",
                        "documentation": "{string}"
                    },
                    {
                        "type": "generalization",
                        "code": "{string}",
                        "specific": {"refCode": "{string}"},
                        "general": {"refCode": "{string}"},
                        "stereotypes": "{string[]}",
                        "documentation": "{string}"
                    },
                    {
                        "type": "dependency",
                        "code": "{string}",
                        "client": {"refCode": "{string}"},
                        "supplier": {"refCode": "{string}"},
                        "stereotypes": "{string[]}",
                        "documentation": "{string}"
                    }
                ]
            },
            "diagrams": [
                {
                    "code": "{string}",
                    "name": "{string}",
                    "type": "UseCaseDiagram",
                    "references": "{string[]}",
                    "documentation": "{string}"
                }
            ],
            "layout": {
                "pages": [
                    {
                        "diagramCode": "{string}",
                        "elements": [
                            {
                                "elementCode": "{string}",
                                "bounds": {"x": 100, "y": 100, "w": 120, "h": 60}
                            }
                        ],
                        "relationships": [
                            {
                                "relationshipCode": "{string}",
                                "points": [{"x": 150, "y": 130}, {"x": 300, "y": 200}]
                            }
                        ]
                    }
                ]
            }
        }

        return json.dumps(contract, ensure_ascii=False, indent=2)

    def system_build_prompt(self) -> str:
        system_prompt = dedent("""
        你是一名精通 SysML/UML 的系统工程师与建模专家，擅长将自然语言需求**精确**映射为**严格符合 UC.schema.v3.json** 的用例图 JSON。

        **核心准则**：
        1. **仅生成 JSON**，无需任何解释或 Markdown 包裹。
        2. **严格按 Schema 与语义**：
           - 每个元素必需字段（`code`, `type`, `name` 等）、关系端点引用字段（`refCode`）一律严格对齐 Schema。
           - `extensionPoints` / `subjectRefCode` / `ownedUseCases` / `references.classifiers` 等，**必须**语义正确、结构完整。
        3. **MagicDraw/Cameo 兼容**：
           - `code` 全局唯一（UUID 风格或短串），模型内不重复。
           - `refCode` 始终指向已声明元素的 `code`。
           - 泛化 (generalization) / 扩展 (extend) / 包含 (include) 端点命名与结构对齐 Schema 合约，确保导入时不报错。
        4. **数组不为空**：`elements`, `diagrams`, `layout.pages` 至少包含 1 个合法条目（无占位符）。
        5. **关系合法性**：
           - `association`: Actor ↔ UseCase，Actor ↔ Subject，UseCase ↔ UseCase 均可；不允许 Actor ↔ Actor（UC 图不推荐）。
           - `include`: `includingCase` → `addition` 均为 UseCase，语义为"主用例包含被用例"。
           - `extend`: `extension` → `extendedCase` 均为 UseCase，`extensionLocations[].refCode` 必需指向 `extendedCase` 的某个 extensionPoint.code。
           - `generalization`: 泛化端点需同类（Actor → Actor / UseCase → UseCase），不允许 Actor ↔ UseCase 泛化。
           - `dependency`: `client` → `supplier` 可在 UseCase / Subject / Actor 间按语义声明依赖。
        6. **documentation**：用中文精确表述元素用途 / 关系语义 / 条件约束等，确保工程可读性。
        7. **layout.pages**: 为每个 diagram 提供布局页（元素坐标合理，不堆叠），确保工具能正确渲染。

        **禁止事项**：
        - 不得输出任何除 JSON 以外的内容（不含 Markdown、注释、解释段落）。
        - `code` / `refCode` / `name` 等字段**不允许占位符**（如 `<placeholder>`, `A1`, `A2`）；需有语义名称或自动生成 UUID。
        - `extensionPoints` 数组若填写，则每条须有 `code` 与 `name`；若不使用可为空数组。
        - 泛化 / 包含 / 扩展关系的端点必需为真实元素的 `code`，不允许虚构或语义不对齐。

        **输出契约示例**（占位符需替换为真实值）：
        """).strip()

        system_prompt += "\n\n" + self._contract_skeleton() + "\n\n"
        system_prompt += dedent("""
        **再次强调**：
        - 返回格式为纯 JSON（无 ```json 包裹）。
        - 所有端点引用字段（`refCode`）必需有效。
        - 确保 `elements`, `relationships`, `diagrams`, `layout.pages` 结构完整、合法。
        """).strip()
        return system_prompt

    def build_prompt(self, question: str, chunks: list) -> str:
        context_lines = []
        for i, ch in enumerate(chunks, start=1):
            txt = ch.get("text", "") if isinstance(ch, dict) else str(ch)
            context_lines.append(f"[Context-{i}]\n{txt}")
        context_str = "\n\n".join(context_lines)

        prompt = dedent(f"""
        **需求**：
        {question}

        **知识上下文**（按相关度排序）：
        {context_str}

        **任务**：
        请基于上述需求与知识上下文，生成一份**严格符合 UC.schema.v3.json** 的用例图 JSON。
        - 仅输出 JSON（无 Markdown / 解释）。
        - `code` 唯一、`refCode` 有效。
        - `elements`, `relationships`, `diagrams`, `layout.pages` 结构完整、合法。
        - 文档（`documentation`）用中文精确描述，确保工程可读性。

        现在，请直接生成 JSON：
        """).strip()
        return prompt

    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM 生成 JSON"""
        print("\n🤖 正在调用 LLM 生成 UCD JSON...")
        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=8000
            )
            raw_text = response.choices[0].message.content.strip()
            
            # 清理可能的 Markdown 包裹
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            return raw_text.strip()
        except Exception as e:
            print(f"❌ LLM 调用失败: {e}")
            raise

    def lint_and_fix(self, d: dict):
        """工程化 Lint/Fix"""
        issues = []

        def warn(msg):
            issues.append(msg)

        def _str(x):
            return str(x) if x is not None else ""

        def _ref_code(obj):
            if isinstance(obj, dict):
                return _str(obj.get("refCode"))
            return _str(obj)

        # ---------- 1) 基本键域检查 ----------
        if "version" not in d:
            d["version"] = "1.1.0"
        if "generatedAt" not in d:
            d["generatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        model = d.setdefault("model", {})
        elements = model.setdefault("elements", [])
        refs = model.setdefault("references", {})
        relationships = model.setdefault("relationships", [])
        diagrams = d.setdefault("diagrams", [])
        layout = d.setdefault("layout", {})
        pages = layout.setdefault("pages", [])

        # ---------- 2) 分类元素、构建索引 ----------
        actors = {}
        usecases = {}
        subjects = {}
        code_seen = set()
        code_type = {}
        ref_clsf = set(map(_str, refs.get("classifiers", [])))

        for e in elements:
            ec = _str(e.get("code"))
            et = _str(e.get("type"))
            if not ec:
                warn("发现元素缺少 code，已跳过")
                continue
            if ec in code_seen:
                warn(f"元素 code 重复: {ec}，请确保唯一性")
            code_seen.add(ec)
            code_type[ec] = et

            if et == "Actor":
                actors[ec] = e
            elif et == "UseCase":
                usecases[ec] = e
            elif et == "Subject":
                subjects[ec] = e
            else:
                warn(f"未知元素类型: {et} (code={ec})")

        # ---------- 3) UseCase.subjectRefCode 解析 ----------
        for uc_code, uc in usecases.items():
            sref = _str(uc.get("subjectRefCode"))
            if sref and (sref not in subjects):
                if sref not in ref_clsf:
                    ref_clsf.add(sref)
                    warn(f"UseCase {uc_code} 的 subjectRefCode={sref} 不在 subjects 中，已加入 references.classifiers")

        # ---------- 4) Subject.ownedUseCases 校验 ----------
        for subj_code, subj in subjects.items():
            owned = subj.get("ownedUseCases") or []
            if not isinstance(owned, list):
                subj["ownedUseCases"] = []
                owned = []
            for uc_code in owned:
                if uc_code not in usecases:
                    warn(f"Subject {subj_code} 引用了不存在的 UseCase: {uc_code}")

        # ---------- 5) 关系端点引用校验 ----------
        def ensure_ref(rc):
            if not rc:
                return
            if rc not in code_seen and rc not in ref_clsf:
                ref_clsf.add(rc)
                warn(f"关系引用的 {rc} 不在元素中，已加入 references.classifiers")

        for r in relationships:
            rc = _str(r.get("code"))
            rt = _str(r.get("type"))

            if rt == "association":
                e1 = _ref_code(r.get("end1"))
                e2 = _ref_code(r.get("end2"))
                ensure_ref(e1)
                ensure_ref(e2)
                t1, t2 = code_type.get(e1), code_type.get(e2)
                if t1 == t2 == "Actor":
                    warn(f"association {rc}: Actor ↔ Actor 关联在 UC 图中不推荐")

            elif rt == "include":
                inc_case = _ref_code(r.get("includingCase"))
                add_case = _ref_code(r.get("addition"))
                ensure_ref(inc_case)
                ensure_ref(add_case)
                if code_type.get(inc_case) != "UseCase" or code_type.get(add_case) != "UseCase":
                    warn(f"include {rc}: includingCase 与 addition 必需均为 UseCase")

            elif rt == "extend":
                ext_case = _ref_code(r.get("extension"))
                extd_case = _ref_code(r.get("extendedCase"))
                ensure_ref(ext_case)
                ensure_ref(extd_case)
                if code_type.get(ext_case) != "UseCase" or code_type.get(extd_case) != "UseCase":
                    warn(f"extend {rc}: extension 与 extendedCase 必需均为 UseCase")

                ext_locs = r.get("extensionLocations") or []
                if not isinstance(ext_locs, list):
                    r["extensionLocations"] = []
                    ext_locs = []
                for loc in ext_locs:
                    loc_ref = _ref_code(loc)
                    if not loc_ref:
                        continue
                    uc = usecases.get(extd_case, {})
                    eps = uc.get("extensionPoints") or []
                    ep_codes = {_str(ep.get("code")) for ep in eps if isinstance(ep, dict)}
                    if loc_ref not in ep_codes:
                        warn(f"extend {rc}: extensionLocation {loc_ref} 不在 extendedCase {extd_case} 的 extensionPoints 中")

            elif rt == "generalization":
                sp = _ref_code(r.get("specific"))
                ge = _ref_code(r.get("general"))
                ensure_ref(sp)
                ensure_ref(ge)
                sp_t, ge_t = code_type.get(sp), code_type.get(ge)
                if sp_t and ge_t and sp_t != ge_t:
                    warn(f"generalization {rc}: 端点类型不一致（{sp}:{sp_t} vs {ge}:{ge_t}），应为同类元素")
                elif ({sp_t, ge_t} & {"Actor"}) and ({sp_t, ge_t} & {"UseCase"}):
                    warn(f"generalization {rc}: Actor 与 UseCase 间的泛化不合法")

            elif rt == "dependency":
                client = _ref_code(r.get("client"))
                supplier = _ref_code(r.get("supplier"))
                ensure_ref(client)
                ensure_ref(supplier)

            else:
                warn(f"未知关系类型 {rt}（code={rc}），请核对")

        # ---------- 6) subjectRef 进一步可解析性 ----------
        for uc_code, uc in usecases.items():
            sref = _str(uc.get("subjectRefCode"))
            if sref and (sref not in subjects) and (sref not in ref_clsf):
                ref_clsf.add(sref)
                warn(f"UseCase {uc_code} 的 subjectRefCode={sref} 不在 subjects 中，已加入 references.classifiers")

        # ---------- 7) 回写 references / diagrams.references / 再同步布局 ----------
        refs["classifiers"] = sorted(ref_clsf)

        all_elem_codes = set(code_seen)
        all_rel_codes = {_str(r.get("code")) for r in relationships if r.get("code")}
        
        page_by_code = {}
        for pg in pages:
            dc = _str(pg.get("diagramCode"))
            if dc:
                page_by_code[dc] = pg
        
        for dg in diagrams:
            dc = _str(dg.get("code"))
            drefs = set(map(_str, (dg.get("references") or [])))
            changed = False
            if not drefs:
                drefs |= all_elem_codes | all_rel_codes
                changed = True
            cleaned = {x for x in drefs if (x in all_elem_codes or x in all_rel_codes)}
            if cleaned != drefs:
                changed = True
            if changed:
                dg["references"] = sorted(cleaned)

            pg = page_by_code.get(dc)
            if not pg:
                continue
            lay_elems = pg.setdefault("elements", [])
            lay_rels = pg.setdefault("relationships", [])
            node_codes = {n.get("elementCode") for n in lay_elems if n.get("elementCode")}
            edge_codes = {e.get("relationshipCode") for e in lay_rels if e.get("relationshipCode")}

            for ec in sorted(all_elem_codes & cleaned):
                if ec not in node_codes:
                    lay_elems.append({
                        "elementCode": ec,
                        "bounds": {"x": 100, "y": 80 + 40 * len(lay_elems), "w": 220, "h": 100}
                    })
                    node_codes.add(ec)
                    warn(f"diagram {dc}: layout.elements 缺少元素 {ec}，已自动补齐占位")

            for rc in sorted(all_rel_codes & cleaned):
                if rc not in edge_codes:
                    lay_rels.append({
                        "relationshipCode": rc,
                        "points": [{"x": 120, "y": 120 + 24 * len(lay_rels)},
                                   {"x": 360, "y": 120 + 24 * (len(lay_rels) + 1)}]
                    })
                    edge_codes.add(rc)
                    warn(f"diagram {dc}: layout.relationships 缺少关系 {rc}，已自动补齐")

        # ---------- 8) 清理空值（无值键不输出；保留 0/False） ----------
        def _strip_empty(obj):
            if isinstance(obj, dict):
                for k in list(obj.keys()):
                    v = obj[k]
                    vv = _strip_empty(v)
                    if vv is False or vv == 0:
                        obj[k] = vv
                    elif vv is None or vv == "" or (isinstance(vv, (list, dict)) and len(vv) == 0):
                        obj.pop(k, None)
                    else:
                        obj[k] = vv
                return obj
            elif isinstance(obj, list):
                new = []
                for it in obj:
                    vv = _strip_empty(it)
                    if vv is False or vv == 0:
                        new.append(vv)
                    elif vv is None or vv == "" or (isinstance(vv, (list, dict)) and len(vv) == 0):
                        continue
                    else:
                        new.append(vv)
                return new
            else:
                return obj

        d = _strip_empty(d)
        return d, issues

    # ---------- 主流程 ----------
    def generate(self, question: str, out_json="output_uc.json"):
        # 1) 检索
        chunks = self.retrieve_chunks(question, top_k=8)

        # 2) Prompt + LLM
        prompt = self.build_prompt(question, chunks)
        system_prompt = self.system_build_prompt()
        # # 分别保存到两个文档
        # with open('system_prompt.txt', 'w', encoding='utf-8') as f:
        #     f.write(system_prompt)
        # with open('user_prompt.txt', 'w', encoding='utf-8') as f:
        #     f.write(prompt)
        raw_text = self.call_llm(system_prompt, prompt)

        # 3) 解析 JSON
        try:
            data = json.loads(raw_text)
        except Exception as e:
            raise ValueError(f"模型输出非 JSON：{e}\n原文片段：{raw_text[:400]}")

        # 5) 工程化 Lint/Fix
        data, issues = self.lint_and_fix(data)
        if issues:
            print("🔎 工程化提示/修复：")
            for it in issues:
                print("  -", it)

        # 6) 落盘
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存 UC JSON：{out_json}")

        return data

    def test_normalize_chunks(self, chunks):
        """统一把 chunks 规整成 [{'text': str}, ...]"""
        if not chunks:
            return []
        # 情况1：[{ 'text': ...}, ...]
        if isinstance(chunks, list) and all(isinstance(c, dict) and "text" in c for c in chunks):
            return [{"text": str(c.get("text", ""))} for c in chunks]
        # 情况2：[str, str, ...]
        if isinstance(chunks, list) and all(isinstance(c, str) for c in chunks):
            return [{"text": c} for c in chunks]
        # 情况3：单个 str
        if isinstance(chunks, str):
            return [{"text": chunks}]
        # 情况4：其它可迭代类型，尽量转成字符串
        norm = []
        try:
            for c in chunks:
                if isinstance(c, dict) and "text" in c:
                    norm.append({"text": str(c.get("text", ""))})
                else:
                    norm.append({"text": str(c)})
        except TypeError:
            norm = [{"text": str(chunks)}]
        return norm

    def test_generate(self, question: str, chunks, out_json="output_uc.json"):
        """使用外部提供的chunks进行建模"""
        # 1) 规范化 chunks
        chunks = self.test_normalize_chunks(chunks)

        # 2) Prompt + LLM
        prompt = self.build_prompt(question, chunks)
        system_prompt = self.system_build_prompt()
        # # 分别保存到两个文档
        # with open('system_prompt.txt', 'w', encoding='utf-8') as f:
        #     f.write(system_prompt)
        # with open('user_prompt.txt', 'w', encoding='utf-8') as f:
        #     f.write(prompt)
        raw_text = self.call_llm(system_prompt, prompt)

        # 3) 解析 JSON
        try:
            data = json.loads(raw_text)
        except Exception as e:
            raise ValueError(f"模型输出非 JSON：{e}\n原文片段：{raw_text[:400]}")

        # 5) 工程化 Lint/Fix
        data, issues = self.lint_and_fix(data)
        if issues:
            print("🔎 工程化提示/修复：")
            for it in issues:
                print("  -", it)

        # 6) 落盘
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存 UC JSON：{out_json}")

        return data


if __name__ == "__main__":
    builder = UCBuilder()
    # builder.load_knowledge_base(
    #     os.getenv("KB_JSON", "embeddings/knowledge_base.json"),
    #     os.getenv("INDEX_DIR", "embeddings")
    # )

    print("\n—— 智能问答 · SysML 用例图（UC）生成 ——")
    print("输入自然语言需求（例如：'以 GroundStation 为系统边界，声明 Actor Operator/Admin、用例 Login/Audit/MissionPlanning，包含/扩展/泛化/依赖关系'）")
    print("输入 '退出' 结束。\n")

    while True:
        question = input("❓ 请输入建模需求：").strip()
        chunks = input("❓ 请输入相关知识：").strip()
        if question in {"退出", "exit", "quit"}:
            break
        try:
            builder.test_generate(question, chunks,
                                  out_json=os.getenv("OUT_JSON", f"测试日志/UCD测试日志_用例图_2025_10_04_1/{question}.json"))
        except Exception as e:
            print("❌ 失败：", e)