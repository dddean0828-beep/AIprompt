# AI 提示词管理系统 — 自动化测试套件

> **项目简介**：AI Prompt 是一个基于 Spring Boot + Vue.js 的提示词管理与分享平台。本目录包含 API 接口测试、E2E 端到端测试、Locust 性能压测三套自动化测试体系，共 **88 条测试用例** + **4 组压测场景**，总计约 3,200 行测试代码。

---

## 📋 目录

- [测试架构](#-测试架构)
- [环境要求](#-环境要求)
- [快速开始](#-快速开始)
- [测试分层](#-测试分层)
  - [API 接口测试](#1-api-接口测试)
  - [E2E 端到端测试](#2-e2e-端到端测试)
  - [Locust 性能测试](#3-locust-性能测试)
- [一键全量测试](#-一键全量测试-run_allsh)
- [报告解读](#-报告解读)
- [项目文件结构](#-项目文件结构)
- [CI 集成](#-ci-集成)
- [贡献指南](#-贡献指南)

---

## 🏗 测试架构

```
┌──────────────────────────────────────────────────┐
│                 Test Pyramid                      │
│                                                  │
│                    ┌───┐                          │
│                    │ E2E│  28 tests  (Playwright) │
│                    └───┘                          │
│               ┌──────────────┐                    │
│               │  API Tests    │  60 tests (pytest)│
│               └──────────────┘                    │
│         ┌──────────────────────────┐              │
│         │   Performance (Locust)   │  4 scenarios │
│         └──────────────────────────┘              │
└──────────────────────────────────────────────────┘
```

| 层级 | 工具 | 数量 | 覆盖范围 |
|------|------|------|----------|
| **API 接口测试** | pytest + requests | 60 条 | 用户、提示词、收藏、排行、使用记录、场景组合 |
| **E2E 端到端测试** | pytest + Playwright | 28 条 | 注册登录、提示词 CRUD、收藏全流程 |
| **性能压测** | Locust | 4 组场景 | 基准、负载、压力、稳定性 |

---

## 🔧 环境要求

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.9 | 测试运行环境 |
| Java (JDK) | ≥ 17 | 后端 Spring Boot |
| Maven | ≥ 3.8 | 后端构建 |
| Node.js | ≥ 18 | 前端 Vite 开发服务器 |
| MySQL | 8.0 | 数据库（需提前创建 `ai_prompt_manager` 库） |
| Playwright 浏览器 | Chromium / Firefox / WebKit | E2E 浏览器自动化 |

### 安装 Python 依赖

```bash
cd tests/
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
playwright install chromium      # 安装浏览器
```

**`requirements.txt`** 依赖清单：

| 包名 | 版本 | 用途 |
|------|------|------|
| `requests` | ≥ 2.31.0 | HTTP 请求（API 测试） |
| `pytest` | ≥ 7.4.0 | 测试框架 |
| `pytest-html` | ≥ 4.1.0 | HTML 报告生成 |
| `pytest-xdist` | ≥ 3.5.0 | 并行测试执行 |
| `pytest-timeout` | ≥ 2.2.0 | 测试超时控制 |
| `pytest-playwright` | ≥ 0.4.0 | Playwright 集成 |
| `playwright` | ≥ 1.40.0 | 浏览器自动化 |
| `locust` | ≥ 2.20.0 | 性能压测 |

---

## 🚀 快速开始

### 方式一：一键全量运行（推荐）

```bash
# 启动前后端 → 运行所有测试 → 生成报告 → 关闭服务
bash tests/run_all.sh

# 仅运行 API 测试
bash tests/run_all.sh --api-only

# 仅运行 E2E 测试
bash tests/run_all.sh --e2e-only

# 全部四组压测场景
bash tests/run_all.sh --perf-only --perf-full

# 使用 Firefox 运行 E2E
bash tests/run_all.sh --browser firefox

# 测试完成后保持服务运行
bash tests/run_all.sh --keep-running
```

### 方式二：手动运行

#### 前提：确保后端已启动

```bash
# 终端 1：启动后端
cd backend && mvn spring-boot:run

# 终端 2：启动前端（仅 E2E 需要）
cd frontend && npm install && npm run dev
```

#### 运行 API 测试

```bash
# 运行全部 API 测试（含 HTML 报告）
pytest tests/api/ -v --html=tests/reports/api_report.html --self-contained-html

# 仅运行用户模块
pytest tests/api/ -v -m user

# 仅运行冒烟测试
pytest tests/api/ -v -m smoke

# 并行运行（4 进程）
pytest tests/api/ -v -n 4
```

#### 运行 E2E 测试

```bash
# 使用 Chromium（默认）
pytest tests/e2e/ -v --browser chromium --html=tests/reports/e2e_report.html --self-contained-html

# 使用 Firefox
pytest tests/e2e/ -v --browser firefox

# 单文件运行
pytest tests/e2e/test_register_login.py -v
```

#### 运行性能测试

```bash
# 基准测试：10 用户，2/s 孵化，持续 1 分钟
locust -f tests/perf/locustfile.py --headless -u 10 -r 2 --run-time 1m \
  --csv=tests/reports/perf_baseline

# 生成静态 HTML 报告
python tests/perf/generate_report.py \
  --stats-csv=tests/reports/perf_baseline_stats.csv \
  --history-csv=tests/reports/perf_baseline_stats_history.csv \
  --output=tests/reports/perf_report_baseline.html \
  --scenario="基准测试" --users=10 --rate=2 --duration=1m
```

---

## 📚 测试分层

### 1. API 接口测试

**目录**: `tests/api/`  
**文件数**: 7 个测试文件，60 条测试用例  
**依赖**: 仅需后端 `http://localhost:8080`

| 文件 | 用例数 | 覆盖接口 |
|------|--------|----------|
| [`test_user.py`](api/test_user.py) | 10 | `POST /api/user/register`、`POST /api/user/login`、`GET /api/user/info`、`PUT /api/user/update` |
| [`test_prompt.py`](api/test_prompt.py) | 20 | `POST /api/prompt/add`、`GET /api/prompt/list`、`GET /api/prompt/{id}`、`PUT /api/prompt/update`、`DELETE /api/prompt/{id}`、`PUT /api/prompt/audit/{id}` |
| [`test_favorite.py`](api/test_favorite.py) | 9 | `POST /api/favorite/add`、`DELETE /api/favorite/{promptId}`、`GET /api/favorite/list` |
| [`test_rank.py`](api/test_rank.py) | 6 | `GET /api/prompt/hot`、`GET /api/rank/favorite` |
| [`test_usage.py`](api/test_usage.py) | 5 | `POST /api/usage/record`、`GET /api/usage/list` |
| [`test_smoke.py`](api/test_smoke.py) | 5 | 环境连通性冒烟验证 |
| [`test_scenarios.py`](api/test_scenarios.py) | 5 | 跨模块场景组合测试 |

#### Fixture 能力

由 [`tests/api/conftest.py`](api/conftest.py) 提供：

| Fixture | Scope | 说明 |
|---------|-------|------|
| `base_url` | session | 后端 API 根地址 `http://localhost:8080` |
| `session` | function | 独立 HTTP 会话（Cookie/Header 隔离） |
| `auth_token` | function | 自动注册+登录，返回 Bearer token |
| `test_user` | function | 完整用户信息 `{token, userId, username}` |
| `other_user` | function | 另一个独立用户（用于越权/隔离测试） |

### 2. E2E 端到端测试

**目录**: `tests/e2e/`  
**文件数**: 3 个测试文件 + `utils.py` 帮助函数库，28 条测试用例  
**依赖**: 后端 `:8080` + 前端 `:5173` + Playwright 浏览器

| 文件 | 用例数 | 覆盖场景 |
|------|--------|----------|
| [`test_register_login.py`](e2e/test_register_login.py) | 10 | 注册→登录→登出→权限拦截→Token 管理 |
| [`test_prompt_crud.py`](e2e/test_prompt_crud.py) | 10 | 提示词创建→编辑→删除→审核→搜索 |
| [`test_favorite_flow.py`](e2e/test_favorite_flow.py) | 8 | 收藏→取消→列表→登录态保持 |

#### E2E 核心特性

- **`authenticated_page` fixture**：自动完成注册+登录，测试从已登录首页开始
- **失败自动截图**：测试失败时自动保存 `tests/reports/e2e_screenshots/{test_name}_{browser}.png`
- **多浏览器支持**：`pytest tests/e2e/ --browser chromium --browser firefox --browser webkit`
- **浏览器上下文隔离**：viewport 1280×720，locale zh-CN，每个测试独立上下文

### 3. Locust 性能测试

**目录**: `tests/perf/`  
**文件**: `locustfile.py`（压测脚本）+ `generate_report.py`（HTML 报告生成）  
**依赖**: 仅需后端 `:8080`

#### 模拟用户行为链路

```
注册 → 登录 → 浏览提示词列表 → 查看详情 → 点击收藏 → 查看排行 → 记录使用
```

#### 四组压测场景

| 场景 | 用户数 | 孵化率 | 持续时间 | 目标 |
|------|--------|--------|----------|------|
| **baseline**（基准） | 10 | 2/s | 1 min | 确认系统正常运行，获取基线数据 |
| **load**（负载） | 50 | 10/s | 3 min | 观察响应时间随负载增长的趋势 |
| **stress**（压力） | 200 | 50/s | 5 min | 找到系统吞吐量瓶颈和失败阈值 |
| **stability**（稳定性） | 30 | 5/s | 10 min | 验证长时间运行无内存泄漏、连接泄漏 |

#### 报告生成流程

```
Locust 运行 → 产出 CSV 原始数据 → generate_report.py → 纯静态 HTML 报告
```

报告包含：请求统计表（百分位延迟）、RPS 时间序列图、响应时间时间序列图、用户数时间序列图。

---

## 🔄 一键全量测试 (run_all.sh)

[`run_all.sh`](run_all.sh) 是测试套件的一键入口，约 560 行 Shell 脚本，实现：

```
环境检查 → 启动服务 → 等待就绪 → API 测试 → E2E 测试 → Locust 压测 → 汇总报告 → 关闭服务
```

### 关键特性

- **智能服务检测**：如果前后端已在运行，跳过启动步骤
- **服务就绪等待**：轮询端口直到服务返回 2xx/3xx/4xx 响应（最多 60-90 秒）
- **仅单项运行**：`--api-only` / `--e2e-only` / `--perf-only` 跳过服务启停
- **中断安全**：`trap INT TERM` 捕获 Ctrl+C，自动清理前后端进程
- **彩色输出**：INFO/OK/WARN/ERROR 分级带颜色打印
- **MD 汇总**：测试结束后自动生成 Markdown 格式的执行摘要

### 帮助

```bash
bash tests/run_all.sh --help
```

---

## 📊 报告解读

所有报告输出到 `tests/reports/`（已 gitignore）。

### 报告文件清单

```
tests/reports/
├── api_report.html              # API 测试 HTML 报告
├── e2e_report.html              # E2E 测试 HTML 报告
├── api_test.log                 # API 测试终端日志
├── e2e_test.log                 # E2E 测试终端日志
├── perf_report_baseline.html    # 基准测试报告
├── perf_report_load.html        # 负载测试报告
├── perf_report_stress.html      # 压力测试报告
├── perf_report_stability.html   # 稳定性测试报告
├── perf_baseline_stats.csv      # 基准测试原始数据
├── perf_load_stats.csv          # 负载测试原始数据
├── summary_20260623_120000.md   # 执行汇总（按时间戳命名）
└── e2e_screenshots/             # E2E 失败截图
```

### pytest-html 报告

- **全局摘要**：执行时间、通过/失败/跳过计数
- **按模块分组**：user / prompt / favorite / rank / usage / smoke / scenarios
- **失败详情**：断言错误消息 + 完整 Traceback
- **`--self-contained-html`**：CSS/JS 内嵌入 HTML，单文件可分发给任何人直接打开

### Locust 性能报告

- **请求统计表**：各接口的 RPS、平均/最小/最大/百分位响应时间、失败率
- **RPS 图表**：每秒请求数随时间变化
- **响应时间图表**：P50/P95/P99 随时间变化
- **用户数图表**：并发用户数增长曲线

> 💡 **性能基线参考**：在 10 用户 / 2 RPS / 1min 的基准场景下，P95 响应时间应 < 200ms，失败率应 = 0。

---

## 📁 项目文件结构

```
tests/
├── README.md                    # ← 本文档
├── conftest.py                  # 项目级共享配置（服务探测 + 自动标记）
├── pytest.ini                   # pytest 全局配置（标记注册、超时、警告过滤）
├── requirements.txt             # Python 依赖清单
├── run_all.sh                   # 一键全量测试脚本
│
├── api/                         # API 接口测试
│   ├── __init__.py
│   ├── conftest.py              # API fixture：session、auth_token、test_user
│   ├── test_user.py             # 用户模块：注册/登录/信息/更新
│   ├── test_prompt.py           # 提示词模块：CRUD + 审核 + 权限
│   ├── test_favorite.py         # 收藏模块：添加/移除/列表
│   ├── test_rank.py             # 排行模块：热门/收藏排行
│   ├── test_usage.py            # 使用记录：记录/列表
│   ├── test_smoke.py            # 冒烟测试：环境链路验证
│   └── test_scenarios.py        # 场景测试：跨模块组合
│
├── e2e/                         # E2E 端到端测试
│   ├── __init__.py
│   ├── conftest.py              # Playwright fixture + 失败自动截图
│   ├── utils.py                 # 帮助函数：register、login、navigate_to
│   ├── test_register_login.py   # 注册登录流程
│   ├── test_prompt_crud.py      # 提示词 CRUD 流程
│   └── test_favorite_flow.py    # 收藏全流程
│
├── perf/                        # 性能压测
│   ├── __init__.py
│   ├── locustfile.py            # Locust 压测脚本（模拟真实用户链路）
│   └── generate_report.py       # CSV → 静态 HTML 报告生成器
│
└── reports/                     # 测试报告输出（gitignore）
    ├── *.html
    ├── *.csv
    ├── *.log
    └── e2e_screenshots/
```

---

## 🔗 pytest.ini 关键配置

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    smoke: 冒烟测试（核心流程快速验证）
    slow: 慢速测试（如浏览器交互、多步骤流程）
    user: 用户模块测试（注册/登录/鉴权）
    prompt: 提示词模块测试（CRUD + 权限边界）
    favorite: 收藏模块测试
    e2e: 端到端测试（需要前端服务 + 浏览器）

addopts = -v --tb=short --strict-markers --timeout=30

norecursedirs =
    .venv
    .pytest_cache
    __pycache__
    node_modules
    reports
```

> 详细配置及注释请查看 [`pytest.ini`](pytest.ini)。

---

## 🤖 CI 集成

本项目已配置 GitHub Actions 自动化 CI（[`.github/workflows/tests.yml`](../.github/workflows/tests.yml)）：

| 触发器 | 说明 |
|--------|------|
| `push` 到 `master` | 每次推送运行 API + E2E 测试 |
| `pull_request` 到 `master` | PR 合入前门禁检查 |
| `workflow_dispatch` | 手动触发（GitHub UI → Actions → Run workflow） |

### CI 矩阵

| 维度 | 选项 |
|------|------|
| Python | 3.9, 3.11 |
| 浏览器 | chromium |

### CI 工作流步骤

1. **Checkout** 代码
2. **Setup** JDK 17 + Maven + Python + Node.js
3. **Start** MySQL 服务并初始化数据库
4. **Start** Spring Boot 后端（后台运行）
5. **Run** API 测试（pytest + HTML 报告）
6. **Upload** 测试报告为 CI Artifact

---

## 🤝 贡献指南

### 添加新 API 测试

1. 在 `tests/api/` 下新建 `test_<module>.py`
2. 使用 `conftest.py` 提供的 `auth_token` / `test_user` fixture
3. 在 `pytest.ini` 的 `markers` 中注册新标记（如果需要分类运行）
4. 运行 `pytest tests/api/ -v` 验证

### 添加新 E2E 测试

1. 在 `tests/e2e/` 下新建 `test_<feature>.py`
2. 使用 `page` / `authenticated_page` fixture
3. 工具函数放入 `utils.py` 复用
4. 确保失败时截图能自动保存

### 命名规范

- 测试文件：`test_<模块名>.py`
- 测试类：`Test<功能描述>`
- 测试方法：`test_<动作>_<预期结果>`
- 例如：`test_register_with_duplicate_username_returns_400`

---

## 📝 测试标记速查

```bash
# 冒烟测试（每次部署后快速验证）
pytest tests/ -v -m smoke

# 用户模块
pytest tests/ -v -m user

# 提示词模块
pytest tests/ -v -m prompt

# 收藏模块
pytest tests/ -v -m favorite

# E2E 测试
pytest tests/ -v -m e2e

# 排除慢速测试
pytest tests/ -v -m "not slow"

# 并行运行
pytest tests/api/ -n auto
```

---

> **维护者**：dddean0828-beep  
> **最后更新**：2026-06-23  
> **许可证**：MIT
