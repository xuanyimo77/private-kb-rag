"""文档解析、切分、向量化、Milvus 写入与删除业务逻辑。

文档增量更新流程：先按 doc_id 删除旧向量，再重新切分写入新向量，避免全量重建。

文档元信息（created_at / updated_at）存储在本地 JSON 文件中，与 Milvus Collection 同名，
位于 config.METADATA_DIR 下。Milvus Collection schema 一旦创建不能修改，
故时间戳不存进向量库。
"""

import json
import time
from pathlib import Path
from typing import List, Optional, Tuple

import config
from core.embedding_client import embedding_client
from core.milvus_client import milvus_client
from models.schemas import DocInfo
from service.kb_service import KnowledgeBaseNotFoundError
from utils.loader import UnsupportedFileError, guess_doc_id, load_document
from utils.text_splitter import split_text


class DocumentError(Exception):
    """文档业务异常。"""


# ---------------- 本地元信息文件 ----------------

def _meta_dir() -> Path:
    """返回元信息文件目录，不存在则创建。"""
    d = Path(getattr(config, "METADATA_DIR", "data/metadata"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _meta_path(kb_id: str) -> Path:
    return _meta_dir() / f"{kb_id}.json"


def _load_meta(kb_id: str) -> dict:
    """读取知识库元信息。返回 {doc_id: {created_at, updated_at}}。"""
    p = _meta_path(kb_id)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_meta(kb_id: str, meta: dict) -> None:
    _meta_path(kb_id).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _record_doc(meta: dict, doc_id: str, now: float) -> None:
    """记录一个文档的时间戳。"""
    if doc_id in meta:
        # 已存在：只更新 updated_at（增量更新场景）
        meta[doc_id]["updated_at"] = now
    else:
        meta[doc_id] = {"created_at": now, "updated_at": now}


def _remove_doc(meta: dict, doc_id: str) -> None:
    meta.pop(doc_id, None)


# ---------------- 核心业务 ----------------

def _ensure_kb(kb_id: str) -> None:
    """校验知识库存在。"""
    if kb_id not in milvus_client.list_collections():
        raise KnowledgeBaseNotFoundError(f"知识库不存在: {kb_id}")


def upload_document(kb_id: str, file_path: str, file_name: str | None = None) -> Tuple[str, int]:
    """上传并入库一个文档。

    解析 -> 切分 -> 向量化 -> 写入 Milvus。若同 doc_id 已存在则先删除旧向量再写入，
    实现增量更新。

    Args:
        kb_id: 目标知识库 ID
        file_path: 已暂存到 uploads 的本地文件路径
        file_name: 原始文件名（用于生成 doc_id），为空则用 file_path 基名

    Returns:
        (doc_id, chunk_count) 文档 ID 与切分块数

    Raises:
        KnowledgeBaseNotFoundError: 知识库不存在
        UnsupportedFileError: 文件格式不支持
    """
    _ensure_kb(kb_id)

    # 1. 加载与解析
    text = load_document(file_path)
    doc_id = guess_doc_id(file_name or file_path)

    # 2. 切分
    chunks = split_text(text)
    if not chunks:
        raise DocumentError(f"文档内容为空或切分后无有效片段: {doc_id}")

    # 3. 增量更新：先删旧向量再写新向量
    milvus_client.delete_by_doc_id(kb_id, doc_id)

    # 4. 向量化（批量）
    vectors = embedding_client.embed(chunks)

    # 5. 写入 Milvus
    chunk_indexes = list(range(len(chunks)))
    milvus_client.insert(
        kb_id=kb_id,
        vectors=vectors,
        doc_id=doc_id,
        texts=chunks,
        chunk_indexes=chunk_indexes,
    )

    # 6. 更新本地元信息（记录上传时间）
    now = time.time()
    meta = _load_meta(kb_id)
    _record_doc(meta, doc_id, now)
    _save_meta(kb_id, meta)

    return doc_id, len(chunks)


def delete_document(kb_id: str, doc_id: str) -> int:
    """按 doc_id 删除该文档全部向量（增量更新基础）。

    Returns:
        删除的向量条数
    """
    _ensure_kb(kb_id)
    deleted = milvus_client.delete_by_doc_id(kb_id, doc_id)
    # 同步清理元信息
    meta = _load_meta(kb_id)
    _remove_doc(meta, doc_id)
    _save_meta(kb_id, meta)
    return deleted


def list_documents(
    kb_id: str,
    sort_field: Optional[str] = None,
    sort_order: Optional[str] = None,
) -> List[DocInfo]:
    """列出知识库下已入库的文档及其块数，支持排序。

    Args:
        kb_id: 知识库 ID
        sort_field: 排序字段，支持 doc_id / created_at / updated_at / chunk_count
        sort_order: asc / desc，默认 desc

    Returns:
        排序后的 DocInfo 列表
    """
    _ensure_kb(kb_id)
    doc_ids = milvus_client.list_doc_ids(kb_id)
    meta = _load_meta(kb_id)

    items: List[DocInfo] = []
    for did in doc_ids:
        m = meta.get(did, {})
        items.append(
            DocInfo(
                doc_id=did,
                chunk_count=milvus_client.count_chunks(kb_id, did),
                created_at=m.get("created_at"),
                updated_at=m.get("updated_at"),
            )
        )

    # 内存排序（数据量小，Milvus 本身无文档级 ORDER BY）
    if sort_field:
        order = (sort_order or "desc").lower()
        reverse = order == "desc"

        def _key(it: DocInfo):
            val = getattr(it, sort_field, None)
            if val is None:
                # None 放末尾
                return (1, "")
            # 字符串字段按字典序，数值按大小
            if sort_field in ("created_at", "updated_at", "chunk_count"):
                return (0, float(val))
            return (0, str(val))

        items.sort(key=_key, reverse=reverse)
    else:
        # 默认按 doc_id 字典序
        items.sort(key=lambda it: it.doc_id)

    return items
