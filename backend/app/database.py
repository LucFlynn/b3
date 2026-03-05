from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _create_engine():
    from app.config import settings
    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def _create_session_factory(eng=None):
    if eng is None:
        eng = _create_engine()
    return async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)


# Lazy-initialized globals — overridable in tests
engine = None
async_session = None


def _ensure_initialized():
    global engine, async_session
    if engine is None:
        engine = _create_engine()
    if async_session is None:
        async_session = _create_session_factory(engine)


async def get_db() -> AsyncSession:
    _ensure_initialized()
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
