/**
 * 接口类型定义，与后端 Pydantic 模型（models/schemas.py）对齐。
 */

/** 知识库信息 */
export interface KBInfo {
  kb_id: string
  doc_count: number
  vector_count: number
  suggestions: string[]
}

/** 知识库列表响应 */
export interface KBListResponse {
  total: number
  items: KBInfo[]
}

/** 知识库创建/删除通用响应 */
export interface KBActionResponse {
  kb_id: string
  success: boolean
  message: string
}

/** 文档元信息 */
export interface DocInfo {
  doc_id: string
  chunk_count: number
  created_at: number | null
  updated_at: number | null
}

/** 文档列表响应 */
export interface DocListResponse {
  kb_id: string
  total: number
  items: DocInfo[]
  sort_field: string | null
  sort_order: string | null
}

/** 文档上传响应 */
export interface DocUploadResponse {
  doc_id: string
  chunk_count: number
  success: boolean
  message: string
}

/** 文档删除响应 */
export interface DocDeleteResponse {
  doc_id: string
  deleted: number
  success: boolean
  message: string
}

/** 对话历史消息（多轮） */
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

/** 流式问答请求体 */
export interface ChatStreamRequest {
  kb_id: string
  question: string
  history: ChatMessage[]
}

/** 检索来源片段 */
export interface SourceChunk {
  doc_id: string
  text: string
  sim_score: number
  score: number | null
}

/** 非流式问答响应 */
export interface ChatQueryResponse {
  question: string
  answer: string
  source: SourceChunk[]
}

/** SSE meta 事件数据 */
export interface StreamMeta {
  question: string
  rewritten_question: string
  source: SourceChunk[]
}

/** SSE 事件回调集合 */
export interface StreamHandlers {
  onMeta?: (meta: StreamMeta) => void
  onDelta?: (text: string) => void
  onDone?: () => void
  onError?: (code: string, message: string) => void
}
