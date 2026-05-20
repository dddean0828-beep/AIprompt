<template>
  <section class="container">
    <h2>我的收藏</h2>
    <div class="grid" v-if="list.length">
      <article v-for="item in list" :key="item.favoriteId" class="card fav-card">
        <h3>{{ item.prompt.title }}</h3>
        <p class="content">{{ item.prompt.content }}</p>
        <div class="ops">
          <el-button type="primary" plain @click="$router.push(`/prompt/${item.prompt.id}`)">查看详情</el-button>
          <el-button type="danger" @click="cancelFavorite(item.favoriteId)">取消收藏</el-button>
        </div>
      </article>
    </div>
    <el-empty v-else description="暂无收藏内容" />
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { api } from "../api";
import { useUserStore } from "../store/user";

const list = ref([]);
const store = useUserStore();

async function load() {
  if (!store.userId) return;
  const { data } = await api.favoriteList(store.userId);
  list.value = data.data || [];
}
async function cancelFavorite(favoriteId) {
  await api.favoriteRemove(favoriteId);
  ElMessage.success("已取消收藏");
  await load();
}
onMounted(load);
</script>

<style scoped>
.grid { display: grid; gap: 14px; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
.fav-card { padding: 16px; }
.content {
  color: #4b5563;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.ops { display: flex; gap: 8px; }
</style>
