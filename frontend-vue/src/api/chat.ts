/**
 * RAG 问答 API。
 * - queryRag：非流式（POST /chat/query）
 * - streamRag：流式 SSE（POST /chat/stream），使用 fetch ReadableStream 解析，
 *   因 EventSource 不支持 POST 请求，故采用 fetch + 手动解析事件流。
 */
import request from './request'
import type {
  ChatQueryResponse,
  ChatStreamRequest,
  StreamHandlers,
} from '@/types/api'

/** 非流式问答 */
export function queryRag(data: ChatStreamRequest): Promise<ChatQueryResponse> {
  return request.post('/chat/query', data)
}

/**
 * 流式问答（SSE）。
 * @param data 请求体（含历史）
 * @param handlers 事件回调：onMeta/onDelta/onDone/onError
 * @param signal AbortSignal，用于“停止生成”
 */
export async function streamRag(
  data: ChatStreamRequest,
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response
  try {
    response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal,
    })
  } catch (e) {
    // 主动 abort 不视为错误
    if ((e as Error).name === 'AbortError') {
      handlers.onDone?.()
      return
    }
    handlers.onError?.('network', `网络请求失败：${(e as Error).message}`)
    return
  }

  if (!response.ok || !response.body) {
    handlers.onError?.('http', `服务异常（HTTP ${response.status}）`)
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  const handleBlock = (block: string) => {
    // 一个 SSE 事件块由若干行组成，形如：
    //   event: meta
    //   data: {...}
    let event = 'message'
    const dataLines: string[] = []
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
    }
    if (!dataLines.length) return
    const raw = dataLines.join('\n')
    let payload: any = {}
    try {
      payload = JSON.parse(raw)
    } catch {
      payload = { text: raw }
    }

    switch (event) {
      case 'meta':
        handlers.onMeta?.(payload)
        break
      case 'delta':
        handlers.onDelta?.(payload.text ?? '')
        break
      case 'done':
        handlers.onDone?.()
        break
      case 'error':
        handlers.onError?.(payload.code ?? 'rag_error', payload.message ?? '生成失败')
        break
    }
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      // SSE 事件以空行（\n\n）分隔
      let idx: number
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.slice(0, idx)
        buffer = buffer.slice(idx + 2)
        if (block.trim()) handleBlock(block)
      }
    }
    // 处理缓冲区残余
    if (buffer.trim()) handleBlock(buffer)
  } catch (e) {
    if ((e as Error).name === 'AbortError') {
      handlers.onDone?.()
      return
    }
    handlers.onError?.('stream', `流式读取中断：${(e as Error).message}`)
  }
}
