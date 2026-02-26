import pytest

from app.security import (
    encrypt_pii,
    decrypt_pii,
    hash_pii,
    hash_ip,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_api_key,
    verify_api_key,
)


def test_pii_encryption_roundtrip():
    original = "test@example.com"
    encrypted = encrypt_pii(original)
    assert encrypted != original
    assert decrypt_pii(encrypted) == original


def test_pii_encryption_empty():
    assert encrypt_pii("") == ""
    assert decrypt_pii("") == ""


def test_pii_hash_deterministic():
    h1 = hash_pii("test@example.com")
    h2 = hash_pii("test@example.com")
    assert h1 == h2
    assert len(h1) == 64  # SHA-256


def test_pii_hash_case_insensitive():
    h1 = hash_pii("Test@Example.com")
    h2 = hash_pii("test@example.com")
    assert h1 == h2


def test_ip_hashing():
    h1 = hash_ip("192.168.1.1")
    h2 = hash_ip("192.168.1.1")
    assert h1 == h2
    assert h1 != "192.168.1.1"  # never stores raw IP


def test_password_hashing():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed)
    assert not verify_password("wrongpassword", hashed)


def test_jwt_roundtrip():
    token = create_access_token({"sub": "user-123", "agency_id": "agency-456"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["agency_id"] == "agency-456"


def test_api_key_generation():
    raw, hashed = generate_api_key()
    assert raw.startswith("epi_")
    assert len(hashed) == 64
    assert verify_api_key(raw) == hashed
