from functools import lru_cache
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./sentinel.db"
    postgres_db: str = "sentinel_legacy"
    postgres_user: str = "sentinel"
    postgres_password: str = "sentinel"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "sentinel-legacy-hackathon-secret-32c-production-grade"
    jwt_algorithm: str = "HS256"
    jwt_expiry_seconds: int = 3600

    # LLM Providers (Free Tiers: Gemini, OpenRouter)
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: str = "auto"
    gemini_model: str = "gemini-1.5-flash"
    openrouter_model: str = "google/gemini-2.0-flash-exp:free"

    # Cedar
    cedar_policies_path: str = "./sentinel/policy/policies.cedar"
    cedar_schema_path: str = "./sentinel/policy/schema.cedarschema"

    # Trust Score
    trust_restricted_threshold: float = 70.0
    trust_auto_suspend_threshold: float = 40.0

    # HITL
    hitl_default_timeout_seconds: int = 300
    hitl_require_rationale: bool = True
    hitl_require_checkbox_ack: bool = True

    # Violations
    violation_window_seconds: int = 300
    violation_warning_count: int = 2
    violation_critical_count: int = 3

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    # Token Cost
    cost_per_input_token_usd: float = 0.000003
    cost_per_output_token_usd: float = 0.000015

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def resolved_cedar_policy_path(self) -> str:
        candidates = [
            Path(self.cedar_policies_path),
            Path(__file__).parent.parent / "policy" / "policies.cedar",
            Path.cwd() / "sentinel" / "policy" / "policies.cedar",
            Path.cwd() / "backend" / "sentinel" / "policy" / "policies.cedar",
        ]
        for p in candidates:
            if p.is_file():
                return str(p.resolve())
        return str(candidates[1].resolve())

    def resolved_cedar_schema_path(self) -> str:
        candidates = [
            Path(self.cedar_schema_path),
            Path(__file__).parent.parent / "policy" / "schema.cedarschema",
            Path.cwd() / "sentinel" / "policy" / "schema.cedarschema",
            Path.cwd() / "backend" / "sentinel" / "policy" / "schema.cedarschema",
        ]
        for p in candidates:
            if p.is_file():
                return str(p.resolve())
        return str(candidates[1].resolve())


@lru_cache()
def get_settings() -> Settings:
    return Settings()
