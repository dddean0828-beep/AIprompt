<template>
  <section class="container">
    <article class="card page" v-if="detail">
      <h2>{{ detail.title }}</h2>
      <el-tag>{{ detail.category }}</el-tag>
      <div class="meta">
        <span>发布者：{{ detail.creatorName || "未知" }}</span>
        <span>发布时间：{{ formatDate(detail.createdAt) }}</span>
      </div>
      <pre>{{ detail.content }}</pre>
      <el-button type="primary" @click="copy">一键复制</el-button>
    </article>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { api } from "../api";

const route = useRoute();
const detail = ref();
async function load() {
  const { data } = await api.promptDetail(route.params.id);
  detail.value = data.data;
}
async function copy() {
  await navigator.clipboard.writeText(detail.value.content || "");
  ElMessage.success("复制成功");
}
function formatDate(v) {
  if (!v) return "-";
  return new Date(v).toLocaleString();
}
onMounted(load);
</script>

<style scoped>
.page { padding: 20px; }
.meta { margin: 10px 0; color: #6b7280; display: flex; gap: 16px; flex-wrap: wrap; }
pre { white-space: pre-wrap; }
</style>
