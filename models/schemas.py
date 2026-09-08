"""Pydantic 请求/响应模型。

定义所有 API 接口的请求体与响应体结构，统一类型契约。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== 知识库管理 ====================
class KBCreateRequest(BaseModel):
    """知识库创建请求（kb_id 通过 query 传递，这里留作扩展）。"""

    description: Optional[str] = Field(None, description="知识库描述")


class KBInfo(BaseModel):
    """知识库信息。"""

    kb_id: str = Field(..., description="知识库 ID，对应 Milvus Collection 名")
    doc_count: int = Field(0, description="已入库文档数")
    vector_count: int = Field(0, description="向量总数")
    suggestions: List[str] = Field(
        default_factory=list, description="该知识库的预设问题列表（空会话时展示）"
    )


class KBListResponse(BaseModel):
    """知识库列表响应。"""

    total: int
    items: List[KBInfo]


class KBActionResponse(BaseModel):
    """知识库创建/删除通用响应。"""

    kb_id: str
    success: bool
    message: str


# ==================== 文档管理 ====================
class DocInfo(BaseModel):
    """文档元信息。"""

    doc_id: str = Field(..., description="文档 ID，通常为文件名")
    chunk_count: int = Field(0, description="切分块数")
    created_at: Optional[float] = Field(
        None, description="文档首次入库时间（Unix 时间戳，秒）"
    )
    updated_at: Optional[float] = Field(
        None, description="文档最近一次入库时间（Unix 时间戳，秒）"
    )


class DocListResponse(BaseModel):
    """文档列表响应。"""

    kb_id: str
    total: int
    items: List[DocInfo]
    sort_field: Optional[str] = Field(None, description="本次排序字段")
    sort_order: Optional[str] = Field(None, description="本次排序方向 asc/desc")


class DocUploadResponse(BaseModel):
    """文档上传响应。"""

    doc_id: str
    chunk_count: int
    success: bool
    message: str


class DocDeleteResponse(BaseModel):
    """文档删除响应。"""

    doc_id: str
    deleted: int = Field(..., description="删除的向量条数")
    success: bool
    message: str


# ==================== RAG 问答 ====================
class ChatQueryRequest(BaseModel):
    """单轮 RAG 问答请求。"""

    kb_id: str = Field(..., description="知识库 ID")
    question: str = Field(..., description="用户问题")


class SourceChunk(BaseModel):
    """检索来源片段。"""

    doc_id: str
    text: str
    sim_score: float = Field(..., description="向量相似度得分")
    score: Optional[float] = Field(None, description="Reranker 精排得分")


class ChatQueryResponse(BaseModel):
    """单轮 RAG 问答响应。"""

    question: str
    answer: str
    source: List[SourceChunk] = Field(default_factory=list)


class ChatMessage(BaseModel):
    """对话历史中的一条消息（多轮对话）。"""

    role: str = Field(..., description="角色：user / assistant")
    content: str = Field(..., description="消息内容")


class ChatStreamRequest(BaseModel):
    """流式 RAG 问答请求（支持多轮对话）。

    history 为当前问题之前的对话记录（不含本次 question），
    后端会结合历史将 question 改写为独立的检索问题。
    """

    kb_id: str = Field(..., description="知识库 ID")
    question: str = Field(..., description="本轮用户问题")
    history: List[ChatMessage] = Field(
        default_factory=list, description="历史对话（不含本轮），用于指代消解"
    )


# ==================== 通用错误响应 ====================
class ErrorResponse(BaseModel):
    """标准错误响应。"""

    detail: str
    code: Optional[str] = None
