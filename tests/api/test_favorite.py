"""
收藏模块接口测试

覆盖接口：
- POST   /api/favorite/add         添加收藏
- DELETE /api/favorite/remove/{id} 取消收藏
- GET    /api/favorite/list        收藏列表

注意：所有 /api/favorite/* 也被 AuthInterceptor 拦截，必须携带 Authorization header。
"""

import pytest
from .conftest import BASE_URL
from .test_prompt import create_prompt, get_my_prompt_id


class TestAddFavorite:
    """POST /api/favorite/add"""

    def test_add_favorite_success(self, session, test_user):
        """正常收藏一个公开提示词"""
        create_prompt(session, test_user["token"])
        pid = get_my_prompt_id(session, test_user["token"])

        resp = session.post(f"{BASE_URL}/api/favorite/add", json={
            "userId": test_user["userId"],
            "promptId": pid,
        }, headers={"Authorization": test_user["token"]})
        assert resp.json()["data"] is True

    def test_duplicate_favorite_idempotent(self, session, test_user):
        """
        重复收藏同一提示词：当前实现是幂等的（返回 true，不报错）。

        注：这是一个值得讨论的设计选择 —— 幂等 vs 提示"已收藏"。
        """
        create_prompt(session, test_user["token"])
        pid = get_my_prompt_id(session, test_user["token"])

        headers = {"Authorization": test_user["token"]}
        payload = {"userId": test_user["userId"], "promptId": pid}

        r1 = session.post(f"{BASE_URL}/api/favorite/add", json=payload, headers=headers)
        assert r1.json()["data"] is True

        r2 = session.post(f"{BASE_URL}/api/favorite/add", json=payload, headers=headers)
        assert r2.json()["data"] is True  # 幂等，不报错

    def test_add_favorite_nonexistent_prompt(self, session, test_user):
        """收藏不存在的提示词：insert 成功但 favoriteCount 更新无目标"""
        resp = session.post(f"{BASE_URL}/api/favorite/add", json={
            "userId": test_user["userId"],
            "promptId": 9999999,
        }, headers={"Authorization": test_user["token"]})
        assert resp.json()["data"] is True

    def test_add_favorite_nonexistent_user(self, session, test_user):
        """使用不存在的 userId 收藏（外键无约束）"""
        create_prompt(session, test_user["token"])
        pid = get_my_prompt_id(session, test_user["token"])

        resp = session.post(f"{BASE_URL}/api/favorite/add", json={
            "userId": 9999999,
            "promptId": pid,
        }, headers={"Authorization": test_user["token"]})
        assert resp.json()["data"] is True


class TestRemoveFavorite:
    """DELETE /api/favorite/remove/{id}"""

    def test_remove_favorite(self, session, test_user):
        """收藏后取消收藏"""
        create_prompt(session, test_user["token"])
        pid = get_my_prompt_id(session, test_user["token"])

        # 先收藏
        session.post(f"{BASE_URL}/api/favorite/add", json={
            "userId": test_user["userId"], "promptId": pid,
        }, headers={"Authorization": test_user["token"]})

        # 获取收藏记录 ID
        list_resp = session.get(f"{BASE_URL}/api/favorite/list",
                                params={"userId": test_user["userId"]},
                                headers={"Authorization": test_user["token"]})
        items = list_resp.json()["data"]
        assert len(items) >= 1, f"应有收藏记录，实际 {items}"
        favorite_id = items[0]["favoriteId"]

        # 取消收藏
        resp = session.delete(
            f"{BASE_URL}/api/favorite/remove/{favorite_id}",
            headers={"Authorization": test_user["token"]},
        )
        assert resp.json()["data"] is True

    def test_remove_nonexistent_favorite_id(self, session, auth_token):
        """取消不存在的收藏 ID"""
        resp = session.delete(
            f"{BASE_URL}/api/favorite/remove/9999999",
            headers={"Authorization": auth_token},
        )
        assert resp.json()["data"] is False

    def test_remove_favorite_without_token_blocked(self, session):
        """无 token 删除收藏被拦截"""
        resp = session.delete(f"{BASE_URL}/api/favorite/remove/1")
        assert resp.status_code == 401


class TestListFavorites:
    """GET /api/favorite/list"""

    def test_favorite_list_returns_correct_structure(self, session, test_user):
        """收藏列表返回正确的数据结构（含 favoriteId 和 prompt 对象）"""
        create_prompt(session, test_user["token"])
        pid = get_my_prompt_id(session, test_user["token"])

        session.post(f"{BASE_URL}/api/favorite/add", json={
            "userId": test_user["userId"], "promptId": pid,
        }, headers={"Authorization": test_user["token"]})

        resp = session.get(f"{BASE_URL}/api/favorite/list",
                           params={"userId": test_user["userId"]},
                           headers={"Authorization": test_user["token"]})
        data = resp.json()
        assert data["code"] == 200
        assert len(data["data"]) >= 1
        first = data["data"][0]
        assert "favoriteId" in first
        assert "prompt" in first
        assert first["prompt"]["id"] == pid

    def test_favorite_list_empty_for_new_user(self, session, test_user):
        """新用户的收藏列表为空"""
        resp = session.get(f"{BASE_URL}/api/favorite/list",
                           params={"userId": test_user["userId"]},
                           headers={"Authorization": test_user["token"]})
        assert resp.json()["data"] == []
