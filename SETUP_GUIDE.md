# AI提示词管理系统 - 完整运行指南

## 项目概述

AI提示词管理系统是一个基于 Spring Boot + Vue 3 + MyBatis-Plus 的前后端分离系统，用于管理和使用AI提示词。

## 前置条件

在开始之前，请确保已安装以下软件：

- JDK 11 或更高版本（推荐 JDK 17）
- Node.js 16+ 和 npm 或 yarn
- MySQL 5.7 或 8.0
- Git（可选）
- IDE：IntelliJ IDEA 或 Eclipse（后端）、VS Code（前端）

## 第一部分：数据库设置

### 1.1 创建数据库

连接到 MySQL 数据库，执行以下命令：

```sql
CREATE DATABASE ai_prompt_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_prompt_manager;
```

### 1.2 创建数据表

执行以下SQL脚本创建所有必需的表：

```sql
-- 用户表
CREATE TABLE user (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 提示词表
CREATE TABLE prompt (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  category VARCHAR(50) NOT NULL,
  use_count INT DEFAULT 0,
  favorite_count INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 标签表
CREATE TABLE tag (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL UNIQUE
);

-- 提示词标签关系表
CREATE TABLE prompt_tag (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  prompt_id BIGINT NOT NULL,
  tag_id BIGINT NOT NULL,
  FOREIGN KEY (prompt_id) REFERENCES prompt(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

-- 收藏表
CREATE TABLE favorite (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  prompt_id BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (prompt_id) REFERENCES prompt(id) ON DELETE CASCADE
);

-- 使用记录表
CREATE TABLE usage_record (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  prompt_id BIGINT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  FOREIGN KEY (prompt_id) REFERENCES prompt(id) ON DELETE CASCADE
);
```

### 1.3 插入初始数据

#### 1.3.1 插入初始标签

```sql
INSERT INTO tag (name) VALUES
('GPT'), 
('写作'), 
('编程'), 
('学习'), 
('AI绘画');
```

#### 1.3.2 插入初始提示词数据

```sql
INSERT INTO prompt (title, content, category, use_count, favorite_count, created_at) VALUES
('写一篇高质量文章', '请以专业作者身份，围绕【主题】写一篇结构清晰、逻辑严谨的文章，包含引言、正文和总结。', '写作', 120, 45, NOW()),
('Java代码优化助手', '请优化以下Java代码，提高性能和可读性，并给出优化说明：\n【代码】', '编程', 98, 30, NOW()),
('英语翻译助手', '请将以下中文翻译为地道的英文，并给出语法解释：\n【文本】', '学习', 150, 60, NOW()),
('Midjourney绘图提示词', 'A highly detailed illustration of 【主题】，cinematic lighting, 8k, ultra realistic', 'AI绘画', 200, 80, NOW()),
('总结文章内容', '请总结以下文章的核心观点，并列出要点：\n【文章】', '学习', 110, 40, NOW());
```

## 第二部分：后端配置与运行

### 2.1 项目结构

后端项目目录结构应如下所示：

```
backend/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/aiprompt/
│   │   │       ├── controller/
│   │   │       ├── service/
│   │   │       ├── mapper/
│   │   │       ├── entity/
│   │   │       ├── config/
│   │   │       ├── utils/
│   │   │       └── AipromptApplication.java
│   │   └── resources/
│   │       ├── application.yml
│   │       └── db/
│   │           └── init.sql
│   └── test/
└── target/
```

### 2.2 Maven 依赖配置

在 `pom.xml` 中配置以下依赖项：

```xml
<properties>
  <maven.compiler.source>11</maven.compiler.source>
  <maven.compiler.target>11</maven.compiler.target>
  <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  <spring.boot.version>2.7.0</spring.boot.version>
</properties>

<dependencies>
  <!-- Spring Boot Web -->
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <version>${spring.boot.version}</version>
  </dependency>

  <!-- Spring Boot Data JPA -->
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
    <version>${spring.boot.version}</version>
  </dependency>

  <!-- MyBatis Plus -->
  <dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-boot-starter</artifactId>
    <version>3.5.1</version>
  </dependency>

  <!-- MySQL Driver -->
  <dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.33</version>
  </dependency>

  <!-- Lombok -->
  <dependency>
    <groupId>org.projectlombok</groupId>
    <artifactId>lombok</artifactId>
    <version>1.18.26</version>
    <scope>provided</scope>
  </dependency>

  <!-- JWT -->
  <dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt</artifactId>
    <version>0.11.5</version>
  </dependency>

  <!-- Spring Boot Test -->
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <version>${spring.boot.version}</version>
    <scope>test</scope>
  </dependency>
</dependencies>
```

