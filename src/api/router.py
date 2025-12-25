"""Router registration for all API endpoints."""

from fastapi import APIRouter

from src.api.v1 import chat, history, status

# Create main API router
api_router = APIRouter()

# Register v1 routers
api_router.include_router(chat.router)
api_router.include_router(history.router)
api_router.include_router(status.router)

__all__ = ["api_router"]

