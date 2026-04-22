from fastapi import FastAPI

from app.entrypoints.api.errors import register_exception_handlers
from app.entrypoints.api.middlewares.auth import AuthMiddleware
from app.entrypoints.api.routers import api_router
from app.infrastructure.config.settings import get_settings
from app.infrastructure.lifecycle import lifespan


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    register_exception_handlers(app)
    app.add_middleware(AuthMiddleware)
    app.include_router(api_router)
    return app
