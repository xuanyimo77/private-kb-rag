"""基础冒烟测试：验证模块可正常导入、配置加载正确。

运行：pytest tests/test_smoke.py -v
（需 Milvus/LLM 服务的测试见 tests/test_rag.py，启动相关服务后运行）
"""

import config


def test_config_loaded():
    """配置项应正确加载。"""
    assert config.EMBEDDING_DIM == 1536
    assert config.CHUNK_SIZE > 0
    assert config.RETRIEVE_TOP_K > 0
    assert config.RERANK_TOP_N > 0


def test_imports():
    """核心模块应可正常导入。"""
    from models import schemas  # noqa: F401
    from core import milvus_client, llm_client, embedding_client  # noqa: F401
    from utils import loader, text_splitter  # noqa: F401
    from service import kb_service, doc_service, rag_service  # noqa: F401
    from routes import kb_router, doc_router, chat_router  # noqa: F401
    from main import app  # noqa: F401


def test_split_text():
    """切分器应对普通文本返回非空列表。"""
    from utils.text_splitter import split_text

    chunks = split_text("这是一段测试文本。这是一段测试文本。" * 50)
    assert len(chunks) >= 1
