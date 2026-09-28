from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_dummy_password, verify_password
from app.models.enums import UserRole
from app.models.user import User


class EmailAlreadyRegisteredError(Exception):
    pass


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def create_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    password: str,
    role: UserRole = UserRole.USER,
) -> User:
    if get_by_email(db, email) is not None:
        raise EmailAlreadyRegisteredError(email)

    user = User(
        email=email.strip().lower(),
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two simultaneous registrations with the same email: the unique index wins
        db.rollback()
        raise EmailAlreadyRegisteredError(email)
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_by_email(db, email)
    if user is None:
        verify_dummy_password(password)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
