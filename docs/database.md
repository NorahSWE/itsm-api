# Database design

PostgreSQL 16, accessed through SQLAlchemy 2.0. Schema changes are managed with Alembic migrations.

```mermaid
erDiagram
    USERS ||--o{ TICKETS : "creates (created_by_id)"
    USERS |o--o{ TICKETS : "assigned to (assigned_to_id)"
    TICKETS ||--o{ TICKET_HISTORY : "has"
    USERS ||--o{ TICKET_HISTORY : "changed_by_id"

    USERS {
        int id PK
        string email UK
        string full_name
        string hashed_password
        user_role role
        bool is_active
        timestamptz created_at
        timestamptz updated_at
    }
    TICKETS {
        int id PK
        string title
        text description
        ticket_status status
        ticket_priority priority
        int created_by_id FK
        int assigned_to_id FK
        timestamptz resolved_at
        timestamptz closed_at
        timestamptz created_at
        timestamptz updated_at
    }
    TICKET_HISTORY {
        int id PK
        int ticket_id FK
        int changed_by_id FK
        string field
        string old_value
        string new_value
        timestamptz created_at
    }
```

## Enums (native PostgreSQL types)

| Type | Values |
|---|---|
| `user_role` | admin, technician, user |
| `ticket_status` | open, in_progress, resolved, closed |
| `ticket_priority` | low, medium, high, critical |

## Foreign keys

| Column | References | On delete |
|---|---|---|
| `tickets.created_by_id` | users.id | RESTRICT (deactivate users instead of deleting) |
| `tickets.assigned_to_id` | users.id | SET NULL (ticket becomes unassigned) |
| `ticket_history.ticket_id` | tickets.id | CASCADE |
| `ticket_history.changed_by_id` | users.id | RESTRICT |

## Check constraints

- `users.email` must be lowercase (uniqueness is therefore case-insensitive).
- `users.full_name` and `tickets.title` must not be blank.
- `resolved` / `closed` tickets must have `resolved_at`; `closed` tickets must have `closed_at`.

Rules that span tables (e.g. "assigned user must be a technician", allowed status transitions) are enforced in the service layer.

## Indexes

`users.email` (unique), `tickets.created_by_id`, `tickets.assigned_to_id`, `(tickets.status, tickets.priority)`, `ticket_history.(ticket_id, created_at)`, `ticket_history.changed_by_id`.
