from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_dummy_password,
    verify_password,
)
from app.models.enums import UserRole
from app.models.user import User


class EmailAlreadyRegisteredError(Exception):
    pass


class UserHasRelatedRecordsError(Exception):
    pass


class IncorrectPasswordError(Exception):
    pass


class SamePasswordError(Exception):
    pass


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_users(
    db: Session,
    *,
    role: UserRole | None = None,
    is_active: bool | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[User], int]:
    conditions = []
    if role is not None:
        conditions.append(User.role == role)
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    if q:
        pattern = f"%{_escape_like(q.strip())}%"
        conditions.append(
            or_(
                User.email.ilike(pattern, escape="\\"),
                User.full_name.ilike(pattern, escape="\\"),
            )
        )

    total = db.scalar(select(func.count()).select_from(User).where(*conditions)) or 0
    items = db.scalars(
        select(User).where(*conditions).order_by(User.id).limit(limit).offset(offset)
    ).all()
    return list(items), total


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


def update_user(db: Session, user: User, changes: dict) -> User:
    new_email = changes.get("email")
    if new_email is not None and new_email != user.email:
        other = get_by_email(db, new_email)
        if other is not None and other.id != user.id:
            raise EmailAlreadyRegisteredError(new_email)

    for field, value in changes.items():
        setattr(user, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if "email" in changes:
            raise EmailAlreadyRegisteredError(changes["email"])
        raise
    db.refresh(user)
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise IncorrectPasswordError()
    if verify_password(new_password, user.hashed_password):
        raise SamePasswordError()
    user.hashed_password = hash_password(new_password)
    db.commit()


def delete_user(db: Session, user: User) -> None:
    """Hard delete. The database enforces the FK rules (RESTRICT / SET NULL) we designed."""
    try:
        db.execute(delete(User).where(User.id == user.id))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise UserHasRelatedRecordsError(user.id)


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_by_email(db, email)
    if user is None:
        verify_dummy_password(password)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
