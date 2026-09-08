"""检索、Reranker 重排序、Prompt 组装、LLM 调用业务逻辑。

两阶段检索：
1. 向量粗召回 Top-K（config.RETRIEVE_TOP_K），保证召回率。
2. Reranker 精排 Top-N（config.RERANK_TOP_N），用 Cross-Encoder 对 query
   和每条召回文本联合编码打分，精度高于双塔模型。
最后将精排片段拼为上下文，调用 LLM 生成回答，并返回来源溯源。

流式接口额外支持多轮对话：结合历史将最新问题改写为独立检索问题（指代消解）。
"""

import json
from typing import List, Optional, Tuple

import config
from core.embedding_client import embedding_client
from core.llm_client import llm_client
from core.milvus_client import milvus_client
from models.schemas import ChatQueryResponse, SourceChunk
from service.kb_service import KnowledgeBaseNotFoundError


class Reranker:
    """本地 Cross-Encoder Reranker（BAAI/bge-reranker-v2-m3）。

    首次运行自动从 HuggingFace 下载（约 2.27GB，568M 参数），需 6-8GB 显存。
    无 GPU 时回退 CPU 推理，延迟较高。
    """

    def __init__(self) -> None:
        self._model = None

    @property
    def model(self):
        """惰性加载模型，避免启动期占用显存。"""
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(config.RERANKER_MODEL_NAME)
        return self._model

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = config.RERANK_TOP_N,
    ) -> List[dict]:
        """对候选文档联合编码打分并排序，返回 Top-N。

        Args:
            query: 用户问题
            documents: 粗召回的文本片段列表
            top_n: 精排后保留数量

        Returns:
            按 score 降序排列的 [{"index": int, "score": float}]，长度 <= top_n
        """
        if not documents:
            return []
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs).tolist()
        ranked = sorted(
            [{"index": i, "score": float(s)} for i, s in enumerate(scores)],
            key=lambda x: x["score"],
            reverse=True,
        )
        return ranked[:top_n]


# 全局 Reranker 单例
_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    """惰性获取 Reranker 单例。"""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker


def _ensure_kb(kb_id: str) -> None:
    """校验知识库存在。"""
    if kb_id not in milvus_client.list_collections():
        raise KnowledgeBaseNotFoundError(f"知识库不存在: {kb_id}")


def _retrieve(kb_id: str, query: str) -> Tuple[List[SourceChunk], List[str]]:
    """向量粗召回 + Reranker 精排。

    Args:
        kb_id: 知识库 ID
        query: 用于检索的问题（多轮场景为改写后的独立问题）

    Returns:
        (sources, ranked_texts)：精排后的来源片段列表与对应原文；
        无召回时返回 ([], [])。
    """
    query_vector = embedding_client.embed_query(query)
    candidates = milvus_client.search(kb_id, query_vector, top_k=config.RETRIEVE_TOP_K)
    if not candidates:
        return [], []

    texts = [c["text"] for c in candidates]
    ranked = get_reranker().rerank(query, texts, top_n=config.RERANK_TOP_N)

    sources: List[SourceChunk] = []
    ranked_texts: List[str] = []
    for r in ranked:
        c = candidates[r["index"]]
        sources.append(
            SourceChunk(
                doc_id=c["doc_id"],
                text=c["text"],
                sim_score=c["sim_score"],
                score=r["score"],
            )
        )
        ranked_texts.append(c["text"])
    return sources, ranked_texts


def query_rag(kb_id: str, question: str) -> ChatQueryResponse:
    """单轮 RAG 问答主流程。

    Args:
        kb_id: 知识库 ID
        question: 用户问题

    Returns:
        包含答案与检索来源片段的响应

    Raises:
        KnowledgeBaseNotFoundError: 知识库不存在
    """
    _ensure_kb(kb_id)
    sources, ranked_texts = _retrieve(kb_id, question)

    # 无召回时直接让 LLM 说明无法回答，避免幻觉
    if not ranked_texts:
        answer = "根据现有知识库无法回答该问题（未检索到相关内容）。"
        return ChatQueryResponse(question=question, answer=answer, source=[])

    answer = llm_client.chat(question, ranked_texts)
    return ChatQueryResponse(question=question, answer=answer, source=sources)


def _sse(event: str, data: dict) -> str:
    """组装一条 SSE 事件字符串。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_query_rag(kb_id: str, question: str, history: Optional[List[dict]] = None):
    """流式 RAG 问答生成器（SSE），支持多轮对话。

    流程：校验知识库 →（有历史时）查询改写做指代消解 → 向量检索 + Reranker
    → 下发 meta（改写问题 + 来源）→ 流式下发答案增量 → done。

    Args:
        kb_id: 知识库 ID
        question: 本轮用户问题
        history: [{"role": "user"/"assistant", "content": "..."}] 历史消息

    Yields:
        str: SSE 事件字符串，事件类型为 meta / delta / done / error
    """
    history = history or []
    try:
        _ensure_kb(kb_id)

        # 多轮指代消解：将含指代词的最新问题改写为可独立检索的问题
        rewritten = llm_client.rewrite_question(question, history) if history else question

        # 检索 + 精排（使用改写后的问题）
        sources, ranked_texts = _retrieve(kb_id, rewritten)

        # meta 事件：先下发改写问题与检索来源，前端可立即展示来源面板
        yield _sse(
            "meta",
            {
                "question": question,
                "rewritten_question": rewritten,
                "source": [s.model_dump() for s in sources],
            },
        )

        if not ranked_texts:
            yield _sse("delta", {"text": "根据现有知识库无法回答该问题（未检索到相关内容）。"})
        else:
            # 流式生成答案（携带历史上下文）
            for piece in llm_client.chat_stream(question, ranked_texts, history):
                yield _sse("delta", {"text": piece})

        yield _sse("done", {})
    except KnowledgeBaseNotFoundError as e:
        yield _sse("error", {"code": "kb_not_found", "message": str(e)})
    except Exception as e:  # noqa: BLE001 - 流式中出错通过 SSE error 事件下发
        yield _sse("error", {"code": "rag_error", "message": str(e)})
