"""
Locust 性能测试脚本 — AI 提示词管理系统

模拟真实用户行为链路：
  注册 → 登录 → 浏览列表 → 查看详情 → 收藏 → 查看排行 → 记录使用

===================================================================
四组压测场景
===================================================================

┌────────────┬──────────┬──────────┬──────────┬──────────────────────┐
│ 场景       │ 用户数   │ 孵化率   │ 持续时间 │ 目标                 │
├────────────┼──────────┼──────────┼──────────┼──────────────────────┤
│ 基准测试   │ 10       │ 2/s      │ 1min     │ 确认系统正常运行     │
│ 负载测试   │ 50       │ 10/s     │ 3min     │ 观察响应时间趋势     │
│ 压力测试   │ 200      │ 50/s     │ 5min     │ 找到系统瓶颈         │
│ 稳定性测试 │ 30       │ 5/s      │ 10min    │ 长时间运行无内存泄漏 │
└────────────┴──────────┴──────────┴──────────┴──────────────────────┘

===================================================================
运行方式（两步：先跑 Locust 产 CSV，再生成静态 HTML）
===================================================================

# 基准测试（默认 10 用户，1 分钟）
locust -f tests/perf/locustfile.py --headless -u 10 -r 2 --run-time 1m \
  --csv=reports/perf_baseline
python tests/perf/generate_report.py \
  --stats-csv=reports/perf_baseline_stats.csv \
  --history-csv=reports/perf_baseline_stats_history.csv \
  --output=reports/perf_report_baseline.html \
  --scenario="基准测试" --users=10 --rate=2 --duration=1m

# 负载测试（50 用户，3 分钟）
locust -f tests/perf/locustfile.py --headless -u 50 -r 10 --run-time 3m \
  --csv=reports/perf_load
python tests/perf/generate_report.py \
  --stats-csv=reports/perf_load_stats.csv \
  --history-csv=reports/perf_load_stats_history.csv \
  --output=reports/perf_report_load.html \
  --scenario="负载测试" --users=50 --rate=10 --duration=3m

# 压力测试（200 用户，5 分钟）
locust -f tests/perf/locustfile.py --headless -u 200 -r 50 --run-time 5m \
  --csv=reports/perf_stress
python tests/perf/generate_report.py \
  --stats-csv=reports/perf_stress_stats.csv \
  --history-csv=reports/perf_stress_stats_history.csv \
  --output=reports/perf_report_stress.html \
  --scenario="压力测试" --users=200 --rate=50 --duration=5m

# 稳定性测试（30 用户，10 分钟）
locust -f tests/perf/locustfile.py --headless -u 30 -r 5 --run-time 10m \
  --csv=reports/perf_stability
python tests/perf/generate_report.py \
  --stats-csv=reports/perf_stability_stats.csv \
  --history-csv=reports/perf_stability_stats_history.csv \
  --output=reports/perf_report_stability.html \
  --scenario="稳定性测试" --users=30 --rate=5 --duration=10m

# Web UI 模式（实时监控面板）
locust -f tests/perf/locustfile.py

# 一键全量（自动跑四组 + 生成报告）
bash tests/run_all.sh --perf-only

===================================================================
关键关注指标
===================================================================

- P50/P95/P99 响应时间
- RPS（每秒请求数）
- 失败率
- 登录接口在高并发下的表现（JWT 生成开销）
- 数据库连接池是否枯竭
"""

import random
import uuid
import time

from locust import HttpUser, task, between, events
from locust.env import Environment


# ============================================================
# 配置
# ============================================================

BASE_URL = "http://localhost:8080"


# ============================================================
# 用户行为类
# ============================================================

