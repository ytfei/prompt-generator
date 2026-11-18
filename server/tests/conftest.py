"""共享 fixture：测试用临时 SQLite，避免污染开发库。"""

import os
import tempfile

import pytest

_TMP = tempfile.mkdtemp(prefix="pg-test-")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP}/test.db"
# 确保测试永远不触网
os.environ["LLM_PROVIDER"] = ""
os.environ["LLM_MODEL"] = ""


@pytest.fixture()
async def client():
    from httpx import ASGITransport, AsyncClient

    from app.db.session import init_db
    from app.main import app

    await init_db()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
