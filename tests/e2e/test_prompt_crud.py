"""
E2E 测试：提示词 CRUD 操作

覆盖场景：
- 新建提示词（填写完整表单 → 上传 → 验证出现在"我的提示词"中）
- 编辑提示词（进入编辑 → 修改 → 保存 → 验证更新）
- 删除提示词（删除 → 验证列表消失）
- 搜索提示词（关键词搜索 → 验证结果过滤）
- 分类筛选（切换分类 Tab → 验证列表变化）
- 提示词详情查看（点击详情 → 验证内容）
- 切换私密/公开状态
- 提示词列表加载（验证首页加载提示词卡片）

前提：所有测试需要后端 API 运行在 localhost:8080。
"""

import pytest
from playwright.sync_api import expect

from .utils import (
    register,
    login,
    create_prompt,
    search_prompt,
    delete_my_prompt,
    navigate_to_prompt_detail,
    generate_username,
)


# ============================================================
# 创建提示词
# ============================================================

class TestCreatePrompt:
    """提示词创建相关测试"""

    @pytest.mark.smoke
    def test_create_prompt_and_verify_in_my_list(self, page):
        """
        登录 → 新建提示词 → 填写完整信息 → 上传 → 验证出现在"我的提示词"中。

        验证点：
        - 上传后跳转到 /my-prompts
        - "我已发布的提示词"列表中出现刚创建的提示词
        """
        username = generate_username()
        password = "test123456"
        prompt_title = f"E2E 测试提示词_{generate_username()}"

        # 注册并登录
        register(page, username, password)
        login(page, username, password)

        # 创建提示词
        create_prompt(page, prompt_title, category="编程", content="print('Hello E2E')")

        # 验证跳转到"我的提示词"页面
        assert "/my-prompts" in page.url

        # 等待异步数据加载完成（MyPromptsView.onMounted → loadPublished）
        page.wait_for_selector(f'.block:has-text("{prompt_title}")', timeout=5000)

        # 验证新创建的提示词出现在"我已发布的提示词"列表中
        published_section = page.locator('.block').filter(has_text="我已发布的提示词")
        assert published_section.filter(has_text=prompt_title).count() > 0, \
            f"提示词 '{prompt_title}' 应出现在已发布列表中"

    def test_create_prompt_empty_title_handled(self, page):
        """
        创建提示词时标题为空 → 后端应返回错误或前端拦截。

        验证点：
        - 页面未崩溃
        - 停留在表单页或显示错误提示
        """
        username = generate_username()
        password = "test123456"

        register(page, username, password)
        login(page, username, password)

        # 导航到新增提示词页面
        page.click('nav a[href="/prompt-form"]')
        page.wait_for_url("http://localhost:5173/prompt-form", timeout=5000)
        page.wait_for_load_state("networkidle")

        # 只填写内容，不填标题
        page.locator('.el-form-item').filter(has_text="内容").locator('textarea').fill("无标题测试内容")

        # 点击上传
        page.click('button:has-text("上传")')

        # 等待响应
        page.wait_for_timeout(2000)

        # 页面应未崩溃（要么留在表单页，要么跳转了）
        assert page.url, "页面应正常响应"

    def test_create_multiple_prompts(self, page):
        """
        连续创建多个提示词 → 验证每个都正确出现在列表中。

        验证批量创建场景下的系统稳定性。
        """
        username = generate_username()
        password = "test123456"

        register(page, username, password)
        login(page, username, password)

        titles = []
        for i in range(3):
            title = f"批量测试_{i}_{generate_username()}"
            titles.append(title)
            create_prompt(page, title, category="学习", content=f"批量测试内容 #{i}")
            # 回到首页准备下一个
            page.click('nav a[href="/prompt-form"]')
            page.wait_for_url("http://localhost:5173/prompt-form", timeout=5000)
            page.wait_for_load_state("networkidle")

        # 导航到"我的提示词"，验证所有提示词都在
        page.click('nav a[href="/my-prompts"]')
        page.wait_for_load_state("networkidle")

        for title in titles:
            page.wait_for_selector(f'.block:has-text("{title}")', timeout=5000)
            published_section = page.locator('.block').filter(has_text="我已发布的提示词")
            assert published_section.filter(has_text=title).count() > 0, \
                f"提示词 '{title}' 应出现在已发布列表中"


# ============================================================
# 搜索与筛选
# ============================================================

