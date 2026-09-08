<template>
  <div class="kb-view">
    <!-- 知识库列表 -->
    <el-card shadow="never" class="panel">
      <template #header>
        <div class="card-head">
          <span class="card-title">
            <el-icon><FolderOpened /></el-icon>
            知识库列表
          </span>
          <el-button type="primary" :icon="Plus" @click="createOpen = true">创建知识库</el-button>
        </div>
      </template>

      <el-table
        :data="kbStore.kbs"
        v-loading="kbStore.loadingKbs"
        highlight-current-row
        stripe
        empty-text="暂无知识库，点击右上角创建"
        @current-change="onSelectKb"
      >
        <el-table-column prop="kb_id" label="知识库 ID" min-width="220">
          <template #default="{ row }">
            <el-icon><CollectionTag /></el-icon>
            <span class="kb-name">{{ row.kb_id }}</span>
            <el-tag v-if="row.kb_id === kbStore.currentKbId" size="small" type="success" class="cur-tag">
              当前
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="doc_count" label="文档数" width="110" align="center" />
        <el-table-column prop="vector_count" label="向量块数" width="110" align="center" />
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button text type="primary" @click="onSelectKb(row)">查看文档</el-button>
            <el-popconfirm
              :title="`删除知识库 ${row.kb_id} 及其全部数据？`"
              width="280"
              @confirm="onDeleteKb(row.kb_id)"
            >
              <template #reference>
                <el-button text type="danger" :icon="Delete" />
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 文档管理 -->
    <el-card shadow="never" class="panel">
      <template #header>
        <div class="card-head">
          <span class="card-title">
            <el-icon><Files /></el-icon>
            文档管理
            <el-tag v-if="kbStore.currentKbId" size="small">{{ kbStore.currentKbId }}</el-tag>
          </span>
          <el-button text :icon="Refresh" @click="kbStore.fetchDocs()">刷新</el-button>
        </div>
      </template>

      <el-empty v-if="!kbStore.currentKbId" description="请先在上方选择或创建一个知识库" />
      <template v-else>
        <DocUpload />
        <el-divider />
        <DocList />
      </template>
    </el-card>

    <KbCreateDialog v-model="createOpen" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CollectionTag,
  Delete,
  Files,
  FolderOpened,
  Plus,
  Refresh,
} from '@element-plus/icons-vue'
import { useKbStore } from '@/stores/kb'
import type { KBInfo } from '@/types/api'
import KbCreateDialog from '@/components/kb/KbCreateDialog.vue'
import DocUpload from '@/components/kb/DocUpload.vue'
import DocList from '@/components/kb/DocList.vue'

const kbStore = useKbStore()
const createOpen = ref(false)

const onSelectKb = async (row: KBInfo | null) => {
  if (!row) return
  await kbStore.setCurrent(row.kb_id)
}

const onDeleteKb = async (kbId: string) => {
  try {
    await kbStore.removeKb(kbId)
    ElMessage.success(`知识库 ${kbId} 已删除`)
  } catch {
    // 拦截器已提示
  }
}
</script>

<style scoped>
.kb-view {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.panel {
  margin: 0;
}
.panel :deep(.el-card__body) {
  padding: 14px 16px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.kb-name {
  margin: 0 6px;
  font-weight: 500;
}
.cur-tag {
  margin-left: 4px;
}

@media (max-width: 992px) {
  .kb-view {
    grid-template-columns: 1fr;
    height: auto;
  }
}
</style>