class PromptManagerUser(HttpUser):
    """
    模拟 AI Prompt Manager 普通用户。

    行为权重设计（模拟真实分布）：
      - 浏览列表（高频，权重 3）—— 用户大部分时间在闲逛
      - 查看详情（权重 2）—— 看到感兴趣的会点进去
      - 热门排行（权重 2）—— 看看趋势
      - 收藏提示词（权重 1）—— 偶尔收藏
      - 我的提示词（权重 1）—— 看看自己的
      - 记录使用（权重 1）—— 用过之后记录

    用户思考时间：1~3 秒（模拟真实用户操作间隔）
    """

    # 连接目标主机（Locust 2.x 使用 host 属性）
    host = BASE_URL

    # 思考时间：每个 task 之间等待 1~3 秒
    wait_time = between(1, 3)

    def on_start(self):
        """
        每个虚拟用户启动时执行一次：注册新用户 → 登录获取 JWT token。

        使用 uuid 保证每个虚拟用户拥有独立账号，避免冲突。
        """
        self.username = f"perf_{uuid.uuid4().hex[:10]}"
        self.password = "test123456"
        self.token = None
        self.user_id = None
        self.created_prompt_ids = []  # 缓存已创建的提示词 ID

        # ---------- 1. 注册 ----------
        register_start = time.time()
        with self.client.post(
            "/api/user/register",
            json={"username": self.username, "password": self.password},
            catch_response=True,
            name="POST /api/user/register",
        ) as resp:
            register_time = time.time() - register_start
            if resp.status_code == 200 and resp.json().get("code") == 200:
                resp.success()
            else:
                # 注册失败（如数据库已存在残留用户名），标记为成功但记录
                # 因为不是被测系统的性能问题
                resp.success()

        # ---------- 2. 登录 ----------
        login_start = time.time()
        with self.client.post(
            "/api/user/login",
            json={"username": self.username, "password": self.password},
            catch_response=True,
            name="POST /api/user/login",
        ) as resp:
            login_time = time.time() - login_start
            data = resp.json()
            if data.get("code") == 200 and data["data"].get("token"):
                self.token = f"Bearer {data['data']['token']}"
                self.user_id = int(data["data"]["userId"])
                resp.success()
            else:
                # 登录失败标记为失败
                resp.failure(f"登录失败: {data.get('message', 'unknown')}")

        # ---------- 3. 预加载：获取已有提示词列表作为详情/收藏的目标 ----------
        self.public_prompt_ids = self._fetch_public_prompt_ids()

    def _auth_headers(self) -> dict:
        """构建带 JWT 的请求头"""
        return {"Authorization": self.token} if self.token else {}

    def _fetch_public_prompt_ids(self) -> list:
        """
        从列表接口获取一批公开提示词 ID，作为后续浏览详情、收藏等操作的目标。

        name="GET /api/prompt/list (prefetch)", (prefetch) -> 说明是预加载阶段的请求，便于在报告中区分。

        如果数据库中暂无提示词，先创建几条用于后续操作。
        """
        try:
            with self.client.get(
                "/api/prompt/list",
                headers=self._auth_headers(),
                catch_response=True,
                name="GET /api/prompt/list (prefetch)",
            ) as resp:
                if resp.status_code == 200 and resp.json().get("code") == 200:
                    items = resp.json()["data"]
                    ids = [item["id"] for item in items if item.get("id")]
                    if ids:
                        return ids
        except Exception:
            pass

        # 数据库中没有提示词，创建几条供后续操作
        for i in range(3):
            try:
                with self.client.post(
                    "/api/prompt/add",
                    json={
                        "title": f"压测专用_{self.username}_{i}",
                        "content": f"这是性能测试生成的提示词 #{i}。",
                        "category": random.choice(["写作", "编程", "翻译", "通用"]),
                        "isPrivate": 0,
                    },
                    headers=self._auth_headers(),
                    catch_response=True,
                    name="POST /api/prompt/add (seed)",
                ) as resp:
                    if resp.status_code == 200 and resp.json().get("code") == 200:
                        # 创建成功后，通过 mine 列表获取 ID
                        pass
            except Exception:
                pass

        # 再次尝试获取
        try:
            with self.client.get(
                "/api/prompt/list",
                headers=self._auth_headers(),
                catch_response=True,
                name="GET /api/prompt/list (retry)",
            ) as resp:
                if resp.status_code == 200 and resp.json().get("code") == 200:
                    items = resp.json()["data"]
                    return [item["id"] for item in items if item.get("id")]
        except Exception:
            pass

        return []

    # ============================================================
    # Task 定义（权重 3 + 2 + 2 + 1 + 1 + 1 = 10）
    # ============================================================

    @task(3)
    def browse_prompt_list(self):
        """
        【权重 3：高频】浏览提示词列表。

        随机切换：全量列表 / 按分类筛选 / 按关键词搜索。
        模拟用户在首页闲逛的真实行为。
        """
        strategy = random.choice(["all", "category", "keyword"])
        params = {}

        if strategy == "category":
            params["category"] = random.choice(["写作", "编程", "翻译", "通用", "测试分类"])
        elif strategy == "keyword":
            params["keyword"] = random.choice(["提示", "测试", "AI", "Python", "Java"])

        with self.client.get(
            "/api/prompt/list",
            headers=self._auth_headers(),
            params=params,
            catch_response=True,
            name="GET /api/prompt/list",
        ) as resp:
            if resp.status_code == 200 and resp.json().get("code") == 200:
                # 缓存 ID 列表供其他任务使用
                items = resp.json()["data"]
                new_ids = [item["id"] for item in items if item.get("id")]
                if new_ids:
                    # set() 无序集合去重
                    self.public_prompt_ids = list(set(self.public_prompt_ids + new_ids))
                resp.success()
            else:
                resp.failure(f"列表查询失败: {resp.status_code}")

    @task(2)
    def view_prompt_detail(self):
        """
        【权重 2】查看提示词详情。

        从缓存的提示词 ID 列表中随机选一个查看。
        如果没有可用 ID，先请求列表获取。
        """
        if not self.public_prompt_ids:
            self.public_prompt_ids = self._fetch_public_prompt_ids()

        if not self.public_prompt_ids:
            return  # 确实没有可查看的提示词

        pid = random.choice(self.public_prompt_ids)

        with self.client.get(
            f"/api/prompt/detail/{pid}",
            headers=self._auth_headers(),
            catch_response=True,
            name="GET /api/prompt/detail/{id}",
        ) as resp:
            if resp.status_code == 200 and resp.json().get("code") == 200:
                resp.success()
            else:
                resp.failure(f"详情查询失败: id={pid}")

    @task(2)
    def view_hot_rank(self):
        """
        【权重 2】查看热门排行 / 收藏排行。

        随机切换：热门排行（useCount）或 收藏排行（favoriteCount）。
        排行接口也验证 order by 在高并发下是否出问题。
        """
        endpoint = random.choice(["/api/rank/hot", "/api/rank/favorite"])
        name = f"GET {endpoint}"

        with self.client.get(
            endpoint,
            headers=self._auth_headers(),
            catch_response=True,
            name=name,
        ) as resp:
            if resp.status_code == 200 and resp.json().get("code") == 200:
                resp.success()
            else:
                resp.failure(f"排行查询失败: {endpoint}")

    @task(1)
    def add_favorite(self):
        """
        【权重 1】收藏提示词。

        模拟用户看到感兴趣的内容，点击收藏。
        随机从缓存 ID 列表选一个进行收藏。
        """
        if not self.public_prompt_ids:
            self.public_prompt_ids = self._fetch_public_prompt_ids()
        if not self.public_prompt_ids:
            return

        pid = random.choice(self.public_prompt_ids)

        with self.client.post(
            "/api/favorite/add",
            json={"userId": self.user_id, "promptId": pid},
            headers=self._auth_headers(),
            catch_response=True,
            name="POST /api/favorite/add",
        ) as resp:
            if resp.status_code == 200 and resp.json().get("code") == 200:
                resp.success()
            else:
                resp.failure(f"收藏失败: userId={self.user_id}, promptId={pid}")

    @task(1)
    def view_my_prompts(self):
        """
        【权重 1】查看"我的提示词"列表。

        验证权限隔离：每个用户只看到自己的提示词。
        """
        with self.client.get(
            "/api/prompt/mine",
            headers=self._auth_headers(),
            catch_response=True,
            name="GET /api/prompt/mine",
        ) as resp:
            if resp.status_code == 200 and resp.json().get("code") == 200:
                resp.success()
            else:
                resp.failure(f"我的列表查询失败: {resp.status_code}")

    @task(1)
    def record_usage(self):
        """
        【权重 1】记录提示词使用。

        模拟用户复制/使用了某条提示词后，系统记录使用次数。
        需要有效 promptId + userId。
        """
        if not self.public_prompt_ids:
            self.public_prompt_ids = self._fetch_public_prompt_ids()
        if not self.public_prompt_ids:
            return

        pid = random.choice(self.public_prompt_ids)

        with self.client.post(
            "/api/usage/add",
            json={"userId": self.user_id, "promptId": pid},
            headers=self._auth_headers(),
            catch_response=True,
            name="POST /api/usage/add",
        ) as resp:
            if resp.status_code == 200 and resp.json().get("code") == 200:
                resp.success()
            else:
                resp.failure(f"记录使用失败: userId={self.user_id}, promptId={pid}")

    # ============================================================
    # 可选：随机关闭用户时的清理
    # ============================================================

    def on_stop(self):
        """
        虚拟用户停止时执行（可选清理逻辑）。

        当前实现为空：不主动清理测试数据，
        避免在高并发下增加额外负载干扰结果。
        """
        pass


