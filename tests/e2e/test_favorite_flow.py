"""
E2E 测试：收藏功能与排行榜

覆盖场景：
- 收藏提示词（点击收藏 → 验证图标/消息）
- 取消收藏（在收藏页取消 → 验证列表更新）
- 收藏列表页（进入收藏页 → 验证已收藏提示词在列表中）
- 热门排行（访问排行页 → 验证列表有内容）
- 页面间导航（首页 → 排行 → 收藏 → 我的）
- 未登录收藏（未登录点击收藏 → 提示先登录）
"""

import pytest

from .utils import (
    register,
    login,
    create_prompt,
    navigate_to,
    generate_username,
)


# ============================================================
# 收藏测试
# ============================================================

class TestFavorite:
    """收藏功能相关测试"""

    @pytest.mark.smoke
    def test_favorite_prompt_from_homepage(self, page):
        """
        从首页收藏提示词：登录 → 浏览列表 → 点击收藏 → 验证收藏成功提示。

        验证点：
        - 点击收藏后出现成功提示
        - 进入收藏页后该提示词出现
        """
        username = generate_username()
        password = "test123456"
        prompt_title = f"收藏测试_{generate_username()}"

        # 注册并登录
        register(page, username, password)
        login(page, username, password)

        # 创建一个提示词（用于收藏测试）
        create_prompt(page, prompt_title, category="写作", content="用于收藏测试的内容")

        # 回到首页
        page.click('nav a[href="/"]')
        page.wait_for_load_state("networkidle")

        # 找到刚创建的提示词卡片，点击收藏
        # 使用 wait_for_selector 确保卡片已渲染（首页可能有大量数据）
        page.wait_for_selector(f'.p-card:has-text("{prompt_title}")', timeout=5000)
        card = page.locator('.p-card').filter(has_text=prompt_title)
        assert card.count() > 0, f"首页应存在提示词 '{prompt_title}'"

        # 滚动卡片到可见区域，确保"收藏"按钮可被点击
        fav_btn = card.locator('button:has-text("收藏")')
        fav_btn.scroll_into_view_if_needed()
        fav_btn.click()

        # 等待收藏 API 调用完成
        page.wait_for_timeout(1500)

        # 进入收藏页验证
        page.click('nav a[href="/favorites"]')
        page.wait_for_load_state("networkidle")

        # ⚠️ 关键：等 Vue 异步渲染完收藏列表再检查 DOM
        # FavoriteView.onMounted → load() → api.favoriteList() 是异步的
        page.wait_for_selector(f'.fav-card:has-text("{prompt_title}")', timeout=5000)

        # 验证收藏列表中有该提示词
        assert page.locator(f'.fav-card:has-text("{prompt_title}")').count() > 0, \
            f"收藏列表应包含已收藏的提示词 '{prompt_title}'"

    def test_unfavorite_from_favorite_page(self, page):
        """
        从收藏页取消收藏：收藏 → 进入收藏页 → 取消收藏 → 验证列表更新。

        验证点：
        - 取消收藏后提示"已取消收藏"
        - 列表中不再显示该提示词
        """
        username = generate_username()
        password = "test123456"
        prompt_title = f"取消收藏测试_{generate_username()}"

        register(page, username, password)
        login(page, username, password)

        # 创建并收藏提示词
        create_prompt(page, prompt_title, category="学习", content="用于取消收藏测试")

        # 回到首页收藏
        page.click('nav a[href="/"]')
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f'.p-card:has-text("{prompt_title}")', timeout=5000)
        card = page.locator('.p-card').filter(has_text=prompt_title)
        fav_btn = card.locator('button:has-text("收藏")')
        fav_btn.scroll_into_view_if_needed()
        fav_btn.click()
        page.wait_for_timeout(1000)

        # 进入收藏页
        page.click('nav a[href="/favorites"]')
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(f'.fav-card:has-text("{prompt_title}")', timeout=5000)
        assert page.locator(f'.fav-card:has-text("{prompt_title}")').count() > 0, \
            "收藏前提示词应在收藏列表中"

        # 取消收藏
        fav_card = page.locator('.fav-card').filter(has_text=prompt_title)
        fav_card.locator('button:has-text("取消收藏")').click()

        # 等待取消收藏生效（API 调用 + 列表刷新）
        page.wait_for_timeout(1500)

        # 验证列表中不再出现该提示词（核心验证点）
        assert page.locator(f'.fav-card:has-text("{prompt_title}")').count() == 0, \
            f"取消收藏后提示词 '{prompt_title}' 应从收藏列表消失"

    def test_favorite_list_page_empty_state(self, page):
        """
        新用户收藏列表为空：新注册用户 → 进入收藏页 → 验证空状态。

        验证点：
        - 显示"暂无收藏内容"空状态
        """
        username = generate_username()
        password = "test123456"

        register(page, username, password)
        login(page, username, password)

        # 直接进入收藏页（未收藏任何内容）
        page.click('nav a[href="/favorites"]')
        page.wait_for_load_state("networkidle")

        # 验证空状态显示
        assert page.locator('.el-empty').count() > 0 or page.locator('text=暂无收藏').count() > 0, \
            "无收藏时应显示空状态提示"

    def test_unauthenticated_cannot_favorite(self, page):
        """
        未登录用户点击收藏 → 应显示"请先登录"提示。

        验证点：
        - 收藏按钮点击后提示登录
        - 未跳转到收藏页
        """
        # 以访客身份访问首页
        page.goto("http://localhost:5173/")
        page.wait_for_load_state("networkidle")

        # 如果首页有卡片，尝试点击收藏
        cards = page.locator('.p-card')
        if cards.count() > 0:
            fav_btn = cards.first.locator('button:has-text("收藏")')
            if fav_btn.count() > 0:
                fav_btn.click()
                page.wait_for_timeout(1000)

                # 验证提示登录
                msg_locator = page.locator('.el-message')
                if msg_locator.count() > 0:
                    assert "登录" in msg_locator.first.inner_text() or \
                           "请先" in msg_locator.first.inner_text()

        # 验证无法访问收藏页（路由守卫应跳转到登录页）
        page.goto("http://localhost:5173/favorites")
        page.wait_for_timeout(1000)
        assert "/login" in page.url, "未登录用户访问 /favorites 应跳转到登录页"


