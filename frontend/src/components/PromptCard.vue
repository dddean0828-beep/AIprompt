<template>
  <article class="card p-card fade-in">
    <h3>{{ prompt.title }}</h3>
    <el-tag type="primary">{{ prompt.category }}</el-tag>
    <p>{{ prompt.content }}</p>
    <div class="meta">使用 {{ prompt.useCount || 0 }} | 收藏 {{ prompt.favoriteCount || 0 }}</div>
    <div class="ops">
      <el-button type="primary" @click="useAndCopy">复制</el-button>
      <el-button @click="$emit('favorite', prompt.id)">收藏</el-button>
      <el-button @click="$router.push(`/prompt/${prompt.id}`)">详情</el-button>
    </div>
  </article>
</template>

<script setup>
import { ElMessage } from "element-plus";
import { api } from "../api";
import { useUserStore } from "../store/user";

const store = useUserStore();
const props = defineProps({ prompt: { type: Object, required: true } });

async function useAndCopy() {
  await navigator.clipboard.writeText(props.prompt.content || "");
  if (store.userId) {
    await api.usageAdd({ userId: store.userId, promptId: props.prompt.id });
  }
  ElMessage.success("已复制");
}
</script>

<style scoped>
.p-card { padding: 16px; transition: transform .2s ease; }
.p-card:hover { transform: translateY(-4px) scale(1.01); }
h3 { margin: 0 0 10px; }
p { min-height: 54px; color: #4b5563; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.meta { color: #6b7280; margin-bottom: 10px; }
.ops { display: flex; gap: 8px; }
</style>
