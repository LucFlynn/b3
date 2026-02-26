import asyncio
import os
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.agency import Agency
from app.models.user import User
from app.models.site import Site
from app.security import hash_password, create_access_token

TEST_DB_URL = "sqlite+aiosqlite://"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def _override_get_db():
        # Don't auto-commit in tests — let the test control the session
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def agency(db_session: AsyncSession):
    a = Agency(
        id=uuid.UUID("a1000000-0000-0000-0000-000000000001"),
        name="Test Agency",
        slug="test-agency",
    )
    db_session.add(a)
    await db_session.flush()
    return a


@pytest_asyncio.fixture
async def agency2(db_session: AsyncSession):
    a = Agency(
        id=uuid.UUID("a2000000-0000-0000-0000-000000000002"),
        name="Other Agency",
        slug="other-agency",
    )
    db_session.add(a)
    await db_session.flush()
    return a


@pytest_asyncio.fixture
async def user(db_session: AsyncSession, agency: Agency):
    u = User(
        id=uuid.UUID("01000000-0000-0000-0000-000000000001"),
        agency_id=agency.id,
        email="test@example.com",
        hashed_password=hash_password("password123"),
        role="admin",
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest_asyncio.fixture
async def user2(db_session: AsyncSession, agency2: Agency):
    u = User(
        id=uuid.UUID("02000000-0000-0000-0000-000000000002"),
        agency_id=agency2.id,
        email="other@example.com",
        hashed_password=hash_password("password123"),
        role="admin",
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest_asyncio.fixture
async def site(db_session: AsyncSession, agency: Agency):
    s = Site(
        id=uuid.UUID("51000000-0000-0000-0000-000000000001"),
        agency_id=agency.id,
        domain="www.test-site.com",
        name="Test Site",
        pixel_id="px_test_001",
    )
    db_session.add(s)
    await db_session.flush()
    return s


@pytest_asyncio.fixture
async def site_agency2(db_session: AsyncSession, agency2: Agency):
    s = Site(
        id=uuid.UUID("52000000-0000-0000-0000-000000000002"),
        agency_id=agency2.id,
        domain="www.other-site.com",
        name="Other Site",
        pixel_id="px_other_001",
    )
    db_session.add(s)
    await db_session.flush()
    return s


@pytest_asyncio.fixture
def auth_headers(user: User):
    token = create_access_token({"sub": str(user.id), "agency_id": str(user.agency_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def auth_headers2(user2: User):
    token = create_access_token({"sub": str(user2.id), "agency_id": str(user2.agency_id)})
    return {"Authorization": f"Bearer {token}"}
