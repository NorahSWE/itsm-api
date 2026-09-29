from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import (
    AdminUserCreate,
    AdminUserUpdate,
    PasswordChange,
    ProfileUpdate,
    UserList,
    UserRead,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])

# Upper bound = PostgreSQL INTEGER max, so absurd ids give 422 instead of a DB error
UserId = Annotated[int, Path(ge=1, le=2_147_483_647, description="User id")]

_ADMIN_ERRORS = {
    401: {"description": "Missing or invalid token"},
    403: {"description": "Admin role required"},
}


def _get_user_or_404(db, user_id: int) -> User:
    user = user_service.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# --------------------------------------------------------------------------- #
# Current user (profile). Declared BEFORE /{user_id} so "me" is not parsed as an id.
# --------------------------------------------------------------------------- #
@router.get(
    "/me",
    response_model=UserRead,
    summary="Get my profile",
    responses={401: {"description": "Missing or invalid token"}},
)
def get_my_profile(current_user: CurrentUser):
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update my profile",
    responses={401: {"description": "Missing or invalid token"}},
)
def update_my_profile(payload: ProfileUpdate, db: DbSession, current_user: CurrentUser):
    """Users can only change their own display name. Role/email/status are admin-only."""
    return user_service.update_user(db, current_user, {"full_name": payload.full_name})


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change my password",
    responses={
        400: {"description": "Current password incorrect, or new password equals the old one"},
        401: {"description": "Missing or invalid token"},
    },
)
def change_my_password(payload: PasswordChange, db: DbSession, current_user: CurrentUser):
    try:
        user_service.change_password(
            db, current_user, payload.current_password, payload.new_password
        )
    except user_service.IncorrectPasswordError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    except user_service.SamePasswordError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )


# --------------------------------------------------------------------------- #
# Admin: user management
# --------------------------------------------------------------------------- #
@router.get("", response_model=UserList, summary="List users (admin)", responses=_ADMIN_ERRORS)
def list_users(
    _: AdminUser,
    db: DbSession,
    role: UserRole | None = Query(default=None, description="Filter by role"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    q: str | None = Query(
        default=None, min_length=1, max_length=100, description="Search in email and full name"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = user_service.list_users(
        db, role=role, is_active=is_active, q=q, limit=limit, offset=offset
    )
    return UserList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user with any role (admin)",
    responses={**_ADMIN_ERRORS, 409: {"description": "Email already registered"}},
)
def create_user(payload: AdminUserCreate, _: AdminUser, db: DbSession):
    try:
        return user_service.create_user(
            db,
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
            role=payload.role,
        )
    except user_service.EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get a user by id (admin)",
    responses={**_ADMIN_ERRORS, 404: {"description": "User not found"}},
)
def get_user(user_id: UserId, _: AdminUser, db: DbSession):
    return _get_user_or_404(db, user_id)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user: role, status, name, email (admin)",
    responses={
        **_ADMIN_ERRORS,
        400: {"description": "Admins cannot change their own role or deactivate themselves"},
        404: {"description": "User not found"},
        409: {"description": "Email already registered"},
    },
)
def update_user(user_id: UserId, payload: AdminUserUpdate, admin: AdminUser, db: DbSession):
    user = _get_user_or_404(db, user_id)
    changes = payload.model_dump(exclude_unset=True)

    # Prevents an admin from locking themselves (and possibly everyone) out
    if user.id == admin.id and (
        ("role" in changes and changes["role"] != user.role) or changes.get("is_active") is False
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot change their own role or deactivate their own account",
        )

    try:
        return user_service.update_user(db, user, changes)
    except user_service.EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (admin)",
    responses={
        **_ADMIN_ERRORS,
        400: {"description": "Admins cannot delete themselves"},
        404: {"description": "User not found"},
        409: {"description": "User has related tickets/history: deactivate instead"},
    },
)
def delete_user(user_id: UserId, admin: AdminUser, db: DbSession):
    """Only works for users with no tickets or history. Otherwise deactivate with PATCH."""
    user = _get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot delete their own account"
        )
    try:
        user_service.delete_user(db, user)
    except user_service.UserHasRelatedRecordsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User has related tickets or history and cannot be deleted. "
            "Deactivate the account instead (PATCH is_active=false).",
        )
