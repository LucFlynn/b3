#!/usr/bin/env python3
"""Generate an invite code for EPI self-serve onboarding.

Usage:
    DATABASE_URL_SYNC=... API_KEY_SALT=... python scripts/generate_invite.py --label "Chowan - March 2026"

The raw invite code is printed once and cannot be retrieved again.
"""
import argparse
import hashlib
import secrets
import sys
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, text


def main():
    parser = argparse.ArgumentParser(description="Generate an EPI invite code")
    parser.add_argument("--label", required=True, help='Admin note, e.g. "Chowan - March 2026"')
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL_SYNC")
    salt = os.environ.get("API_KEY_SALT")

    if not db_url:
        print("ERROR: Set DATABASE_URL_SYNC environment variable", file=sys.stderr)
        sys.exit(1)
    if not salt:
        print("ERROR: Set API_KEY_SALT environment variable", file=sys.stderr)
        sys.exit(1)

    # Generate raw code
    raw_code = f"epi-invite-{secrets.token_urlsafe(24)}"
    code_hash = hashlib.sha256(f"{salt}:{raw_code}".encode()).hexdigest()

    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO invite_codes (id, code_hash, label, used, created_at) "
                "VALUES (:id, :code_hash, :label, false, :created_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "code_hash": code_hash,
                "label": args.label,
                "created_at": datetime.now(timezone.utc),
            },
        )
        conn.commit()

    print(f"\nInvite code (give to client — shown once):\n\n  {raw_code}\n")
    print(f"Label: {args.label}")


if __name__ == "__main__":
    main()