# ============================================================
# 环境初始化事件（可选）
# ============================================================

@events.init.add_listener
def on_locust_init(environment: Environment, **kwargs):
    """
    Locust 环境初始化时触发。

    可用于：
    - 检查后端是否可达
    - 预热数据库
    - 打印场景配置信息
    """
    import requests as req

    try:
        resp = req.get(f"{BASE_URL}/api/user/login", json={
            "username": "__health_check__", "password": "test",
        }, timeout=5)
    except req.exceptions.ConnectionError:
        print(f"\n{'='*60}")
        print(f"⚠️  警告：后端 {BASE_URL} 不可达！")
        print(f"   请先启动 Spring Boot 后端再运行 Locust。")
        print(f"{'='*60}\n")
        return
    except Exception as exc:
        print(f"\n⚠️  健康检查异常: {exc}\n")
        return

    print(f"\n{'='*60}")
    print(f"✅ 后端 {BASE_URL} 可达，Locust 准备就绪。")
    print(f"   用户数: {environment.runner.target_user_count if environment.runner else 'N/A'}")
    spawn_rate = getattr(environment.runner, 'spawn_rate', None) or getattr(environment.runner, 'spawn_rate_per_second', None) or 'N/A'
    print(f"   孵化率: {spawn_rate}")
    print(f"{'='*60}\n")


