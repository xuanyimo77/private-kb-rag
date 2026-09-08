/**
 * 知识库状态管理：知识库列表、当前选中知识库、文档列表。
 */
import { defineStore } from 'pinia'
import {
  createKb as apiCreateKb,
  deleteKb as apiDeleteKb,
  deleteDoc as apiDeleteDoc,
  listDocs,
  listKbs,
  uploadDoc as apiUploadDoc,
} from '@/api/kb'
import type { DocInfo, KBInfo } from '@/types/api'

interface KbState {
  kbs: KBInfo[]
  currentKbId: string
  docs: DocInfo[]
  loadingKbs: boolean
  loadingDocs: boolean
  // 排序状态
  sortField: string
  sortOrder: 'asc' | 'desc'
}

export const useKbStore = defineStore('kb', {
  state: (): KbState => ({
    kbs: [],
    currentKbId: '',
    docs: [],
    loadingKbs: false,
    loadingDocs: false,
    sortField: 'doc_id',
    sortOrder: 'desc',
  }),

  getters: {
    currentKb: (state) => state.kbs.find((k) => k.kb_id === state.currentKbId),
  },

  actions: {
    /** 拉取知识库列表 */
    async fetchKbs() {
      this.loadingKbs = true
      try {
        const res = await listKbs()
        this.kbs = res.items
        // 默认选中第一个知识库
        if (!this.currentKbId && this.kbs.length) {
          this.currentKbId = this.kbs[0].kb_id
        }
      } finally {
        this.loadingKbs = false
      }
    },

    /** 设置当前知识库并加载其文档 */
    async setCurrent(kbId: string) {
      this.currentKbId = kbId
      await this.fetchDocs()
    },

    /** 拉取当前知识库文档列表（带排序） */
    async fetchDocs() {
      if (!this.currentKbId) {
        this.docs = []
        return
      }
      this.loadingDocs = true
      try {
        const res = await listDocs(this.currentKbId, this.sortField, this.sortOrder)
        this.docs = res.items
      } finally {
        this.loadingDocs = false
      }
    },

    /** 切换排序（触发重新拉取） */
    async setSort(field: string, order: 'asc' | 'desc') {
      this.sortField = field
      this.sortOrder = order
      await this.fetchDocs()
    },

    /** 创建知识库 */
    async createKb(kbId: string) {
      await apiCreateKb(kbId)
      await this.fetchKbs()
      await this.setCurrent(kbId)
    },

    /** 删除知识库 */
    async removeKb(kbId: string) {
      await apiDeleteKb(kbId)
      if (this.currentKbId === kbId) this.currentKbId = ''
      await this.fetchKbs()
      if (this.kbs.length) await this.setCurrent(this.kbs[0].kb_id)
      else this.docs = []
    },

    /** 上传文档 */
    async uploadDoc(file: File, onProgress?: (p: number) => void) {
      // 锁定上传时的目标知识库，避免用户中途切换导致 fetchDocs 拉错库
      const targetKbId = this.currentKbId
      if (!targetKbId) {
        throw new Error('请先选择知识库')
      }
      const res = await apiUploadDoc(targetKbId, file, onProgress)
      // 仅在目标库仍是当前选中库时刷新文档列表
      if (this.currentKbId === targetKbId) {
        await this.fetchDocs()
      }
      // 无论如何刷新知识库列表（更新计数）
      await this.fetchKbs()
      return res
    },

    /** 删除文档 */
    async removeDoc(docId: string) {
      await apiDeleteDoc(this.currentKbId, docId)
      await this.fetchDocs()
    },
  },
})
