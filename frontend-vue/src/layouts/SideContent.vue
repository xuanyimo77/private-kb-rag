<template>
  <div class="side-content">
    <div class="logo">
      <el-icon :size="22" color="#4f46e5"><CollectionTag /></el-icon>
      <span class="logo-text">私有知识库</span>
    </div>

    <el-menu
      :default-active="activeRoute"
      router
      class="side-menu"
      @select="emit('navigate')"
    >
      <el-menu-item index="chat" route="/chat">
        <el-icon><ChatDotRound /></el-icon>
        <span>RAG 问答</span>
      </el-menu-item>
      <el-menu-item index="kb" route="/kb">
        <el-icon><FolderOpened /></el-icon>
        <span>知识库管理</span>
      </el-menu-item>
    </el-menu>

    <div class="side-footer">
      <el-tag size="small" type="info" effect="plain">FastAPI · Milvus · DeepSeek</el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CollectionTag, ChatDotRound, FolderOpened } from '@element-plus/icons-vue'

defineProps<{ activeRoute: string }>()
const emit = defineEmits<{ navigate: [] }>()
</script>

<style scoped>
.side-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px 8px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 16px;
  font-size: 17px;
  font-weight: 700;
}

.side-menu {
  border-right: none;
  flex: 1;
}

.side-footer {
  padding: 12px;
  text-align: center;
}
</style>
