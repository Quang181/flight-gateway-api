from typing import Any

from pydantic import BaseModel, Field


class OfferDetailDataResponse(BaseModel):
    policy: dict[str, Any] = Field(default_factory=dict)
    baggage_allowance: dict[str, Any] = Field(default_factory=dict)
    conditions: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    expires_at: str | None = None


class OfferDetailResponse(BaseModel):
    data: OfferDetailDataResponse
