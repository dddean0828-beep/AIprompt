# AI Prompt 接口文档

## 目录

- [通用说明](#通用说明)
- [通用返回结构](#通用返回结构)
- [用户模块 - UserController](#用户模块---usercontroller)
- [提示词模块 - PromptController](#提示词模块---promptcontroller)
- [收藏模块 - FavoriteController](#收藏模块---favoritecontroller)
- [排行榜模块 - RankController](#排行榜模块---rankcontroller)
- [使用记录模块 - UsageController](#使用记录模块---usagecontroller)
- [数据模型](#数据模型)

---

## 通用说明

- **Base URL**: `/api`
- **接口前缀**: 各模块接口均以 `/api/{module}` 开头
- **请求方式**: RESTful 风格（GET / POST / PUT / DELETE）
- **Content-Type**: `application/json`
- **认证规则（重要）**: 全局 `AuthInterceptor` 拦截所有 `/api/**` 路径，仅放行 `/api/user/login` 和 `/api/user/register`。**除登录注册外，所有接口都必须在请求头中携带 `Authorization: Bearer {token}`**，否则被拦截器直接返回 HTTP 401。

---

## 通用返回结构

所有接口均采用统一的 `Result<T>` 封装返回：

| 字段 | 类型 | 说明 |
|------|------|------|
| code | Integer | 状态码，200 表示成功，500 表示失败 |
| message | String | 状态描述信息 |
| data | T | 响应数据，泛型，具体类型见各接口说明 |

成功返回示例：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

失败返回示例：

```json
{
  "code": 500,
  "message": "错误描述信息",
  "data": null
}
```

---

## 用户模块 - UserController

**接口前缀**: `/api/user`

### 1. 用户注册

| 项 | 说明 |
|----|------|
| **请求方式** | POST |
| **接口路径** | `/api/user/register` |
| **是否需要认证** | 否 |

#### 方法定义

```java
Result<User> register(@RequestBody AuthRequest request)
```

#### 功能说明

接收用户名和密码，完成新用户注册。

- **前置检查**: 校验用户名是否已存在
- **操作**: 若用户名不存在，则创建新用户记录并写入数据库
- **结果**: 返回注册成功的用户信息；若用户名已存在则返回失败

#### 请求参数（Body）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | String | 是 | 用户名 |
| password | String | 是 | 密码 |

请求示例：

```json
{
  "username": "testuser",
  "password": "123456"
}
```

#### 返回值

- **成功**: 返回 `User` 对象（包含 id、username、password、createdAt）
- **失败**: message 为 "用户名已存在"，data 为 null

返回示例（成功）：

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "testuser",
    "password": "123456",
    "createdAt": "2026-06-12T10:00:00"
  }
}
```

#### Service 逻辑说明

调用 `UserService.register(username, password)`：

1. 通过用户名查询数据库，判断是否已存在同名用户
2. 若已存在，返回 null
3. 若不存在，构建 User 对象，设置用户名、密码和当前时间，插入数据库
4. 返回新创建的用户对象

---

### 2. 用户登录

| 项 | 说明 |
|----|------|
| **请求方式** | POST |
| **接口路径** | `/api/user/login` |
| **是否需要认证** | 否 |

#### 方法定义

```java
Result<Map<String, String>> login(@RequestBody AuthRequest request)
```

#### 功能说明

接收用户名和密码，完成登录并返回 token 和 userId。

- **前置检查**: 根据用户名和密码查询是否存在匹配用户
- **操作**: 若匹配成功，生成 JWT token 并组装 userId
- **结果**: 返回包含 token 和 userId 的 Map；若用户名或密码错误则返回失败

#### 请求参数（Body）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | String | 是 | 用户名 |
| password | String | 是 | 密码 |

请求示例：

```json
{
  "username": "testuser",
  "password": "123456"
}
```

#### 返回值

- **成功**: 返回包含 `token`（JWT 令牌）和 `userId`（用户ID字符串）的 Map
- **失败**: message 为 "用户名或密码错误"，data 为 null

返回示例（成功）：

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "userId": "1"
  }
}
```

#### Service 逻辑说明

调用 `UserService.login(username, password)` 和 `UserService.loginUser(username, password)`：

1. `loginUser`：根据用户名和密码精确查询用户记录
2. `login`：若用户存在，调用 `JwtUtils.createToken(userId, username)` 生成 JWT token；否则返回 null
3. Controller 层组装 token 和 userId 到 Map 中返回

---

### 3. 获取用户信息

| 项 | 说明 |
|----|------|
| **请求方式** | GET |
| **接口路径** | `/api/user/info` |
| **是否需要认证** | 是（需在请求头携带 `Authorization: Bearer {token}`） |

#### 方法定义

```java
Result<User> info(@RequestParam Long userId)
```

#### 功能说明

根据用户 ID 查询用户基本信息。

- **操作**: 直接根据主键查询用户表
- **结果**: 返回对应用户 ID 的用户信息

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Header | Authorization | String | 是 | Bearer {token}，由全局 AuthInterceptor 校验 |
| Query | userId | Long | 是 | 用户 ID |

请求示例：

```
GET /api/user/info?userId=1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 返回值

- **成功**: 返回 `User` 对象
- **若用户不存在**: data 为 null

返回示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "testuser",
    "password": "123456",
    "createdAt": "2026-06-12T10:00:00"
  }
}
```

#### Service 逻辑说明

调用 `UserService.getById(userId)`：

1. 直接通过 MyBatis-Plus 的 `selectById` 方法按主键查询
2. 返回匹配的用户对象，无则返回 null

---

## 提示词模块 - PromptController

**接口前缀**: `/api/prompt`

### 1. 提示词列表

| 项 | 说明 |
|----|------|
| **请求方式** | GET |
| **接口路径** | `/api/prompt/list` |
| **是否需要认证** | 是（需在请求头携带 `Authorization: Bearer {token}`，由全局 AuthInterceptor 校验） |

#### 方法定义

```java
Result<List<Prompt>> list(@RequestParam(required = false) String category,
                          @RequestParam(required = false) String keyword,
                          @RequestHeader(value = "Authorization", required = false) String authorization)
```

#### 功能说明

按分类/关键字筛选并获取提示词列表，token 用于解析当前用户 ID，以判断是否可以查看私有提示词。

- **条件**:
  - 登录用户：可见公开提示词 + 自己创建的私有提示词
  - （注意：匿名访问被全局 AuthInterceptor 拦截，会直接返回 401）
- **操作**: 根据传入的分类、关键字和当前用户 ID 组合查询
- **结果**: 按创建时间倒序排列的提示词列表

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Header | Authorization | String | 是 | Bearer {token}，由全局 AuthInterceptor 校验，token 中解析出用户 ID 用于判断可见范围 |
| Query | category | String | 否 | 分类过滤 |
| Query | keyword | String | 否 | 标题关键字模糊搜索 |

请求示例：

```
GET /api/prompt/list?category=写作&keyword=总结
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 返回值

返回符合条件的 `Prompt` 数组，按创建时间倒序排列。

返回示例：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "title": "文章总结助手",
      "content": "请帮我总结以下文章...",
      "category": "写作",
      "creatorId": 1,
      "creatorName": "testuser",
      "isPrivate": 0,
      "useCount": 10,
      "favoriteCount": 5,
      "createdAt": "2026-06-12T10:00:00"
    }
  ]
}
```

#### Service 逻辑说明

调用 `PromptService.list(category, keyword, currentUserId)`：

1. 从请求头解析 token 获取当前用户 ID（因拦截器已校验，token 必定有效）
2. 构建查询条件：
   - 若 category 非空，按分类精确匹配
   - 若 keyword 非空，按标题模糊匹配
   - 仅查询公开提示词 **或** 当前用户创建的提示词
3. 按创建时间倒序排列后返回结果列表

---

### 2. 提示词详情

| 项 | 说明 |
|----|------|
| **请求方式** | GET |
| **接口路径** | `/api/prompt/detail/{id}` |
| **是否需要认证** | 是 |

#### 方法定义

```java
Result<Prompt> detail(@PathVariable Long id,
                      @RequestHeader("Authorization") String authorization)
```

#### 功能说明

查看指定 ID 的提示词详情，私有提示词仅创建者可查看。

- **条件**: 若提示词为私有（isPrivate = 1），只有创建者本人可以查看
- **操作**: 根据 ID 查询提示词，校验访问权限
- **结果**: 返回提示词详情；无权查看或不存在时返回 null

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Path | id | Long | 是 | 提示词 ID |
| Header | Authorization | String | 是 | Bearer token |

请求示例：

```
GET /api/prompt/detail/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 返回值

返回单个 `Prompt` 对象；若不存在或无权查看则 data 为 null。

返回示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "文章总结助手",
    "content": "请帮我总结以下文章...",
    "category": "写作",
    "creatorId": 1,
    "creatorName": "testuser",
    "isPrivate": 0,
    "useCount": 10,
    "favoriteCount": 5,
    "createdAt": "2026-06-12T10:00:00"
  }
}
```

#### Service 逻辑说明

调用 `PromptService.detail(id, currentUserId)`：

1. 根据 ID 查询提示词记录
2. 若提示词不存在，返回 null
3. 若提示词为私有状态，且当前用户不是创建者，返回 null
4. 权限校验通过后返回提示词详情

---

### 3. 新增提示词

| 项 | 说明 |
|----|------|
| **请求方式** | POST |
| **接口路径** | `/api/prompt/add` |
| **是否需要认证** | 是 |

#### 方法定义

```java
Result<Boolean> add(@RequestBody Prompt prompt,
                    @RequestHeader("Authorization") String authorization)
```

#### 功能说明

由当前登录用户创建一条新的提示词。

- **操作**: 从 token 中解析用户 ID 和用户名，自动填充到提示词的创建者信息中，并设置创建时间、默认的使用/收藏数
- **结果**: 返回 true 表示创建成功，false 表示失败

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Body | title | String | 是 | 提示词标题 |
| Body | content | String | 是 | 提示词内容 |
| Body | category | String | 否 | 分类 |
| Body | isPrivate | Integer | 否 | 是否私有（0=公开，1=私有），默认为 0 |
| Header | Authorization | String | 是 | Bearer token |

请求示例：

```json
{
  "title": "代码评审助手",
  "content": "请帮我评审以下代码...",
  "category": "编程",
  "isPrivate": 0
}
```

#### 返回值

返回布尔值，true 表示新增成功。

返回示例：

```json
{
  "code": 200,
  "message": "success",
  "data": true
}
```

#### Service 逻辑说明

调用 `PromptService.add(prompt, currentUserId, currentUsername)`：

1. 自动设置创建时间为当前时间
2. 自动设置 creatorId 和 creatorName 为当前登录用户信息
3. isPrivate 若为空则默认设为 0（公开）
4. useCount 和 favoriteCount 若为空则默认设为 0
5. 插入数据库，返回影响行数是否大于 0

---

### 4. 更新提示词

| 项 | 说明 |
|----|------|
| **请求方式** | PUT |
| **接口路径** | `/api/prompt/update` |
| **是否需要认证** | 是 |

#### 方法定义

```java
Result<Boolean> update(@RequestBody Prompt prompt,
                       @RequestHeader("Authorization") String authorization)
```

#### 功能说明

更新已创建的提示词，仅创建者本人可以更新。

- **条件**: 当前用户必须是提示词的创建者
- **操作**: 先校验权限，再执行更新，保留原创建者信息和创建时间不变
- **结果**: 返回 true 表示更新成功

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Body | id | Long | 是 | 提示词 ID |
| Body | title | String | 是 | 标题 |
| Body | content | String | 是 | 内容 |
| Body | category | String | 否 | 分类 |
| Body | isPrivate | Integer | 否 | 是否私有 |
| Header | Authorization | String | 是 | Bearer token |

请求示例：

```json
{
  "id": 1,
  "title": "更新后的标题",
  "content": "更新后的内容",
  "category": "编程",
  "isPrivate": 1
}
```

#### 返回值

返回布尔值，true 表示更新成功，false 表示无权限或提示词不存在。

#### Service 逻辑说明

调用 `PromptService.update(prompt, currentUserId)`：

1. 根据 ID 查询数据库中的提示词记录
2. 若记录不存在或当前用户不是创建者，返回 false
3. 保留原记录的 creatorId、creatorName、createdAt 不变
4. 使用传入的 prompt 对象执行更新，返回是否成功

---

### 5. 删除提示词

| 项 | 说明 |
|----|------|
| **请求方式** | DELETE |
| **接口路径** | `/api/prompt/delete/{id}` |
| **是否需要认证** | 是 |

#### 方法定义

```java
Result<Boolean> delete(@PathVariable Long id,
                       @RequestHeader("Authorization") String authorization)
```

#### 功能说明

删除指定提示词，仅创建者本人可以删除。

- **条件**: 当前用户必须是提示词的创建者
- **操作**: 先校验权限，再执行删除
- **结果**: 返回 true 表示删除成功

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Path | id | Long | 是 | 提示词 ID |
| Header | Authorization | String | 是 | Bearer token |

请求示例：

```
DELETE /api/prompt/delete/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 返回值

返回布尔值，true 表示删除成功。

#### Service 逻辑说明

调用 `PromptService.delete(id, currentUserId)`：

1. 根据 ID 查询数据库中的提示词记录
2. 若记录不存在或当前用户不是创建者，返回 false
3. 按 ID 删除该记录，返回是否成功

---

### 6. 切换公开/私有状态

| 项 | 说明 |
|----|------|
| **请求方式** | PUT |
| **接口路径** | `/api/prompt/toggle-private/{id}` |
| **是否需要认证** | 是 |

#### 方法定义

```java
Result<Boolean> togglePrivate(@PathVariable Long id,
                              @RequestParam Integer isPrivate,
                              @RequestHeader("Authorization") String authorization)
```

#### 功能说明

切换提示词的公开/私有状态，仅创建者可操作。

- **条件**: 当前用户必须是提示词的创建者
- **操作**: 根据传入的 isPrivate 参数更新状态（0 表示公开，非 0 视为私有，最终落库为 1）
- **结果**: 返回 true 表示更新成功

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Path | id | Long | 是 | 提示词 ID |
| Query | isPrivate | Integer | 是 | 0=公开，1=私有 |
| Header | Authorization | String | 是 | Bearer token |

请求示例：

```
PUT /api/prompt/toggle-private/1?isPrivate=1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 返回值

返回布尔值，true 表示状态切换成功。

#### Service 逻辑说明

调用 `PromptService.updatePrivate(id, isPrivate, currentUserId)`：

1. 根据 ID 查询数据库中的提示词记录
2. 若记录不存在或当前用户不是创建者，返回 false
3. 将 isPrivate 参数规范化为 0 或 1（null 或 0 取 0，其他取 1）
4. 更新该字段并返回是否成功

---

### 7. 我的提示词列表

| 项 | 说明 |
|----|------|
| **请求方式** | GET |
| **接口路径** | `/api/prompt/mine` |
| **是否需要认证** | 是 |

#### 方法定义

```java
Result<List<Prompt>> mine(@RequestHeader("Authorization") String authorization)
```

#### 功能说明

获取当前登录用户创建的所有提示词列表。

- **操作**: 根据当前用户 ID 查询其创建的提示词
- **结果**: 按创建时间倒序排列的提示词列表

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Header | Authorization | String | 是 | Bearer token |

#### 返回值

返回当前用户创建的 `Prompt` 数组，按创建时间倒序排列。

#### Service 逻辑说明

调用 `PromptService.mine(currentUserId)`：

1. 按 creatorId = 当前用户 ID 过滤查询
2. 按创建时间倒序排列后返回

---

## 收藏模块 - FavoriteController

**接口前缀**: `/api/favorite`

### 1. 添加收藏

| 项 | 说明 |
|----|------|
| **请求方式** | POST |
| **接口路径** | `/api/favorite/add` |
| **是否需要认证** | 是（需在请求头携带 `Authorization: Bearer {token}`） |

#### 方法定义

```java
Result<Boolean> add(@RequestBody FavoriteRequest request)
```

#### 功能说明

将指定提示词加入用户收藏列表，同时更新提示词的收藏数。

- **前置检查**: 若该用户已收藏同一条提示词，则视为成功，不重复插入
- **操作**: 插入收藏记录，并将对应提示词的 favoriteCount + 1
- **结果**: 返回 true 表示收藏成功

#### 请求参数（Body + Header）

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Header | Authorization | String | 是 | Bearer {token}，由全局 AuthInterceptor 校验 |
| Body | userId | Long | 是 | 用户 ID |
| Body | promptId | Long | 是 | 提示词 ID |

请求示例：

```
POST /api/favorite/add
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "userId": 1,
  "promptId": 1
}
```

#### 返回值

返回布尔值，true 表示收藏成功。

#### Service 逻辑说明

调用 `InteractionService.addFavorite(userId, promptId)`：

1. 根据 userId + promptId 查询是否已有重复收藏记录
2. 若已存在，直接返回 true，不重复添加
3. 若不存在，创建新的 Favorite 记录并插入，记录创建时间
4. 查询对应的 Prompt，将 favoriteCount 自增 1 后更新

---

### 2. 取消收藏

| 项 | 说明 |
|----|------|
| **请求方式** | DELETE |
| **接口路径** | `/api/favorite/remove/{id}` |
| **是否需要认证** | 是（需在请求头携带 `Authorization: Bearer {token}`） |

#### 方法定义

```java
Result<Boolean> remove(@PathVariable Long id)
```

#### 功能说明

根据收藏记录 ID 删除收藏，同时扣减对应提示词的收藏数。

- **操作**: 删除指定 ID 的收藏记录，若对应提示词存在且收藏数大于 0，则 favoriteCount - 1
- **结果**: 返回 true 表示删除成功

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Header | Authorization | String | 是 | Bearer {token}，由全局 AuthInterceptor 校验 |
| Path | id | Long | 是 | 收藏记录 ID |

请求示例：

```
DELETE /api/favorite/remove/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 返回值

返回布尔值，true 表示取消收藏成功。

#### Service 逻辑说明

调用 `InteractionService.removeFavorite(id)`：

1. 根据 ID 查询收藏记录
2. 若收藏记录存在，查询对应提示词记录，将 favoriteCount - 1（需大于 0 才执行）
3. 删除收藏记录，返回是否成功

---

### 3. 收藏列表

| 项 | 说明 |
|----|------|
| **请求方式** | GET |
| **接口路径** | `/api/favorite/list` |
| **是否需要认证** | 是（需在请求头携带 `Authorization: Bearer {token}`） |

#### 方法定义

```java
Result<List<FavoritePromptVO>> list(@RequestParam Long userId)
```

#### 功能说明

查询用户收藏的所有提示词，返回包含收藏 ID 和提示词详情的组合列表。

- **操作**: 先按用户 ID 查询所有收藏记录，再逐条关联对应提示词组装返回
- **结果**: 返回 FavoritePromptVO 列表，每项包含 favoriteId 和对应 Prompt 详情

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Header | Authorization | String | 是 | Bearer {token}，由全局 AuthInterceptor 校验 |
| Query | userId | Long | 是 | 用户 ID |

请求示例：

```
GET /api/favorite/list?userId=1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 返回值

返回 `FavoritePromptVO` 数组，按收藏时间倒序排列。

返回示例：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "favoriteId": 1,
      "prompt": {
        "id": 1,
        "title": "文章总结助手",
        "content": "请帮我总结以下文章...",
        "category": "写作",
        "creatorId": 1,
        "creatorName": "testuser",
        "isPrivate": 0,
        "useCount": 10,
        "favoriteCount": 5,
        "createdAt": "2026-06-12T10:00:00"
      }
    }
  ]
}
```

#### Service 逻辑说明

调用 `InteractionService.favoriteList(userId)`：

1. 先调用 `rawFavoriteList(userId)` 获取该用户的所有收藏记录（按创建时间倒序）
2. 遍历每条收藏记录，根据 promptId 查询对应的提示词详情
3. 将收藏 ID 和提示词详情组装为 FavoritePromptVO 对象
4. 收集所有有效结果返回列表

---

## 排行榜模块 - RankController

**接口前缀**: `/api/rank`

### 1. 热门排行榜

| 项 | 说明 |
|----|------|
| **请求方式** | GET |
| **接口路径** | `/api/rank/hot` |
| **是否需要认证** | 是（需在请求头携带 `Authorization: Bearer {token}`，由全局 AuthInterceptor 校验；接口本体无其他业务校验） |

#### 方法定义

```java
Result<List<Prompt>> hot()
```

#### 功能说明

按使用次数（useCount）倒序排列，返回使用量最高的提示词列表。

- **操作**: 按 useCount 字段降序查询所有提示词
- **结果**: 返回热门提示词列表

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Header | Authorization | String | 是 | Bearer {token}，由全局 AuthInterceptor 校验 |

请求示例：

```
GET /api/rank/hot
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 返回值

返回 `Prompt` 数组，按 useCount 降序排列。

#### Service 逻辑说明

调用 `PromptService.rankByHot()`：

1. 按 useCount 字段降序排列查询所有提示词
2. 直接返回查询结果

---

### 2. 收藏排行榜

| 项 | 说明 |
|----|------|
| **请求方式** | GET |
| **接口路径** | `/api/rank/favorite` |
| **是否需要认证** | 是（需在请求头携带 `Authorization: Bearer {token}`，由全局 AuthInterceptor 校验；接口本体无其他业务校验） |

#### 方法定义

```java
Result<List<Prompt>> favorite()
```

#### 功能说明

按收藏数（favoriteCount）倒序排列，返回最受收藏欢迎的提示词列表。

- **操作**: 按 favoriteCount 字段降序查询所有提示词
- **结果**: 返回收藏量最高的提示词列表

#### 请求参数

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Header | Authorization | String | 是 | Bearer {token}，由全局 AuthInterceptor 校验 |

请求示例：

```
GET /api/rank/favorite
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 返回值

返回 `Prompt` 数组，按 favoriteCount 降序排列。

#### Service 逻辑说明

调用 `PromptService.rankByFavorite()`：

1. 按 favoriteCount 字段降序排列查询所有提示词
2. 直接返回查询结果

---

## 使用记录模块 - UsageController

**接口前缀**: `/api/usage`

### 1. 记录使用

| 项 | 说明 |
|----|------|
| **请求方式** | POST |
| **接口路径** | `/api/usage/add` |
| **是否需要认证** | 是（需在请求头携带 `Authorization: Bearer {token}`） |

#### 方法定义

```java
Result<Boolean> add(@RequestBody UsageRequest request)
```

#### 功能说明

记录用户对某条提示词的一次使用行为，同时将该提示词的使用数 + 1。

- **操作**: 插入一条使用记录，记录用户 ID、提示词 ID 和使用时间；并将对应提示词的 useCount + 1
- **结果**: 返回 true 表示记录成功

#### 请求参数（Body + Header）

| 位置 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| Header | Authorization | String | 是 | Bearer {token}，由全局 AuthInterceptor 校验 |
| Body | userId | Long | 是 | 用户 ID |
| Body | promptId | Long | 是 | 提示词 ID |

请求示例：

```
POST /api/usage/add
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "userId": 1,
  "promptId": 1
}
```

#### 返回值

返回布尔值，true 表示使用记录添加成功。

#### Service 逻辑说明

调用 `InteractionService.addUsage(userId, promptId)`：

1. 创建 UsageRecord 对象，设置 userId、promptId 和当前时间
2. 插入使用记录
3. 查询对应提示词，将 useCount + 1 后更新
4. 返回插入是否成功

---

## 数据模型

### User（用户）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 用户 ID（主键） |
| username | String | 用户名 |
| password | String | 密码 |
| createdAt | LocalDateTime | 创建时间 |

### Prompt（提示词）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 提示词 ID（主键） |
| title | String | 标题 |
| content | String | 内容 |
| category | String | 分类 |
| creatorId | Long | 创建者用户 ID |
| creatorName | String | 创建者用户名 |
| isPrivate | Integer | 是否私有（0=公开，1=私有） |
| useCount | Integer | 使用次数 |
| favoriteCount | Integer | 收藏次数 |
| createdAt | LocalDateTime | 创建时间 |

### Favorite（收藏）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 收藏记录 ID（主键） |
| userId | Long | 用户 ID |
| promptId | Long | 提示词 ID |
| createdAt | LocalDateTime | 收藏时间 |

### UsageRecord（使用记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Long | 使用记录 ID（主键） |
| userId | Long | 用户 ID |
| promptId | Long | 提示词 ID |
| createdAt | LocalDateTime | 使用时间 |

### FavoritePromptVO（收藏视图对象）

| 字段 | 类型 | 说明 |
|------|------|------|
| favoriteId | Long | 收藏记录 ID |
| prompt | Prompt | 对应的提示词详情 |

### AuthRequest（认证请求）

| 字段 | 类型 | 说明 |
|------|------|------|
| username | String | 用户名 |
| password | String | 密码 |

### FavoriteRequest（收藏请求）

| 字段 | 类型 | 说明 |
|------|------|------|
| userId | Long | 用户 ID |
| promptId | Long | 提示词 ID |

### UsageRequest（使用记录请求）

| 字段 | 类型 | 说明 |
|------|------|------|
| userId | Long | 用户 ID |
| promptId | Long | 提示词 ID |

---

*文档生成时间: 2026-06-12*
