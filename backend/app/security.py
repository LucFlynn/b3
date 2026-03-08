import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import httpx
import jwt as pyjwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# Fernet cipher for PII encryption — fail hard if key is misconfigured
def _init_fernet() -> Fernet:
    key = settings.fernet_key
    if not key or len(key) != 44:
        raise RuntimeError(
            f"FERNET_KEY must be exactly 44 characters (base64-encoded 32-byte key), "
            f"got {len(key)}. Generate with: "
            'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    try:
        return Fernet(key.encode())
    except Exception as e:
        raise RuntimeError(f"FERNET_KEY is not valid base64: {e}") from e


_fernet = _init_fernet()

# ── Clerk JWKS cache ──
_clerk_jwks: dict | None = None


async def _get_clerk_jwks() -> dict:
    """Fetch and cache Clerk's JWKS for JWT verification."""
    global _clerk_jwks
    if _clerk_jwks is not None:
        return _clerk_jwks
    if not settings.clerk_secret_key:
        raise HTTPException(status_code=500, detail="Clerk not configured")
    # Clerk JWKS endpoint — derive from secret key's instance ID
    # Format: sk_live_xxx or sk_test_xxx
    jwks_url = "https://api.clerk.com/v1/jwks"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            jwks_url,
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
        )
        resp.raise_for_status()
        _clerk_jwks = resp.json()
    return _clerk_jwks


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Legacy JWT creation — kept for backward compat with old auth routes."""
    from jose import jwt as jose_jwt
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jose_jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    from jose import jwt as jose_jwt, JWTError
    try:
        return jose_jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
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


async def _get_or_create_clerk_user(clerk_user_id: str, email: str, db: AsyncSession):
    """Find existing user by clerk_user_id, or create user + agency on first login."""
    from app.models.user import User
    from app.models.agency import Agency

    result = await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    user = result.scalar_one_or_none()
    if user:
        return user

    # Check if user exists by email (migrated from old auth)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.clerk_user_id = clerk_user_id
        db.add(user)
        await db.flush()
        return user

    # New user — create agency + user
    agency = Agency(name=email.split("@")[0], slug=f"user-{clerk_user_id}")
    db.add(agency)
    await db.flush()

    user = User(
        agency_id=agency.id,
        email=email,
        clerk_user_id=clerk_user_id,
        role="admin",
    )
    db.add(user)
    await db.flush()
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import User

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials

    # Try API key first (for Slack bot / programmatic access)
    if token.startswith("epi_"):
        hashed = verify_api_key(token)
        result = await db.execute(select(User).where(User.api_key_hash == hashed))
        user = result.scalar_one_or_none()
        if user is not None:
            return user
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    # Try Clerk JWT
    if settings.clerk_secret_key:
        try:
            jwks = await _get_clerk_jwks()
            # Get signing key from JWKS
            header = pyjwt.get_unverified_header(token)
            kid = header.get("kid")
            key_data = None
            for k in jwks.get("keys", []):
                if k.get("kid") == kid:
                    key_data = k
                    break
            if key_data is None:
                # Invalidate cache and retry once
                global _clerk_jwks
                _clerk_jwks = None
                jwks = await _get_clerk_jwks()
                for k in jwks.get("keys", []):
                    if k.get("kid") == kid:
                        key_data = k
                        break

            if key_data is None:
                raise HTTPException(status_code=401, detail="Unknown signing key")

            public_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(key_data)
            payload = pyjwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
            clerk_user_id = payload.get("sub")
            # Clerk stores email in session claims or we can extract from metadata
            email = payload.get("email") or payload.get("primary_email_address") or ""
            if not clerk_user_id:
                raise HTTPException(status_code=401, detail="Invalid Clerk token")

            user = await _get_or_create_clerk_user(clerk_user_id, email, db)
            return user
        except pyjwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except pyjwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("Clerk JWT verification failed: %s", e)
            raise HTTPException(status_code=401, detail="Authentication failed")

    # Fallback: legacy JWT (for backwards compat during migration)
    try:
        from jose import jwt as jose_jwt, JWTError
        payload = jose_jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except (JWTError, Exception):
        pass

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
