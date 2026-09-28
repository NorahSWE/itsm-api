from fastapi import FastAPI

from app.api.v1 import health
from app.core.config import settings

tags_metadata = [
    {"name": "Health", "description": "Service and database health checks."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RESTful API for IT Service Management: tickets, users, technicians, statuses and priorities.",
    openapi_tags=tags_metadata,
)

app.include_router(health.router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"message": settings.PROJECT_NAME, "docs": "/docs"}
