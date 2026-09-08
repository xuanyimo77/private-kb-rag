# 私有知识库 RAG 系统 · 前端

基于 **Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router** 的 RAG 知识库前端，
对接 FastAPI 后端（默认 `http://127.0.0.1:8000`），支持知识库管理、文档上传、**流式问答**与**多轮对话（指代改写）**。

## 功能

- **RAG 问答**：SSE 流式逐字渲染答案；检索完成即展示可折叠**检索来源**（文档 ID、向量相似度 sim、Reranker 精排得分、原文片段）。
- **多轮对话**：携带对话历史，后端用 LLM 把含指代词（它/这个/那）的问题**改写为独立检索问题**，前端展示改写标签。
- **停止生成 / 新建会话**。
- **知识库管理**：创建、删除、列表（文档数 / 向量块数）。
- **文档管理**：拖拽上传 PDF/TXT/MD（上传进度条、格式与大小校验、同名增量更新）、文档列表、按文档删除。
- **暗色主题**、响应式布局（移动端抽屉导航）、Markdown 答案渲染。

## 技术栈

| 维度 | 选型 |
|------|------|
| 框架 | Vue 3（`<script setup>`）+ TypeScript |
| 构建 | Vite 5 |
| UI | Element Plus + @element-plus/icons-vue |
| 状态 | Pinia |
| 路由 | Vue Router（页面懒加载） |
| 请求 | Axios（REST）+ fetch ReadableStream（SSE，POST 无法用 EventSource） |
| Markdown | markdown-it（禁用原始 HTML 防注入） |

## 快速开始

```bash
# 1. 确保后端已启动（FastAPI 端口 8000）与 Milvus 已运行
#    后端根目录：uvicorn main:app --host 0.0.0.0 --port 8000

# 2. 安装依赖（首次）
cd frontend-vue
npm install

# 3. 启动开发服务器（默认 http://localhost:5173）
npm run dev
```

打开 http://localhost:5173 即可。开发环境下 `/api` 由 Vite 代理到 `127.0.0.1:8000`，无跨域问题。

> 后端地址可用环境变量覆盖：`VITE_BACKEND_ORIGIN=http://其他地址:8000 npm run dev`（见 `vite.config.ts`）。

## 构建与部署

```bash
npm run build     # 类型检查（vue-tsc）+ 产物输出到 dist/
npm run preview   # 本地预览生产产物
```

生产部署时把 `dist/` 交给 Nginx 等静态服务器，并将 `/api` 反向代理到 FastAPI：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_buffering off;          # SSE 必须关闭缓冲，保证实时推送
    proxy_read_timeout 300s;
}
```

## 目录结构

```
frontend-vue/src/
├── main.ts                # 入口：Pinia/Router/ElementPlus/暗色主题
├── App.vue
├── style.css              # 主题变量、Markdown 样式、流式光标
├── router/index.ts        # 路由（懒加载）
├── types/api.ts           # 与后端 Pydantic 对齐的 TS 类型
├── api/
│   ├── request.ts         # Axios 实例（/api 前缀 + 错误提示）
│   ├── kb.ts              # 知识库/文档接口
│   └── chat.ts            # 问答接口 + SSE 流式解析
├── stores/
│   ├── kb.ts              # 知识库列表/当前库/文档
│   └── chat.ts            # 消息流/流式问答/多轮历史/停止
├── utils/markdown.ts      # markdown-it 渲染
├── layouts/
│   ├── MainLayout.vue     # 侧边栏 + 顶栏（知识库切换/主题）
│   └── SideContent.vue
├── views/
│   ├── ChatView.vue       # 问答页
│   └── KbView.vue         # 知识库管理页
└── components/
    ├── chat/  ChatWindow / MessageBubble / SourcePanel / RewriteTag / ChatInput
    └── kb/    KbCreateDialog / DocUpload / DocList
```

## 后端配套接口

前端流式与多轮依赖后端新增能力（已实现）：

- `POST /chat/stream`：SSE 流式问答。请求体 `{ kb_id, question, history: [{role, content}] }`。
  事件流：`meta`（改写问题 + 来源）→ 多个 `delta`（答案增量）→ `done`；异常发 `error`。
- `POST /chat/query`：非流式问答（保留）。

## 关键实现说明

- **SSE 解析**：`EventSource` 仅支持 GET，故用 `fetch` + `response.body.getReader()` 按 `\n\n` 切分事件块。
- **停止生成**：`AbortController` 中断 fetch。注意 AbortController 不能放进 Pinia 响应式 state（Vue 的 Proxy 会破坏带内部槽的 DOM 对象），故在 store 中用模块级变量持有。
- **响应式更新**：流式回调中更新的消息对象，必须是 `this.messages` 数组里的 **Vue 代理对象**（push 后通过索引取回），直接改原始普通对象不会触发视图更新。
- **性能**：路由级代码分割、第三方库分包（vue / element / markdown）、Axios 与 fetch 错误统一处理。

## 常见问题

| 现象 | 处理 |
|------|------|
| 页面请求报网络错误 | 后端未启动或端口非 8000；检查 FastAPI / Milvus |
| 问答一直“检索中”无答案 | 查看后端日志；多为 Milvus 未连接或 LLM Key/网络问题 |
| 首次问答较慢 | 本地 Reranker 模型（约 2.3GB）首次加载，后续即快 |
| element 包体积提示 | 全量引入 gzip 约 341KB；如需更小体积可改 `unplugin-vue-components` 按需引入 |
