<template>
  <!-- 仅当改写后的问题与原问题不同时展示，体现多轮指代消解 -->
  <el-tooltip v-if="rewritten && rewritten !== original" placement="top">
    <template #content>多轮对话已将问题改写为独立检索问题</template>
    <div class="rewrite-tag">
      <el-icon><MagicStick /></el-icon>
      <span class="rewrite-label">检索问题：</span>
      <span class="rewrite-text">{{ rewritten }}</span>
    </div>
  </el-tooltip>
</template>

<script setup lang="ts">
import { MagicStick } from '@element-plus/icons-vue'

defineProps<{ original?: string; rewritten?: string }>()
</script>

<style scoped>
.rewrite-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  margin-bottom: 8px;
  padding: 4px 10px;
  font-size: 12px;
  color: var(--brand);
  background: var(--brand-light);
  border-radius: 6px;
}
.rewrite-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
