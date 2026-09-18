# 私有知识库 RAG 系统（后端 API 版）

基于 FastAPI + LangChain + Milvus 构建的私有知识库问答系统，支持多知识库隔离、文档上传与增量入库、RAG 检索问答、检索来源溯源。

---

## 一、技术栈

| 层级 | 技术选型 |
|------|----------|
| Web 框架 | FastAPI + Uvicorn |
| RAG 编排 | LangChain |
| 向量数据库 | Milvus（standalone，Docker 部署） |
| Embedding | OpenAI text-embedding-3-small（1536 维，API 调用） |
| Reranker | BAAI/bge-reranker-v2-m3（568M，多语言，本地部署，6-8GB 显存） |
| LLM | OpenAI 兼容协议（可对接本地 Qwen / 通义千问 / OpenAI） |
| 文档解析 | PyPDF（PDF）、纯文本 / Markdown 原生读取 |
| 前端 | Streamlit 或独立 HTML（可选） |

---

## 二、目录结构

```
private_kb/
├── main.py              # FastAPI 入口，挂载路由、CORS、启动事件
├── config.py            # 全局配置：Milvus 地址、模型名、分块参数、TopK 等
├── requirements.txt     # Python 依赖清单
├── frontend.py          # Streamlit 演示前端（可选）
│
├── routes/              # API 路由层（只做参数校验和转发）
│   ├── kb_router.py     # 知识库 CRUD 接口
│   ├── doc_router.py    # 文档上传、删除、列表接口
│   └── chat_router.py   # RAG 问答、多轮对话接口
│
├── service/             # 业务逻辑层
│   ├── kb_service.py    # 知识库管理（创建/删除/列表）
│   ├── doc_service.py   # 文档解析、切分、向量化、Milvus 写入与删除
│   └── rag_service.py   # 检索、Reranker 重排序、Prompt 组装、LLM 调用
│
├── models/              # 数据模型
│   ├── schemas.py       # Pydantic 请求/响应模型
│   └── db_models.py     # （可选）关系型数据模型，记录文档元信息
│
├── core/                # 核心客户端封装
│   ├── milvus_client.py # Milvus 连接、Collection 管理、搜索、删除
│   ├── llm_client.py    # LLM 统一封装（OpenAI 兼容协议）
│   └── embedding_client.py  # Embedding 模型加载与向量化
│
├── utils/               # 工具函数
│   ├── loader.py        # 文档加载器（PDF/TXT/MD）
│   └── text_splitter.py # 文本切分工具
│
├── data/                # 本地测试数据（电商知识库 md 文件等）
├── uploads/             # 上传文件暂存目录
└── tests/               # 测试用例
```

---

## 三、环境准备

### 3.1 启动 Milvus（Docker）

```bash
# 下载 standalone 编排文件
wget https://github.com/milvus-io/milvus/releases/download/v2.4.0/milvus-standalone-docker-compose.yml -O docker-compose.yml

# 启动
docker-compose up -d
```

启动后 Milvus 地址：`127.0.0.1:19530`，可视化管理端 Attu：`http://127.0.0.1:9000`。

### 3.2 Python 依赖

```bash
pip install -r requirements.txt
```

> Embedding 使用 OpenAI text-embedding-3-small API，无需本地下载模型；需在 `config.py` 中配置 OpenAI API Key。Reranker 使用本地 `bge-reranker-v2-m3` 模型（约 2.27GB，568M 参数），首次运行自动下载，需 6-8GB 显存。

### 3.3 LLM 服务

任选一种：
- **本地部署**：用 `vllm` 或 `text-generation-webui` 启动 Qwen-7B，开启 OpenAI 兼容接口（默认 `http://localhost:8000/v1`）。
- **云端 API**：直接使用 OpenAI / 通义千问 / DeepSeek 的 API Key，在 `config.py` 中配置 `base_url` 和 `api_key`。

### 3.4 Embedding 服务

