<template>
  <div class="bubble-row" :class="message.role">
    <!-- AI 头像 -->
    <div v-if="message.role === 'assistant'" class="avatar ai">
      <el-icon><Cpu /></el-icon>
    </div>

    <div class="bubble" :class="[message.role, message.status]">
      <!-- 用户消息纯文本 -->
      <template v-if="message.role === 'user'">
        <div class="user-text">{{ message.content }}</div>
      </template>

      <!-- AI 消息 -->
      <template v-else>
        <RewriteTag :rewritten="message.rewritten" />

        <!-- 检索中骨架 -->
        <div v-if="message.status === 'streaming' && !message.content && !message.sources" class="loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          正在检索知识库…
        </div>

        <!-- 答案正文（markdown） -->
        <div
          v-if="message.content"
          class="md-body"
          :class="{ 'stream-cursor': message.status === 'streaming' }"
          v-html="rendered"
        ></div>

        <!-- 错误提示 -->
        <el-alert
          v-if="message.status === 'error'"
          :title="message.error || '生成失败'"
          type="error"
          :closable="false"
          show-icon
          class="err-alert"
        />

        <!-- 检索来源 -->
        <SourcePanel :sources="message.sources" />
      </template>
    </div>

    <!-- 用户头像 -->
    <div v-if="message.role === 'user'" class="avatar user">
      <el-icon><User /></el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Cpu, Loading, User } from '@element-plus/icons-vue'
import { renderMarkdown } from '@/utils/markdown'
import type { UIMessage } from '@/stores/chat'
import RewriteTag from './RewriteTag.vue'
import SourcePanel from './SourcePanel.vue'

const props = defineProps<{ message: UIMessage }>()

// 流式过程中实时渲染 markdown
const rendered = computed(() => renderMarkdown(props.message.content))
</script>

<style scoped>
.bubble-row {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  align-items: flex-start;
}
.bubble-row.user {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #fff;
}
.avatar.ai {
  background: var(--brand);
}
.avatar.user {
  background: #64748b;
}

.bubble {
  max-width: 78%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14.5px;
  line-height: 1.7;
}
.bubble.user {
  background: var(--brand);
  color: #fff;
  border-top-right-radius: 4px;
}
.bubble.assistant {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-top-left-radius: 4px;
}

.user-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.loading {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-sub);
  font-size: 13.5px;
}

.err-alert {
  margin-top: 8px;
}

@media (max-width: 768px) {
  .bubble {
    max-width: 88%;
  }
}
</style>
