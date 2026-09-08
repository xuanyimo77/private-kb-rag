<template>
  <div v-if="sources && sources.length" class="source-panel">
    <el-collapse>
      <el-collapse-item name="sources">
        <template #title>
          <span class="source-title">
            <el-icon><Document /></el-icon>
            检索来源（{{ sources.length }}）
          </span>
        </template>

        <div v-for="(s, i) in sources" :key="i" class="source-item">
          <div class="source-head">
            <el-tag size="small" type="primary" effect="plain" class="doc-tag">
              {{ s.doc_id }}
            </el-tag>
            <span class="scores">
              <el-tooltip content="向量相似度（COSINE）">
                <el-tag size="small" type="info" effect="plain">
                  sim {{ (s.sim_score ?? 0).toFixed(3) }}
                </el-tag>
              </el-tooltip>
              <el-tooltip v-if="s.score != null" content="Reranker 精排得分（越高越相关）">
                <el-tag size="small" type="success" effect="plain">
                  rerank {{ s.score.toFixed(3) }}
                </el-tag>
              </el-tooltip>
            </span>
          </div>
          <!-- 相关性进度条 -->
          <el-progress
            v-if="s.score != null"
            :percentage="scorePercent(s.score)"
            :stroke-width="4"
            :show-text="false"
            class="score-bar"
          />
          <div class="source-text">{{ s.text }}</div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { Document } from '@element-plus/icons-vue'
import type { SourceChunk } from '@/types/api'

defineProps<{ sources?: SourceChunk[] }>()

// rerank 得分通常在 0~1 区间（sigmoid 后），转为百分比展示
const scorePercent = (score: number) => {
  const pct = Math.round(Math.min(Math.max(score, 0), 1) * 100)
  return pct
}
</script>

<style scoped>
.source-panel {
  margin-top: 10px;
  border-top: 1px dashed var(--border);
  padding-top: 6px;
}
.source-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-sub);
}
.source-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}
.source-item:last-child {
  border-bottom: none;
}
.source-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}
.scores {
  display: inline-flex;
  gap: 4px;
}
.score-bar {
  margin: 6px 0;
}
.source-text {
  margin-top: 6px;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--text-sub);
  white-space: pre-wrap;
  background: rgba(127, 127, 127, 0.08);
  border-radius: 6px;
  padding: 8px 10px;
  max-height: 180px;
  overflow-y: auto;
}
</style>