### 2.3 配置 application.yml

创建或修改 `src/main/resources/application.yml` 文件：

```yaml
spring:
  application:
    name: ai-prompt-manager

  datasource:
    url: jdbc:mysql://localhost:3306/ai_prompt_manager?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=UTC
    username: root
    password: your_mysql_password
    driver-class-name: com.mysql.cj.jdbc.Driver

  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true
    properties:
      hibernate:
        dialect: org.hibernate.dialect.MySQL8Dialect
        format_sql: true

  mvc:
    cors:
      allowed-origins: http://localhost:5173
      allowed-methods: GET,POST,PUT,DELETE,OPTIONS
      allowed-headers: "*"
      allow-credentials: true

mybatis-plus:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: com.aiprompt.entity
  configuration:
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl

server:
  port: 8080
  servlet:
    context-path: /api

logging:
  level:
    com.aiprompt: DEBUG
    org.springframework: INFO
```

注意：将 `your_mysql_password` 替换为实际的 MySQL 密码。

### 2.4 创建核心实体类

#### 2.4.1 User 实体

创建 `src/main/java/com/aiprompt/entity/User.java`：

```java
package com.aiprompt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("user")
public class User {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String username;
    private String password;
    private LocalDateTime createdAt;
}
```

#### 2.4.2 Prompt 实体

创建 `src/main/java/com/aiprompt/entity/Prompt.java`：

```java
package com.aiprompt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("prompt")
public class Prompt {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String title;
    private String content;
    private String category;
    private Integer useCount;
    private Integer favoriteCount;
    private LocalDateTime createdAt;
}
```

#### 2.4.3 Tag 实体

创建 `src/main/java/com/aiprompt/entity/Tag.java`：

```java
package com.aiprompt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("tag")
public class Tag {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
}
```

#### 2.4.4 Favorite 实体

创建 `src/main/java/com/aiprompt/entity/Favorite.java`：

```java
package com.aiprompt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("favorite")
public class Favorite {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long promptId;
    private LocalDateTime createdAt;
}
```

#### 2.4.5 UsageRecord 实体

创建 `src/main/java/com/aiprompt/entity/UsageRecord.java`：

```java
package com.aiprompt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("usage_record")
public class UsageRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long promptId;
    private LocalDateTime createdAt;
}
```

### 2.5 统一响应格式

创建 `src/main/java/com/aiprompt/utils/Result.java`：

```java
package com.aiprompt.utils;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Result<T> {
    private Integer code;
    private String message;
    private T data;

    public static <T> Result<T> success(T data) {
        return new Result<>(200, "success", data);
    }

    public static <T> Result<T> success(T data, String message) {
        return new Result<>(200, message, data);
    }

    public static <T> Result<T> error(String message) {
        return new Result<>(500, message, null);
    }

    public static <T> Result<T> error(Integer code, String message) {
        return new Result<>(code, message, null);
    }
}
```

### 2.6 创建 Mapper 接口

创建 `src/main/java/com/aiprompt/mapper/UserMapper.java`：

```java
package com.aiprompt.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.aiprompt.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
}
```

类似地创建其他 Mapper：
- PromptMapper
- TagMapper
- FavoriteMapper
- UsageRecordMapper

### 2.7 创建 Service 层

创建 `src/main/java/com/aiprompt/service/UserService.java`：

```java
package com.aiprompt.service;

import com.aiprompt.entity.User;
import com.baomidou.mybatisplus.extension.service.IService;

public interface UserService extends IService<User> {
    User login(String username, String password);
    User register(String username, String password);
}
```

创建实现类 `src/main/java/com/aiprompt/service/impl/UserServiceImpl.java`：

