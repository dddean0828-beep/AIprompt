"""
提示词模块接口测试

覆盖接口：
- POST   /api/prompt/add             新增提示词
- GET    /api/prompt/list            列表查询
- GET    /api/prompt/detail/{id}     查看详情
- PUT    /api/prompt/update          修改
- DELETE /api/prompt/delete/{id}     删除
- PUT    /api/prompt/toggle-private/{id}  切换私密
- GET    /api/prompt/mine            我的提示词

核心测试重点：权限边界（越权修改/删除/查看私密）
"""

import pytest
from .conftest import BASE_URL, generate_username


# ============================================================
# 辅助函数
# ============================================================

def create_prompt(session, token: str, title: str = "测试提示词",
                  content: str = "这是一条测试提示词的内容。",
                  category: str = "测试分类",
                  is_private: int = 0) -> dict:
    """
    创建一个提示词。

    add 接口只返回 Result<Boolean>，不返回 Prompt 对象，
    因此调用后需通过 mine 接口查找确认创建成功。

    Returns:
        dict: {"title": ..., "content": ..., "category": ..., "isPrivate": ...}
    """
    resp = session.post(f"{BASE_URL}/api/prompt/add", json={
        "title": title,
        "content": content,
        "category": category,
        "isPrivate": is_private,
    }, headers={"Authorization": token})
    data = resp.json()
    # assert 条件, "错误信息"，如果 code == 200，不会打印创建提示词失败
    assert data["code"] == 200, f"创建提示词失败: {data}"
    return {"title": title, "content": content, "category": category, "isPrivate": is_private}


def get_my_prompt_id(session, token: str, title: str = None) -> int | None:
    """
    从 mine 接口获取当前用户创建的提示词 ID。

    - 指定 title：精确匹配标题
    - 不指定 title：返回最近创建的一条（mine 按 createdAt DESC 排序）

    用 mine（而非 list）确保拿到的一定是自己创建的。
    """
    resp = session.get(f"{BASE_URL}/api/prompt/mine",
                       headers={"Authorization": token})
    items = resp.json()["data"]
    if not items:
        return None
    if title:
        for item in items:
            if item["title"] == title:
                return item["id"]
        return None
    # 没有指定 title，返回最近创建的一条
    return items[0]["id"]


# ============================================================
# 新增提示词
# ============================================================

class TestAddPrompt:
    """POST /api/prompt/add"""

    def test_add_prompt_success(self, session, auth_token):
        """正常新增提示词"""
        resp = session.post(f"{BASE_URL}/api/prompt/add", json={
            "title": "测试标题",
            "content": "测试内容",
            "category": "通用",
        }, headers={"Authorization": auth_token})
        assert resp.json()["code"] == 200
        assert resp.json()["data"] is True

    def test_add_prompt_without_token_blocked_by_interceptor(self, session):
        """
        无 token 添加：AuthInterceptor 直接拦截返回 401。

        注意：因为是全局拦截器，请求不会到达 Controller。
        """
        resp = session.post(f"{BASE_URL}/api/prompt/add", json={
            "title": "越权测试",
            "content": "不应成功",
        })
        assert resp.status_code == 401

    def test_add_prompt_with_private_flag(self, session, auth_token):
        """新增私密提示词（isPrivate=1）"""
        resp = session.post(f"{BASE_URL}/api/prompt/add", json={
            "title": "私密提示词",
            "content": "只有我能看到",
            "category": "私密",
            "isPrivate": 1,
        }, headers={"Authorization": auth_token})
        assert resp.json()["code"] == 200

    @pytest.mark.parametrize("title, content, category, desc", [
        ("", "正常内容", "通用", "空标题"),
        ("正常标题", "", "通用", "空内容"),
        ("正常标题", "正常内容", "", "空分类"),
        ("a" * 200, "正常内容", "通用", "超长标题"),
    ])
    def test_add_prompt_boundary(self, session, auth_token, title, content, category, desc):
        """边界值测试：接口应正常响应不崩溃"""
        resp = session.post(f"{BASE_URL}/api/prompt/add", json={
            "title": title,
            "content": content,
            "category": category,
        }, headers={"Authorization": auth_token})
        data = resp.json()
        assert "code" in data, f"{desc}: 响应缺少 code 字段: {resp.text[:200]}"


# ============================================================
# 列表查询
# ============================================================

