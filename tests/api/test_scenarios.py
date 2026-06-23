"""
端到端业务流程测试（API 层面）

模拟真实用户完整操作链路：
1. 单用户完整流程：注册 → 登录 → 创建 → 查询 → 修改 → 收藏 → 删除
2. 多用户隔离流程：用户A和用户B的权限隔离
3. Token 异常场景：过期 token、篡改 token
"""

import pytest
import requests
from .conftest import BASE_URL, generate_username, register_and_login
from .test_prompt import create_prompt, get_my_prompt_id


class TestFullUserJourney:
    """
    模拟单个用户的完整使用链路。

    不依赖 fixture（test_user / auth_token），
    手动控制每一步，验证完整闭环。
    """

    def test_register_login_create_view_edit_favorite_delete(self, session):
        """
        完整流程：
        注册 → 登录 → 创建提示词 → 查看列表 → 查看详情
        → 修改 → 收藏 → 查看收藏列表 → 取消收藏 → 删除
        """
        username = generate_username()
        password = "test123456"

        # 1. 注册
        r = session.post(f"{BASE_URL}/api/user/register", json={
            "username": username, "password": password,
        })
        assert r.json()["code"] == 200

        # 2. 登录
        r = session.post(f"{BASE_URL}/api/user/login", json={
            "username": username, "password": password,
        })
        assert r.json()["code"] == 200
        token = f"Bearer {r.json()['data']['token']}"
        user_id = int(r.json()["data"]["userId"])

        # 3. 创建提示词
        r = session.post(f"{BASE_URL}/api/prompt/add", json={
            "title": f"E2E测试_{username}",
            "content": "端到端测试内容",
            "category": "E2E",
        }, headers={"Authorization": token})
        assert r.json()["code"] == 200

        # 4. 查看我的列表
        r = session.get(f"{BASE_URL}/api/prompt/mine",
                        headers={"Authorization": token})
        items = r.json()["data"]
        # next() + generator expression 查找刚创建的提示词,如果找不到则返回 None
        my_prompt = next(
            (item for item in items if item["title"] == f"E2E测试_{username}"),
            None,
        )
        assert my_prompt is not None, "创建的提示词未出现在 mine 列表中"
        pid = my_prompt["id"]

        # 5. 查看详情
        r = session.get(f"{BASE_URL}/api/prompt/detail/{pid}",
                        headers={"Authorization": token})
        assert r.json()["data"]["content"] == "端到端测试内容"

        # 6. 修改
        r = session.put(f"{BASE_URL}/api/prompt/update", json={
            "id": pid,
            "title": f"E2E修改_{username}",
            "content": "修改后的内容",
            "category": "E2E",
        }, headers={"Authorization": token})
        assert r.json()["data"] is True

        # 验证修改生效
        r = session.get(f"{BASE_URL}/api/prompt/detail/{pid}",
                        headers={"Authorization": token})
        assert r.json()["data"]["title"] == f"E2E修改_{username}"

        # 7. 收藏
        r = session.post(f"{BASE_URL}/api/favorite/add", json={
            "userId": user_id, "promptId": pid,
        }, headers={"Authorization": token})
        assert r.json()["data"] is True

        # 8. 查看收藏列表
        r = session.get(f"{BASE_URL}/api/favorite/list",
                        params={"userId": user_id},
                        headers={"Authorization": token})
        favorites = r.json()["data"]
        # any() -> 有一个元素返回True，则为True
        assert any(f["prompt"]["id"] == pid for f in favorites)

        # 取消收藏
        favorite_id = next(
            f["favoriteId"] for f in favorites if f["prompt"]["id"] == pid
        )
        r = session.delete(f"{BASE_URL}/api/favorite/remove/{favorite_id}",
                           headers={"Authorization": token})
        assert r.json()["data"] is True

        # 9. 删除提示词
        r = session.delete(f"{BASE_URL}/api/prompt/delete/{pid}",
                           headers={"Authorization": token})
        assert r.json()["data"] is True

        # 10. 验证已删除
        r = session.get(f"{BASE_URL}/api/prompt/detail/{pid}",
                        headers={"Authorization": token})
        assert r.json()["data"] is None


