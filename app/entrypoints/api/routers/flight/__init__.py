from fastapi import APIRouter

from app.entrypoints.api.routers.flight.list.router import router as list_router

router = APIRouter(tags=["flight"])

router.include_router(list_router)
