# 后端单元测试环境说明

## 测试框架

- **JUnit 5**（Jupiter）：通过 Spring Boot 父工程引入的 `spring-boot-starter-test` 使用。
- **AssertJ**：流式断言，用于可读性更好的期望值校验。
- **Mockito**：在 `PromptServiceImplTest` 中对 `PromptMapper` 做 Mock，不连接真实数据库。

## 运行方式

在项目根目录下的 `backend` 模块执行：

```bash
cd backend
mvn test
```

仅运行测试、跳过打包可用：

```bash
mvn -DskipTests=false test
```

在 IDE（如 IntelliJ IDEA）中：右键测试类或 `src/test/java` 目录，选择「运行测试」即可。

## 环境要求

- **JDK 17**（与 `pom.xml` 中 `java.version` 一致）。
- **Maven 3.8+**（用于下载依赖与执行 Surefire 插件）。

## 测试范围说明

当前单元测试为**纯单元测试**，**不启动** Spring 容器，**不依赖** MySQL：

- `ResultTest`：统一返回体 `Result` 的静态工厂方法行为。
- `JwtUtilsTest`：JWT 生成与解析（合法 token / 非法 token）。
- `PromptServiceImplTest`：提示词服务在 Mock Mapper 下的删除权限、私密详情可见性、`mine` / `list` 委托行为。

若后续需要集成测试（真实数据源或 Testcontainers），可再增加 `@SpringBootTest` 与测试专用 `application.yml`，本文档可随之扩展。