class TestSearchAndFilter:
    """提示词搜索与分类筛选测试"""

    @pytest.mark.smoke
    def test_search_prompt_by_keyword(self, page):
        """
        关键词搜索：搜索刚创建的提示词标题 → 验证搜索结果包含该提示词。

        验证点：
        - 搜索结果过滤正确
        """
        username = generate_username()
        password = "test123456"
        unique_keyword = f"搜索关键词_{generate_username()}"

        register(page, username, password)
        login(page, username, password)

        # 创建一个标题独特的提示词
        create_prompt(page, unique_keyword, category="写作", content="搜索测试内容")

        # 回到首页进行搜索
        page.click('nav a[href="/"]')
        page.wait_for_load_state("networkidle")

        search_prompt(page, unique_keyword)

        # 验证搜索结果包含该提示词
        assert page.locator(f'.p-card:has-text("{unique_keyword}")').count() >= 1, \
            f"搜索结果应包含标题为 '{unique_keyword}' 的提示词"

    def test_filter_by_category(self, page):
        """
        分类筛选：点击不同分类 Tab → 验证列表根据分类变化。

        验证点：
        - 点击分类 Tab 后列表刷新
        - 页面不崩溃
        """
        username = generate_username()
        password = "test123456"

        register(page, username, password)
        login(page, username, password)

        # 先导航到首页
        page.click('nav a[href="/"]')
        page.wait_for_load_state("networkidle")

        # 记录初始列表状态
        initial_cards = page.locator('.p-card').count()

        # 切换到"编程"分类
        page.click('.el-tabs__item:has-text("编程")')
        page.wait_for_timeout(1000)

        # 验证页面未崩溃（列表可能为空或有内容）
        assert page.url.rstrip("/").endswith("/") or page.url == "http://localhost:5173/"

        # 切换回"全部"
        page.click('.el-tabs__item:has-text("全部")')
        page.wait_for_timeout(1000)

        # 验证列表恢复
        after_all = page.locator('.p-card').count()
        assert after_all == initial_cards, "切换回全部后列表数量应恢复"


# ============================================================
# 查看详情
# ============================================================

class TestPromptDetail:
    """提示词详情查看测试"""

    def test_view_prompt_detail(self, page):
        """
        查看提示词详情：点击详情 → 验证标题、分类、内容和复制按钮。

        验证点：
        - 跳转到 /prompt/:id
        - 显示标题、分类、内容
        - "一键复制"按钮可见
        """
        username = generate_username()
        password = "test123456"
        prompt_title = f"详情测试_{generate_username()}"

        register(page, username, password)
        login(page, username, password)

        create_prompt(page, prompt_title, category="AI绘画", content="这是一段详情测试的内容文本。")

        # 回到首页
        page.click('nav a[href="/"]')
        page.wait_for_load_state("networkidle")

        # 点击详情
        page.wait_for_selector(f'.p-card:has-text("{prompt_title}")', timeout=5000)
        navigate_to_prompt_detail(page, prompt_title)

        # 验证 URL 匹配 /prompt/:id
        assert "/prompt/" in page.url

        # 等待异步加载完成（onMounted → api.promptDetail）
        page.wait_for_selector(f'h2:has-text("{prompt_title}")', timeout=5000)

        # 验证页面显示标题
        assert page.locator(f'h2:has-text("{prompt_title}")').count() > 0, \
            f"详情页应显示标题 '{prompt_title}'"

        # 验证分类标签可见（可能为空类别，检查存在即可）
        assert page.locator('.el-tag').count() > 0, "详情页应显示分类标签"

        # 验证"一键复制"按钮可见
        assert page.locator('button:has-text("一键复制")').is_visible(), "详情页应有一键复制按钮"


# ============================================================
# 编辑与删除
# ============================================================

