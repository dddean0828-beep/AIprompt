<template>
  <section class="container">
    <h2>我的提示词管理</h2>

    <article class="card block">
      <h3>本地保存草稿（仅自己可见）</h3>
      <div v-if="drafts.length" class="list">
        <div v-for="d in drafts" :key="d.localId" class="row">
          <div>
            <strong>{{ d.title || "未命名草稿" }}</strong>
            <p>{{ d.category }} | {{ formatDate(d.savedAt) }}</p>
          </div>
          <div class="ops">
            <el-button size="small" @click="editDraft(d)">编辑到上传页</el-button>
            <el-button size="small" type="danger" @click="removeDraft(d.localId)">删除</el-button>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无本地草稿" />
    </article>

    <article class="card block">
      <h3>我已发布的提示词</h3>
      <div v-if="published.length" class="list">
        <div v-for="p in published" :key="p.id" class="row">
          <div>
            <strong>{{ p.title }}</strong>
            <p>
              {{ p.category }} | {{ formatDate(p.createdAt) }} |
              <span>{{ Number(p.isPrivate) === 1 ? "私密" : "公开" }}</span>
            </p>
          </div>
          <div class="ops">
            <el-button size="small" @click="$router.push(`/prompt-form/${p.id}`)">编辑</el-button>
            <el-button size="small" @click="togglePrivate(p)">{{ Number(p.isPrivate) === 1 ? "设为公开" : "设为私密" }}</el-button>
            <el-button size="small" type="danger" @click="removePublished(p.id)">删除</el-button>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无已发布提示词" />
    </article>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { api } from "../api";
import { useUserStore } from "../store/user";

const router = useRouter();
const userStore = useUserStore();
const drafts = ref([]);
const published = ref([]);

const draftKey = () => `promptDrafts_${userStore.userId}`;
const editingDraftKey = () => `editingDraft_${userStore.userId}`;

function loadDrafts() {
  drafts.value = JSON.parse(localStorage.getItem(draftKey()) || "[]")
    .filter((d) => Number(d.ownerId) === Number(userStore.userId));
}
async function loadPublished() {
  const { data } = await api.promptMine();
  published.value = (data.data || []).filter((p) => Number(p.creatorId) === Number(userStore.userId));
}
function removeDraft(localId) {
  drafts.value = drafts.value.filter((i) => i.localId !== localId);
  localStorage.setItem(draftKey(), JSON.stringify(drafts.value));
  ElMessage.success("草稿已删除");
}
function editDraft(draft) {
  sessionStorage.setItem(editingDraftKey(), JSON.stringify(draft));
  router.push("/prompt-form");
}
async function togglePrivate(prompt) {
  const next = Number(prompt.isPrivate) === 1 ? 0 : 1;
  await api.promptTogglePrivate(prompt.id, next);
  ElMessage.success("可见性已更新");
  await loadPublished();
}
async function removePublished(id) {
  await api.promptDelete(id);
  ElMessage.success("已删除");
  await loadPublished();
}
function formatDate(v) {
  if (!v) return "-";
  return new Date(v).toLocaleString();
}

onMounted(async () => {
  loadDrafts();
  await loadPublished();
});
</script>

<style scoped>
.block { padding: 16px; margin-bottom: 14px; }
.list { display: grid; gap: 10px; }
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
}
.row p { margin: 4px 0 0; color: #6b7280; }
.ops { display: flex; gap: 8px; flex-wrap: wrap; }
</style>
