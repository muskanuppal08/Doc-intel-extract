"""Central API v1 router consolidating all domain endpoints."""

from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.questions import router as questions_router
from app.api.v1.endpoints.reviews import router as reviews_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(questions_router)
api_router.include_router(reviews_router)
