import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import PromptDetailView from "../views/PromptDetailView.vue";
import FavoriteView from "../views/FavoriteView.vue";
import RankView from "../views/RankView.vue";
import PromptFormView from "../views/PromptFormView.vue";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import MyPromptsView from "../views/MyPromptsView.vue";

const routes = [
  { path: "/", component: HomeView },
  { path: "/prompt/:id", component: PromptDetailView },
  { path: "/favorites", component: FavoriteView },
  { path: "/rank", component: RankView },
  { path: "/prompt-form/:id?", component: PromptFormView },
  { path: "/my-prompts", component: MyPromptsView },
  { path: "/login", component: LoginView },
  { path: "/register", component: RegisterView }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

const whiteList = ["/login", "/register"];

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token") || sessionStorage.getItem("token");
  if (!token && !whiteList.includes(to.path)) {
    next("/login");
    return;
  }
  if (token && whiteList.includes(to.path)) {
    next("/");
    return;
  }
  next();
});

export default router;
