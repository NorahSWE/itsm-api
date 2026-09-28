from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    USER = "user"


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def db_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    """Native PostgreSQL ENUM storing the lowercase *values* (not the member names)."""
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda e: [m.value for m in e],
    )
