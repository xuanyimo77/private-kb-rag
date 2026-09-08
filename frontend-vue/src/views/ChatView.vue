<template>
  <div class="chat-view">
    <!-- 会话工具栏 -->
    <div class="chat-toolbar">
      <el-button :icon="Plus" plain @click="chatStore.newConversation()">
        新建会话
      </el-button>
      <span v-if="kbStore.currentKbId" class="kb-hint">
        当前知识库：<el-tag size="small">{{ kbStore.currentKbId }}</el-tag>
      </span>
      <span v-else class="kb-hint warn">尚未选择知识库，请先在右上角选择或在“知识库管理”中创建</span>
    </div>

    <!-- 消息区 -->
    <div class="chat-body">
      <div class="chat-inner">
        <ChatWindow :messages="chatStore.messages" @send="onSend" />
      </div>
    </div>

    <!-- 输入区 -->
    <div class="chat-footer">
      <div class="chat-inner">
        <ChatInput
          :streaming="chatStore.streaming"
          :kb-ready="!!kbStore.currentKbId"
          @send="onSend"
          @stop="chatStore.stop()"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useKbStore } from '@/stores/kb'
import ChatWindow from '@/components/chat/ChatWindow.vue'
import ChatInput from '@/components/chat/ChatInput.vue'

const chatStore = useChatStore()
const kbStore = useKbStore()

const onSend = async (q: string) => {
  if (!kbStore.currentKbId) return
  await chatStore.send(kbStore.currentKbId, q)
}

/** 切换知识库时清空会话，让预设问题自动切换展示 */
watch(
  () => kbStore.currentKbId,
  () => {
    chatStore.newConversation()
  },
)
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-card);
}
.kb-hint {
  font-size: 13px;
  color: var(--text-sub);
}
.kb-hint.warn {
  color: #e6a23c;
}

.chat-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  justify-content: center;
}
.chat-inner {
  width: 100%;
  max-width: 900px;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0 20px;
}

.chat-footer {
  padding: 12px 0 20px;
  display: flex;
  justify-content: center;
  background: var(--bg-page);
}
</style>
