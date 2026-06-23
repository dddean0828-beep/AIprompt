# AI提示词管理系统 - 项目说明文档

## 一、项目概述

**AI提示词管理系统**是一个基于Spring Boot + Vue 3的全栈Web应用，旨在帮助用户管理、分享和发现高质量的AI提示词。系统提供提示词的增删改查、收藏、使用统计和排行榜等功能。

---

## 二、技术栈

### 后端技术栈
| 技术 | 版本 | 说明 |
|------|------|------|
| Java | 17 | 编程语言 |
| Spring Boot | 3.3.5 | 后端框架 |
| MyBatis Plus | 3.5.7 | ORM框架 |
| MySQL | 8.0.33 | 数据库 |
| JWT | 0.12.6 | 身份认证 |
| Lombok | - | 简化代码 |

### 前端技术栈
| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.5.13 | 前端框架 |
| Vue Router | 4.5.0 | 路由管理 |
| Pinia | 3.0.1 | 状态管理 |
| Element Plus | 2.9.8 | UI组件库 |
| Axios | 1.8.4 | HTTP客户端 |
| Vite | 6.2.3 | 构建工具 |

---

## 三、项目结构

### 3.1 后端目录结构

```
backend/
├── src/main/java/com/aiprompt/
│   ├── controller/          # REST API控制器
│   │   ├── UserController.java
│   │   ├── PromptController.java
│   │   ├── FavoriteController.java
│   │   ├── RankController.java
│   │   └── UsageController.java
│   ├── service/             # 业务逻辑层
│   │   ├── UserService.java
│   │   ├── PromptService.java
│   │   ├── InteractionService.java
│   │   └── impl/            # 服务实现类
│   ├── mapper/              # MyBatis Mapper接口
│   │   ├── UserMapper.java
│   │   ├── PromptMapper.java
│   │   ├── FavoriteMapper.java
│   │   ├── TagMapper.java
│   │   └── UsageRecordMapper.java
│   ├── entity/              # 数据库实体类
│   │   ├── User.java
│   │   ├── Prompt.java
│   │   ├── Favorite.java
│   │   ├── Tag.java
│   │   ├── PromptTag.java
│   │   └── UsageRecord.java
│   ├── dto/                 # 数据传输对象
│   │   ├── AuthRequest.java
│   │   ├── FavoriteRequest.java
│   │   ├── FavoritePromptVO.java
│   │   └── UsageRequest.java
│   ├── config/              # 配置类
│   │   ├── WebConfig.java
│   │   └── AuthInterceptor.java
│   ├── utils/               # 工具类
│   │   └── JwtUtils.java
│   ├── common/              # 通用模块
│   │   └── Result.java
│   └── AipromptApplication.java
├── src/main/resources/
│   ├── application.yml      # 应用配置
│   └── db/
│       └── init.sql         # 数据库初始化脚本
└── pom.xml                  # Maven依赖管理
```

### 3.2 前端目录结构

```
frontend/
├── src/
│   ├── views/               # 页面视图组件
│   │   ├── HomeView.vue         # 首页
│   │   ├── LoginView.vue        # 登录页
│   │   ├── RegisterView.vue     # 注册页
│   │   ├── PromptDetailView.vue # 提示词详情页
│   │   ├── PromptFormView.vue   # 提示词表单页
│   │   ├── MyPromptsView.vue    # 我的提示词页
│   │   ├── FavoriteView.vue     # 收藏页
│   │   └── RankView.vue         # 排行榜页
│   ├── components/           # 公共组件
│   │   ├── NavigationBar.vue    # 导航栏
│   │   └── PromptCard.vue       # 提示词卡片
│   ├── router/               # 路由配置
│   │   └── index.js
│   ├── store/                # 状态管理
│   │   └── user.js
│   ├── api/                  # API接口封装
│   │   ├── index.js             # API方法
│   │   └── http.js              # Axios配置
│   ├── assets/               # 静态资源
│   │   └── main.css
│   ├── App.vue               # 根组件
│   └── main.js               # 入口文件
├── index.html
├── package.json
└── vite.config.js            # Vite配置
```

---

## 四、核心功能模块

### 4.1 用户认证模块

| 功能 | API | 说明 |
|------|-----|------|
| 用户注册 | `POST /api/user/register` | 创建新用户 |
| 用户登录 | `POST /api/user/login` | 验证并返回JWT token |
| 获取用户信息 | `GET /api/user/info` | 根据ID获取用户详情 |

