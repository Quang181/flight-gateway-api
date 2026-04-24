from fastapi import APIRouter

from app.entrypoints.api.routers.booking import router as booking_router
from app.entrypoints.api.routers.flight import router as flight_router


api_router = APIRouter(prefix="/flights")
api_router.include_router(flight_router)
api_router.include_router(booking_router)
