from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from app.application.use_cases.list_flights import ListFlights
from app.entrypoints.api.dependencies import get_list_flights_use_case
from app.entrypoints.api.routers.flight.list.schema import FlightListQuery, FlightListResponse

router = APIRouter()


@router.get("/search", response_model=FlightListResponse)
# @require_token
async def list_flights(
    background_tasks: BackgroundTasks,
    query: FlightListQuery = Depends(),
    use_case: ListFlights = Depends(get_list_flights_use_case),
) -> FlightListResponse:
    return FlightListResponse(**await use_case.execute(query.model_dump(mode="json"), background_tasks))