**认证流程**：
1. 用户登录获取JWT token
2. 前端将token存储在localStorage/sessionStorage
3. 每次请求通过`Authorization: Bearer <token>`携带
4. 后端通过`AuthInterceptor`统一校验token有效性

### 4.2 提示词管理模块

| 功能 | API | 说明 |
|------|-----|------|
| 获取提示词列表 | `GET /api/prompt/list` | 支持分类和关键词筛选 |
| 获取提示词详情 | `GET /api/prompt/detail/{id}` | 根据ID获取详情 |
| 新增提示词 | `POST /api/prompt/add` | 创建新提示词 |
| 更新提示词 | `PUT /api/prompt/update` | 修改已有提示词 |
| 删除提示词 | `DELETE /api/prompt/delete/{id}` | 删除提示词（仅作者） |
| 切换隐私状态 | `PUT /api/prompt/toggle-private/{id}` | 设置公开/私密 |
| 获取我的提示词 | `GET /api/prompt/mine` | 获取当前用户发布的提示词 |

**提示词字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 主键ID |
| title | String | 提示词标题 |
| content | Text | 提示词内容 |
| category | String | 分类（写作/编程/学习/AI绘画） |
| creatorId | Long | 创建者ID |
| creatorName | String | 创建者名称 |
| isPrivate | Integer | 是否私密（0公开/1私密） |
| useCount | Integer | 使用次数 |
| favoriteCount | Integer | 收藏次数 |
| createdAt | LocalDateTime | 创建时间 |

### 4.3 收藏模块

| 功能 | API | 说明 |
|------|-----|------|
| 添加收藏 | `POST /api/favorite/add` | 将提示词加入收藏 |
| 取消收藏 | `DELETE /api/favorite/remove/{id}` | 移除收藏 |
| 获取收藏列表 | `GET /api/favorite/list` | 获取用户收藏的提示词 |

### 4.4 使用记录模块

| 功能 | API | 说明 |
|------|-----|------|
| 添加使用记录 | `POST /api/usage/add` | 记录提示词使用 |

### 4.5 排行榜模块

| 功能 | API | 说明 |
|------|-----|------|
| 热门排行 | `GET /api/rank/hot` | 按使用次数排序 |
| 收藏排行 | `GET /api/rank/favorite` | 按收藏次数排序 |

---

## 五、数据库设计

### 5.1 数据库表结构

#### user（用户表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PRIMARY KEY AUTO_INCREMENT | 用户ID |
| username | VARCHAR(50) | NOT NULL UNIQUE | 用户名 |
| password | VARCHAR(100) | NOT NULL | 密码 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### prompt（提示词表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PRIMARY KEY AUTO_INCREMENT | 提示词ID |
| title | VARCHAR(255) | NOT NULL | 标题 |
| content | TEXT | NOT NULL | 内容 |
| category | VARCHAR(50) | NOT NULL | 分类 |
| creator_id | BIGINT | NOT NULL DEFAULT 0 | 创建者ID |
| creator_name | VARCHAR(100) | NOT NULL DEFAULT '' | 创建者名称 |
| is_private | TINYINT | NOT NULL DEFAULT 0 | 是否私密 |
| use_count | INT | DEFAULT 0 | 使用次数 |
| favorite_count | INT | DEFAULT 0 | 收藏次数 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### favorite（收藏表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PRIMARY KEY AUTO_INCREMENT | 收藏ID |
| user_id | BIGINT | NOT NULL | 用户ID |
| prompt_id | BIGINT | NOT NULL | 提示词ID |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### usage_record（使用记录表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PRIMARY KEY AUTO_INCREMENT | 记录ID |
| user_id | BIGINT | NOT NULL | 用户ID |
| prompt_id | BIGINT | NOT NULL | 提示词ID |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 使用时间 |

#### tag（标签表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PRIMARY KEY AUTO_INCREMENT | 标签ID |
| name | VARCHAR(50) | NOT NULL UNIQUE | 标签名称 |

#### prompt_tag（提示词标签关联表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PRIMARY KEY AUTO_INCREMENT | 关联ID |
| prompt_id | BIGINT | NOT NULL | 提示词ID |
| tag_id | BIGINT | NOT NULL | 标签ID |

---

## 六、安全机制

### 6.1 JWT认证

**Token生成**：登录成功后生成包含`userId`和`username`的JWT token，有效期24小时。

