"""
排行模块接口测试

覆盖接口：
- GET /api/rank/hot      热门排行（按 useCount 降序）
- GET /api/rank/favorite 收藏排行（按 favoriteCount 降序）

注意：/api/rank/hot 和 /api/rank/favorite 被 AuthInterceptor 拦截，
调用时需要携带有效的 Bearer token。
"""

import pytest
from .conftest import BASE_URL


class TestHotRank:
    """GET /api/rank/hot"""

    def test_hot_rank_returns_list(self, session, auth_token):
        """热门排行应返回 List<Prompt>"""
        resp = session.get(f"{BASE_URL}/api/rank/hot",
                           headers={"Authorization": auth_token})
        data = resp.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_hot_rank_no_token_blocked(self, session):
        """无 token 时 AuthInterceptor 拦截返回 401"""
        resp = session.get(f"{BASE_URL}/api/rank/hot")
        assert resp.status_code == 401


class TestFavoriteRank:
    """GET /api/rank/favorite"""

    def test_favorite_rank_returns_list(self, session, auth_token):
        """收藏排行应返回 List<Prompt>"""
        resp = session.get(f"{BASE_URL}/api/rank/favorite",
                           headers={"Authorization": auth_token})
        data = resp.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_favorite_rank_no_token_blocked(self, session):
        """无 token 时 AuthInterceptor 拦截返回 401"""
        resp = session.get(f"{BASE_URL}/api/rank/favorite")
        assert resp.status_code == 401


class TestRankOrdering:
    """验证排行顺序逻辑"""

    def test_hot_rank_respects_use_count(self, session, auth_token):
        """
        验证热门排行按 useCount 降序排列。

        注：当前数据库可能多条记录 useCount 相同（默认为0），
        但排序方向应是 DESC。
        """
        resp = session.get(f"{BASE_URL}/api/rank/hot",
                           headers={"Authorization": auth_token})
        items = resp.json()["data"]
        if len(items) >= 2:
            # 验证 useCount 降序（后一条的使用记录不应大于前一条）
            for i in range(len(items) - 1):
                assert items[i]["useCount"] >= items[i + 1]["useCount"], \
                    f"排行顺序错误: items[{i}].useCount={items[i]['useCount']} < items[{i+1}].useCount={items[i+1]['useCount']}"

    def test_favorite_rank_respects_favorite_count(self, session, auth_token):
        """验证收藏排行按 favoriteCount 降序排列"""
        resp = session.get(f"{BASE_URL}/api/rank/favorite",
                           headers={"Authorization": auth_token})
        items = resp.json()["data"]
        if len(items) >= 2:
            for i in range(len(items) - 1):
                assert items[i]["favoriteCount"] >= items[i + 1]["favoriteCount"], \
                    f"排行顺序错误: items[{i}].favoriteCount={items[i]['favoriteCount']} < items[{i+1}].favoriteCount={items[i+1]['favoriteCount']}"