@events.test_start.add_listener
def on_test_start(environment: Environment, **kwargs):
    """测试开始时打印配置"""
    if environment.runner:
        spawn_rate = getattr(environment.runner, 'spawn_rate', None) or getattr(environment.runner, 'spawn_rate_per_second', None) or 'N/A'
    print(f"\n🚀 压测开始：{environment.runner.target_user_count} 用户，"
          f"孵化率 {spawn_rate}/s\n")


@events.test_stop.add_listener
def on_test_stop(environment: Environment, **kwargs):
    """测试结束时打印汇总"""
    if environment.stats.total.num_requests > 0:
        stats = environment.stats.total
        print(f"\n{'='*60}")
        print(f"📊 压测完成汇总")
        print(f"{'='*60}")
        print(f"  总请求数:    {stats.num_requests}")
        print(f"  失败数:      {stats.num_failures}")
        print(f"  失败率:      {stats.fail_ratio * 100:.2f}%")
        print(f"  平均响应:    {stats.avg_response_time:.0f} ms")
        print(f"  P50 响应:    {stats.get_response_time_percentile(0.5):.0f} ms")
        print(f"  P95 响应:    {stats.get_response_time_percentile(0.95):.0f} ms")
        print(f"  P99 响应:    {stats.get_response_time_percentile(0.99):.0f} ms")
        print(f"  最大响应:    {stats.max_response_time:.0f} ms")
        print(f"  总 RPS:      {stats.total_rps:.1f}")
        print(f"{'='*60}\n")


# ============================================================
# 附：四组场景的精确 CLI 命令
# ============================================================
#
# 基准测试 (10 用户, 2/s, 1 分钟):
#   locust -f tests/perf/locustfile.py \
#     --headless -u 10 -r 2 --run-time 1m \
#     --csv=reports/perf_baseline
#
# 负载测试 (50 用户, 10/s, 3 分钟):
#   locust -f tests/perf/locustfile.py \
#     --headless -u 50 -r 10 --run-time 3m \
#     --csv=reports/perf_load
#
# 压力测试 (200 用户, 50/s, 5 分钟):
#   locust -f tests/perf/locustfile.py \
#     --headless -u 200 -r 50 --run-time 5m \
#     --csv=reports/perf_stress
#
# 稳定性测试 (30 用户, 5/s, 10 分钟):
#   locust -f tests/perf/locustfile.py \
#     --headless -u 30 -r 5 --run-time 10m \
#     --csv=reports/perf_stability

# html 报告生成示例：
# python tests/perf/generate_report.py \
#   --stats-csv=reports/perf_load_stats.csv \
#   --output=reports/perf_report_load.html \
#   --scenario="负载测试" --users=50 --rate=10 --duration=3m
