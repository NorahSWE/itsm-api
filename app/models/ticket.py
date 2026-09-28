from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TicketPriority, TicketStatus, db_enum
from app.models.mixins import TimestampMixin
from app.models.user import User


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="title_not_blank"),
        # Timestamps must be consistent with the workflow state
        CheckConstraint(
            "status NOT IN ('resolved', 'closed') OR resolved_at IS NOT NULL",
            name="resolved_has_timestamp",
        ),
        CheckConstraint(
            "status <> 'closed' OR closed_at IS NOT NULL",
            name="closed_has_timestamp",
        ),
        Index("ix_tickets_status_priority", "status", "priority"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(
        db_enum(TicketStatus, "ticket_status"),
        default=TicketStatus.OPEN,
        server_default=TicketStatus.OPEN.value,
    )
    priority: Mapped[TicketPriority] = mapped_column(
        db_enum(TicketPriority, "ticket_priority"),
        default=TicketPriority.MEDIUM,
        server_default=TicketPriority.MEDIUM.value,
    )

    # A user who created tickets cannot be hard-deleted (deactivate instead)
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    # If the technician account is removed, the ticket becomes unassigned
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, default=None
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    creator: Mapped[User] = relationship(
        back_populates="created_tickets", foreign_keys=[created_by_id]
    )
    assignee: Mapped[User | None] = relationship(
        back_populates="assigned_tickets", foreign_keys=[assigned_to_id]
    )
    history: Mapped[list[TicketHistory]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketHistory.created_at",
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} status={self.status} priority={self.priority}>"


class TicketHistory(Base):
    """Append-only audit log: one row per change made to a ticket."""

    __tablename__ = "ticket_history"
    __table_args__ = (Index("ix_ticket_history_ticket_id_created_at", "ticket_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    changed_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    # e.g. "created", "status", "priority", "assigned_to", "title", "description"
    field: Mapped[str] = mapped_column(String(50))
    old_value: Mapped[str | None] = mapped_column(String(255), default=None)
    new_value: Mapped[str | None] = mapped_column(String(255), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ticket: Mapped[Ticket] = relationship(back_populates="history")
    changed_by: Mapped[User] = relationship()
