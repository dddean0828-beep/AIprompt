# AI提示词管理系统运行步骤

## 一、环境准备

请先安装以下软件：

- JDK 17 及以上
- Maven 3.8 及以上
- Node.js 18 及以上
- MySQL 8.0

## 二、初始化数据库

1. 打开 MySQL 客户端，执行脚本：

   - `backend/src/main/resources/db/init.sql`

2. 确认数据库名称为 `ai_prompt_manager`。

## 三、配置后端数据库连接

编辑文件：`backend/src/main/resources/application.yml`

主要检查以下配置是否与你本机一致：

- `spring.datasource.url`
- `spring.datasource.username`
- `spring.datasource.password`

## 四、启动后端

在终端进入后端目录：

```bash
cd backend
mvn clean package
mvn spring-boot:run
```

后端默认端口：`8080`

可用测试地址：

- `http://localhost:8080/api/prompt/list`

## 五、启动前端

新开一个终端，进入前端目录：

```bash
cd frontend
npm install
npm run dev
```

前端默认端口：`5173`

浏览器访问：

- `http://localhost:5173`

## 六、功能验证建议

建议依次验证：

1. 注册与登录
2. 首页分类筛选与卡片展示
3. 提示词详情与一键复制
4. 收藏与收藏列表
5. 使用记录增长
6. 热门排行与收藏排行

## 七、常见问题

1. 前端无法访问后端

- 检查后端是否启动在 `8080`
- 检查 `frontend/vite.config.js` 代理配置是否存在 `/api -> http://localhost:8080`

2. 后端连接数据库失败

- 检查 MySQL 服务是否启动
- 检查 `application.yml` 用户名和密码
- 检查数据库 `ai_prompt_manager` 是否已创建

3. 端口冲突

- 后端端口在 `application.yml` 修改
- 前端端口在 `vite.config.js` 修改
