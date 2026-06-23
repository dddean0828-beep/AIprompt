# AI 提示词管理系统 — 简历项目描述 & 模拟面试话术

> 配套测试项目地址：https://github.com/dddean0828-beep/AIprompt/tree/master/tests

---

## 📝 简历项目描述（3-5 行）

### 中文版

> **AI 提示词管理系统**（Spring Boot + Vue.js 全栈项目）
> - 独立设计并实现了覆盖 **API / E2E / 性能** 三层测试体系，编写 **88 条自动化测试用例**（pytest + requests + Playwright），覆盖用户注册登录、提示词 CRUD、收藏排行等核心业务链路。
> - 基于 **Locust** 搭建 4 组压测场景（基准/负载/压力/稳定性），产出静态 HTML 性能报告，定位 API 响应瓶颈。
> - 编写 **560 行 Shell 一键全量测试脚本**（环境检查 → 启动服务 → 执行测试 → 汇总报告），配置 **GitHub Actions CI 流水线**实现提交自动触发测试，报告归档为 Artifact。

### English Version

> **AI Prompt Management Platform** (Spring Boot + Vue.js Full-Stack Project)
> - Designed and implemented a **3-tier test automation suite** (API / E2E / Performance) with **88 test cases** using pytest + requests + Playwright, covering core user journeys including authentication, prompt CRUD, favorites, and rankings.
> - Built **4 Locust load-test scenarios** (baseline / load / stress / stability) with auto-generated static HTML performance reports to identify API bottlenecks.
> - Developed a **560-line shell script** for one-click full-suite execution and configured **GitHub Actions CI** for automated test runs on every push with artifact-archived reports.

---

## 🎤 模拟面试问题 & 回答话术

### Q1: 这个项目的测试体系是怎么设计的？为什么选择这三层？

**回答要点**：

> 我按照经典的测试金字塔模型设计了三个层次。最底层是 **API 接口测试**，用 pytest + requests，直接调用后端接口验证业务逻辑，60 条用例覆盖了用户、提示词、收藏、排行全部接口——包括正常流程和异常边界（比如越权访问、重复注册）。
>
> 中间层是 **E2E 端到端测试**，用 Playwright 模拟真实用户在浏览器中的完整操作流程，28 条用例覆盖了注册→登录→浏览→收藏→登出的完整链路。
>
> 最上层是**性能测试**，用 Locust 模拟真实用户行为链路——注册、登录、浏览列表、查看详情、收藏——设计了 4 组不同负载场景（基准、负载、压力、稳定性），分别验证系统在 10、50、200 并发下的表现。

**加分点**：可以提到 `conftest.py` 中的 fixture 设计（如 `test_user`/`other_user` 用于越权测试），以及 E2E 的失败自动截图机制。

---

### Q2: 你的测试中怎么处理数据隔离问题？多个测试并发执行不会互相影响吗？

**回答要点**：

> 这是个很好的问题。我采用了几种策略来保证数据隔离：
>
> 首先，**每个测试用例都使用唯一用户名**——我在 `conftest.py` 中封装了 `generate_username()` 函数，用 `uuid4` 的前 8 位生成唯一标识，确保每次注册的都是新用户，不会和已有数据冲突。
>
> 其次，**fixture scope 设置得当**：`auth_token` 和 `test_user` 都是 `scope="function"`，每个测试函数会创建独立的用户和 token，用例之间完全隔离。同时 `session` fixture 也是 function 级别的 `requests.Session`，Cookie/Header 不会泄漏。
>
> 第三，**E2E 测试**利用 Playwright 的 `BrowserContext`，每个测试独占一个上下文，localStorage、Cookie、IndexedDB 天然隔离。
>
> 这种设计保证了即使用 `pytest-xdist` 多进程并行运行，测试之间也不会互相干扰。

---

### Q3: 你提到用 Locust 做了性能测试，怎么读懂压测报告？你有没有发现什么性能问题？

**回答要点**：

> Locust 本身输出 CSV，我额外写了一个 `generate_report.py`（约 480 行）把 CSV 转成包含图表的纯静态 HTML 报告，可以直接 `file://` 打开，不需要任何 Web 服务器。
>
> 我主要关注三个指标：
> 1. **P95/P99 响应时间**——代表绝大多数用户的体验。如果 P95 在 200ms 以内，说明体验良好；如果出现尖峰，说明有瓶颈。
> 2. **RPS（每秒请求数）**——系统吞吐量。我会观察 RPS 是否随用户数线性增长，以及何时达到拐点。
> 3. **失败率**——当失败率开始从 0 上升，说明系统接近极限了。
>
> 实际测试中，我发现在压力场景（200 并发）下，某些涉及数据库联表查询的接口（如排行接口）响应时间明显增加。这提示我们可能需要加缓存或优化 SQL 查询。
>
> （如果被追问怎么优化）可以从 Redis 缓存热门排行、数据库索引优化、连接池参数调优等角度展开。

