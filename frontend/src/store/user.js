import { defineStore } from "pinia";
import { ref } from "vue";

export const useUserStore = defineStore("user", () => {
  const cachedUserId = localStorage.getItem("userId") || sessionStorage.getItem("userId") || 0;
  const cachedToken = localStorage.getItem("token") || sessionStorage.getItem("token") || "";
  const userId = ref(Number(cachedUserId));
  const token = ref(cachedToken);

  function setAuth(id, tk, remember = true) {
    userId.value = id;
    token.value = tk;
    const storage = remember ? localStorage : sessionStorage;
    const otherStorage = remember ? sessionStorage : localStorage;
    storage.setItem("userId", String(id));
    storage.setItem("token", tk);
    otherStorage.removeItem("userId");
    otherStorage.removeItem("token");
  }

  function logout() {
    userId.value = 0;
    token.value = "";
    localStorage.removeItem("userId");
    localStorage.removeItem("token");
    sessionStorage.removeItem("userId");
    sessionStorage.removeItem("token");
  }

  return { userId, token, setAuth, logout };
});
