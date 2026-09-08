"""Milvus 连接、Collection 管理、搜索、删除封装。

每个知识库对应一个独立 Collection，Collection 名即 kb_id，实现多知识库物理隔离。
向量字段 dim 必须与 config.EMBEDDING_DIM 一致。
"""

from typing import Any, Dict, List, Optional

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

import config


class MilvusClient:
    """Milvus 客户端：连接管理、Collection 增删查、向量写入/检索/删除。

    Collection schema:
        - pk: int64 主键（自增）
        - vector: FLOAT_VECTOR(dim=EMBEDDING_DIM)
        - doc_id: VARCHAR 文档 ID（文件名），用于按文档增量删除
        - text: VARCHAR 原文片段，用于来源溯源展示
        - chunk_index: INT64 块序号
    """

    # 字段名常量，供 service 层引用避免拼写不一致
    FIELD_PK = "pk"
    FIELD_VECTOR = "vector"
    FIELD_DOC_ID = "doc_id"
    FIELD_TEXT = "text"
    FIELD_CHUNK_INDEX = "chunk_index"

    def __init__(self) -> None:
        self._connected = False
        # 缓存已 load 的 Collection，避免每次查询都重新 load
        self._loaded_cols: Dict[str, Collection] = {}

    # ---------------- 连接 ----------------
    def connect(self) -> None:
        """建立与 Milvus 的连接（幂等）。"""
        if self._connected:
            return
        connections.connect(
            alias="default",
            host=config.MILVUS_HOST,
            port=config.MILVUS_PORT,
        )
        self._connected = True

    # ---------------- Collection ----------------
    def create_collection(self, kb_id: str) -> Collection:
        """创建知识库 Collection。已存在则直接返回。"""
        self.connect()
        if utility.has_collection(kb_id):
            return Collection(kb_id)

        schema = CollectionSchema(
            fields=[
                FieldSchema(name=self.FIELD_PK, dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name=self.FIELD_VECTOR, dtype=DataType.FLOAT_VECTOR, dim=config.EMBEDDING_DIM),
                FieldSchema(name=self.FIELD_DOC_ID, dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name=self.FIELD_TEXT, dtype=DataType.VARCHAR, max_length=4096),
                FieldSchema(name=self.FIELD_CHUNK_INDEX, dtype=DataType.INT64),
            ],
            description=f"knowledge base: {kb_id}",
        )
        col = Collection(name=kb_id, schema=schema)
        # 向量字段建索引（IVF_FLAT + COSINE），随后 load 入内存用于检索
        col.create_index(
            field_name=self.FIELD_VECTOR,
            index_params={
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 128},
            },
        )
        col.load()
        return col

    def drop_collection(self, kb_id: str) -> None:
        """删除知识库（Collection 及全部向量数据）。"""
        self.connect()
        if utility.has_collection(kb_id):
            utility.drop_collection(kb_id)
        self._loaded_cols.pop(kb_id, None)

    def list_collections(self) -> List[str]:
        """列出所有知识库 Collection 名。"""
        self.connect()
        return utility.list_collections()

    def get_collection(self, kb_id: str) -> Optional[Collection]:
        """获取已存在的 Collection（已 load 入内存），不存在返回 None。"""
        self.connect()
        if not utility.has_collection(kb_id):
            self._loaded_cols.pop(kb_id, None)
            return None
        # 命中缓存直接返回
        if kb_id in self._loaded_cols:
            return self._loaded_cols[kb_id]
        col = Collection(kb_id)
        col.load()
        self._loaded_cols[kb_id] = col
        return col

    # ---------------- 向量写入 ----------------
    def insert(
        self,
        kb_id: str,
        vectors: List[List[float]],
        doc_id: str,
        texts: List[str],
        chunk_indexes: List[int],
    ) -> List[int]:
        """写入文档向量。返回生成的主键列表。

        Args:
            vectors: 与 texts 等长的向量列表
            doc_id: 文档 ID（文件名）
            texts: 切分后的原文片段
            chunk_indexes: 块序号
        """
        col = self.get_collection(kb_id)
        if col is None:
            raise ValueError(f"知识库不存在: {kb_id}")
        result = col.insert([vectors, [doc_id] * len(vectors), texts, chunk_indexes])
        col.flush()
        return result.primary_keys

    # ---------------- 检索 ----------------
    def search(
        self,
        kb_id: str,
        query_vector: List[float],
        top_k: int = config.RETRIEVE_TOP_K,
    ) -> List[Dict[str, Any]]:
        """向量粗召回。返回命中片段列表（含 doc_id/text/sim_score）。"""
        col = self.get_collection(kb_id)
        if col is None:
            raise ValueError(f"知识库不存在: {kb_id}")

        results = col.search(
            data=[query_vector],
            anns_field=self.FIELD_VECTOR,
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=[self.FIELD_DOC_ID, self.FIELD_TEXT],
        )
        hits = results[0]
        out: List[Dict[str, Any]] = []
        for hit in hits:
            out.append(
                {
                    "doc_id": hit.entity.get(self.FIELD_DOC_ID),
                    "text": hit.entity.get(self.FIELD_TEXT),
                    "sim_score": float(hit.distance),  # COSINE 度量下 distance 即相似度
                }
            )
        return out

    # ---------------- 删除 ----------------
    def delete_by_doc_id(self, kb_id: str, doc_id: str) -> int:
        """按 doc_id 删除该文档全部向量（逻辑删除）。返回删除条数。

        Milvus 删除为逻辑删除，需定期 compact 回收空间。
        """
        col = self.get_collection(kb_id)
        if col is None:
            return 0
        expr = f'{self.FIELD_DOC_ID} == "{doc_id}"'
        before = col.num_entities
        col.delete(expr)
        col.flush()
        after = col.num_entities
        return max(before - after, 0)

    # ---------------- 元信息聚合 ----------------
    def list_doc_ids(self, kb_id: str) -> List[str]:
        """列出知识库下已入库的 doc_id（去重）。"""
        col = self.get_collection(kb_id)
        if col is None:
            return []
        res = col.query(
            expr="",
            output_fields=[self.FIELD_DOC_ID],
            limit=16384,
        )
        seen = []
        for item in res:
            did = item.get(self.FIELD_DOC_ID)
            if did and did not in seen:
                seen.append(did)
        return seen

    def count_entities(self, kb_id: str) -> int:
        """统计知识库的实际有效向量数。

        Milvus 的 num_entities 统计的是累计插入数（含已逻辑删除未回收的），
        不可靠。这里用 query 实际查询当前存活实体数。
        """
        col = self.get_collection(kb_id)
        if col is None:
            return 0
        res = col.query(
            expr="",
            output_fields=[self.FIELD_PK],
            limit=16384,
        )
        return len(res)

    def count_chunks(self, kb_id: str, doc_id: str) -> int:
        """统计指定文档的向量块数。"""
        col = self.get_collection(kb_id)
        if col is None:
            return 0
        res = col.query(
            expr=f'{self.FIELD_DOC_ID} == "{doc_id}"',
            output_fields=[self.FIELD_PK],
            limit=16384,
        )
        return len(res)


# 单例：全局共享一个客户端
milvus_client = MilvusClient()
