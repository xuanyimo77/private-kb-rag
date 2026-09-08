<template>
  <div class="doc-list">
    <!-- 排序控制栏 -->
    <div class="sort-bar">
      <span class="sort-label">排序方式：</span>
      <el-dropdown trigger="click" @command="onSortCommand">
        <el-button class="sort-btn">
          <el-icon><Sort /></el-icon>
          <span>{{ currentSortLabel }}</span>
          <el-icon class="caret"><CaretBottom /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu class="sort-menu">
            <el-dropdown-item
              v-for="opt in sortOptions"
              :key="opt.field + opt.order"
              :command="{ field: opt.field, order: opt.order as 'asc' | 'desc' }"
              :class="{ active: isActive(opt.field, opt.order) }"
            >
              <span class="sort-icon">{{ opt.icon }}</span>
              <span>{{ opt.label }}</span>
              <el-icon v-if="isActive(opt.field, opt.order)" class="check">
                <Check />
              </el-icon>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <el-table
      :data="kbStore.docs"
      v-loading="kbStore.loadingDocs"
      stripe
      style="width: 100%"
      empty-text="该知识库暂无文档，请先上传"
      row-key="doc_id"
    >
      <el-table-column prop="doc_id" label="文档 (doc_id)" min-width="260">
        <template #default="{ row }">
          <el-icon class="doc-icon"><Document /></el-icon>
          <span>{{ row.doc_id }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="chunk_count" label="向量块数" width="120" align="center">
        <template #default="{ row }">
          <el-tag size="small" type="info" effect="plain">{{ row.chunk_count }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="上传时间" width="170" align="center">
        <template #default="{ row }">
          <span v-if="row.created_at" class="time-cell">{{ formatTime(row.created_at) }}</span>
          <span v-else class="time-cell unknown">—</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" align="center">
        <template #default="{ row }">
          <el-popconfirm
            title="确认删除该文档的全部向量？"
            width="260"
            @confirm="onDelete(row.doc_id)"
          >
            <template #reference>
              <el-button type="danger" text :icon="Delete">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { CaretBottom, Check, Delete, Document, Sort } from '@element-plus/icons-vue'
import { useKbStore } from '@/stores/kb'

const kbStore = useKbStore()

/** 排序选项 */
const sortOptions = [
  { field: 'doc_id', order: 'desc', label: '文件名 Z→A', icon: '🔤' },
  { field: 'doc_id', order: 'asc', label: '文件名 A→Z', icon: '🔤' },
  { field: 'chunk_count', order: 'desc', label: '向量块 多→少', icon: '🔢' },
  { field: 'chunk_count', order: 'asc', label: '向量块 少→多', icon: '🔢' },
  { field: 'created_at', order: 'desc', label: '时间 最新优先', icon: '🕐' },
  { field: 'created_at', order: 'asc', label: '时间 最早优先', icon: '🕐' },
]

const currentSortLabel = computed(() => {
  const opt = sortOptions.find(
    (o) => o.field === kbStore.sortField && o.order === kbStore.sortOrder,
  )
  return opt?.label || '默认'
})

const isActive = (field: string, order: string) =>
  field === kbStore.sortField && order === kbStore.sortOrder

const onSortCommand = async (cmd: { field: string; order: 'asc' | 'desc' }) => {
  if (isActive(cmd.field, cmd.order)) return
  await kbStore.setSort(cmd.field, cmd.order)
}

/** Unix 时间戳 → YYYY-MM-DD HH:mm */
const formatTime = (ts: number) => {
  const d = new Date(ts * 1000)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(
    d.getHours(),
  )}:${pad(d.getMinutes())}`
}

const onDelete = async (docId: string) => {
  try {
    await kbStore.removeDoc(docId)
    ElMessage.success(`已删除文档 ${docId}`)
  } catch {
    // request 拦截器已提示
  }
}
</script>

<style scoped>
.doc-list {
  position: relative;
}

.sort-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.sort-label {
  font-size: 13px;
  color: var(--text-sub);
}

.sort-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}
.sort-btn:hover {
  color: var(--brand);
  border-color: var(--brand);
}
.sort-btn .caret {
  font-size: 12px;
  opacity: 0.6;
}

.sort-menu {
  min-width: 180px;
}
.sort-menu .active {
  background: var(--brand-light);
  color: var(--brand);
}
.sort-menu .sort-icon {
  margin-right: 6px;
  font-size: 14px;
}
.sort-menu .check {
  margin-left: auto;
  color: var(--brand);
}

.doc-icon {
  vertical-align: -2px;
  margin-right: 4px;
}

.time-cell {
  font-size: 12px;
  color: var(--text-sub);
}
.time-cell.unknown {
  color: var(--text-sub);
  opacity: 0.5;
}

/* el-table 排序过渡动画 */
:deep(.el-table__body-wrapper) {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
</style>
