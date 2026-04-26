import pytest

from app.application.use_cases.get_offer_detail import GetOfferDetail
from app.entrypoints.api.routers.flight.offer.schema import OfferDetailResponse


class FakeFlightRepository:
    def __init__(self, offer_detail_result: dict) -> None:
        self.offer_detail_result = offer_detail_result
        self.offer_detail_calls: list[str] = []

    async def get_airports(self) -> dict:
        raise NotImplementedError

    async def get_airport_detail(self, code: str) -> dict:
        raise NotImplementedError

    async def search_flights(self, criteria: dict) -> dict:
        raise NotImplementedError

    async def get_offer_detail(self, offer_id: str) -> dict:
        self.offer_detail_calls.append(offer_id)
        return self.offer_detail_result

    async def create_booking(self, payload: dict) -> dict:
        raise NotImplementedError

    async def get_booking(self, reference: str) -> dict:
        raise NotImplementedError

    async def get(self, key: str) -> dict | None:
        raise NotImplementedError

    async def set(self, key: str, value: dict, ttl_seconds: int) -> None:
        raise NotImplementedError

    async def set_offer_metadata(self, offer_id: str, value: dict, ttl_seconds: int) -> None:
        raise NotImplementedError

    async def get_offer_metadata(self, offer_id: str) -> dict | None:
        raise NotImplementedError


@pytest.mark.anyio
async def test_get_offer_detail_normalizes_to_clean_minimal_offer_shape() -> None:
    repository = FakeFlightRepository(
        {
            "data": {
                "offer": {
                    "id": "e945dda8961622a2",
                    "offer_id": "e945dda8961622a2",
                    "status": "LIVE",
                    "StatusCode": "A",
                    "fare_details": {
                        "rules": {
                            "refund": {
                                "allowed": False,
                                "penalty": {
                                    "amount": 150,
                                    "currency": "MYR",
                                    "CurrencyCode": "MYR",
                                },
                            },
                            "change": {
                                "allowed": True,
                                "penalty": {
                                    "amount": 0,
                                    "currency": "MYR",
                                },
                            },
                            "no_show": {
                                "penalty": {
                                    "amount": 500,
                                    "currency": "MYR",
                                }
                            },
                        },
                        "fare_family": "FLEX",
                        "FareFamily": "BS",
                    },
                    "baggage_allowance": {
                        "checked": {
                            "quantity": 0,
                            "max_weight_kg": 0,
                            "MaxWeight": "30KG",
                        },
                        "carry_on": {
                            "quantity": 1,
                            "max_weight_kg": 7,
                        },
                    },
                    "conditions": {
                        "advance_purchase_days": 21,
                        "min_stay_days": 0,
                        "max_stay_days": 365,
                    },
                    "payment_requirements": {
                        "accepted_methods": ["CC", "DC", "BT"],
                        "time_limit": "20260427235853",
                        "instant_ticketing_required": True,
                    },
                    "created_at": "26/04/2026 04:58",
                    "expires_at": "26/04/2026 06:53",
                }
            }
        }
    )
    use_case = GetOfferDetail(repository=repository)

    result = await use_case.execute("e945dda8961622a2")

    assert repository.offer_detail_calls == ["e945dda8961622a2"]
    assert result == {
        "offer": {
            "offer_id": "e945dda8961622a2",
            "status": "LIVE",
            "status_code": "A",
            "fare": {
                "family": "FLEX",
                "code": "BS",
            },
            "policy": {
                "refund": {
                    "allowed": False,
                    "penalty": {
                        "amount": 150.0,
                        "currency": "MYR",
                    },
                },
                "change": {
                    "allowed": True,
                    "penalty": {
                        "amount": 0.0,
                        "currency": "MYR",
                    },
                },
                "no_show": {
                    "penalty": {
                        "amount": 500.0,
                        "currency": "MYR",
                    },
                },
            },
            "baggage": {
                "checked": {
                    "quantity": 0,
                    "max_weight_kg": 30,
                },
                "carry_on": {
                    "quantity": 1,
                    "max_weight_kg": 7,
                },
            },
            "conditions": {
                "advance_purchase_days": 21,
                "min_stay_days": 0,
                "max_stay_days": 365,
            },
            "payment_requirements": {
                "accepted_methods": ["CC", "DC", "BT"],
                "time_limit": "2026-04-27T23:58:53Z",
                "instant_ticketing_required": True,
            },
            "created_at": "2026-04-26T04:58:00Z",
            "expires_at": "2026-04-26T06:53:00Z",
        }
    }


def test_offer_detail_response_schema_accepts_clean_offer_shape() -> None:
    payload = {
        "offer": {
            "offer_id": "offer-1",
            "status": "LIVE",
            "status_code": "A",
            "fare": {
                "family": "FLEX",
                "code": "BS",
            },
            "policy": {
                "refund": {
                    "allowed": False,
                    "penalty": {
                        "amount": 150.0,
                        "currency": "MYR",
                    },
                },
                "change": {
                    "allowed": True,
                    "penalty": {
                        "amount": 0.0,
                        "currency": "MYR",
                    },
                },
                "no_show": {
                    "penalty": {
                        "amount": 500.0,
                        "currency": "MYR",
                    },
                },
            },
            "baggage": {
                "checked": {
                    "quantity": 0,
                    "max_weight_kg": 30,
                },
                "carry_on": {
                    "quantity": 1,
                    "max_weight_kg": 7,
                },
            },
            "conditions": {
                "advance_purchase_days": 21,
                "min_stay_days": 0,
                "max_stay_days": 365,
            },
            "payment_requirements": {
                "accepted_methods": ["CC", "DC", "BT"],
                "time_limit": "2026-04-27T23:58:53Z",
                "instant_ticketing_required": True,
            },
            "created_at": "2026-04-26T04:58:00Z",
            "expires_at": "2026-04-26T06:53:00Z",
        }
    }

    response = OfferDetailResponse(**payload)

    assert response.offer.offer_id == "offer-1"
    assert response.offer.baggage.checked.max_weight_kg == 30
    assert response.offer.payment_requirements.instant_ticketing_required is True