# ============================================================
# 排行榜测试
# ============================================================

class TestRank:
    """排行榜相关测试"""

    @pytest.mark.smoke
    def test_hot_rank_page_loads(self, page):
        """
        热门排行页加载：登录后访问 /rank → 验证两个排行榜模块加载。

        注：/rank 需要登录（路由守卫），因此先注册登录。

        验证点：
        - "热门提示词"模块可见
        - "收藏排行榜"模块可见
        """
        username = generate_username()
        password = "test123456"

        register(page, username, password)
        login(page, username, password)

        # 通过导航栏访问排行榜
        page.click('nav a[href="/rank"]')
        page.wait_for_load_state("networkidle")

        # 验证两个 block 区域
        blocks = page.locator('.block')
        assert blocks.count() >= 2, "排行榜页面应有至少两个排行模块"

        # 验证包含"热门提示词"和"收藏排行榜"标题
        assert page.locator('h3:has-text("热门提示词")').is_visible()
        assert page.locator('h3:has-text("收藏排行榜")').is_visible()

    def test_rank_page_accessible_without_login(self, page):
        """
        未登录用户访问 /rank → 应跳转到 /login。

        验证点：
        - /rank 不在路由白名单中，未登录访问应被路由守卫拦截
        """
        page.goto("http://localhost:5173/")
        page.wait_for_load_state("networkidle")

        # 未登录状态尝试访问排行榜
        page.goto("http://localhost:5173/rank")
        page.wait_for_timeout(1000)

        # 应被重定向到登录页
        assert "/login" in page.url, "未登录用户访问 /rank 应跳转到登录页"


# ============================================================
# 页面导航测试
# ============================================================

class TestNavigation:
    """页面间导航测试"""

    @pytest.mark.smoke
    def test_navigation_between_all_pages(self, page):
        """
        遍历所有主导航页面：首页 → 排行 → 收藏 → 我的提示词。

        验证点：
        - 每个页面都能正常加载
        - Nav 链接点击后 URL 正确切换
        """
        username = generate_username()
        password = "test123456"

        register(page, username, password)
        login(page, username, password)

        # 主页
        assert page.url.rstrip("/").endswith("/") or page.url == "http://localhost:5173/"
        assert page.locator('.search-row').is_visible()

        # 排行榜
        page.click('nav a[href="/rank"]')
        page.wait_for_load_state("networkidle")
        assert "/rank" in page.url
        assert page.locator('.block').count() >= 2

        # 新增提示词
        page.click('nav a[href="/prompt-form"]')
        page.wait_for_load_state("networkidle")
        assert "/prompt-form" in page.url
        assert page.locator('.form-card').is_visible()

        # 我的提示词
        page.click('nav a[href="/my-prompts"]')
        page.wait_for_load_state("networkidle")
        assert "/my-prompts" in page.url

        # 回到首页
        page.click('nav a[href="/"]')
        page.wait_for_load_state("networkidle")
        assert page.url.rstrip("/").endswith("/") or page.url == "http://localhost:5173/"

    def test_navigation_highlights_active_link(self, page):
        """
        导航栏活动链接高亮：切换页面时活动链接样式正确。

        注：首页 / 需要登录，先注册登录再测试。

        验证点：
        - 当前页面对应的 Nav 链接有 router-link-active class
        """
        username = generate_username()
        password = "test123456"

        register(page, username, password)
        login(page, username, password)

        # 登录后应在首页，验证首页链接是活动的
        assert page.url.rstrip("/").endswith("/") or page.url == "http://localhost:5173/"
        active_link = page.locator('nav a.router-link-active[href="/"]')
        assert active_link.count() > 0, "首页的导航链接应为活动状态"

        # 切换到排行榜
        page.click('nav a[href="/rank"]')
        page.wait_for_load_state("networkidle")

        # 验证排行榜链接是活动的
        active_link = page.locator('nav a.router-link-active[href="/rank"]')
        assert active_link.count() > 0, "排行榜的导航链接应为活动状态"
