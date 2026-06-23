"""
E2E 测试全局 Fixture（Playwright）

提供的能力：
- FRONTEND_URL：前端开发服务器地址
- browser：Chromium/Firefox/WebKit 浏览器实例
- context：浏览器上下文（自动清理 Cookie/Storage，
  自定义 viewport=1280x720，locale=zh-CN）
- page：新页面（自动关闭）
- authenticated_page：已登录的页面（含 token）

多浏览器支持：
  pytest tests/e2e/ --browser chromium --browser firefox --browser webkit

失败自动截图（保存在 tests/reports/e2e_screenshots/）。
"""

from pathlib import Path

import pytest
from playwright.sync_api import BrowserContext, Page

from .utils import generate_username  # noqa: F401 — 供测试文件使用


# ============================================================
# 基础配置
# ============================================================

FRONTEND_URL = "http://localhost:5173"
BACKEND_URL = "http://localhost:8080"

# 截图保存目录
# resolve() 获取当前文件绝对路径，parent.parent 定位到项目根目录，再进入 reports/e2e_screenshots
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "reports" / "e2e_screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# pytest-playwright 配置 Fixtures
# ============================================================

@pytest.fixture(scope="session")
def base_url() -> str:
    """前端根地址"""
    return FRONTEND_URL


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """
    自定义浏览器上下文启动参数。

    通过 pytest-playwright 的 browser_context_args fixture 覆盖，
    设置统一的 viewport 和 locale，模拟真实用户环境。
    """
    return {
        **browser_context_args,     # ** 字典解包
        "viewport": {"width": 1280, "height": 720},
        "locale": "zh-CN",
        # 录制 trace 便于调试（仅在调试时启用）
        # "record_video_dir": str(SCREENSHOT_DIR / "videos"),
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict) -> dict:
    """
    自定义浏览器启动参数。

    关闭 Chrome 的自动化检测标志，避免被某些网站拦截。
    headless 模式通过 pytest-playwright 的 --headed 参数控制。
    """
    return {
        **browser_type_launch_args,
        "args": [
            "--disable-blink-features=AutomationControlled",
        ],
    }


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    """
    每个测试函数独立的浏览器页面。

    通过 pytest-playwright 的 context fixture 创建，
    测试结束后自动关闭。
    """
    page = context.new_page()
    # 设置默认超时
    page.set_default_timeout(10000)
    yield page
    page.close()


@pytest.fixture(scope="function")
def authenticated_page(page: Page) -> Page:
    """
    返回一个已完成登录的页面。

    步骤：
    1. 注册新用户（通过 API 或 UI）
    2. 登录
    3. 返回已登录的 page 对象

    使用此 fixture 的测试可以直接从首页开始操作，
    无需重复编写登录逻辑。
    """
    username = generate_username()
    password = "test123456"

    # 通过前端 UI 完成注册 + 登录
    page.goto(f"{FRONTEND_URL}/register")
    page.wait_for_load_state("networkidle")

    # 填写注册表单
    page.fill('input[placeholder="用户名"]', username)
    page.fill('input[placeholder="密码"]', password)
    page.click('button:has-text("注册")')

    # 等待跳转到登录页
    page.wait_for_url(f"{FRONTEND_URL}/login", timeout=5000)

    # 登录
    page.fill('input[placeholder="用户名"]', username)
    page.fill('input[placeholder="密码"]', password)
    page.click('.login-btn')

    # 等待跳转到首页（已登录状态）
    page.wait_for_url(f"{FRONTEND_URL}/", timeout=5000)
    page.wait_for_load_state("networkidle")

    return page


# ============================================================
# 失败自动截图 Hooks（Day 5）
# ============================================================
# tryfirst=True -> 多个 Hook 存在时，优先实现这个

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    pytest hook：在测试执行后生成报告。

    如果测试失败（call 阶段），自动截取 page 的屏幕截图，
    保存到 tests/reports/e2e_screenshots/ 目录。
    文件名格式：{test_name}_{browser}.png
    """
    outcome = yield
    report = outcome.get_result()

    # 只在测试执行阶段失败时截图
    if report.when == "call" and report.failed:
        # 从 fixture 中获取 page 对象
        page = item.funcargs.get("page") or item.funcargs.get("authenticated_page")
        if page is not None:
            try:
                test_name = item.nodeid.replace("::", "_").replace("/", "_")
                safe_name = test_name[:100]  # 截断过长文件名
                # 标记浏览器类型
                browser = item.funcargs.get("browser_name", "unknown")
                screenshot_path = SCREENSHOT_DIR / f"{safe_name}_{browser}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"[E2E] 失败截图已保存: {screenshot_path}")
            except Exception as exc:
                print(f"[E2E] 截图失败: {exc}")


def pytest_configure(config):
    """注册自定义 e2e marker（与 pytest.ini 中的声明互补）"""
    config.addinivalue_line(
        "markers", "e2e: E2E 端到端测试标记"
    )
