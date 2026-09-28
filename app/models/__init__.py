# Import all models so they register on Base.metadata (needed by Alembic)
from app.models.enums import TicketPriority, TicketStatus, UserRole
from app.models.ticket import Ticket, TicketHistory
from app.models.user import User

__all__ = [
    "User",
    "Ticket",
    "TicketHistory",
    "UserRole",
    "TicketStatus",
    "TicketPriority",
]
