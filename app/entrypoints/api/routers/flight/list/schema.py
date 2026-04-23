from typing import Literal

from pydantic import BaseModel, Field

from app.application.common.constant import DATE_YYYY_MM_DD_REGEX


class FlightListQuery(BaseModel):
    origin: str
    destination: str
    departure_date: str = Field(..., pattern=DATE_YYYY_MM_DD_REGEX)
    return_date: str = Field(..., pattern=DATE_YYYY_MM_DD_REGEX)
    pax_count: int
    cabin: Literal["Y", "W", "C", "F"] = "Y"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
