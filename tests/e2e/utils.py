"""
E2E 测试工具函数

这个文件专门存放 E2E 测试中常用的页面操作函数，通过封装重复步骤来减少代码冗余。
它借鉴了 Page Object 模式的思想。
但为了保持简单，没有专门创建页面类，而是直接使用普通函数来实现可复用的页面操作。
"""

import uuid

from playwright.sync_api import Page, expect


# ============================================================
# 测试数据生成
# ============================================================

def generate_username() -> str:
    """生成唯一的测试用户名，避免数据库冲突"""
    return f"e2e_{uuid.uuid4().hex[:8]}"


# ============================================================
# 导航辅助
# ============================================================

def navigate_to(page: Page, path: str) -> None:
    """导航到指定页面并等待加载完成"""
    page.goto(f"http://localhost:5173{path}")
    page.wait_for_load_state("networkidle")


def go_home(page: Page) -> None:
    """通过导航栏返回首页"""
    page.click('nav a[href="/"]')


# ============================================================
# 登录 / 注册
# ============================================================

def register(page: Page, username: str, password: str) -> None:
    """
    通过 UI 完成注册。
    预期：注册成功后跳转到 /login。
    """
    page.goto("http://localhost:5173/register")
    page.wait_for_load_state("networkidle")
    page.fill('input[placeholder="用户名"]', username)
    page.fill('input[placeholder="密码"]', password)
    page.click('button:has-text("注册")')
    # 等待跳转到登录页
    page.wait_for_url("http://localhost:5173/login", timeout=5000)
    page.wait_for_load_state("networkidle")


def login(page: Page, username: str, password: str) -> None:
    """
    通过 UI 完成登录。
    预期：登录成功后跳转到首页 /，localStorage 存入 token。

    注意：调用前需要确保当前用户在数据库中存在。
    """
    page.goto("http://localhost:5173/login")
    page.wait_for_load_state("networkidle")
    page.fill('input[placeholder="用户名"]', username)
    page.fill('input[placeholder="密码"]', password)
    page.click('.login-btn')
    # 等待跳转到首页
    page.wait_for_url("http://localhost:5173/", timeout=5000)
    page.wait_for_load_state("networkidle")


def logout(page: Page) -> None:
    """点击退出登录按钮"""
    page.click('.logout-btn')
    page.wait_for_url("http://localhost:5173/login", timeout=5000)


def is_logged_in(page: Page) -> bool:
    """检查当前是否处于已登录状态（导航栏有退出按钮）"""
    return page.locator('.logout-btn').is_visible()


def get_token_from_storage(page: Page) -> str | None:
    """从 localStorage 中读取 JWT token"""
    return page.evaluate("() => localStorage.getItem('token')")


# ============================================================
# 提示词操作
# ============================================================

def create_prompt(
    page: Page,
    title: str,
    category: str = "写作",
    content: str = "这是一个 E2E 测试创建的提示词内容。",
) -> None:
    """
    通过 UI 创建一个新提示词。

    前提：用户已登录，当前在任意页面。
    操作：导航到新增页 → 填写表单 → 点击上传 → 验证成功。
    """
    # 导航到新增提示词页面
    page.click('nav a[href="/prompt-form"]')
    page.wait_for_url("http://localhost:5173/prompt-form", timeout=5000)
    page.wait_for_load_state("networkidle")

    # 填写表单
    # 标题：el-form-item label="标题" → 内部 input.el-input__inner
    page.locator('.el-form-item:has-text("标题")').locator('input.el-input__inner').clear()
    page.locator('.el-form-item:has-text("标题")').locator('input.el-input__inner').fill(title)

    # 选择分类（Element Plus 的 el-select 分两步：先点开下拉，再选选项）
    page.locator('.el-form-item').filter(has_text="分类").locator('.el-select').click()    # ① 点击触发框，展开下拉列表
    page.locator('.el-select-dropdown__item').filter(has_text=category).click()             # ② 下拉菜单被 teleport 到 <body>，需从全局定位选项

    # 填写内容
    page.locator('.el-form-item').filter(has_text="内容").locator('textarea').fill(content)

    # 点击上传
    page.click('button:has-text("上传")')

    # 等待跳转到我的提示词页面
    page.wait_for_url("http://localhost:5173/my-prompts", timeout=5000)
    page.wait_for_load_state("networkidle")


def search_prompt(page: Page, keyword: str) -> None:
    """在首页搜索框输入关键词并搜索"""
    search_input = page.locator('.search-row input')
    search_input.clear()
    search_input.fill(keyword)
    page.click('.search-row button:has-text("搜索")')
    page.wait_for_load_state("networkidle")


def filter_by_category(page: Page, category: str) -> None:
    """在首页点击分类 Tab 进行筛选"""
    page.click(f'.el-tabs .el-tabs__item:has-text("{category}")')
    page.wait_for_load_state("networkidle")


def favorite_prompt_from_card(page: Page, prompt_title: str) -> None:
    """从首页提示词卡片中点击收藏按钮"""
    card = page.locator('.p-card').filter(has_text=prompt_title)
    card.locator('button:has-text("收藏")').click()
    # 等待 ElMessage 出现消失
    page.wait_for_timeout(500)


def unfavorite_prompt_from_list(page: Page, favorite_id_selector: str = ".fav-card") -> None:
    """在收藏列表中取消收藏第一项"""
    page.locator(f'{favorite_id_selector} button:has-text("取消收藏")').first.click()
    page.wait_for_timeout(500)


def navigate_to_prompt_detail(page: Page, prompt_title: str) -> None:
    """从首页点击提示词卡片进入详情页"""
    card = page.locator('.p-card').filter(has_text=prompt_title)
    card.locator('button:has-text("详情")').click()
    page.wait_for_load_state("networkidle")


def delete_my_prompt(page: Page, prompt_title: str) -> None:
    """在"我的提示词"页面删除一个已发布的提示词"""
    page.goto("http://localhost:5173/my-prompts")
    page.wait_for_load_state("networkidle")
    row = page.locator('.row').filter(has_text=prompt_title)
    row.locator('button:has-text("删除")').click()
    page.wait_for_timeout(500)


# ============================================================
# 等待 & 断言辅助
# ============================================================

def wait_for_el_message(page: Page, text: str | None = None, timeout: int = 5000) -> None:
    """
    等待 Element Plus 消息出现。

    如果提供 text，则等待包含指定文本的消息。
    """
    if text:
        page.wait_for_selector(f'.el-message:has-text("{text}")', timeout=timeout)
    else:
        page.wait_for_selector('.el-message', timeout=timeout)
    # 等待消息动画
    page.wait_for_timeout(300)


def assert_on_page(page: Page, path: str) -> None:
    """断言当前 URL 匹配预期路径"""
    expect(page).to_have_url(f"http://localhost:5173{path}")


def assert_element_visible(page: Page, selector: str) -> None:
    """断言元素可见"""
    expect(page.locator(selector).first).to_be_visible()


def assert_element_text(page: Page, selector: str, text: str) -> None:
    """断言元素包含指定文本"""
    expect(page.locator(selector).first).to_contain_text(text)


def assert_el_message(page: Page, text: str) -> None:
    """断言 Element Plus 消息包含指定文本"""
    expect(page.locator('.el-message').first).to_contain_text(text)


def assert_no_element(page: Page, selector: str) -> None:
    """断言元素不存在于 DOM 中"""
    expect(page.locator(selector)).to_have_count(0)
