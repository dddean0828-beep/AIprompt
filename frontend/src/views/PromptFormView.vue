<template>
  <section class="container">
    <article class="card form-card">
      <h2>{{ form.id ? "编辑提示词" : "新增提示词" }}</h2>
      <el-form :model="form" label-width="90px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category">
            <el-option label="写作" value="写作" />
            <el-option label="编程" value="编程" />
            <el-option label="学习" value="学习" />
            <el-option label="AI绘画" value="AI绘画" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="7" /></el-form-item>
        <div class="btn-row">
          <el-button type="success" @click="uploadPrompt">上传</el-button>
          <el-button type="primary" plain @click="saveLocalDraft">保存</el-button>
        </div>
      </el-form>
    </article>
  </section>
</template>

<script setup>
import { onMounted, reactive } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { api } from "../api";
import { useUserStore } from "../store/user";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const form = reactive({ id: null, title: "", category: "写作", content: "" });

const draftKey = () => `promptDrafts_${userStore.userId}`;
const editingDraftKey = () => `editingDraft_${userStore.userId}`;

async function load() {
  const editingDraft = sessionStorage.getItem(editingDraftKey());
  if (editingDraft) {
    const parsed = JSON.parse(editingDraft);
    form.id = null;
    form.title = parsed.title || "";
    form.category = parsed.category || "写作";
    form.content = parsed.content || "";
    sessionStorage.removeItem(editingDraftKey());
    return;
  }
  if (!route.params.id) return;
  const { data } = await api.promptDetail(route.params.id);
  Object.assign(form, data.data);
}
async function uploadPrompt() {
  if (form.id) await api.promptUpdate(form);
  else await api.promptAdd(form);
  ElMessage.success("上传成功");
  router.push("/my-prompts");
}

function saveLocalDraft() {
  const draft = {
    localId: Date.now(),
    ownerId: userStore.userId,
    title: form.title,
    category: form.category,
    content: form.content,
    savedAt: new Date().toISOString()
  };
  const oldDrafts = JSON.parse(localStorage.getItem(draftKey()) || "[]");
  oldDrafts.unshift(draft);
  localStorage.setItem(draftKey(), JSON.stringify(oldDrafts));
  ElMessage.success("已保存到本地草稿");
}
onMounted(load);
</script>

<style scoped>
.form-card { padding: 20px; }
.btn-row { display: flex; gap: 10px; }
</style>
