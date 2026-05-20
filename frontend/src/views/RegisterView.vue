<template>
  <section class="container auth">
    <article class="card auth-card">
      <h2>注册</h2>
      <el-input v-model="form.username" placeholder="用户名" />
      <el-input v-model="form.password" type="password" placeholder="密码" />
      <el-button type="primary" @click="submit">注册</el-button>
    </article>
  </section>
</template>

<script setup>
import { reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { api } from "../api";

const router = useRouter();
const form = reactive({ username: "", password: "" });

async function submit() {
  await api.register(form);
  ElMessage.success("注册成功，请登录");
  router.push("/login");
}
</script>

<style scoped>
.auth { display: flex; justify-content: center; }
.auth-card { width: min(420px, 96vw); padding: 20px; display: grid; gap: 12px; }
</style>
