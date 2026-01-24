from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.knowledge import router as knowledge_router
from app.api.v1.endpoints.agents import router as agents_router
from app.api.v1.endpoints.analytics import router as analytics_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(projects_router)
api_router.include_router(reports_router)
api_router.include_router(knowledge_router)
api_router.include_router(agents_router)
api_router.include_router(analytics_router)
