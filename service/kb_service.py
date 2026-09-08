"""知识库管理业务逻辑（创建/删除/列表）。

每个知识库对应 Milvus 一个 Collection，Collection 名即 kb_id。
路由层只做参数校验和转发，业务逻辑写于此。
"""

import json
from pathlib import Path
from typing import List

import config
from core.milvus_client import milvus_client
from models.schemas import KBInfo


def _suggestions_meta_dir() -> Path:
    return Path(getattr(config, "METADATA_DIR", "data/metadata"))


def _load_suggestions(kb_id: str) -> List[str]:
    """读取该知识库的预设问题列表。"""
    p = _suggestions_meta_dir() / f"{kb_id}.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return list(data.get("suggestions", []))
    except Exception:
        return []


class KnowledgeBaseError(Exception):
    """知识库业务异常基类。"""


class KnowledgeBaseExistsError(KnowledgeBaseError):
    """知识库已存在。"""


class KnowledgeBaseNotFoundError(KnowledgeBaseError):
    """知识库不存在。"""


def create_kb(kb_id: str, description: str | None = None) -> None:
    """创建知识库（Collection）。

    Args:
        kb_id: 知识库 ID，作为 Collection 名
        description: 描述（当前仅用于扩展，未持久化）

    Raises:
        KnowledgeBaseExistsError: 知识库已存在
    """
    if kb_id in milvus_client.list_collections():
        raise KnowledgeBaseExistsError(f"知识库已存在: {kb_id}")
    milvus_client.create_collection(kb_id)


def delete_kb(kb_id: str) -> None:
    """删除知识库及全部向量数据。

    Args:
        kb_id: 知识库 ID

    Raises:
        KnowledgeBaseNotFoundError: 知识库不存在
    """
    if kb_id not in milvus_client.list_collections():
        raise KnowledgeBaseNotFoundError(f"知识库不存在: {kb_id}")
    milvus_client.drop_collection(kb_id)


def list_kbs() -> List[KBInfo]:
    """列出所有知识库及其文档数、向量数。"""
    items: List[KBInfo] = []
    for kb_id in milvus_client.list_collections():
        doc_ids = milvus_client.list_doc_ids(kb_id)
        # 用 count_entities 实际查询有效实体数，不可依赖 num_entities（含逻辑删除残留）
        vector_count = milvus_client.count_entities(kb_id)
        items.append(
            KBInfo(
                kb_id=kb_id,
                doc_count=len(doc_ids),
                vector_count=vector_count,
                suggestions=_load_suggestions(kb_id),
            )
        )
    return items
