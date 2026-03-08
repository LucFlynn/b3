import hashlib
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.agency import Agency
from app.models.user import User
from app.models.invite_code import InviteCode
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, ApiKeyResponse
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_api_key,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _hash_invite_code(code: str) -> str:
    return hashlib.sha256(f"{settings.api_key_salt}:{code}".encode()).hexdigest()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Validate invite code
    code_hash = _hash_invite_code(req.invite_code)
    result = await db.execute(select(InviteCode).where(InviteCode.code_hash == code_hash))
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid invite code")
    if invite.used:
        raise HTTPException(status_code=400, detail="Invite code already used")

    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create agency + user in same transaction
    agency = Agency(name=req.agency_name, slug=_slugify(req.agency_name))
    db.add(agency)
    await db.flush()

    user = User(
        agency_id=agency.id,
        email=req.email,
        hashed_password=hash_password(req.password),
        role="admin",
    )
    db.add(user)
    await db.flush()

    # Mark invite as used
    invite.used = True
    invite.used_by_agency_id = agency.id
    invite.used_at = datetime.now(timezone.utc)

    token = create_access_token({"sub": str(user.id), "agency_id": str(agency.id)})
    return TokenResponse(access_token=token, agency_id=str(agency.id), user_id=str(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id), "agency_id": str(user.agency_id)})
    return TokenResponse(access_token=token, agency_id=str(user.agency_id), user_id=str(user.id))


@router.post("/api-key", response_model=ApiKeyResponse)
async def create_api_key(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw_key, hashed_key = generate_api_key()
    user.api_key_hash = hashed_key
    db.add(user)
    return ApiKeyResponse(api_key=raw_key)


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "agency_id": str(user.agency_id),
        "role": user.role,
        "plan": user.plan,
        "usage_count": user.usage_count,
        "usage_limit": user.usage_limit,
    }
