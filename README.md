# IT Service Management API

RESTful API (FastAPI + PostgreSQL) for managing IT support tickets, users and technicians.

## Quick start (Docker)

```powershell
Copy-Item .env.example .env
docker compose up --build
```

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- DB health: http://localhost:8000/api/v1/health/db

Full documentation will be added as the project progresses.
