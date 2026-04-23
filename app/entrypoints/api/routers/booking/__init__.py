from fastapi import APIRouter

from app.entrypoints.api.routers.booking.create.router import router as create_router
from app.entrypoints.api.routers.booking.detail.router import router as detail_router

router = APIRouter(tags=["booking"])
router.include_router(create_router)
router.include_router(detail_router)
