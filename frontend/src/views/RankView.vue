<template>
  <section class="container rank-wrap">
    <article class="card block">
      <h3>热门提示词</h3>
      <ol><li v-for="i in hot" :key="i.id">{{ i.title }}（{{ i.useCount }}）</li></ol>
    </article>
    <article class="card block">
      <h3>收藏排行榜</h3>
      <ol><li v-for="i in favorite" :key="i.id">{{ i.title }}（{{ i.favoriteCount }}）</li></ol>
    </article>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { api } from "../api";

const hot = ref([]);
const favorite = ref([]);
async function load() {
  hot.value = (await api.hotRank()).data.data || [];
  favorite.value = (await api.favoriteRank()).data.data || [];
}
onMounted(load);
</script>

<style scoped>
.rank-wrap { display: grid; gap: 14px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.block { padding: 16px; }
@media (max-width: 800px) { .rank-wrap { grid-template-columns: 1fr; } }
</style>
