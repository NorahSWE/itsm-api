from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings

tags_metadata = [
    {"name": "Authentication", "description": "Register and login (JWT)."},
    {"name": "Users", "description": "My profile, and user management for admins."},
    {"name": "Health", "description": "Service and database health checks."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "RESTful API for IT Service Management: tickets, users, technicians, "
        "statuses and priorities.\n\n"
        "**To try protected endpoints:** register, then click **Authorize** and log in "
        "(use your email as the username)."
    ),
    openapi_tags=tags_metadata,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"message": settings.PROJECT_NAME, "docs": "/docs"}
