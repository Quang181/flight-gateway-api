from fastapi import APIRouter

from app.entrypoints.api.routers.flight import router as flight_router
from app.entrypoints.api.routers.system import router as system_router


api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(flight_router)
