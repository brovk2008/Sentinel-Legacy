import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from jose import jwt, JWTError


class TokenManager:
    BLACKLIST_KEY = "sentinel:blacklist:jti:{jti}"
    AGENT_BLACKLIST_KEY = "sentinel:blacklist:agent:{agent_id}"

    def __init__(self, redis: Any, secret_key: str, algorithm: str = "HS256", expiry_seconds: int = 3600):
        self.redis = redis
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiry_seconds = expiry_seconds

    async def issue_token(
        self,
        agent_id: str,
        agent_role: str,
        scope: str,
        resource: str,
        trust_score: float,
        owner_id: str = "own_priya_sharma_01",
    ) -> dict:
        now_ts = int(time.time())
        exp_ts = now_ts + self.expiry_seconds
        jti = f"tok_{hashlib.sha256(f'{agent_id}{now_ts}'.encode()).hexdigest()[:16]}"
        payload = {
            "iss": "sentinel-legacy",
            "sub": agent_id,
            "aud": resource,  # RFC 8707 audience binding
            "iat": now_ts,
            "exp": exp_ts,
            "jti": jti,
            "scope": scope,
            "client_id": agent_id,
            "sentinel": {
                "agent_role": agent_role,
                "trust_score": trust_score,
                "owner_id": owner_id,
                "issued_for_resource": resource,
            },
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": self.expiry_seconds,
            "jti": jti,
            "scope": scope,
            "aud": resource,
        }

    async def validate_token(self, token: str, expected_audience: Optional[str] = None) -> dict:
        """
        Validates token signature, expiration, audience claim, and Redis blacklist.
        Fail-closed: raises JWTError on any validation violation.
        """
        decode_kwargs = {"algorithms": [self.algorithm]}
        if expected_audience:
            decode_kwargs["audience"] = expected_audience
        else:
            decode_kwargs["options"] = {"verify_aud": False}

        payload = jwt.decode(token, self.secret_key, **decode_kwargs)

        jti = payload.get("jti", "")
        agent_id = payload.get("sub", "")

        # O(1) Redis Blacklist checks
        if jti and await self.redis.exists(self.BLACKLIST_KEY.format(jti=jti)):
            raise JWTError("Token revoked (individual JTI blacklisted)")

        if agent_id and await self.redis.exists(self.AGENT_BLACKLIST_KEY.format(agent_id=agent_id)):
            raise JWTError("Token revoked (agent suspended)")

        return payload

    async def revoke_token(self, jti: str, ttl_seconds: int = 86400):
        """Revoke a single token by JTI."""
        await self.redis.setex(self.BLACKLIST_KEY.format(jti=jti), ttl_seconds, "revoked")

    async def revoke_all_agent_tokens(self, agent_id: str, ttl_seconds: int = 86400):
        """Revoke all current and future tokens for an agent — called by Kill Switch."""
        await self.redis.setex(self.AGENT_BLACKLIST_KEY.format(agent_id=agent_id), ttl_seconds, "suspended")

    async def clear_agent_revocation(self, agent_id: str):
        """Clear agent revocation when restored."""
        await self.redis.delete(self.AGENT_BLACKLIST_KEY.format(agent_id=agent_id))