使用 OpenAI `text-embedding-3-small` API，无需本地部署模型：
- 在 `config.py` 中配置 `EMBEDDING_API_KEY`（OpenAI API Key）。
- 如无法直连 OpenAI，可配置 `EMBEDDING_BASE_URL` 指向代理地址（如 `https://api.openai.com/v1` 或第三方兼容端点）。
- 默认输出维度 1536，Milvus Collection 的 `vector` 字段 `dim` 必须设为 1536。

### 3.5 Reranker 服务

使用智源开源的 `BAAI/bge-reranker-v2-m3`，本地部署，无需 API：
- **模型规模**：568M 参数，模型文件约 2.27GB，首次运行自动从 HuggingFace 下载。
- **硬件要求**：推荐 6-8GB 显存（如 RTX 3060/4060 8GB）；无 GPU 时可回退 CPU 推理，但延迟较高。
- **语言支持**：100+ 多语言，中文场景优化，Apache 2.0 协议可商用。
- **推理方式**：交叉编码器（Cross-Encoder），对 query 和每条候选文本联合编码打分，精度高于双塔模型。
- **如显存不足**：可降级为 `BAAI/bge-reranker-base`（278M，4-6GB 显存），精度略低但速度更快。

---

## 四、核心配置（config.py）

```python
# 模型
EMBEDDING_MODEL_NAME = "text-embedding-3-small"   # OpenAI API，输出 1536 维
EMBEDDING_API_KEY  = "sk-xxxxxxxx"                  # OpenAI API Key
EMBEDDING_BASE_URL = "https://api.openai.com/v1"    # OpenAI API 地址（可代理）
RERANKER_MODEL_NAME  = "BAAI/bge-reranker-v2-m3"   # 本地交叉编码器，568M，多语言

# Milvus
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"

# 分块与检索
CHUNK_SIZE      = 500     # 文本块大小（字符数）
CHUNK_OVERLAP   = 80      # 块重叠大小
RETRIEVE_TOP_K  = 4       # 向量检索召回数量
RERANK_TOP_N    = 3       # Reranker 后保留数量

# LLM（OpenAI 兼容协议）
LLM_BASE_URL = "http://localhost:8000/v1"
LLM_API_KEY  = "dummy"
LLM_MODEL    = "qwen-7b-instruct"
```

> Embedding 维度必须与 Milvus Collection 的 `vector` 字段 `dim` 一致。text-embedding-3-small 默认输出 1536 维；如需降低维度可在调用时传 `dimensions=512` 参数，但需同步修改 Milvus 字段 dim。

---

## 五、API 接口清单

所有接口启动后可访问 `http://127.0.0.1:8000/docs` 查看 Swagger 文档并在线调试。

### 5.1 知识库管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/kb/create?kb_id=xxx` | 创建知识库（对应 Milvus 一个 Collection） |
| DELETE | `/kb/delete?kb_id=xxx` | 删除知识库及全部向量数据 |
| GET | `/kb/list` | 列出所有知识库 |

### 5.2 文档管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/doc/upload?kb_id=xxx` | 上传文件（multipart/form-data），解析后向量化入库 |
| DELETE | `/doc/delete?kb_id=xxx&doc_id=xxx` | 按 doc_id 删除该文档的全部向量（增量更新基础） |
| GET | `/doc/list?kb_id=xxx` | 列出知识库下已入库的文档 |

### 5.3 RAG 问答

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat/query` | 单轮 RAG 问答，返回答案 + 检索来源片段 |

**请求体：**
```json
{
  "kb_id": "ecommerce_kb_01",
  "question": "破壁机Pro-01有加热功能吗？"
}
```

**响应体：**
```json
{
  "question": "破壁机Pro-01有加热功能吗？",
  "answer": "便携式破壁机 Pro-01 不支持热煮功能，只可搅拌加热后的液体。",
  "source": [
    {
      "doc_id": "doc_01_商品总览.md",
      "text": "便携式破壁机 Pro-01...不支持：热煮功能，只可搅拌加热后的液体",
      "sim_score": 0.873,
      "score": 1.234
    }
  ]
}
```

---

## 六、快速开始

```bash
# 1. 启动 Milvus
cd <milvus目录> && docker-compose up -d