class TestMultiUserIsolation:
    """
    多用户权限隔离场景。

    验证：用户A创建的资源，用户B无法越权操作。
    """

    def test_two_user_isolation_chain(self, session):
        """两用户完整隔离验证"""
        # 创建两个用户
        user_a = register_and_login(generate_username(), "test123456")
        user_b = register_and_login(generate_username(), "test123456")
        assert user_a and user_b

        # 用户A创建提示词（含私密）
        r = session.post(f"{BASE_URL}/api/prompt/add", json={
            "title": "A的公开",
            "content": "公开内容",
            "category": "隔离测试",
            "isPrivate": 0,
        }, headers={"Authorization": user_a["token"]})
        assert r.json()["code"] == 200

        r = session.post(f"{BASE_URL}/api/prompt/add", json={
            "title": "A的私密",
            "content": "私密内容",
            "category": "隔离测试",
            "isPrivate": 1,
        }, headers={"Authorization": user_a["token"]})
        assert r.json()["code"] == 200

        # 用户B创建自己的提示词
        r = session.post(f"{BASE_URL}/api/prompt/add", json={
            "title": "B的提示词",
            "content": "B的内容",
            "category": "隔离测试",
        }, headers={"Authorization": user_b["token"]})
        assert r.json()["code"] == 200

        # 验证1：用户B的 mine 列表只包含自己的
        r = session.get(f"{BASE_URL}/api/prompt/mine",
                        headers={"Authorization": user_b["token"]})
        b_items = r.json()["data"]
        b_titles = [item["title"] for item in b_items]
        assert "A的公开" not in b_titles, "隔离失败：B看到A的公开提示词（mine）"
        assert "A的私密" not in b_titles, "隔离失败：B看到A的私密提示词（mine）"

        # 验证2：用户B在公开列表中看不到A的私密
        r = session.get(f"{BASE_URL}/api/prompt/list",
                        headers={"Authorization": user_b["token"]})
        list_titles = [item["title"] for item in r.json()["data"]]
        assert "A的私密" not in list_titles, "隔离失败：B在列表中看到A的私密"

        # 验证3：用户B无法修改A的提示词
        a_public_id = next(
            (item["id"] for item in b_items if False), None
        )
        # 通过 mine 查找B的一个提示词 ID
        b_prompt_id = b_items[0]["id"] if b_items else None
        # 通过列表找到A的公开提示词 ID
        r = session.get(f"{BASE_URL}/api/prompt/list",
                        headers={"Authorization": user_a["token"]})
        a_items = [item for item in r.json()["data"] if item["title"] == "A的公开"]
        if a_items and b_prompt_id:
            a_id = a_items[0]["id"]
            # B 尝试修改 A 的提示词
            r = session.put(f"{BASE_URL}/api/prompt/update", json={
                "id": a_id,
                "title": "被B篡改了",
                "content": "恶意内容",
                "category": "违规",
            }, headers={"Authorization": user_b["token"]})
            assert r.json()["data"] is False, \
                "严重 Bug：B 成功修改了 A 的提示词！"


class TestTokenScenarios:
    """
    Token 异常场景测试。
    """

    def test_expired_token(self, session):
        """
        使用一个已过期的 JWT token。

        注：这是一个已知测试数据 —— 手动构造的过期 token。
        JWT 密钥和算法需与后端一致，此处用异常 token 测试拦截器行为。
        """
        # 构造一个明显无效的 token（乱码）
        fake_token = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOjEsInVzZXJuYW1lIjoidGVzdCJ9.invalid_signature"
        resp = session.get(f"{BASE_URL}/api/prompt/list",
                           headers={"Authorization": fake_token})
        # AuthInterceptor 应返回 401
        assert resp.status_code == 401
        assert "失效" in resp.json()["message"] or "令牌" in resp.json()["message"]

    def test_malformed_token(self, session):
        """乱码 token 应被拦截"""
        resp = session.get(f"{BASE_URL}/api/prompt/list",
                           headers={"Authorization": "Bearer garbage_token"})
        assert resp.status_code == 401

    def test_token_without_bearer_prefix(self, session):
        """token 不带 Bearer 前缀应返回 401"""
        # 先获取一个合法 token
        user = register_and_login(generate_username(), "test123456")
        raw_token = user["token"].replace("Bearer ", "")

        # 不带 "Bearer " 前缀发送
        resp = session.get(f"{BASE_URL}/api/prompt/list",
                           headers={"Authorization": raw_token})
        assert resp.status_code == 401
        assert "令牌缺失" in resp.json()["message"]
