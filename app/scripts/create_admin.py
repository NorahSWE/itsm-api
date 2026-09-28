"""Create the first admin account from ADMIN_EMAIL / ADMIN_PASSWORD env vars.

Usage:  python -m app.scripts.create_admin
Idempotent: does nothing if the user already exists.
"""
import sys

from pydantic import ValidationError

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.schemas.user import UserCreate
from app.services import user_service


def main() -> int:
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        print("ERROR: set ADMIN_EMAIL and ADMIN_PASSWORD in your environment / .env")
        return 1

    try:
        data = UserCreate(
            email=settings.ADMIN_EMAIL,
            full_name=settings.ADMIN_FULL_NAME,
            password=settings.ADMIN_PASSWORD,
        )
    except ValidationError as exc:
        print("ERROR: invalid admin settings:")
        for err in exc.errors():
            print(f"  - {err['loc'][0]}: {err['msg']}")
        return 1

    with SessionLocal() as db:
        existing = user_service.get_by_email(db, data.email)
        if existing:
            print(f"User {existing.email} already exists (role={existing.role.value}). Nothing to do.")
            return 0
        user = user_service.create_user(
            db,
            email=data.email,
            full_name=data.full_name,
            password=data.password,
            role=UserRole.ADMIN,
        )
        print(f"Admin created: {user.email} (id={user.id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
