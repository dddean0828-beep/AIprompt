"""
API 测试全局 Fixture

提供的能力：
- BASE_URL：后端地址
- session：requests.Session 实例
- auth_token：自动注册用户并登录，返回 Bearer token 字符串
- test_user：已登录用户的信息 {"userId": ..., "username": ..., "token": ...}
- other_user：另一个用户（用于越权测试）
"""

import uuid
import pytest
import requests


# ============================================================
# 基础配置
# ============================================================

BASE_URL = "http://localhost:8080"


def generate_username() -> str:
    """生成唯一的测试用户名，避免数据库冲突"""
    return f"test_{uuid.uuid4().hex[:8]}"


def register_and_login(username: str, password: str) -> dict | None:
    """
    注册 + 登录的原子操作。

    如果用户名已存在（比如从数据库残留），跳过注册直接登录。
    返回 {"token": str, "userId": int, "username": str}，失败返回 None。
    """
    session = requests.Session()

    # 1. 注册（可能失败：用户名已存在）
    resp = session.post(f"{BASE_URL}/api/user/register", json={
        "username": username,
        "password": password,
    })
    # 注册失败时打印日志（便于调试）
    if resp.status_code != 200 or resp.json().get("code") != 200:
        print(f"[conftest] 注册 {username} 失败: {resp.json()}")

    # 2. 登录
    resp = session.post(f"{BASE_URL}/api/user/login", json={
        "username": username,
        "password": password,
    })
    data = resp.json()
    if data.get("code") != 200:
        print(f"[conftest] 登录 {username} 失败: {data}")
        return None

    return {
        "token": f"Bearer {data['data']['token']}",
        "userId": int(data["data"]["userId"]),
        "username": username,
    }


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="session")
def base_url() -> str:
    """后端 API 根地址"""
    return BASE_URL


@pytest.fixture(scope="function")
def session() -> requests.Session:
    """
    每个测试函数独立的 HTTP 会话。

    scope="function" 保证测试间不会互相污染 Cookie/Header。
    """
    return requests.Session()


@pytest.fixture(scope="function")
def auth_token() -> str:
    """
    返回一个已登录用户的 Bearer token。

    每个测试函数调用时，都会注册一个新用户并登录，
    保证测试数据隔离。
    """
    username = generate_username()
    info = register_and_login(username, "test123456")
    assert info is not None, f"无法获取 auth_token，请确认后端 {BASE_URL} 已启动"
    return info["token"]


@pytest.fixture(scope="function")
def test_user() -> dict:
    """
    返回一个完整已登录用户的信息 dict：
        {"token": "Bearer xxx", "userId": 1, "username": "test_abc"}
    """
    username = generate_username()
    info = register_and_login(username, "test123456")
    assert info is not None, f"无法创建测试用户，请确认后端 {BASE_URL} 已启动"
    return info


@pytest.fixture(scope="function")
def other_user() -> dict:
    """
    返回另一个已登录用户的信息，专门用于越权/隔离测试。

    例如：用 other_user 的 token 去操作 test_user 创建的资源，
    预期应该被拒绝。
    """
    username = generate_username()
    info = register_and_login(username, "test123456")
    assert info is not None, f"无法创建 other_user，请确认后端 {BASE_URL} 已启动"
    return info
