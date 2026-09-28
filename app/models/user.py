from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole, db_enum
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.ticket import Ticket


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # Emails are stored lowercase => uniqueness is effectively case-insensitive
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint("length(trim(full_name)) > 0", name="full_name_not_blank"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        db_enum(UserRole, "user_role"),
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())

    created_tickets: Mapped[list[Ticket]] = relationship(
        back_populates="creator", foreign_keys="Ticket.created_by_id"
    )
    assigned_tickets: Mapped[list[Ticket]] = relationship(
        back_populates="assignee", foreign_keys="Ticket.assigned_to_id"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