class TestListPrompts:
    """GET /api/prompt/list"""

    def test_list_all_with_auth(self, session, auth_token):
        """携带 token 查询列表（包含自己的私密 + 所有公开）"""
        resp = session.get(f"{BASE_URL}/api/prompt/list",
                           headers={"Authorization": auth_token})
        assert resp.json()["code"] == 200
        assert isinstance(resp.json()["data"], list)

    def test_list_filter_by_category(self, session, auth_token):
        """按分类筛选"""
        # 创建一条特定分类的提示词
        create_prompt(session, auth_token, title="分类测试", category="Java")
        resp = session.get(f"{BASE_URL}/api/prompt/list",
                           headers={"Authorization": auth_token},
                           params={"category": "Java"})
        data = resp.json()
        assert data["code"] == 200
        for item in data["data"]:
            assert item["category"] == "Java"

    def test_list_filter_by_keyword(self, session, auth_token):
        """按关键词搜索标题"""
        unique_keyword = f"关键词_{generate_username()}"
        create_prompt(session, auth_token, title=unique_keyword)
        resp = session.get(f"{BASE_URL}/api/prompt/list",
                           headers={"Authorization": auth_token},
                           params={"keyword": unique_keyword})
        data = resp.json()
        assert data["code"] == 200
        assert len(data["data"]) >= 1
        assert unique_keyword in data["data"][0]["title"]

    def test_private_not_visible_to_other_user(self, session, test_user, other_user):
        """
        权限测试核心：用户A创建的私密提示词，用户B在列表中看不到。
        """
        # 用户A创建私密提示词
        create_prompt(session, test_user["token"], title="A的私密",
                      is_private=1)
        # 用户B查询列表
        resp = session.get(f"{BASE_URL}/api/prompt/list",
                           headers={"Authorization": other_user["token"]})
        items = resp.json()["data"]
        # 用户B不应该看到用户A的私密提示词
        titles = [item["title"] for item in items]
        assert "A的私密" not in titles, \
            f"越权泄露：用户B看到了用户A的私密提示词！看到 {titles}"


# ============================================================
# 查看详情
# ============================================================

class TestDetailPrompt:
    """GET /api/prompt/detail/{id}"""

    def test_detail_own_prompt(self, session, test_user):
        """查看自己创建的提示词详情"""
        create_prompt(session, test_user["token"], title="我的提示词")
        pid = get_my_prompt_id(session, test_user["token"])
        assert pid is not None, "无法获取提示词 ID"

        resp = session.get(f"{BASE_URL}/api/prompt/detail/{pid}",
                           headers={"Authorization": test_user["token"]})
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["title"] == "我的提示词"

    def test_detail_others_private_should_be_null(self, session, test_user, other_user):
        """
        权限测试核心：查看他人私密提示词应返回 data=null。
        """
        # 用户A创建私密提示词
        create_prompt(session, test_user["token"], title="A的秘密",
                      is_private=1)
        pid = get_my_prompt_id(session, test_user["token"])
        # 用户B查看详情
        resp = session.get(f"{BASE_URL}/api/prompt/detail/{pid}",
                           headers={"Authorization": other_user["token"]})
        data = resp.json()
        assert data["code"] == 200
        assert data["data"] is None, \
            f"越权访问：用户B看到了用户A的私密提示词详情！data={data['data']}"

    def test_detail_others_public_visible(self, session, test_user, other_user):
        """查看他人公开提示词：允许"""
        create_prompt(session, test_user["token"], title="A的公开",
                      is_private=0)
        pid = get_my_prompt_id(session, test_user["token"])
        resp = session.get(f"{BASE_URL}/api/prompt/detail/{pid}",
                           headers={"Authorization": other_user["token"]})
        assert resp.json()["data"] is not None

    def test_detail_nonexistent_id(self, session, auth_token):
        """查看不存在的 ID 返回 data=null"""
        resp = session.get(f"{BASE_URL}/api/prompt/detail/9999999",
                           headers={"Authorization": auth_token})
        data = resp.json()
        assert data["code"] == 200
        assert data["data"] is None


# ============================================================
# 修改提示词
# ============================================================

