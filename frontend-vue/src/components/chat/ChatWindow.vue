<template>
  <div ref="scrollRef" class="chat-window">
    <!-- 空状态欢迎 + 示例问题 -->
    <div v-if="!messages.length" class="welcome">
      <el-icon :size="44" color="#4f46e5"><ChatLineSquare /></el-icon>
      <h2>私有知识库 RAG 问答</h2>
      <p>基于已入库文档回答问题，答案附带可溯源的检索片段。试试下面的问题：</p>
      <div class="suggestions">
        <el-button
          v-for="q in suggestions"
          :key="q"
          round
          @click="emit('send', q)"
        >
          {{ q }}
        </el-button>
      </div>
    </div>

    <!-- 消息列表 -->
    <MessageBubble v-for="m in messages" :key="m.id" :message="m" />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { ChatLineSquare } from '@element-plus/icons-vue'
import type { UIMessage } from '@/stores/chat'
import { useKbStore } from '@/stores/kb'
import MessageBubble from './MessageBubble.vue'

const props = defineProps<{ messages: UIMessage[] }>()
const emit = defineEmits<{ send: [q: string] }>()

const scrollRef = ref<HTMLElement>()
const kbStore = useKbStore()

/** 当前知识库的预设问题（随 KB 切换自动更新） */
const suggestions = computed<string[]>(() => kbStore.currentKb?.suggestions ?? [])

// 监听末条消息的内容长度与状态（流式增量），自动滚动到底部
watch(
  () => {
    const last = props.messages[props.messages.length - 1]
    return last ? `${last.id}:${last.content.length}:${last.status}` : 'empty'
  },
  async () => {
    await nextTick()
    const el = scrollRef.value
    if (el) el.scrollTop = el.scrollHeight
  },
)
</script>

<style scoped>
.chat-window {
  flex: 1;
  overflow-y: auto;
  padding: 24px 8px 24px 0;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-sub);
}
.welcome h2 {
  margin: 16px 0 8px;
  color: var(--text-main);
}
.suggestions {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}
</style>
