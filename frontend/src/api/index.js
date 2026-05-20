import http from "./http";

export const api = {
  register: (payload) => http.post("/user/register", payload),
  login: (payload) => http.post("/user/login", payload),
  userInfo: (userId) => http.get("/user/info", { params: { userId } }),
  promptList: (category, keyword) => http.get("/prompt/list", { params: { category, keyword } }),
  promptDetail: (id) => http.get(`/prompt/detail/${id}`),
  promptAdd: (payload) => http.post("/prompt/add", payload),
  promptUpdate: (payload) => http.put("/prompt/update", payload),
  promptDelete: (id) => http.delete(`/prompt/delete/${id}`),
  promptMine: () => http.get("/prompt/mine"),
  promptTogglePrivate: (id, isPrivate) => http.put(`/prompt/toggle-private/${id}`, null, { params: { isPrivate } }),
  favoriteAdd: (payload) => http.post("/favorite/add", payload),
  favoriteRemove: (id) => http.delete(`/favorite/remove/${id}`),
  favoriteList: (userId) => http.get("/favorite/list", { params: { userId } }),
  usageAdd: (payload) => http.post("/usage/add", payload),
  hotRank: () => http.get("/rank/hot"),
  favoriteRank: () => http.get("/rank/favorite")
};
