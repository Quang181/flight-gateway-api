from fastapi import Depends

from app.application.use_cases.get_health_status import GetHealthStatus
from app.entrypoints.api.dependencies import get_health_use_case
from app.entrypoints.api.routers.system import router


@router.get("/health")
async def health(use_case: GetHealthStatus = Depends(get_health_use_case)) -> dict[str, str]:
    dependencies = await use_case.execute()
    status = "ok" if all(value == "ok" for value in dependencies.values()) else "degraded"
    return {"status": status, **dependencies}
