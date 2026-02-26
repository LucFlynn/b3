import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# Fernet cipher for PII encryption
_fernet = Fernet(settings.fernet_key.encode() if len(settings.fernet_key) == 44 else Fernet.generate_key())


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# PII encryption
def encrypt_pii(value: str) -> str:
    if not value:
        return ""
    return _fernet.encrypt(value.encode()).decode()


def decrypt_pii(encrypted: str) -> str:
    if not encrypted:
        return ""
    return _fernet.decrypt(encrypted.encode()).decode()


def hash_pii(value: str) -> str:
    """SHA-256 hash for indexed lookups without decryption."""
    if not value:
        return ""
    normalized = value.strip().lower()
    return hashlib.sha256(f"{settings.api_key_salt}:{normalized}".encode()).hexdigest()


def hash_ip(ip: str) -> str:
    """One-way hash for IP addresses — never store raw IPs."""
    return hashlib.sha256(f"{settings.api_key_salt}:{ip}".encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Returns (raw_key, hashed_key). Store hashed_key in DB, give raw_key to user."""
    raw_key = f"epi_{secrets.token_urlsafe(32)}"
    hashed_key = hashlib.sha256(f"{settings.api_key_salt}:{raw_key}".encode()).hexdigest()
    return raw_key, hashed_key


def verify_api_key(raw_key: str) -> str:
    """Returns the hash of the key for DB lookup."""
    return hashlib.sha256(f"{settings.api_key_salt}:{raw_key}".encode()).hexdigest()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import User

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials

    # Try JWT first
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except HTTPException:
        pass

    # Try API key
    if token.startswith("epi_"):
        hashed = verify_api_key(token)
        result = await db.execute(select(User).where(User.api_key_hash == hashed))
        user = result.scalar_one_or_none()
        if user is not None:
            return user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
