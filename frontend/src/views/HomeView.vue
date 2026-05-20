<template>
  <section class="container">
    <div class="search-row">
      <el-input
        v-model="keyword"
        placeholder="按提示词标题模糊搜索"
        clearable
        @keyup.enter="load"
      />
      <el-button type="primary" @click="load">搜索</el-button>
    </div>
    <el-tabs v-model="category" @tab-change="load">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="写作" name="写作" />
      <el-tab-pane label="编程" name="编程" />
      <el-tab-pane label="学习" name="学习" />
      <el-tab-pane label="AI绘画" name="AI绘画" />
    </el-tabs>
    <div class="grid">
      <PromptCard v-for="item in list" :key="item.id" :prompt="item" @favorite="favorite" />
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { api } from "../api";
import { useUserStore } from "../store/user";
import PromptCard from "../components/PromptCard.vue";

const list = ref([]);
const category = ref("");
const keyword = ref("");
const store = useUserStore();

async function load() {
  const { data } = await api.promptList(category.value || undefined, keyword.value || undefined);
  list.value = data.data || [];
}
async function favorite(promptId) {
  if (!store.userId) return ElMessage.warning("请先登录");
  await api.favoriteAdd({ userId: store.userId, promptId });
  ElMessage.success("收藏成功");
  await load();
}
onMounted(load);
</script>

<style scoped>
.search-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  margin-bottom: 12px;
}
.grid { display: grid; gap: 14px; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
</style>
