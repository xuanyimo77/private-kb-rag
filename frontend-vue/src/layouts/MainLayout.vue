<template>
  <el-container class="app-layout">
    <!-- 桌面端侧边栏 -->
    <el-aside v-if="!isMobile" width="220px" class="sidebar">
      <SideContent :active-route="activeRoute" />
    </el-aside>

    <!-- 移动端抽屉导航 -->
    <el-drawer v-model="drawerOpen" direction="ltr" size="240px" :with-header="false">
      <SideContent :active-route="activeRoute" @navigate="drawerOpen = false" />
    </el-drawer>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-left">
          <el-button v-if="isMobile" text @click="drawerOpen = true">
            <el-icon :size="22"><Menu /></el-icon>
          </el-button>
          <span class="topbar-title">{{ pageTitle }}</span>
        </div>

        <div class="topbar-right">
          <!-- 全局知识库切换 -->
          <el-select
            v-model="kbStore.currentKbId"
            placeholder="选择知识库"
            class="kb-select"
            filterable
            @change="onKbChange"
          >
            <el-option
              v-for="kb in kbStore.kbs"
              :key="kb.kb_id"
              :label="kb.kb_id"
              :value="kb.kb_id"
            />
          </el-select>
          <el-tooltip :content="kbStore.currentKbId ? '刷新知识库' : '暂无知识库'">
            <el-button text :disabled="!kbStore.currentKbId" @click="kbStore.fetchKbs()">
              <el-icon :size="18"><Refresh /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip :content="isDark ? '切换亮色' : '切换暗色'">
            <el-button text @click="toggleDark">
              <el-icon :size="18">
                <Moon v-if="!isDark" />
                <Sunny v-else />
              </el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Menu, Moon, Refresh, Sunny } from '@element-plus/icons-vue'
import { useKbStore } from '@/stores/kb'
import SideContent from './SideContent.vue'

const route = useRoute()
const kbStore = useKbStore()

const isMobile = ref(window.innerWidth < 768)
const drawerOpen = ref(false)
const isDark = ref(false)

const activeRoute = computed(() => (route.name as string) || '')
const pageTitle = computed(() => (route.meta.title as string) || '私有知识库 RAG')

const onKbChange = async (kbId: string) => {
  await kbStore.setCurrent(kbId)
}

const toggleDark = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('kb_theme', isDark.value ? 'dark' : 'light')
}

const onResize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  // 初始化主题
  isDark.value = localStorage.getItem('kb_theme') === 'dark'
  document.documentElement.classList.toggle('dark', isDark.value)
  window.addEventListener('resize', onResize)
  // 加载知识库列表
  await kbStore.fetchKbs()
  if (kbStore.currentKbId) await kbStore.fetchDocs()
})
</script>

<style scoped>
.app-layout {
  height: 100%;
}

.sidebar {
  background: var(--bg-card);
  border-right: 1px solid var(--border);
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  padding: 0 16px;
  height: 56px;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topbar-title {
  font-size: 16px;
  font-weight: 600;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kb-select {
  width: 200px;
}

.main {
  padding: 0;
  background: var(--bg-page);
  overflow: hidden;
}

@media (max-width: 768px) {
  .kb-select {
    width: 130px;
  }
}
</style>
