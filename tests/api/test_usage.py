"""
使用记录模块接口测试

覆盖接口：
- POST /api/usage/add  记录提示词使用

注意：/api/usage/* 也被 AuthInterceptor 拦截，必须携带 Authorization header。
"""

import pytest
from .conftest import BASE_URL
from .test_prompt import create_prompt, get_my_prompt_id


class TestAddUsage:
    """POST /api/usage/add"""

    def test_add_usage_success(self, session, test_user):
        """正常记录使用"""
        create_prompt(session, test_user["token"])
        pid = get_my_prompt_id(session, test_user["token"])

        resp = session.post(f"{BASE_URL}/api/usage/add", json={
            "userId": test_user["userId"],
            "promptId": pid,
        }, headers={"Authorization": test_user["token"]})
        assert resp.json()["data"] is True

    def test_add_usage_multiple_times(self, session, test_user):
        """
        多次使用同一提示词：每次都会记录并递增 useCount。

        验证 API 不会因为重复使用而报错。
        """
        create_prompt(session, test_user["token"])
        pid = get_my_prompt_id(session, test_user["token"])

        for _ in range(3):
            resp = session.post(f"{BASE_URL}/api/usage/add", json={
                "userId": test_user["userId"],
                "promptId": pid,
            }, headers={"Authorization": test_user["token"]})
            assert resp.json()["data"] is True

    def test_add_usage_nonexistent_prompt(self, session, test_user):
        """使用不存在的提示词：insert 成功但 selectById 为 null"""
        resp = session.post(f"{BASE_URL}/api/usage/add", json={
            "userId": test_user["userId"],
            "promptId": 9999999,
        }, headers={"Authorization": test_user["token"]})
        assert resp.json()["data"] is True

    def test_add_usage_no_token_blocked(self, session):
        """无 token 记录使用：AuthInterceptor 返回 401"""
        resp = session.post(f"{BASE_URL}/api/usage/add", json={
            "userId": 1,
            "promptId": 1,
        })
        assert resp.status_code == 401

    @pytest.mark.parametrize("userId, promptId, desc", [
        (None, 1, "userId 为 null"),
        (1, None, "promptId 为 null"),
    ])
    def test_add_usage_boundary(self, session, auth_token, userId, promptId, desc):
        """边界值：null 参数"""
        resp = session.post(f"{BASE_URL}/api/usage/add", json={
            "userId": userId,
            "promptId": promptId,
        }, headers={"Authorization": auth_token})
        # 接口应正常响应不崩溃
        assert resp.status_code in [200, 400, 500], \
            f"{desc}: 意外的状态码 {resp.status_code}"
