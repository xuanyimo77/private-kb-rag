"""知识库 CRUD 接口（路由层只做参数校验和转发）。

路由：
    POST   /kb/create?kb_id=xxx  创建知识库
    DELETE /kb/delete?kb_id=xxx  删除知识库及全部向量数据
    GET    /kb/list              列出所有知识库
"""

from fastapi import APIRouter, HTTPException, Query

from models.schemas import KBActionResponse, KBListResponse
from service import kb_service

router = APIRouter(prefix="/kb", tags=["知识库管理"])


@router.post("/create", response_model=KBActionResponse)
def create_kb(kb_id: str = Query(..., description="知识库 ID，作为 Milvus Collection 名")):
    """创建知识库（对应 Milvus 一个 Collection）。"""
    try:
        kb_service.create_kb(kb_id)
        return KBActionResponse(kb_id=kb_id, success=True, message="知识库创建成功")
    except kb_service.KnowledgeBaseExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except kb_service.KnowledgeBaseError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete", response_model=KBActionResponse)
def delete_kb(kb_id: str = Query(..., description="知识库 ID")):
    """删除知识库及全部向量数据。"""
    try:
        kb_service.delete_kb(kb_id)
        return KBActionResponse(kb_id=kb_id, success=True, message="知识库删除成功")
    except kb_service.KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except kb_service.KnowledgeBaseError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", response_model=KBListResponse)
def list_kbs():
    """列出所有知识库。"""
    items = kb_service.list_kbs()
    return KBListResponse(total=len(items), items=items)