```java
// JwtUtils.java
public static String createToken(Long userId, String username) {
    long now = System.currentTimeMillis();
    return Jwts.builder()
            .claim("userId", userId)
            .claim("username", username)
            .issuedAt(new Date(now))
            .expiration(new Date(now + 24 * 60 * 60 * 1000))
            .signWith(KEY)
            .compact();
}
```

### 6.2 拦截器配置

通过`AuthInterceptor`拦截所有API请求，验证token有效性：

| 路径 | 是否需要认证 |
|------|-------------|
| `/api/user/login` | 否 |
| `/api/user/register` | 否 |
| `/api/**` | 是 |

### 6.3 权限控制

- **提示词访问**：私密提示词仅作者可见
- **操作权限**：仅提示词作者可编辑/删除/切换隐私状态

---

## 七、运行配置

### 7.1 后端配置

**application.yml**：

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/ai_prompt_manager?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
    username: root
    password: 123456
    driver-class-name: com.mysql.cj.jdbc.Driver

mybatis-plus:
  configuration:
    map-underscore-to-camel-case: true
  global-config:
    db-config:
      id-type: auto
```

### 7.2 前端配置

**vite.config.js**：

```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true
      }
    }
  }
});
```

---

## 八、启动步骤

### 8.1 启动后端

1. 确保MySQL服务运行
2. 创建数据库并执行初始化脚本：
   ```bash
   mysql -u root -p < backend/src/main/resources/db/init.sql
   ```
3. 运行Spring Boot应用：
   ```bash
   cd backend
   mvn spring-boot:run
   ```

### 8.2 启动前端

```bash
cd frontend
npm install
npm run dev
```

---

## 九、功能流程图

```
用户访问首页
    │
    ├── 未登录 ──→ 可浏览公开提示词（部分功能受限）
    │
    └── 已登录 ──→ 完整功能：
        │
        ├── 查看提示词列表（支持分类/搜索）
        ├── 查看提示词详情
        ├── 添加/编辑/删除提示词
        ├── 收藏/取消收藏
        ├── 查看排行榜
        └── 管理我的提示词（草稿+已发布）
```

---

## 十、前端页面说明

| 页面 | 路径 | 功能 |
|------|------|------|
| 首页 | `/` | 提示词列表，支持分类筛选和关键词搜索 |
| 登录 | `/login` | 用户登录表单 |
| 注册 | `/register` | 用户注册表单 |
| 提示词详情 | `/prompt/{id}` | 查看单个提示词详情 |
| 提示词表单 | `/prompt-form/{id}?` | 新增或编辑提示词 |
| 我的提示词 | `/my-prompts` | 管理草稿和已发布提示词 |
| 收藏 | `/favorites` | 查看收藏的提示词 |
| 排行榜 | `/rank` | 热门榜和收藏榜 |

---

## 十一、关键设计说明

### 11.1 状态管理

使用Pinia管理用户认证状态：

```javascript
// store/user.js
export const useUserStore = defineStore("user", () => {
  const userId = ref(Number(cachedUserId));
  const token = ref(cachedToken);
  
  function setAuth(id, tk, remember = true) {
    // 支持记住我功能（localStorage/sessionStorage切换）
  }
  
  function logout() {
    // 清除所有认证信息
  }
});
```

### 11.2 响应式布局

- 首页提示词卡片采用响应式网格布局
- 排行榜采用双栏布局，小屏幕自动切换为单栏

### 11.3 本地草稿机制

前端支持将未完成的提示词保存到localStorage作为草稿：

```javascript
// 草稿存储键：promptDrafts_{userId}
// 编辑中转键：editingDraft_{userId}
```

---

## 十二、代码亮点

1. **统一响应格式**：所有API返回统一的`Result<T>`格式，包含`code`、`message`、`data`字段
2. **自动token注入**：Axios拦截器自动在请求头添加Authorization
3. **401自动重定向**：响应拦截器检测到401自动清除token并重定向到登录页
4. **权限校验**：服务层对用户操作权限进行校验，防止越权访问
5. **响应式设计**：前端采用Element Plus组件，支持响应式布局

---

## 十三、待优化项

1. **密码加密**：当前密码明文存储，建议使用BCrypt加密
2. **分页支持**：提示词列表应支持分页查询
3. **图片上传**：提示词内容可支持图片附件
4. **搜索优化**：支持全文搜索
5. **单元测试**：添加服务层和控制器单元测试
6. **国际化**：支持多语言切换
7. **文件上传**：支持导入/导出提示词模板