class TestUpdatePrompt:
    """PUT /api/prompt/update"""

    def test_update_own_prompt(self, session, test_user):
        """修改自己创建的提示词"""
        create_prompt(session, test_user["token"], title="原始标题")
        pid = get_my_prompt_id(session, test_user["token"])

        resp = session.put(f"{BASE_URL}/api/prompt/update", json={
            "id": pid,
            "title": "修改后标题",
            "content": "修改后内容",
            "category": "新分类",
        }, headers={"Authorization": test_user["token"]})
        assert resp.json()["data"] is True, f"修改失败: {resp.json()}"

        # 验证修改生效
        detail = session.get(f"{BASE_URL}/api/prompt/detail/{pid}",
                             headers={"Authorization": test_user["token"]})
        assert detail.json()["data"]["title"] == "修改后标题"

    def test_update_others_prompt_rejected(self, session, test_user, other_user):
        """
        权限测试核心：越权修改应被拒绝（返回 data=false）。
        """
        create_prompt(session, test_user["token"], title="A的提示词")
        pid = get_my_prompt_id(session, test_user["token"])

        resp = session.put(f"{BASE_URL}/api/prompt/update", json={
            "id": pid,
            "title": "被B改了",
            "content": "越权修改",
            "category": "恶意",
        }, headers={"Authorization": other_user["token"]})
        assert resp.json()["data"] is False, \
            f"越权修改应返回 false，实际 {resp.json()}"

    def test_update_nonexistent_prompt(self, session, auth_token):
        """修改不存在的提示词返回 data=false"""
        resp = session.put(f"{BASE_URL}/api/prompt/update", json={
            "id": 9999999,
            "title": "幽灵",
            "content": "不存在",
            "category": "无",
        }, headers={"Authorization": auth_token})
        assert resp.json()["data"] is False


# ============================================================
# 删除提示词
# ============================================================

class TestDeletePrompt:
    """DELETE /api/prompt/delete/{id}"""

    def test_delete_own_prompt(self, session, test_user):
        """删除自己创建的提示词"""
        create_prompt(session, test_user["token"])
        pid = get_my_prompt_id(session, test_user["token"])

        resp = session.delete(f"{BASE_URL}/api/prompt/delete/{pid}",
                              headers={"Authorization": test_user["token"]})
        assert resp.json()["data"] is True

    def test_delete_others_prompt_rejected(self, session, test_user, other_user):
        """
        权限测试核心：越权删除应被拒绝（返回 data=false）。
        """
        create_prompt(session, test_user["token"], title="A的不可删")
        pid = get_my_prompt_id(session, test_user["token"])

        resp = session.delete(f"{BASE_URL}/api/prompt/delete/{pid}",
                              headers={"Authorization": other_user["token"]})
        assert resp.json()["data"] is False, \
            f"越权删除应返回 false，实际 {resp.json()}"


# ============================================================
# 切换私密状态
# ============================================================

class TestTogglePrivate:
    """PUT /api/prompt/toggle-private/{id}"""

    def test_toggle_own_to_private(self, session, test_user):
        """将自己的公开提示词设为私密"""
        create_prompt(session, test_user["token"], is_private=0)
        pid = get_my_prompt_id(session, test_user["token"])

        resp = session.put(
            f"{BASE_URL}/api/prompt/toggle-private/{pid}",
            params={"isPrivate": 1},
            headers={"Authorization": test_user["token"]},
        )
        assert resp.json()["data"] is True

    def test_toggle_others_private_rejected(self, session, test_user, other_user):
        """
        权限测试核心：越权切换他人提示词的私密状态应被拒绝。
        """
        create_prompt(session, test_user["token"], is_private=0)
        pid = get_my_prompt_id(session, test_user["token"])

        resp = session.put(
            f"{BASE_URL}/api/prompt/toggle-private/{pid}",
            params={"isPrivate": 1},
            headers={"Authorization": other_user["token"]},
        )
        assert resp.json()["data"] is False


# ============================================================
# 我的提示词
# ============================================================

class TestMineList:
    """GET /api/prompt/mine"""

    def test_mine_only_contains_own_prompts(self, session, test_user, other_user):
        """
        用户A创建提示词，用户B的 mine 列表不应包含它。
        """
        create_prompt(session, test_user["token"], title="A的独享")
        create_prompt(session, other_user["token"], title="B的独享")

        resp = session.get(f"{BASE_URL}/api/prompt/mine",
                           headers={"Authorization": test_user["token"]})
        items = resp.json()["data"]
        # test_user 的 mine 不应包含 other_user 创建的
        for item in items:
            assert item["title"] != "B的独享", \
                f"隔离失效：test_user 看到了 other_user 的提示词"
