# AI 提示词管理系统 — 实现说明（含代码与界面截图指引）

本文档分**后端系统**与**前端系统**两部分，**每项核心业务均配合源码说明**。界面功能展示图请放入 `docs/screenshots/` 目录（见该目录下 `README.md` 的命名建议），文档中已用 Markdown 图片语法预留位置；你把图片文件放到对应路径后，预览 Markdown 即可显示。

---

## 截图文件放置说明

- 截图根目录：`docs/screenshots/`
- 文档中的引用路径相对于**项目根目录** `d:\AIprompt\`，例如：`docs/screenshots/01-login.png`
- 若图片尚未放入，Markdown 预览会显示“图片无法加载”，属正常现象，补全文件即可。

---

# 第一部分：后端系统

## 1.1 技术栈与分层

| 技术 | 作用 |
|------|------|
| Spring Boot 3.x | Web、依赖注入、配置 |
| MyBatis-Plus | `BaseMapper` + `LambdaQueryWrapper` 访问 MySQL |
| JWT | 登录态令牌，请求头 `Authorization: Bearer <token>` |
| Lombok | 实体/DTO 简化 |

分层关系：**Controller（REST）→ Service（业务）→ Mapper（持久化）**，统一响应体 `Result<T>`。

---

## 1.2 后端目录结构

```text
backend/src/main/java/com/aiprompt/
├── AipromptApplication.java
├── common/Result.java
├── config/WebConfig.java、AuthInterceptor.java
├── controller/          # User、Prompt、Favorite、Usage、Rank
├── dto/                 # AuthRequest、FavoriteRequest、FavoritePromptVO 等
├── entity/              # User、Prompt、Favorite、UsageRecord …
├── mapper/
├── service/ 与 service/impl/
└── utils/JwtUtils.java
```

---

## 1.3 核心业务与代码讲解

### （1）统一返回格式 `Result`

**业务说明**：所有接口返回 `code`、`message`、`data`，前端可统一判断成功/失败。

**代码位置**：`backend/src/main/java/com/aiprompt/common/Result.java`

```15:24:d:\AIprompt\backend\src\main\java\com\aiprompt\common\Result.java
    public static <T> Result<T> ok(T data) {
        return new Result<>(200, "success", data);
    }

    public static <T> Result<T> ok(String message, T data) {
        return new Result<>(200, message, data);
    }

    public static <T> Result<T> fail(String message) {
        return new Result<>(500, message, null);
    }
```

---

### （2）用户注册 / 登录与 JWT 载荷

**业务说明**：注册写入用户表；登录校验用户名密码后签发 JWT，并返回 `token` 与 `userId` 供前端存储。Token 内携带 `userId`、`username`，后续写接口从 Token 解析当前用户。

**登录接口与返回字段**：

```28:38:d:\AIprompt\backend\src\main\java\com\aiprompt\controller\UserController.java
    @PostMapping("/login")
    public Result<Map<String, String>> login(@RequestBody AuthRequest request) {
        String token = userService.login(request.getUsername(), request.getPassword());
        User user = userService.loginUser(request.getUsername(), request.getPassword());
        if (token == null) {
            return Result.fail("用户名或密码错误");
        }
        Map<String, String> map = new HashMap<>();
        map.put("token", token);
        map.put("userId", String.valueOf(user.getId()));
        return Result.ok("登录成功", map);
    }
