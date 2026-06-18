from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, scans, targets, reports, dashboard, webhooks, internal

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(scans.router, prefix="/scans", tags=["Scans"])
api_router.include_router(targets.router, prefix="/targets", tags=["Targets"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(internal.router, prefix="/internal", tags=["Internal"])
