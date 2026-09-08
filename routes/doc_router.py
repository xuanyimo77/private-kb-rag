"""文档上传、删除、列表接口（路由层只做参数校验和转发）。

路由：
    POST   /doc/upload?kb_id=xxx  上传文件，解析后向量化入库
    DELETE /doc/delete?kb_id=xxx&doc_id=xxx  按 doc_id 删除该文档全部向量
    GET    /doc/list?kb_id=xxx   列出知识库下已入库的文档
"""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

import config
from models.schemas import DocDeleteResponse, DocListResponse, DocUploadResponse
from service import doc_service, kb_service
from utils.loader import UnsupportedFileError, safe_filename

router = APIRouter(prefix="/doc", tags=["文档管理"])


@router.post("/upload", response_model=DocUploadResponse)
def upload_document(
    kb_id: str = Query(..., description="目标知识库 ID"),
    file: UploadFile = File(..., description="待上传文件 PDF/TXT/MD"),
):
    """上传文件（multipart/form-data），解析后向量化入库。

    若同 doc_id 已存在，先删旧向量再写新向量，实现增量更新。

    注意：此路由用同步 def 而非 async def——函数体中含文件解析、
    Embedding API 调用、Milvus 写入等阻塞 I/O，若用 async def 会阻塞
    ASGI 事件循环，导致其他请求（如知识库切换）排队等待。
    """
    # 文件名安全校验
    safe_name = safe_filename(file.filename or "")
    if not safe_name:
        raise HTTPException(status_code=400, detail="非法文件名")

    suffix = Path(safe_name).suffix.lower()
    if suffix not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"不支持的文件格式: {suffix}，仅支持 {sorted(config.ALLOWED_EXTENSIONS)}",
        )

    # 暂存到 uploads/
    Path(config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    tmp_path = Path(config.UPLOAD_DIR) / safe_name
    content = file.file.read()  # 同步读取（async 版本用 await file.read()）
    if len(content) > config.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，上限 {config.MAX_FILE_SIZE_MB}MB",
        )
    tmp_path.write_bytes(content)

    try:
        doc_id, chunk_count = doc_service.upload_document(
            kb_id=kb_id,
            file_path=str(tmp_path),
            file_name=safe_name,
        )
        return DocUploadResponse(
            doc_id=doc_id,
            chunk_count=chunk_count,
            success=True,
            message=f"文档入库成功，切分 {chunk_count} 块",
        )
    except kb_service.KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnsupportedFileError as e:
        raise HTTPException(status_code=415, detail=str(e))
    except doc_service.DocumentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # 入库后清理暂存文件
        if tmp_path.exists():
            tmp_path.unlink()


@router.delete("/delete", response_model=DocDeleteResponse)
def delete_document(
    kb_id: str = Query(..., description="知识库 ID"),
    doc_id: str = Query(..., description="文档 ID"),
):
    """按 doc_id 删除该文档的全部向量（增量更新基础）。"""
    try:
        deleted = doc_service.delete_document(kb_id, doc_id)
        return DocDeleteResponse(
            doc_id=doc_id,
            deleted=deleted,
            success=True,
            message=f"已删除 {deleted} 条向量",
        )
    except kb_service.KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except doc_service.DocumentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", response_model=DocListResponse)
def list_documents(
    kb_id: str = Query(..., description="知识库 ID"),
    sort_field: str | None = Query(
        None,
        description="排序字段：doc_id / created_at / updated_at / chunk_count",
    ),
    sort_order: str | None = Query(None, description="排序方向：asc / desc，默认 desc"),
):
    """列出知识库下已入库的文档（支持排序）。"""
    try:
        items = doc_service.list_documents(kb_id, sort_field, sort_order)
        return DocListResponse(
            kb_id=kb_id,
            total=len(items),
            items=items,
            sort_field=sort_field,
            sort_order=sort_order,
        )
    except kb_service.KnowledgeBaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
