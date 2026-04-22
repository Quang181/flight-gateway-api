from app.entrypoints.api.decorators import require_token
from app.entrypoints.api.errors import AppAuthorizedResponse
from app.entrypoints.api.routers.system import router


@router.get("/secure/ping")
@require_token
async def secure_ping() -> None:
    raise AppAuthorizedResponse()
