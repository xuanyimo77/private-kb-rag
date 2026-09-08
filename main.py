"""FastAPI 入口：挂载路由、CORS、启动事件。

启动：uvicorn main:app --host 0.0.0.0 --port 8000 --reload
文档：http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.milvus_client import milvus_client
from routes import chat_router, doc_router, kb_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建立 Milvus 连接，关闭时释放。"""
    milvus_client.connect()
    yield
    # 如有需要可在此释放资源


app = FastAPI(
    title="私有知识库 RAG 系统",
    description="基于 FastAPI + LangChain + Milvus 的私有知识库问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS：允许前端跨域访问（按需收紧白名单）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(kb_router.router)
app.include_router(doc_router.router)
app.include_router(chat_router.router)


@app.get("/", tags=["健康检查"])
def root():
    """根路径健康检查。"""
    return {"status": "ok", "service": "private_kb_rag"}


if __name__ == "__main__":
    # 支持 PyCharm 中直接右键运行 main.py（点绿色三角即可启动）
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 代码改动自动重启
    )
