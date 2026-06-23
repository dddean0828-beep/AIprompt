"""
冒烟测试 —— 验证测试环境链路通畅

- 后端是否可达
- fixture（auth_token / test_user）是否正常工作
- 核心接口是否返回预期的 HTTP 状态码
"""

import pytest
import requests
from .conftest import BASE_URL, generate_username, register_and_login


class TestEnvironment:
    """环境连通性验证"""

    def test_backend_reachable_via_login(self):
        """
        验证后端可以访问。

        使用 /api/user/login（AuthInterceptor 放行的接口），
        故意传错误密码，但仍能验证后端返回了 JSON 响应。
        """
        resp = requests.post(f"{BASE_URL}/api/user/login", json={
            "username": "nonexistent_test_user",
            "password": "wrong",
        }, timeout=5)
        # 后端有响应即可（500 表示业务拒绝，不是网络错误）
        assert resp.status_code in [200, 401, 500]
        assert "code" in resp.json()

    @pytest.mark.smoke
    def test_auth_required_returns_401_without_token(self):
        """
        验证：带鉴权的接口在无 token 时返回 401。

        AuthInterceptor 拦截 /api/rank/hot，因为不在 excludePathPatterns 中。
        """
        resp = requests.get(f"{BASE_URL}/api/rank/hot", timeout=5)
        assert resp.status_code == 401
        data = resp.json()
        assert data["code"] == 401
        assert "令牌" in data["message"]

    @pytest.mark.smoke
    def test_fixture_auth_token_works(self, auth_token):
        """验证 auth_token fixture 能正常生成 Bearer token"""
        assert auth_token.startswith("Bearer ")
        assert len(auth_token) > 20  # JWT 不会太短

    @pytest.mark.smoke
    def test_fixture_test_user_works(self, test_user):
        """验证 test_user fixture 返回完整用户信息"""
        assert "token" in test_user
        assert "userId" in test_user
        assert "username" in test_user
        assert test_user["token"].startswith("Bearer ")
        assert isinstance(test_user["userId"], int)

    @pytest.mark.smoke
    def test_fixture_other_user_different_from_test_user(self, test_user, other_user):
        """验证 test_user 和 other_user 是两个不同的人"""
        assert test_user["userId"] != other_user["userId"]
        assert test_user["username"] != other_user["username"]
