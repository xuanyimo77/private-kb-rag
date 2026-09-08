/**
 * 知识库与文档管理 API。
 * 对应后端 /kb/* 与 /doc/* 路由。
 */
import request from './request'
import type {
  DocDeleteResponse,
  DocListResponse,
  DocUploadResponse,
  KBActionResponse,
  KBListResponse,
} from '@/types/api'

/** 列出所有知识库 */
export function listKbs(): Promise<KBListResponse> {
  return request.get('/kb/list')
}

/** 创建知识库 */
export function createKb(kbId: string): Promise<KBActionResponse> {
  return request.post('/kb/create', null, { params: { kb_id: kbId } })
}

/** 删除知识库 */
export function deleteKb(kbId: string): Promise<KBActionResponse> {
  return request.delete('/kb/delete', { params: { kb_id: kbId } })
}

/** 列出知识库下已入库文档 */
export function listDocs(
  kbId: string,
  sortField?: string,
  sortOrder?: string,
): Promise<DocListResponse> {
  const params: Record<string, any> = { kb_id: kbId }
  if (sortField) params.sort_field = sortField
  if (sortOrder) params.sort_order = sortOrder
  return request.get('/doc/list', { params })
}

/** 上传文档（multipart/form-data），支持上传进度回调 */
export function uploadDoc(
  kbId: string,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<DocUploadResponse> {
  const form = new FormData()
  form.append('file', file)
  return request.post('/doc/upload', form, {
    params: { kb_id: kbId },
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
}

/** 删除文档（按 doc_id 删除其全部向量） */
export function deleteDoc(
  kbId: string,
  docId: string,
): Promise<DocDeleteResponse> {
  return request.delete('/doc/delete', {
    params: { kb_id: kbId, doc_id: docId },
  })
}
