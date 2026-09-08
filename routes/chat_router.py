"""RAG 问答、多轮对话接口（路由层只做参数校验和转发）。

路由：
    POST /chat/query   单轮 RAG 问答，返回答案 + 检索来源片段（非流式）
    POST /chat/stream  流式 RAG 问答（SSE），支持多轮对话与查询改写
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from core.llm_client import (
    LLMAuthError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
)
from models.schemas import ChatQueryRequest, ChatQueryResponse, ChatStreamRequest
from service import kb_service, rag_service

router = APIRouter(prefix="/chat", tags=["RAG 问答"])


@router.post("/query", response_model=ChatQueryResponse)
def query_rag(req: ChatQueryRequest):
    """单轮 RAG 问答，返回答案 + 检索来源片段。"""
    try:
        return rag_service.query_rag(req.kb_id, req.question)
    except kb_service.KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LLMAuthError as e:
        # 上游认证失败（API Key 错误），非用户侧问题
        raise HTTPException(status_code=502, detail=str(e))
    except LLMRateLimitError as e:
        # 触发限流，建议稍后重试
        raise HTTPException(status_code=503, detail=str(e))
    except LLMConnectionError as e:
        # 无法连接 LLM 服务
        raise HTTPException(status_code=502, detail=str(e))
    except LLMError as e:
        # 其他 LLM 调用错误
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
def stream_rag(req: ChatStreamRequest):
    """流式 RAG 问答（SSE）。

    事件流（event 字段）：
        meta  —— 检索完成，data 含 rewritten_question 与 source 来源片段
        delta —— 答案增量，data.text 为文本片段
        done  —— 生成结束
        error —— 出错，data 含 code 与 message
    """
    # Pydantic 模型转为 dict 列表传入 service
    history = [{"role": m.role, "content": m.content} for m in req.history]
    generator = rag_service.stream_query_rag(req.kb_id, req.question, history)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用反向代理缓冲，保证实时推送
        },
    )
