<template>
  <section class="auth-bg">
    <div class="mesh mesh-one"></div>
    <div class="mesh mesh-two"></div>
    <article class="card auth-card">
      <h2>欢迎回来</h2>
      <p class="desc">登录后可使用提示词、收藏和排行榜等完整功能</p>

      <el-input v-model="form.username" placeholder="用户名" class="focus-input">
        <template #prefix>
          <el-icon><User /></el-icon>
        </template>
      </el-input>

      <el-input v-model="form.password" type="password" placeholder="密码" show-password class="focus-input">
        <template #prefix>
          <el-icon><Lock /></el-icon>
        </template>
      </el-input>

      <div class="assist-row">
        <el-checkbox v-model="rememberMe">记住我</el-checkbox>
        <a class="text-link" href="javascript:void(0)">忘记密码</a>
      </div>

      <el-button type="primary" class="login-btn" @click="submit">登录</el-button>

      <div class="third-login">
        <span>第三方登录</span>
        <div class="third-actions">
          <el-button circle plain>微</el-button>
          <el-button circle plain>G</el-button>
        </div>
      </div>

      <div class="bottom-tip">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
      </div>
    </article>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { User, Lock } from "@element-plus/icons-vue";
import { api } from "../api";
import { useUserStore } from "../store/user";

const router = useRouter();
const store = useUserStore();
const form = reactive({ username: "", password: "" });
const rememberMe = ref(true);

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning("请输入用户名和密码");
    return;
  }
  const loginResp = await api.login(form);
  const token = loginResp.data.data?.token;
  const userId = Number(loginResp.data.data?.userId || 0);
  if (!token || !userId) return ElMessage.error("登录失败");
  store.setAuth(userId, token, rememberMe.value);
  ElMessage.success("登录成功");
  router.push("/");
}
</script>

<style scoped>
.auth-bg {
  position: relative;
  min-height: calc(100vh - 56px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #eef3ff 0%, #f7f0ff 58%, #fef6f2 100%);
  overflow: hidden;
}
.mesh {
  position: absolute;
  border-radius: 50%;
  filter: blur(8px);
  opacity: 0.28;
}
.mesh-one {
  width: 320px;
  height: 320px;
  background: #6d5efc;
  top: 12%;
  left: 14%;
}
.mesh-two {
  width: 260px;
  height: 260px;
  background: #22c1c3;
  bottom: 12%;
  right: 15%;
}
.auth-card {
  width: min(430px, 92vw);
  padding: 28px 24px;
  display: grid;
  gap: 14px;
  position: relative;
  z-index: 2;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
}
h2 {
  margin: 0;
  font-size: 26px;
}
.desc {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}
.assist-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.text-link {
  color: #4f46e5;
  text-decoration: none;
  font-size: 14px;
}
.login-btn {
  transition: transform .2s ease, box-shadow .2s ease;
}
.login-btn:hover {
  transform: scale(1.02);
  box-shadow: 0 8px 18px rgba(79, 70, 229, 0.35);
}
:deep(.focus-input .el-input__wrapper) {
  transition: border-color .2s ease, box-shadow .2s ease;
}
:deep(.focus-input .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #7c3aed inset, 0 0 0 4px rgba(124, 58, 237, 0.12);
}
.third-login {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #6b7280;
  font-size: 14px;
}
.third-actions {
  display: flex;
  gap: 8px;
}
.bottom-tip {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}
.bottom-tip a {
  color: #4f46e5;
  text-decoration: none;
  font-weight: 600;
}
</style>
