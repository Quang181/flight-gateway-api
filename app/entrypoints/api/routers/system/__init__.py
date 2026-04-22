from fastapi import APIRouter


router = APIRouter(tags=["system"])


from app.entrypoints.api.routers.system import health, secure  # noqa: F401,E402