```java
package com.aiprompt.service.impl;

import com.aiprompt.entity.User;
import com.aiprompt.mapper.UserMapper;
import com.aiprompt.service.UserService;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;

@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {
    @Override
    public User login(String username, String password) {
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("username", username).eq("password", password);
        return getOne(queryWrapper);
    }

    @Override
    public User register(String username, String password) {
        User user = new User();
        user.setUsername(username);
        user.setPassword(password);
        user.setCreatedAt(LocalDateTime.now());
        save(user);
        return user;
    }
}
```

类似地创建其他 Service 和实现类。

### 2.8 创建 Controller 层

创建 `src/main/java/com/aiprompt/controller/UserController.java`：

```java
package com.aiprompt.controller;

import com.aiprompt.entity.User;
import com.aiprompt.service.UserService;
import com.aiprompt.utils.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/user")
@CrossOrigin(origins = "*", maxAge = 3600)
public class UserController {
    @Autowired
    private UserService userService;

    @PostMapping("/register")
    public Result<User> register(@RequestParam String username, @RequestParam String password) {
        User user = userService.register(username, password);
        return Result.success(user, "Registration successful");
    }

    @PostMapping("/login")
    public Result<User> login(@RequestParam String username, @RequestParam String password) {
        User user = userService.login(username, password);
        if (user != null) {
            return Result.success(user, "Login successful");
        }
        return Result.error("Invalid credentials");
    }

    @GetMapping("/info")
    public Result<User> info(@RequestParam Long userId) {
        User user = userService.getById(userId);
        return Result.success(user);
    }
}
```

创建 `src/main/java/com/aiprompt/controller/PromptController.java`：

```java
package com.aiprompt.controller;

import com.aiprompt.entity.Prompt;
import com.aiprompt.service.PromptService;
import com.aiprompt.utils.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/prompt")
@CrossOrigin(origins = "*", maxAge = 3600)
public class PromptController {
    @Autowired
    private PromptService promptService;

    @GetMapping("/list")
    public Result<List<Prompt>> list(@RequestParam(required = false) String category) {
        List<Prompt> prompts = promptService.getPromptList(category);
        return Result.success(prompts);
    }

    @GetMapping("/detail/{id}")
    public Result<Prompt> detail(@PathVariable Long id) {
        Prompt prompt = promptService.getById(id);
        return Result.success(prompt);
    }

    @PostMapping("/add")
    public Result<Prompt> add(@RequestBody Prompt prompt) {
        promptService.save(prompt);
        return Result.success(prompt, "Prompt created successfully");
    }

    @PutMapping("/update")
    public Result<Prompt> update(@RequestBody Prompt prompt) {
        promptService.updateById(prompt);
        return Result.success(prompt, "Prompt updated successfully");
    }

    @DeleteMapping("/delete/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        promptService.removeById(id);
        return Result.success(null, "Prompt deleted successfully");
    }
}
```

创建其他 Controller（FavoriteController、UsageController、RankController）。

### 2.9 编译并启动后端

1. 在后端项目根目录打开命令行
2. 执行 Maven 编译：
   ```bash
   mvn clean package
   ```
3. 启动 Spring Boot 应用：
   ```bash
   mvn spring-boot:run
   ```
   或者运行 IDE 中的主类 `AipromptApplication.java`

4. 验证后端运行成功：
   - 打开浏览器访问：http://localhost:8080/api/prompt/list
   - 如果返回 JSON 数据，说明后端启动成功

## 第三部分：前端配置与运行

### 3.1 项目结构

前端项目目录结构应如下所示：

```
frontend/
├── package.json
├── vite.config.js
├── index.html
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── views/
│   │   ├── Home.vue
│   │   ├── PromptDetail.vue
│   │   ├── MyFavorites.vue
│   │   ├── Ranking.vue
│   │   ├── CreatePrompt.vue
│   │   ├── Login.vue
│   │   └── Register.vue
│   ├── components/
│   │   ├── PromptCard.vue
│   │   ├── Navigation.vue
│   │   └── Sidebar.vue
│   ├── api/
│   │   ├── api.js
│   │   ├── user.js
│   │   ├── prompt.js
│   │   ├── favorite.js
│   │   └── rank.js
│   ├── router/
│   │   └── index.js
│   ├── store/
│   │   └── index.js
│   └── styles/
│       └── main.css
└── public/
```

