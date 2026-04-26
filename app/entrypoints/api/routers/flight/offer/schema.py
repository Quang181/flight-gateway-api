from typing import Any

from pydantic import BaseModel, Field


class OfferPenaltyResponse(BaseModel):
    amount: float | None = None
    currency: str | None = None


class OfferPolicyRuleResponse(BaseModel):
    allowed: bool | None = None
    penalty: OfferPenaltyResponse | None = None


class OfferFareResponse(BaseModel):
    family: str | None = None
    code: str | None = None


class OfferBaggagePieceResponse(BaseModel):
    quantity: int | None = None
    max_weight_kg: int | None = None


class OfferBaggageResponse(BaseModel):
    checked: OfferBaggagePieceResponse | None = None
    carry_on: OfferBaggagePieceResponse | None = None


class OfferConditionsResponse(BaseModel):
    advance_purchase_days: int | None = None
    min_stay_days: int | None = None
    max_stay_days: int | None = None


class OfferPaymentRequirementsResponse(BaseModel):
    accepted_methods: list[str] = Field(default_factory=list)
    time_limit: str | None = None
    instant_ticketing_required: bool | None = None


class OfferSummaryResponse(BaseModel):
    offer_id: str | None = None
    status: str | None = None
    status_code: str | None = None
    fare: OfferFareResponse = Field(default_factory=OfferFareResponse)
    policy: dict[str, OfferPolicyRuleResponse | None] = Field(default_factory=dict)
    baggage: OfferBaggageResponse = Field(default_factory=OfferBaggageResponse)
    conditions: OfferConditionsResponse = Field(default_factory=OfferConditionsResponse)
    payment_requirements: OfferPaymentRequirementsResponse = Field(default_factory=OfferPaymentRequirementsResponse)
    created_at: str | None = None
    expires_at: str | None = None


class OfferDetailResponse(BaseModel):
    offer: OfferSummaryResponse
