<template>
  <div class="chat-input">
    <el-input
      v-model="text"
      type="textarea"
      :rows="2"
      :autosize="{ minRows: 2, maxRows: 6 }"
      :placeholder="placeholder"
      :disabled="!kbReady"
      resize="none"
      @keydown="onKeydown"
    />
    <div class="input-actions">
      <span class="hint">Enter 发送 · Shift+Enter 换行</span>
      <!-- 流式中显示停止按钮，否则显示发送按钮 -->
      <el-button
        v-if="streaming"
        type="danger"
        plain
        @click="emit('stop')"
      >
        <el-icon><VideoPause /></el-icon>
        停止生成
      </el-button>
      <el-button
        v-else
        type="primary"
        :disabled="!canSend"
        @click="onSend"
      >
        <el-icon><Promotion /></el-icon>
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Promotion, VideoPause } from '@element-plus/icons-vue'

const props = defineProps<{
  streaming: boolean
  kbReady: boolean
}>()

const emit = defineEmits<{
  send: [q: string]
  stop: []
}>()

const text = ref('')

const placeholder = computed(() =>
  props.kbReady ? '请输入问题，基于当前知识库回答…' : '请先在右上角选择/创建知识库',
)
const canSend = computed(() => props.kbReady && !!text.value.trim())

const onSend = () => {
  const q = text.value.trim()
  if (!q || props.streaming || !props.kbReady) return
  emit('send', q)
  text.value = ''
}

const onKeydown = (e: KeyboardEvent) => {
  // Enter 发送，Shift+Enter 换行
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    onSend()
  }
}
</script>

<style scoped>
.chat-input {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px 12px;
}
.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}
.hint {
  font-size: 12px;
  color: var(--text-sub);
}
</style>