### 3.2 初始化 Vue 3 项目

如果没有现成的 Vue 3 项目，执行以下命令创建：

```bash
npm create vite@latest frontend -- --template vue
cd frontend
npm install
```

### 3.3 安装项目依赖

在前端项目根目录执行：

```bash
npm install
npm install element-plus axios vue-router pinia echarts
```

或使用 yarn：

```bash
yarn install
yarn add element-plus axios vue-router pinia echarts
```

### 3.4 配置 package.json

确保 `package.json` 中包含以下依赖：

```json
{
  "name": "ai-prompt-manager-frontend",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.3.4",
    "element-plus": "^2.3.5",
    "axios": "^1.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.0.32",
    "echarts": "^5.4.2"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.2.3",
    "vite": "^4.3.9"
  }
}
```

### 3.5 配置 Vite

创建 `vite.config.js`：

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  }
})
```

### 3.6 创建主文件结构

#### 3.6.1 main.js

创建 `src/main.js`：

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
```

#### 3.6.2 App.vue

创建 `src/App.vue`：

```vue
<template>
  <div id="app">
    <Navigation />
    <router-view />
  </div>
</template>

<script setup>
import Navigation from './components/Navigation.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

#app {
  background: #f5f7fa;
}
</style>
```

#### 3.6.3 Router 配置

创建 `src/router/index.js`：

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import PromptDetail from '../views/PromptDetail.vue'
import MyFavorites from '../views/MyFavorites.vue'
import Ranking from '../views/Ranking.vue'
import CreatePrompt from '../views/CreatePrompt.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/prompt/:id', component: PromptDetail },
  { path: '/favorites', component: MyFavorites },
  { path: '/ranking', component: Ranking },
  { path: '/create', component: CreatePrompt },
  { path: '/login', component: Login },
  { path: '/register', component: Register }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

#### 3.6.4 API 配置

创建 `src/api/api.js`：

```javascript
import axios from 'axios'

const API_BASE_URL = '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000
})

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

export default apiClient
```

创建 `src/api/prompt.js`：

```javascript
import apiClient from './api'

export const getPromptList = (category) => {
  return apiClient.get('/prompt/list', { params: { category } })
}

export const getPromptDetail = (id) => {
  return apiClient.get(`/prompt/detail/${id}`)
}

export const addPrompt = (data) => {
  return apiClient.post('/prompt/add', data)
}

export const updatePrompt = (data) => {
  return apiClient.put('/prompt/update', data)
}

export const deletePrompt = (id) => {
  return apiClient.delete(`/prompt/delete/${id}`)
}
```

创建 `src/api/user.js`：

```javascript
import apiClient from './api'

export const register = (username, password) => {
  return apiClient.post('/user/register', null, {
    params: { username, password }
  })
}

export const login = (username, password) => {
  return apiClient.post('/user/login', null, {
    params: { username, password }
  })
}

export const getUserInfo = (userId) => {
  return apiClient.get('/user/info', { params: { userId } })
}
```

创建 `src/api/favorite.js`：

```javascript
import apiClient from './api'

export const addFavorite = (userId, promptId) => {
  return apiClient.post('/favorite/add', null, {
    params: { userId, promptId }
  })
}

export const removeFavorite = (id) => {
  return apiClient.delete(`/favorite/remove/${id}`)
}

export const getFavoriteList = (userId) => {
  return apiClient.get('/favorite/list', { params: { userId } })
}
```

创建 `src/api/rank.js`：

```javascript
import apiClient from './api'

export const getHotRank = () => {
  return apiClient.get('/rank/hot')
}

export const getFavoriteRank = () => {
  return apiClient.get('/rank/favorite')
}
```

#### 3.6.5 Pinia Store

