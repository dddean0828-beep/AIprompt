<template>
  <header class="nav">
    <div class="container nav-inner">
      <strong>AI提示词管理系统</strong>
      <nav>
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/favorites">我的收藏</RouterLink>
        <RouterLink to="/rank">排行榜</RouterLink>
        <RouterLink to="/prompt-form">新增提示词</RouterLink>
        <RouterLink to="/my-prompts">我的提示词</RouterLink>
        <RouterLink v-if="!isLoggedIn" to="/login">登录</RouterLink>
        <RouterLink v-if="!isLoggedIn" to="/register">注册</RouterLink>
        <button v-if="isLoggedIn" class="logout-btn" @click="logout">退出登录</button>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "../store/user";

const router = useRouter();
const userStore = useUserStore();
const isLoggedIn = computed(() => !!userStore.token);

function logout() {
  userStore.logout();
  router.push("/login");
}
</script>

<style scoped>
.nav { background: linear-gradient(90deg, #4f46e5, #7c3aed); color: #fff; }
.nav-inner { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; }
nav { display: flex; gap: 14px; }
a { color: #fff; text-decoration: none; opacity: .9; }
a.router-link-active { opacity: 1; font-weight: 700; }
.logout-btn {
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  padding: 4px 10px;
  cursor: pointer;
}
</style>
