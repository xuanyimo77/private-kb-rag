<template>
  <el-dialog v-model="visible" title="创建知识库" width="440px">
    <el-form @submit.prevent>
      <el-form-item label="知识库 ID">
        <el-input
          v-model="kbId"
          placeholder="如 ecommerce_kb_01（将作为 Milvus Collection 名）"
          clearable
        />
      </el-form-item>
      <p class="tip">ID 需唯一，建议使用小写字母、数字、下划线；创建后对应一个独立向量集合。</p>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="onConfirm">创建</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useKbStore } from '@/stores/kb'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [v: boolean] }>()

const kbStore = useKbStore()
const kbId = ref('')
const loading = ref(false)

const visible = ref(props.modelValue)
watch(
  () => props.modelValue,
  (v) => {
    visible.value = v
    if (v) kbId.value = ''
  },
)
watch(visible, (v) => emit('update:modelValue', v))

const onConfirm = async () => {
  const id = kbId.value.trim()
  if (!id) {
    ElMessage.warning('请输入知识库 ID')
    return
  }
  loading.value = true
  try {
    await kbStore.createKb(id)
    ElMessage.success(`知识库 ${id} 创建成功`)
    visible.value = false
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.tip {
  margin: 0;
  font-size: 12px;
  color: var(--text-sub);
}
</style>