# 2. 启动 LLM 服务（本地 Qwen，OpenAI 兼容模式）
#    （或直接在 config.py 配置云端 API）

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动后端
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 5. （可选）启动前端
streamlit run frontend.py
```

---

## 七、核心设计要点

### 7.1 多知识库隔离
每个知识库对应 Milvus 中一个独立 Collection，Collection 名即 `kb_id`。不同知识库的向量数据物理隔离，互不干扰。

### 7.2 文档增量更新
- 每条向量记录携带 `doc_id` 字段，标识所属文档。
- 更新文档时：先按 `doc_id` 删除旧向量，再重新切分写入新向量，**避免全量重建**。
- Milvus 删除为逻辑删除，需定期 `compact` 回收空间。

### 7.3 检索 + Reranker 两阶段
1. **向量粗召回**：Top-K（默认 4）条，保证召回率。
2. **Reranker 精排**：用交叉编码器对 query 和每条召回文本打分，取 Top-N（默认 3），提升相关性。
3. **Prompt 组装**：将精排后的文本拼接为上下文，要求 LLM 基于上下文回答，无答案时明确说明。

### 7.4 来源溯源
回答同时返回命中的文档片段（`doc_id` + 文本 + 相似度），前端可折叠展示，便于验证答案可信度、排查幻觉。

---

## 八、测试数据

`data/` 目录下预置电商领域知识库测试文档（6 份 Markdown）：

| 文件名 | 内容 |
|--------|------|
| doc_01_商品总览.md | 小家电、数码配件、家居日用商品参数 |
| doc_02_售后退换货政策.md | 7天无理由、保修规则、退货流程 |
| doc_03_物流配送规则.md | 发货时效、运费、偏远地区、丢件处理 |
| doc_04_会员与优惠券.md | 会员等级、积分、优惠券规则 |
| doc_05_高频客服FAQ.md | 常见问题标准回答 |
| doc_06_活动促销说明.md | 大促、秒杀、赠品、价保、拼团规则 |

### 验证用提问集

**基础检索（知识库内有答案）：**
1. 便携式破壁机 Pro-01 多少钱，有没有加热功能？
2. 桌面加湿器 H-200 续航多久，能不能直接滴精油？
3. 7 天无理由退货运费谁承担？
4. 满多少包邮？新疆还要额外运费吗？
5. V2 金卡会员有什么权益？生日有什么福利？

**多轮指代（测试查询改写）：**
1. 便携式破壁机 Pro-01 售价多少？
2. 那它支持做生豆浆吗？

**边界测试（知识库无答案，应拒绝编造）：**
1. 破壁机 Pro-01 有没有红色版本？
2. 商城有没有卖冰箱？
3. V4 会员权益是什么？

**跨文档综合：**
1. 我买了破壁机 Pro-01，摔地上坏了，可以保修吗？
2. 我在新疆买收纳箱，订单 110 元，需要付多少运费？

---

## 九、开发规范

1. **分层解耦**：路由层只做参数校验和调用 service；service 层写业务逻辑；core 层封装外部客户端；utils 放纯工具函数。禁止在路由里直接写 Milvus 操作或 LLM 调用。
2. **异常处理**：service 层抛出业务异常（如 `KnowledgeBaseNotFoundError`），路由层统一捕获并返回标准错误响应。
3. **配置外置**：所有地址、模型名、阈值参数写在 `config.py`，不硬编码在业务代码中。
4. **类型标注**：函数参数和返回值加类型注解，Pydantic 模型定义请求/响应结构。
5. **文档字符串**：public 函数/类加 docstring，说明用途、参数、返回值。

---