---

### Q4: `run_all.sh` 脚本你是怎么设计的？有什么亮点？

**回答要点**：

> `run_all.sh` 是我自己写的一个约 560 行的 Shell 脚本，目的是**一键完成从环境检查到报告汇总的完整流程**。核心设计有几个亮点：
>
> 1. **智能服务检测**：脚本会先检查前后端是否已在运行，如果已运行就跳过启动步骤，避免重复启动。通过轮询 URL + HTTP 状态码判断服务就绪（接受 2xx/3xx/4xx，说明端口已监听）。
>
> 2. **子命令模式**：支持 `--api-only`、`--e2e-only`、`--perf-only`、`--perf-full` 等参数，可以只跑某一类测试，适用于不同的场景——比如开发时只想快速跑 API 测试验证接口。
>
> 3. **中断安全**：用 `trap` 捕获 `INT`/`TERM` 信号，用户 Ctrl+C 后会自动清理后台的 Java 和 Node.js 进程，不会残留孤儿进程。
>
> 4. **分层汇总**：测试完成后自动生成 Markdown 格式的执行摘要，包含各套件的通过/失败状态、总耗时、环境版本信息，便于留存和分享。

---

### Q5: GitHub Actions CI 你是怎么配置的？遇到什么坑吗？

**回答要点**：

> 我配置了 GitHub Actions 在每次 push 到 master 和 PR 时自动运行 API 测试。工作流的核心步骤是：
> 1. 用 `services` 启动 MySQL 8.0 容器，设置健康检查
> 2. 并行安装 JDK 17、Maven、Python 依赖
> 3. 执行 `init.sql` 初始化数据库表结构和种子数据
> 4. 后台启动 Spring Boot，用 shell 轮询等待就绪
> 5. 运行 pytest，同时产出 JUnit XML 和 HTML 报告
> 6. 无论成功失败都上传报告为 Artifact（保留 7 天）
>
> **踩过的坑**：
> - MySQL 容器启动后 `mysqladmin ping` 返回成功不代表可以执行 SQL，需要在 workflow 里额外等待几秒
> - Spring Boot 启动需要时间（Maven 下载依赖 + 编译），轮询超时设置 60 次 × 3 秒 = 3 分钟才够
> - `continue-on-error: true` 很关键——即使测试失败也要上传报告，否则看不到失败原因
>
> 我用了矩阵策略同时跑 Python 3.9 和 3.11，确保不同 Python 版本下测试都能通过。

---

### Q6: 如果让你从头重新设计这个测试体系，你会做出什么不同的选择？

**回答要点**：

> 这是一个很好的反思问题。如果重新设计，我可能会做这几个改进：
>
> 1. **引入契约测试**：在前端和后端之间加一层 Pact 契约测试，让前端团队和后端团队可以独立开发而不互相阻塞。目前 E2E 测试需要前后端都启动，契约测试可以更早发现问题。
>
> 2. **数据库测试数据管理**：目前每个测试函数都注册新用户，虽然保证了隔离但效率不高。可以考虑用事务回滚策略——每个测试在数据库事务中运行，执行完自动回滚，不产生任何残留数据。这样更干净也更快。
>
> 3. **更强的事件驱动架构**：目前的 `conftest.py` 通过 `_is_url_reachable` 探测服务可用性，但这个逻辑耦合在 Python 里。更好的做法是让 CI Pipeline 来负责服务健康检查，测试代码只专注测试逻辑。
>
> 4. **测试数据工厂**：目前测试数据（用户名、密码）散落在各测试文件里。可以引入类似 Factory Boy 的模式，统一管理测试数据的生成规则，后续维护更方便。
>
> 不过总体来说，当前的设计在**隔离性、可维护性和可读性**之间取得了不错的平衡，团队的反馈也是正向的。

---

## 📌 面试要点速查

| 维度 | 关键词 | 应对策略 |
|------|--------|----------|
| **技术栈** | pytest, Playwright, Locust, Shell, GitHub Actions | 强调选型理由，而非罗列工具 |
| **设计思路** | 测试金字塔、数据隔离、fixture 复用 | 用具体代码例子说明，不要空谈 |
| **工程能力** | CI/CD、Shell 自动化、报告可视化 | 展示"全流程"思维 |
| **问题意识** | 性能瓶颈发现、越权测试、边界覆盖 | 准备 1-2 个实际发现的 bug 或优化案例 |
| **反思能力** | 契约测试、事务回滚、测试数据管理 | 展示对测试体系更深层的理解 |

---

> **准备建议**：面试前打开 `tests/` 目录，快速浏览 `conftest.py` 的 fixture 设计和 `run_all.sh` 的流程结构，确保能流畅地现场讲解代码。
