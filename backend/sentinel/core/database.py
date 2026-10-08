import logging
import urllib.parse
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sentinel.core.config import get_settings

log = logging.getLogger(__name__)

settings = get_settings()


def normalize_database_url(raw_url: str) -> tuple[str, dict]:
    """
    Normalizes PostgreSQL/SQLite connection URLs from Neon, Supabase, Render, Railway,
    or AWS RDS to be 100% compatible with asyncpg / aiosqlite.

    - Rewrites `postgres://` or `postgresql://` -> `postgresql+asyncpg://`
    - Parses `?sslmode=require` query parameters into asyncpg-compatible `ssl='require'`
    - Configures `check_same_thread=False` for SQLite
    """
    connect_args = {}
    url = raw_url.strip()

    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        return url, connect_args

    # Convert standard PostgreSQL driver prefixes to asyncpg
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    # Parse and sanitize query string for asyncpg
    parsed = urllib.parse.urlsplit(url)
    if parsed.query:
        query_params = urllib.parse.parse_qs(parsed.query)

        # Handle sslmode (Neon / Supabase default)
        if "sslmode" in query_params:
            mode = query_params.pop("sslmode")[0]
            if mode in ("require", "prefer", "verify-ca", "verify-full"):
                connect_args["ssl"] = mode
        elif "ssl" in query_params:
            ssl_val = query_params.pop("ssl")[0]
            if ssl_val.lower() in ("true", "require", "1"):
                connect_args["ssl"] = "require"

        # Reconstruct URL without sslmode query parameter to avoid asyncpg unexpected argument
        new_query = urllib.parse.urlencode({k: v[0] for k, v in query_params.items()})
        clean_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))
        return clean_url, connect_args

    return url, connect_args


clean_db_url, db_connect_args = normalize_database_url(settings.database_url)

if clean_db_url.startswith("postgresql"):
    log.info("Configuring production PostgreSQL engine with asyncpg connection pooling.")
    engine = create_async_engine(
        clean_db_url,
        echo=settings.db_echo,
        connect_args=db_connect_args,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
        pool_timeout=settings.db_pool_timeout,
        pool_pre_ping=True,  # Crucial for Neon serverless idle re-connections
        future=True,
    )
else:
    engine = create_async_engine(
        clean_db_url,
        echo=settings.db_echo,
        connect_args=db_connect_args,
        future=True,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
