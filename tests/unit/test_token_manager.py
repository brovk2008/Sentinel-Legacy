import asyncio
import sys
from pathlib import Path
import pytest
from jose import JWTError

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sentinel.auth.token_manager import TokenManager
from sentinel.core.redis import InMemoryRedis


@pytest.mark.asyncio
async def test_token_issue_and_validate():
    redis = InMemoryRedis()
    tm = TokenManager(redis, secret_key="test-secret-key-32c", algorithm="HS256", expiry_seconds=3600)

    res = await tm.issue_token(
        agent_id="agt_test123",
        agent_role="SupportAgent",
        scope="mcp:tools crm:orders",
        resource="https://crm.corp.internal",
        trust_score=85.0,
    )
    assert "access_token" in res
    assert res["token_type"] == "Bearer"

    payload = await tm.validate_token(res["access_token"], expected_audience="https://crm.corp.internal")
    assert payload["sub"] == "agt_test123"
    assert payload["aud"] == "https://crm.corp.internal"
    assert payload["sentinel"]["trust_score"] == 85.0


@pytest.mark.asyncio
async def test_token_audience_mismatch():
    redis = InMemoryRedis()
    tm = TokenManager(redis, secret_key="test-secret-key-32c", algorithm="HS256")

    res = await tm.issue_token(
        agent_id="agt_test123",
        agent_role="SupportAgent",
        scope="mcp:tools",
        resource="https://crm.corp.internal",
        trust_score=85.0,
    )

    with pytest.raises(JWTError):
        # Mismatched audience must fail-closed
        await tm.validate_token(res["access_token"], expected_audience="https://payments.corp.internal")


@pytest.mark.asyncio
async def test_token_blacklist_revocation():
    redis = InMemoryRedis()
    tm = TokenManager(redis, secret_key="test-secret-key-32c", algorithm="HS256")

    res = await tm.issue_token(
        agent_id="agt_test123",
        agent_role="SupportAgent",
        scope="mcp:tools",
        resource="https://crm.corp.internal",
        trust_score=85.0,
    )
    jti = res["jti"]

    # Revoke single token
    await tm.revoke_token(jti)
    with pytest.raises(JWTError):
        await tm.validate_token(res["access_token"], expected_audience="https://crm.corp.internal")


@pytest.mark.asyncio
async def test_agent_kill_revokes_all_tokens():
    redis = InMemoryRedis()
    tm = TokenManager(redis, secret_key="test-secret-key-32c", algorithm="HS256")

    res = await tm.issue_token(
        agent_id="agt_test123",
        agent_role="SupportAgent",
        scope="mcp:tools",
        resource="https://crm.corp.internal",
        trust_score=85.0,
    )

    # Revoke entire agent (Kill Switch cascade)
    await tm.revoke_all_agent_tokens("agt_test123")
    with pytest.raises(JWTError):
        await tm.validate_token(res["access_token"], expected_audience="https://crm.corp.internal")