```

JWT 生成逻辑见 `JwtUtils.createToken`（与 `UserServiceImpl.login` 配合）。

---

### （3）全局鉴权：拦截器注册与放行规则

**业务说明**：除登录、注册外，所有 `/api/**` 请求必须带合法 Bearer Token，否则返回 401 JSON。

**拦截器注册**（白名单）：

```22:27:d:\AIprompt\backend\src\main\java\com\aiprompt\config\WebConfig.java
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(authInterceptor)
                .addPathPatterns("/api/**")
                .excludePathPatterns("/api/user/login", "/api/user/register");
    }
```

**校验逻辑**（节选）：`AuthInterceptor` 读取 `Authorization`，解析失败或缺失则 `writeUnauthorized`。

```13:27:d:\AIprompt\backend\src\main\java\com\aiprompt\config\AuthInterceptor.java
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String authorization = request.getHeader("Authorization");
        if (authorization == null || !authorization.startsWith("Bearer ")) {
            writeUnauthorized(response, "未登录或令牌缺失");
            return false;
        }
        String token = authorization.substring(7);
        try {
            JwtUtils.parseToken(token);
            return true;
        } catch (Exception e) {
            writeUnauthorized(response, "登录状态已失效，请重新登录");
            return false;
        }
    }
```

---

### （4）提示词：列表（分类 + 标题模糊 + 公开/本人可见）

**业务说明**：

- 支持按 `category`、标题 `keyword` 模糊查询。
- 未携带有效用户上下文时：仅 `is_private = 0` 的公开提示词。
- 已登录用户：公开 **或** `creator_id = 当前用户` 的条目（可包含本人私密）。

**服务层条件拼接**：

```18:33:d:\AIprompt\backend\src\main\java\com\aiprompt\service\impl\PromptServiceImpl.java
    public List<Prompt> list(String category, String keyword, Long currentUserId) {
        LambdaQueryWrapper<Prompt> wrapper = new LambdaQueryWrapper<>();
        if (category != null && !category.isBlank()) {
            wrapper.eq(Prompt::getCategory, category);
        }
        if (keyword != null && !keyword.isBlank()) {
            wrapper.like(Prompt::getTitle, keyword);
        }
        if (currentUserId == null) {
            wrapper.eq(Prompt::getIsPrivate, 0);
        } else {
            wrapper.and(w -> w.eq(Prompt::getIsPrivate, 0).or().eq(Prompt::getCreatorId, currentUserId));
        }
        wrapper.orderByDesc(Prompt::getCreatedAt);
        return promptMapper.selectList(wrapper);
    }
```

**控制器**：从请求头可选解析用户 ID，调用 `list`（见 `PromptController.list`）。

```19:24:d:\AIprompt\backend\src\main\java\com\aiprompt\controller\PromptController.java
    @GetMapping("/list")
    public Result<List<Prompt>> list(@RequestParam(required = false) String category,
                                     @RequestParam(required = false) String keyword,
                                     @RequestHeader(value = "Authorization", required = false) String authorization) {
        Long currentUserId = parseUserIdOrNull(authorization);
        return Result.ok(promptService.list(category, keyword, currentUserId));
    }
```

---

### （5）提示词：详情（私密仅创建者可见）

**业务说明**：若 `is_private = 1` 且当前用户不是创建者，详情返回空（由服务层屏蔽）。

```36:43:d:\AIprompt\backend\src\main\java\com\aiprompt\service\impl\PromptServiceImpl.java
    public Prompt detail(Long id, Long currentUserId) {
        Prompt prompt = promptMapper.selectById(id);
        if (prompt == null) return null;
        if (Integer.valueOf(1).equals(prompt.getIsPrivate()) && !prompt.getCreatorId().equals(currentUserId)) {
            return null;
        }
        return prompt;
    }
```

---

### （6）提示词：新增（绑定发布者）

**业务说明**：新增时写入 `creatorId`、`creatorName`、默认计数与 `is_private`，防止前端伪造作者。

```46:54:d:\AIprompt\backend\src\main\java\com\aiprompt\service\impl\PromptServiceImpl.java
    public boolean add(Prompt prompt, Long currentUserId, String currentUsername) {
        prompt.setCreatedAt(LocalDateTime.now());
        prompt.setCreatorId(currentUserId);
        prompt.setCreatorName(currentUsername);
        if (prompt.getIsPrivate() == null) prompt.setIsPrivate(0);
        if (prompt.getUseCount() == null) prompt.setUseCount(0);
        if (prompt.getFavoriteCount() == null) prompt.setFavoriteCount(0);
        return promptMapper.insert(prompt) > 0;
    }
```

控制器从 JWT 取 `userId`、`username` 传入 `add`（见 `PromptController.add`）。

---

### （7）提示词：修改 / 删除 / 私密切换（防越权）

**业务说明**：先查库比对 `creatorId`，非本人直接失败；修改时保留原创建者与创建时间字段，避免被篡改。

```57:79:d:\AIprompt\backend\src\main\java\com\aiprompt\service\impl\PromptServiceImpl.java
    public boolean update(Prompt prompt, Long currentUserId) {
        Prompt dbPrompt = promptMapper.selectById(prompt.getId());
        if (dbPrompt == null || !dbPrompt.getCreatorId().equals(currentUserId)) return false;
        prompt.setCreatorId(dbPrompt.getCreatorId());
        prompt.setCreatorName(dbPrompt.getCreatorName());
        prompt.setCreatedAt(dbPrompt.getCreatedAt());
        return promptMapper.updateById(prompt) > 0;
    }

    public boolean delete(Long id, Long currentUserId) {
        Prompt dbPrompt = promptMapper.selectById(id);
        if (dbPrompt == null || !dbPrompt.getCreatorId().equals(currentUserId)) return false;
        return promptMapper.deleteById(id) > 0;
    }

    public boolean updatePrivate(Long id, Integer isPrivate, Long currentUserId) {
        Prompt dbPrompt = promptMapper.selectById(id);
        if (dbPrompt == null || !dbPrompt.getCreatorId().equals(currentUserId)) return false;
        dbPrompt.setIsPrivate(isPrivate == null ? 0 : (isPrivate == 0 ? 0 : 1));
        return promptMapper.updateById(dbPrompt) > 0;
    }
```

**我的提示词列表**：按 `creatorId` 查询。

```82:86:d:\AIprompt\backend\src\main\java\com\aiprompt\service\impl\PromptServiceImpl.java
    public List<Prompt> mine(Long currentUserId) {
        return promptMapper.selectList(new LambdaQueryWrapper<Prompt>()
                .eq(Prompt::getCreatorId, currentUserId)
                .orderByDesc(Prompt::getCreatedAt));
    }
```

---

### （8）收藏与使用记录

**业务说明**：

- **收藏**：同一用户对同一提示词重复收藏时直接返回成功（不重复插入）；首次收藏时 `favorite_count + 1`。
- **取消收藏**：删除收藏记录并尝试 `favorite_count - 1`。
- **使用记录**：插入 `usage_record` 且 `use_count + 1`。

**收藏防重与计数**（节选）：

```26:44:d:\AIprompt\backend\src\main\java\com\aiprompt\service\impl\InteractionServiceImpl.java
    public boolean addFavorite(Long userId, Long promptId) {
        LambdaQueryWrapper<Favorite> wrapper = new LambdaQueryWrapper<Favorite>()
                .eq(Favorite::getUserId, userId)
                .eq(Favorite::getPromptId, promptId);
        Favorite exist = favoriteMapper.selectOne(wrapper);
        if (exist != null) {
            return true;
        }
        Favorite favorite = new Favorite();
        favorite.setUserId(userId);
        favorite.setPromptId(promptId);
        favorite.setCreatedAt(LocalDateTime.now());
        int inserted = favoriteMapper.insert(favorite);
        Prompt prompt = promptMapper.selectById(promptId);
        if (prompt != null) {
            prompt.setFavoriteCount((prompt.getFavoriteCount() == null ? 0 : prompt.getFavoriteCount()) + 1);
            promptMapper.updateById(prompt);
        }
        return inserted > 0;
    }
```

**我的收藏列表**：组装 `FavoritePromptVO`（`favoriteId` + `prompt`），供前端「取消收藏」传主键。

```61:74:d:\AIprompt\backend\src\main\java\com\aiprompt\service\impl\InteractionServiceImpl.java
    public List<FavoritePromptVO> favoriteList(Long userId) {
        List<Favorite> favorites = rawFavoriteList(userId);
        List<FavoritePromptVO> result = new ArrayList<>();
        for (Favorite favorite : favorites) {
            Prompt prompt = promptMapper.selectById(favorite.getPromptId());
            if (prompt != null) {
                FavoritePromptVO vo = new FavoritePromptVO();
                vo.setFavoriteId(favorite.getId());
                vo.setPrompt(prompt);
                result.add(vo);
            }
        }
        return result;
    }
```

**使用次数**（节选）：

```77:88:d:\AIprompt\backend\src\main\java\com\aiprompt\service\impl\InteractionServiceImpl.java
    public boolean addUsage(Long userId, Long promptId) {
        UsageRecord usageRecord = new UsageRecord();
        usageRecord.setUserId(userId);
        usageRecord.setPromptId(promptId);
        usageRecord.setCreatedAt(LocalDateTime.now());
        int inserted = usageRecordMapper.insert(usageRecord);
        Prompt prompt = promptMapper.selectById(promptId);
        if (prompt != null) {
            prompt.setUseCount((prompt.getUseCount() == null ? 0 : prompt.getUseCount()) + 1);
            promptMapper.updateById(prompt);
        }
        return inserted > 0;
    }
```

---

### （9）排行榜

**业务说明**：热门按 `use_count` 降序，收藏榜按 `favorite_count` 降序（实现于 `PromptServiceImpl.rankByHot` / `rankByFavorite`，由 `RankController` 暴露 URL）。

---

## 1.4 后端小结

后端通过 **JWT 拦截器** 统一保护业务接口；提示词的**列表可见性、详情私密、增删改与私密切换**均在 `PromptServiceImpl` 与 **Token 解析出的用户 ID** 绑定，避免越权。收藏与使用记录在 `InteractionServiceImpl` 中维护关联表与计数字段。

---

# 第二部分：前端系统

## 2.1 技术栈

| 技术 | 作用 |
|------|------|
| Vue 3 + `<script setup>` | 组件与响应式逻辑 |
| Vue Router | 路由 + 登录守卫 |
| Pinia | `token`、`userId`、登录/退出 |
| Element Plus | UI 组件 |
| Axios | `baseURL: /api`，请求头带 Token；401 跳转登录 |

---

## 2.2 前端目录结构（核心）

```text
frontend/
├── index.html
├── package.json
├── vite.config.js                 # dev server、/api 代理
└── src/
    ├── main.js                    # 创建应用、Pinia、Router、Element Plus
    ├── App.vue                    # 布局：顶栏 + router-view
    ├── assets/main.css            # 全局样式（渐变背景、卡片等）
    ├── router/index.js            # 路由表 + beforeEach 登录校验
    ├── store/user.js              # token、userId、setAuth、logout
    ├── api/http.js                # axios 实例、拦截器
    ├── api/index.js               # 各业务 API 方法聚合
    ├── components/
    │   ├── NavigationBar.vue      # 主导航、登录/注册/退出
    │   └── PromptCard.vue         # 首页卡片：复制、收藏、进详情
    └── views/
        ├── HomeView.vue           # 首页：搜索 + 分类 Tab + 卡片列表
        ├── PromptDetailView.vue   # 详情：全文、发布者、时间、复制
        ├── PromptFormView.vue     # 新增/编辑：上传、本地草稿保存
        ├── MyPromptsView.vue      # 我的提示词：本地草稿 + 已发布管理
        ├── FavoriteView.vue       # 我的收藏：取消收藏
        ├── RankView.vue           # 排行榜
        ├── LoginView.vue          # 登录（增强 UI）
        └── RegisterView.vue       # 注册
```

---

## 2.3 全局请求与鉴权（配合后端拦截器）

**业务说明**：每个请求自动附加 `Authorization: Bearer <token>`；后端返回 401 时清除本地登录信息并跳转登录页。

```8:30:d:\AIprompt\frontend\src\api\http.js
http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token") || sessionStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("userId");
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("userId");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
```

**API 聚合**（与后端路径一一对应，页面只调 `api.*`）：`frontend/src/api/index.js`。

---

## 2.4 路由守卫

**业务说明**：无 Token 禁止进入业务页；已登录访问登录/注册则回首页。

```27:40:d:\AIprompt\frontend\src\router\index.js
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
```

---

## 2.5 分页面：业务说明 + 核心代码 + 界面截图占位

以下每个小节：**文字说明该页做什么** → **对应关键源码** → **请将截图保存为指示路径**（与 `docs/screenshots/README.md` 中命名一致）。

---

### 页面 A：登录 `/login`

**业务说明**：用户输入账号密码登录；勾选「记住我」时 Token 写入 `localStorage`，否则可写入 `sessionStorage`（见 `store/user.js` 的 `setAuth`）。登录成功后保存 `token` 与 `userId`。

**核心代码**：`frontend/src/views/LoginView.vue`（表单提交调用 `api.login`，再 `store.setAuth`）。

**功能展示图（请粘贴/保存截图文件）：**

![登录页：账号密码、记住我、登录按钮与背景层次](docs/screenshots/01-login.png)

---

### 页面 B：注册 `/register`

**业务说明**：新用户注册，成功后跳转登录。

**核心代码**：`frontend/src/views/RegisterView.vue` 调用 `api.register`。

**功能展示图：**

![注册页：用户名与密码注册表单](docs/screenshots/02-register.png)

---

### 页面 C：首页 `/`

**业务说明**：顶部**标题模糊搜索** + **分类 Tab**；下方卡片列表展示提示词摘要；支持复制（并上报使用次数）、收藏、进入详情。

**核心代码**（数据加载与收藏）：

```37:45:d:\AIprompt\frontend\src\views\HomeView.vue
async function load() {
  const { data } = await api.promptList(category.value || undefined, keyword.value || undefined);
  list.value = data.data || [];
}
async function favorite(promptId) {
  if (!store.userId) return ElMessage.warning("请先登录");
  await api.favoriteAdd({ userId: store.userId, promptId });
  ElMessage.success("收藏成功");
  await load();
}
```

卡片组件：`frontend/src/components/PromptCard.vue`。

**功能展示图：**

![首页：搜索框、分类标签与提示词卡片列表](docs/screenshots/03-home.png)

---

### 页面 D：提示词详情 `/prompt/:id`

**业务说明**：展示完整正文、**发布者**、**发布时间**，支持一键复制。

**核心代码**：`frontend/src/views/PromptDetailView.vue` 调用 `api.promptDetail`。

**功能展示图：**

![提示词详情：标题、分类、发布者、时间与正文](docs/screenshots/04-prompt-detail.png)

---

### 页面 E：新增/编辑提示词 `/prompt-form` 与 `/prompt-form/:id`

**业务说明**：

- **上传**：`POST /api/prompt/add` 或 `PUT /api/prompt/update`（见 `uploadPrompt`）。
- **保存**：仅写入浏览器本地 `localStorage`，键为 `promptDrafts_${userId}`，并带 `ownerId`，与其它用户草稿隔离。

**核心代码**：

```55:74:d:\AIprompt\frontend\src\views\PromptFormView.vue
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
```

**功能展示图：**

![新增或编辑提示词：标题、分类、内容与上传/保存按钮](docs/screenshots/05-prompt-form.png)

---

### 页面 F：我的提示词管理 `/my-prompts`

**业务说明**：上半部分为**本地草稿**（读 `localStorage`）；下半部分为**已发布**（`api.promptMine`），支持编辑跳转、删除、公开/私密切换。列表再次按 `creatorId` 过滤，与当前登录用户一致。

**核心代码**：

```60:86:d:\AIprompt\frontend\src\views\MyPromptsView.vue
function loadDrafts() {
  drafts.value = JSON.parse(localStorage.getItem(draftKey()) || "[]")
    .filter((d) => Number(d.ownerId) === Number(userStore.userId));
}
async function loadPublished() {
  const { data } = await api.promptMine();
  published.value = (data.data || []).filter((p) => Number(p.creatorId) === Number(userStore.userId));
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
```

**功能展示图：**

![我的提示词管理：本地草稿区与已发布列表及操作按钮](docs/screenshots/06-my-prompts.png)

---

### 页面 G：我的收藏 `/favorites`

**业务说明**：展示当前用户收藏列表；主操作是**取消收藏**（使用后端返回的 `favoriteId` 调用 `DELETE /api/favorite/remove/{id}`）。

**核心代码**：

```27:35:d:\AIprompt\frontend\src\views\FavoriteView.vue
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
```

**功能展示图：**

![我的收藏：卡片列表与取消收藏按钮](docs/screenshots/07-favorites.png)

---

### 页面 H：排行榜 `/rank`

**业务说明**：展示热门（使用次数）与收藏榜（调用 `api.hotRank`、`api.favoriteRank`）。

**核心代码**：`frontend/src/views/RankView.vue`。

**功能展示图：**

![排行榜：热门提示词与收藏榜列表](docs/screenshots/08-rank.png)

---

## 2.6 导航栏

**业务说明**：入口集中在 `frontend/src/components/NavigationBar.vue`（首页、收藏、排行、新增、我的提示词、登录/注册/退出）。

可将**带导航的整页截图**放在首页或单独文件，例如 `docs/screenshots/00-nav.png`，并在本节自行增加一行 `![导航栏](docs/screenshots/00-nav.png)`。

---

# 第三部分：前后端协作关系（简要）

1. 登录后前端保存 `token` 与 `userId`，Axios 请求头携带 JWT，与后端 `AuthInterceptor` 一致。  
2. 提示词作者、私密性、越权控制以**后端 `PromptServiceImpl` + JWT 用户**为准；前端负责展示与调用 API。  
3. 本地草稿仅存浏览器，不参与多设备同步；已发布数据以 MySQL 为准。  

---

文档版本说明：若你增删页面或改路由，请同步更新「截图占位」文件名与 `docs/screenshots/README.md` 中的对照表。