创建 `src/store/index.js`：

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || '')

  const setUser = (userData) => {
    user.value = userData
  }

  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const logout = () => {
    user.value = null
    token.value = ''
    localStorage.removeItem('token')
  }

  return { user, token, setUser, setToken, logout }
})
```

#### 3.6.6 Navigation 组件

创建 `src/components/Navigation.vue`：

```vue
<template>
  <nav class="navbar">
    <div class="navbar-container">
      <div class="navbar-logo">
        <router-link to="/">AI Prompt Manager</router-link>
      </div>
      <ul class="nav-menu">
        <li><router-link to="/">Home</router-link></li>
        <li><router-link to="/ranking">Ranking</router-link></li>
        <li><router-link to="/favorites">My Favorites</router-link></li>
        <li><router-link to="/create">Create</router-link></li>
        <li v-if="!isLoggedIn">
          <router-link to="/login">Login</router-link>
        </li>
        <li v-if="isLoggedIn">
          <button @click="handleLogout">Logout</button>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '../store'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const isLoggedIn = computed(() => !!userStore.token)

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem 0;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 2rem;
}

.navbar-logo a {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
  display: flex;
  align-items: center;
}

.navbar-logo a:hover {
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

.nav-menu {
  display: flex;
  list-style: none;
  gap: 2rem;
  align-items: center;
}

.nav-menu a {
  color: white;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
  padding: 0.5rem 0;
  border-bottom: 2px solid transparent;
}

.nav-menu a:hover {
  border-bottom-color: white;
  transform: translateY(-2px);
}

.nav-menu button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.nav-menu button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.router-link-active {
  border-bottom-color: white;
}
</style>
```

#### 3.6.7 Home 页面

创建 `src/views/Home.vue`：

```vue
<template>
  <div class="home-container">
    <div class="category-tabs">
      <button
        v-for="category in categories"
        :key="category"
        @click="selectedCategory = category"
        :class="{ active: selectedCategory === category }"
        class="category-btn"
      >
        {{ category }}
      </button>
    </div>

    <div class="prompts-grid">
      <PromptCard
        v-for="prompt in filteredPrompts"
        :key="prompt.id"
        :prompt="prompt"
        @use="handleUsePrompt"
        @favorite="handleFavorite"
      />
    </div>

    <div v-if="filteredPrompts.length === 0" class="empty-state">
      <p>No prompts found</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getPromptList } from '../api/prompt'
import PromptCard from '../components/PromptCard.vue'

const prompts = ref([])
const selectedCategory = ref('All')
const categories = ref(['All', 'Writing', 'Programming', 'Learning', 'AI Painting'])
const loading = ref(false)

const filteredPrompts = computed(() => {
  if (selectedCategory.value === 'All') {
    return prompts.value
  }
  return prompts.value.filter(p => p.category === selectedCategory.value)
})

const loadPrompts = async () => {
  try {
    loading.value = true
    const response = await getPromptList()
    prompts.value = response.data.data || []
  } catch (error) {
    console.error('Failed to load prompts:', error)
  } finally {
    loading.value = false
  }
}

const handleUsePrompt = (promptId) => {
  console.log('Using prompt:', promptId)
}

const handleFavorite = (promptId) => {
  console.log('Favoriting prompt:', promptId)
}

onMounted(() => {
  loadPrompts()
})
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.category-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.category-btn {
  padding: 0.75rem 1.5rem;
  border: 2px solid #ddd;
  background: white;
  border-radius: 25px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.category-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.category-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.prompts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  animation: fadeIn 0.5s ease-in;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #999;
  font-size: 1.2rem;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .prompts-grid {
    grid-template-columns: 1fr;
  }
  
  .category-tabs {
    justify-content: center;
  }
}
</style>
```

#### 3.6.8 PromptCard 组件

创建 `src/components/PromptCard.vue`：

```vue
<template>
  <div class="prompt-card">
    <div class="card-header">
      <h3>{{ prompt.title }}</h3>
    </div>

    <div class="card-category">
      <span class="badge">{{ prompt.category }}</span>
    </div>

    <div class="card-content">
      <p>{{ truncateContent(prompt.content) }}</p>
    </div>

    <div class="card-stats">
      <span class="stat">Uses: {{ prompt.useCount }}</span>
      <span class="stat">Favorites: {{ prompt.favoriteCount }}</span>
    </div>

    <div class="card-actions">
      <button @click="copyToClipboard" class="btn btn-primary">Copy</button>
      <button @click="$emit('favorite', prompt.id)" class="btn btn-secondary">Favorite</button>
      <router-link :to="`/prompt/${prompt.id}`" class="btn btn-tertiary">View</router-link>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'

