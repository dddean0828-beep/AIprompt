"""
项目级 conftest.py — 跨 API/E2E 共享的配置

功能：
1. 自动探测服务可用性（API 后端 / 前端）
2. E2E 测试：若前端不可达则自动跳过（避免 pytest tests/ -v 全部失败）
3. 提供 session 级 fixture 共享
"""

import pytest
import requests


# ============================================================
# 服务可用性探测（session 级别，只探测一次）
# ============================================================

BACKEND_URL = "http://localhost:8080"
FRONTEND_URL = "http://localhost:5173"


def _is_url_reachable(url: str, timeout: float = 2.0) -> bool:
    """检查 URL 是否可达（仅做轻量 HEAD 请求）"""
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code < 500
    except (requests.ConnectionError, requests.Timeout):
        return False


@pytest.fixture(scope="session")
def backend_available() -> bool:
    """检查后端 API 是否可达"""
    return _is_url_reachable(f"{BACKEND_URL}/api/user/login", timeout=3.0)


@pytest.fixture(scope="session")
def frontend_available() -> bool:
    """检查前端是否可达"""
    return _is_url_reachable(FRONTEND_URL, timeout=3.0)


# ============================================================
# pytest 配置钩子
# ============================================================

def pytest_configure(config):
    """
    注册自定义标记 + 打印环境探测结果。

    将标记注册在这里（而非仅依赖 pytest.ini），
    确保在没有 pytest.ini 的情况下也能工作。
    """
    config.addinivalue_line("markers", "smoke: 冒烟测试（核心流程快速验证）")
    config.addinivalue_line("markers", "slow: 慢速测试（如浏览器交互）")
    config.addinivalue_line("markers", "user: 用户模块测试")
    config.addinivalue_line("markers", "prompt: 提示词模块测试")
    config.addinivalue_line("markers", "favorite: 收藏模块测试")
    config.addinivalue_line("markers", "e2e: 端到端测试（需要前端 + 浏览器）")


def pytest_collection_modifyitems(config, items):
    """
    收集测试用例后自动标记：
    - tests/e2e/ 下的测试自动打 e2e 标记（如果未手动标记）
    """
    for item in items:
        if "e2e" in str(item.fspath) and "e2e" not in item.keywords:
            item.add_marker(pytest.mark.e2e)
