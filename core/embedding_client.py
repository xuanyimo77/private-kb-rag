"""Embedding 模型加载与向量化封装。

使用 OpenAI text-embedding-3-small API（1536 维），无需本地下载模型。
通过 OpenAI 兼容协议调用，可配置代理地址。
"""

from typing import List

from openai import OpenAI

import config


class EmbeddingClient:
    """Embedding 客户端：批量文本转向量。

    使用 OpenAI text-embedding-3-small，输出维度由 config.EMBEDDING_DIM 决定，
    须与 Milvus Collection 的 vector 字段 dim 严格一致。
    """

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        """惰性初始化 OpenAI 客户端，避免启动期即建立连接。"""
        if self._client is None:
            self._client = OpenAI(
                api_key=config.EMBEDDING_API_KEY,
                base_url=config.EMBEDDING_BASE_URL,
            )
        return self._client

    def embed(self, texts: List[str]) -> List[List[float]]:
        """批量文本转向量。

        Args:
            texts: 文本片段列表

        Returns:
            与 texts 等长的向量列表，每个向量维度为 config.EMBEDDING_DIM
        """
        if not texts:
            return []
        resp = self.client.embeddings.create(
            model=config.EMBEDDING_MODEL_NAME,
            input=texts,
        )
        # 按 index 顺序对齐，保证与输入一一对应
        data = sorted(resp.data, key=lambda x: x.index)
        return [item.embedding for item in data]

    def embed_query(self, query: str) -> List[float]:
        """单条 query 转向量（用于检索）。"""
        return self.embed([query])[0]


# 单例
embedding_client = EmbeddingClient()
