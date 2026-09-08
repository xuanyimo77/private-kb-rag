"""全局配置示例文件。

实际运行时请复制本文件为 `config.py`，并填入自己的 API Key、地址等敏感信息：

    cp config.example.py config.py

`config.py` 已在 `.gitignore` 中排除，不会被提交到 GitHub。
所有地址、模型名、阈值参数集中写在此处，业务代码不硬编码。
通过环境变量可覆盖默认值，便于不同环境部署。
"""

import os

# Reranker 模型从 HuggingFace 下载，默认走国内镜像（已显式设置则不覆盖）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ==================== Embedding 配置 ====================
# 使用硅基流动 SiliconFlow（OpenAI 兼容协议）的 BAAI/bge-m3，输出 1024 维
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "<your-siliconflow-api-key>")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
EMBEDDING_DIM = 1024  # bge-m3 输出维度，须与 Milvus Collection 的 vector 字段 dim 一致

# ==================== Reranker 配置 ====================
RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"  # 本地交叉编码器，568M，多语言

# ==================== Milvus 配置 ====================
MILVUS_HOST = os.getenv("MILVUS_HOST", "127.0.0.1")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

# ==================== 分块与检索参数 ====================
CHUNK_SIZE = 500      # 文本块大小（字符数）
CHUNK_OVERLAP = 80    # 块重叠大小
RETRIEVE_TOP_K = 4    # 向量检索召回数量
RERANK_TOP_N = 3      # Reranker 后保留数量

# ==================== LLM 配置（DeepSeek，OpenAI 兼容协议）====================
# DeepSeek-V4-Flash：1M 上下文，最大输出 384K，默认思考模式，并发限制 2500
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_API_KEY = os.getenv("LLM_API_KEY", "<your-deepseek-api-key>")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")
LLM_TEMPERATURE = 0.3  # 低温度保证答案稳定
LLM_MAX_TOKENS = 2048  # v4-flash 默认开启思考模式，放宽上限避免截断

# ==================== 文件上传配置 ====================
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
MAX_FILE_SIZE_MB = 20  # 上传文件大小上限
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}

# ==================== 业务异常码 ====================
# 用于业务异常统一捕获
