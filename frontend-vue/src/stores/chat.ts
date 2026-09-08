/**
 * 对话状态管理：消息列表、流式问答、多轮历史、停止生成。
 */
import { defineStore } from 'pinia'
import { streamRag } from '@/api/chat'
import type { ChatMessage, SourceChunk } from '@/types/api'

/** 前端展示用消息 */
export interface UIMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceChunk[]
  rewritten?: string
  status: 'streaming' | 'done' | 'error'
  error?: string
}

let seq = 0
const genId = () => `m_${Date.now()}_${seq++}`

// 注意：AbortController 属于带内部槽的 DOM 对象，不能放进 Pinia 响应式 state
// （Vue 的 Proxy 包装会使传给 fetch 的 AbortSignal 异常），故用模块级变量持有。
let activeController: AbortController | null = null

interface ChatState {
  messages: UIMessage[]
  streaming: boolean
}

export const useChatStore = defineStore('chat', {
  state: (): ChatState => ({
    messages: [],
    streaming: false,
  }),

  actions: {
    /** 新建会话（清空消息） */
    newConversation() {
      this.stop()
      this.messages = []
    },

    /** 停止生成 */
    stop() {
      activeController?.abort()
      activeController = null
      this.streaming = false
      // 把仍在流式中的消息标记为完成
      const pending = this.messages.find((m) => m.status === 'streaming')
      if (pending) {
        pending.status = 'done'
        if (!pending.content) pending.content = '（已停止生成）'
      }
    },

    /** 发送问题（流式） */
    async send(kbId: string, question: string) {
      const q = question.trim()
      if (!q || this.streaming || !kbId) return

      // 本轮之前的对话作为多轮历史（仅取已完成的 user/assistant 文本）
      const history: ChatMessage[] = this.messages
        .filter((m) => m.status === 'done')
        .map((m) => ({ role: m.role, content: m.content }))

      const userMsg: UIMessage = {
        id: genId(),
        role: 'user',
        content: q,
        status: 'done',
      }
      const aiMsg: UIMessage = {
        id: genId(),
        role: 'assistant',
        content: '',
        status: 'streaming',
      }
      this.messages.push(userMsg, aiMsg)
      // 关键：从响应式数组取回 Vue 代理对象。
      // push 时传入的是普通对象，闭包直接持有它时，后续改属性不经过 Proxy 的 set，
      // 无法触发视图更新；必须操作 this.messages 中代理化后的同一个对象。
      const ai = this.messages[this.messages.length - 1]
      this.streaming = true
      activeController = new AbortController()

      await streamRag(
        { kb_id: kbId, question: q, history },
        {
          onMeta: (meta) => {
            ai.rewritten = meta.rewritten_question
            ai.sources = meta.source
          },
          onDelta: (text) => {
            ai.content += text
          },
          onDone: () => {
            ai.status = 'done'
            if (!ai.content) ai.content = '（无返回内容）'
          },
          onError: (_code, message) => {
            ai.status = 'error'
            ai.error = message
            if (!ai.content) ai.content = `生成失败：${message}`
          },
        },
        activeController.signal,
      )

      this.streaming = false
      activeController = null
      if (ai.status === 'streaming') ai.status = 'done'
    },
  },
})