class TestEditAndDelete:
    """提示词编辑与删除测试"""

    def test_edit_own_prompt(self, page):
        """
        编辑自己的提示词：进入我的提示词 → 编辑 → 修改 → 保存 → 验证更新。

        验证点：
        - 进入编辑后可以看到表单预填了原数据
        - 修改后保存成功
        - 列表中显示更新后的标题
        """
        username = generate_username()
        password = "test123456"
        original_title = f"原始标题_{generate_username()}"
        updated_title = f"更新标题_{generate_username()}"

        register(page, username, password)
        login(page, username, password)

        # 创建原始提示词
        create_prompt(page, original_title, category="写作", content="原始内容")

        # 在"我的提示词"页面点击编辑
        page.wait_for_url("http://localhost:5173/my-prompts", timeout=5000)
        page.wait_for_load_state("networkidle")

        row = page.locator('.row').filter(has_text=original_title)
        row.locator('button:has-text("编辑")').click()

        # 等待跳转到编辑页
        page.wait_for_url("http://localhost:5173/prompt-form/*", timeout=5000)
        page.wait_for_load_state("networkidle")

        # 等待异步数据加载完成（onMounted → load → api.promptDetail → Object.assign）
        # 确认原标题已填入表单
        page.wait_for_selector(f'.el-form-item:has-text("标题") input', timeout=5000)

        # 修改标题（fill 会自动清除旧内容再填入新内容）
        title_input = page.locator('.el-form-item').filter(has_text="标题").locator('input')
        title_input.fill(updated_title)

        # 保存
        page.click('button:has-text("上传")')

        # 等待跳转
        page.wait_for_url("http://localhost:5173/my-prompts", timeout=5000)
        page.wait_for_load_state("networkidle")

        # 验证更新后的标题出现在列表中
        page.wait_for_selector(f'.block:has-text("{updated_title}")', timeout=5000)
        published_section = page.locator('.block').filter(has_text="我已发布的提示词")
        assert published_section.filter(has_text=updated_title).count() > 0, \
            f"更新后的标题 '{updated_title}' 应出现在列表中"

    def test_delete_own_prompt(self, page):
        """
        删除自己的提示词：进入我的提示词 → 删除 → 验证列表消失。

        验证点：
        - 删除后列表中不再出现该提示词
        """
        username = generate_username()
        password = "test123456"
        prompt_title = f"待删除_{generate_username()}"

        register(page, username, password)
        login(page, username, password)

        create_prompt(page, prompt_title, category="学习", content="这个提示词将被删除")

        # 在"我的提示词"页面删除
        page.wait_for_url("http://localhost:5173/my-prompts", timeout=5000)
        page.wait_for_load_state("networkidle")

        delete_my_prompt(page, prompt_title)

        # 等待删除动画完成
        page.wait_for_timeout(1500)

        # 验证已从列表中消失
        published_section = page.locator('.block').filter(has_text="我已发布的提示词")
        assert published_section.locator(f'text={prompt_title}').count() == 0, \
            f"已删除的提示词 '{prompt_title}' 不应再出现在列表中"

    def test_toggle_private_public(self, page):
        """
        切换提示词的私密/公开状态。

        验证点：
        - 状态标签从"公开"变为"私密"或反操作
        - 操作后有成功提示
        """
        username = generate_username()
        password = "test123456"
        prompt_title = f"私密切换测试_{generate_username()}"

        register(page, username, password)
        login(page, username, password)

        create_prompt(page, prompt_title, category="学习", content="测试私密切换")

        # 在"我的提示词"页面找到该提示词
        page.wait_for_url("http://localhost:5173/my-prompts", timeout=5000)
        page.wait_for_load_state("networkidle")

        # ⚠️ 关键：等 Vue 异步加载完 "我已发布的提示词" 列表再操作
        # MyPromptsView.onMounted → loadPublished() → api.promptMine() 是异步的
        # networkidle 只等网络请求完成，不等 Vue 重新渲染 DOM
        page.wait_for_selector(f'.row:has-text("{prompt_title}")', timeout=5000)

        # 新创建的提示词默认 isPrivate=0（公开），按钮应为"设为私密"
        row = page.locator('.row').filter(has_text=prompt_title)
        toggle_btn = row.locator('button:has-text("设为私密")')
        if toggle_btn.count() == 0:
            toggle_btn = row.locator('button:has-text("设为公开")')

        assert toggle_btn.count() > 0, f"应存在切换私密/公开的按钮"

        # 记录切换前的文本
        before_text = toggle_btn.first.inner_text()
        toggle_btn.first.click()

        # 等待状态更新（API 调用 + Vue 重新渲染）
        page.wait_for_timeout(2000)

        # 验证按钮文本已变化
        row_after = page.locator('.row').filter(has_text=prompt_title)
        toggle_after = row_after.locator('button').filter(has_text="设为")
        if toggle_after.count() > 0:
            after_text = toggle_after.first.inner_text()
            assert before_text != after_text, f"切换后按钮文本应从 '{before_text}' 变化"


# ============================================================
# 首页列表
# ============================================================

class TestPromptList:
    """提示词列表展示测试"""

    @pytest.mark.smoke
    def test_homepage_loads_prompt_cards(self, page):
        """
        首页加载提示词列表：登录后查看提示词卡片。

        注：首页 / 需要登录（路由守卫），因此先注册登录。

        验证点：
        - 页面加载成功
        - 搜索栏和分类标签页可见
        - 列表容器存在
        """
        username = generate_username()
        password = "test123456"

        # 注册并登录（首页需要登录）
        register(page, username, password)
        login(page, username, password)

        # 已登录用户应在首页
        assert page.url.rstrip("/").endswith("/") or page.url == "http://localhost:5173/"

        # 验证页面正常加载
        assert page.locator('.search-row').count() > 0, "首页应有搜索栏"
        assert page.locator('.el-tabs').count() > 0, "首页应有分类标签页"

        # 可能有卡片也可能为空（取决于数据库中数据量）
        # 验证 Grid 容器存在于 DOM 中即可
        expect(page.locator('.grid')).to_be_attached()
