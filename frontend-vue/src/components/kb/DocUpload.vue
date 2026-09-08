<template>
  <el-upload
    drag
    multiple
    :accept="accept"
    :show-file-list="false"
    :http-request="customUpload"
    :before-upload="beforeUpload"
  >
    <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
    <div class="el-upload__text">
      拖拽文件到此处，或 <em>点击上传</em>
    </div>
    <template #tip>
      <div class="upload-tip">
        支持 PDF / TXT / Markdown，单个文件不超过 20MB；同名文件重新上传将增量更新（先删旧向量再写入）
      </div>
    </template>
  </el-upload>

  <!-- 上传进度列表 -->
  <div v-if="tasks.length" class="upload-tasks">
    <div v-for="t in tasks" :key="t.uid" class="task-row">
      <el-icon><Document /></el-icon>
      <span class="task-name" :title="t.name">{{ t.name }}</span>
      <el-progress
        :percentage="t.progress"
        :status="t.status"
        :stroke-width="6"
        class="task-progress"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadRequestOptions } from 'element-plus'
import { Document, UploadFilled } from '@element-plus/icons-vue'
import { useKbStore } from '@/stores/kb'

const kbStore = useKbStore()
const accept = '.pdf,.txt,.md'

interface UploadTask {
  uid: number
  name: string
  progress: number
  status: '' | 'success' | 'exception'
}
const tasks = ref<UploadTask[]>([])

const beforeUpload = (file: File) => {
  const okExt = /\.(pdf|txt|md)$/i.test(file.name)
  if (!okExt) {
    ElMessage.error(`不支持的文件格式：${file.name}`)
    return false
  }
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error(`文件超过 20MB：${file.name}`)
    return false
  }
  return true
}

// 自定义上传：调用 store，更新进度
const customUpload = async (options: UploadRequestOptions) => {
  const file = options.file as File
  const uid = Date.now() + Math.random()
  const task: UploadTask = { uid, name: file.name, progress: 0, status: '' }
  tasks.value.push(task)

  try {
    const res = await kbStore.uploadDoc(file, (p) => {
      task.progress = p
    })
    task.progress = 100
    task.status = 'success'
    ElMessage.success(res.message || `${file.name} 入库成功`)
  } catch {
    task.status = 'exception'
    ElMessage.error(`${file.name} 上传失败`)
  } finally {
    // 5 秒后移除已完成任务
    setTimeout(() => {
      tasks.value = tasks.value.filter((t) => t.uid !== uid)
    }, 5000)
  }
}
</script>

<style scoped>
.upload-tip {
  font-size: 12px;
  color: var(--text-sub);
  margin-top: 6px;
}
.upload-tasks {
  margin-top: 12px;
}
.task-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}
.task-name {
  font-size: 13px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-progress {
  flex: 1;
}
</style>