const props = defineProps({
  prompt: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['use', 'favorite'])

const truncateContent = (content, length = 80) => {
  return content.length > length ? content.substring(0, length) + '...' : content
}

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.prompt.content)
    ElMessage.success('Copied to clipboard')
    emit('use', props.prompt.id)
  } catch (error) {
    ElMessage.error('Failed to copy')
  }
}
</script>

<style scoped>
.prompt-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.prompt-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.2);
}

.card-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
}

.card-category {
  margin: 0.75rem 0;
}

.badge {
  display: inline-block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.card-content {
  flex: 1;
  margin: 1rem 0;
  color: #666;
  font-size: 0.95rem;
  line-height: 1.5;
}

.card-content p {
  margin: 0;
}

.card-stats {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
  font-size: 0.85rem;
  color: #999;
}

.stat {
  display: flex;
  align-items: center;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.3s ease;
  text-decoration: none;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e8e8e8;
}

.btn-tertiary {
  background: white;
  color: #667eea;
  border: 1px solid #667eea;
}

.btn-tertiary:hover {
  background: #f5f7fa;
}
</style>
```

#### 3.6.9 其他页面

创建 `src/views/PromptDetail.vue`、`src/views/MyFavorites.vue`、`src/views/Ranking.vue`、`src/views/CreatePrompt.vue`、`src/views/Login.vue` 和 `src/views/Register.vue` 等页面。

### 3.7 启动前端开发服务器

1. 在前端项目根目录打开命令行
2. 确保所有依赖已安装：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```
4. 打开浏览器访问：http://localhost:5173

## 第四部分：项目测试

### 4.1 后端接口测试

可以使用 Postman 或 curl 命令测试后端接口：

#### 获取提示词列表
```bash
curl http://localhost:8080/api/prompt/list
```

#### 获取提示词详情
```bash
curl http://localhost:8080/api/prompt/detail/1
```

#### 用户注册
```bash
curl -X POST "http://localhost:8080/api/user/register?username=testuser&password=123456"
```

#### 用户登录
```bash
curl -X POST "http://localhost:8080/api/user/login?username=testuser&password=123456"
```

### 4.2 前端功能测试

打开浏览器访问 http://localhost:5173 并测试以下功能：

1. 查看提示词列表
2. 按分类筛选
3. 查看提示词详情
4. 一键复制提示词
5. 收藏/取消收藏
6. 用户登录和注册
7. 查看排行榜
8. 查看收藏列表

## 第五部分：构建生产版本

### 5.1 后端构建

在后端项目根目录执行：

```bash
mvn clean package -DskipTests
```

生成的 JAR 文件位于 `target/ai-prompt-manager-0.0.1-SNAPSHOT.jar`

运行 JAR 文件：

```bash
java -jar target/ai-prompt-manager-0.0.1-SNAPSHOT.jar
```

### 5.2 前端构建

在前端项目根目录执行：

```bash
npm run build
```

生成的生产文件位于 `dist` 目录，可部署到 Web 服务器。

### 5.3 部署到服务器

1. 将后端 JAR 文件上传到服务器
2. 将前端 `dist` 文件夹上传到 Nginx 或其他 Web 服务器
3. 配置 Nginx 反向代理到后端 API

示例 Nginx 配置：

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        root /var/www/ai-prompt-manager/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8080/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 故障排除

### 问题1：无法连接到数据库

解决方案：
- 检查 MySQL 是否正在运行
- 验证数据库连接信息是否正确
- 确保数据库已创建

### 问题2：前端无法调用后端 API

解决方案：
- 检查 CORS 配置是否正确
- 确保后端服务正在运行
- 在浏览器控制台检查网络错误

### 问题3：port 已被占用

解决方案：
- 后端：修改 `application.yml` 中的 `server.port`
- 前端：修改 `vite.config.js` 中的 `server.port`

## 总结

按照本指南逐步执行，即可成功运行和部署 AI 提示词管理系统。如遇问题，请参考故障排除部分或查阅项目文档。
