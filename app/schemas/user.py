from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.models.enums import UserRole


def validate_password_strength(value: str) -> str:
    if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one letter and one digit")
    return value


def _clean_full_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("full_name must not be blank")
    return value


class UserCreate(BaseModel):
    """Public registration payload. There is intentionally no `role` field."""

    model_config = ConfigDict(
        extra="forbid",  # e.g. {"role": "admin"} is rejected with 422, not silently ignored
        json_schema_extra={
            "example": {
                "email": "ahmed@example.com",
                "full_name": "Ahmed Ali",
                "password": "Str0ngPassw0rd",
            }
        },
    )

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, v: str) -> str:
        return _clean_full_name(v)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password_strength(v)


class AdminUserCreate(UserCreate):
    """Admin-only: create a user with any role (e.g. a technician)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "tech1@example.com",
                "full_name": "Sara Technician",
                "password": "Str0ngPassw0rd",
                "role": "technician",
            }
        },
    )

    role: UserRole = UserRole.USER


class ProfileUpdate(BaseModel):
    """What a user may change about themselves."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1, max_length=150)

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, v: str) -> str:
        return _clean_full_name(v)


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return validate_password_strength(v)


class AdminUserUpdate(BaseModel):
    """Admin-only partial update. Send only the fields you want to change."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"role": "technician", "is_active": True}},
    )

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        return v.strip().lower() if v is not None else v

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, v: str | None) -> str | None:
        return _clean_full_name(v) if v is not None else v

    @model_validator(mode="after")
    def check_fields(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserList(BaseModel):
    items: list[UserRead]
    total: int
    limit: int
    offset: int
