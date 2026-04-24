from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.common.constant import UNKNOWN_LABEL


def first_value(data: Any, *paths: str) -> Any:
    for path in paths:
        value = _get_path(data, path)
        if value is not None and value != "":
            return value
    return None


def normalize_datetime(value: Any) -> str | None:
    if value in (None, ""):
        return None

    if isinstance(value, datetime):
        dt = value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
        return dt.isoformat().replace("+00:00", "Z")

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC).isoformat().replace("+00:00", "Z")
        except (OSError, OverflowError, ValueError):
            return None

    raw = str(value).strip()
    if not raw:
        return None

    if raw.isdigit():
        if len(raw) == 14:
            try:
                dt = datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
                return dt.isoformat().replace("+00:00", "Z")
            except ValueError:
                return None
        try:
            return datetime.fromtimestamp(float(raw), tz=UTC).isoformat().replace("+00:00", "Z")
        except (OSError, OverflowError, ValueError):
            return None

    for parser in (
            lambda text: datetime.fromisoformat(text.replace("Z", "+00:00")),
            lambda text: datetime.strptime(text, "%d/%m/%Y").replace(tzinfo=UTC),
            lambda text: datetime.strptime(text, "%d/%m/%Y %H:%M").replace(tzinfo=UTC),
            lambda text: datetime.strptime(text, "%d/%m/%Y %H:%M:%S").replace(tzinfo=UTC),
            lambda text: datetime.strptime(text, "%d-%b-%Y %I:%M %p").replace(tzinfo=UTC),
            lambda text: datetime.strptime(text, "%Y-%m-%d"),
    ):
        try:
            dt = parser(raw)
            if dt.tzinfo is None:
                # Keep date-only values simple and avoid inventing a local timezone.
                if raw.count("-") == 2 and "T" not in raw and " " not in raw:
                    return dt.strftime("%Y-%m-%d")
                dt = dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
        except ValueError:
            continue

    return None


def normalize_price(data: Any) -> dict[str, Any] | None:
    amount_value = first_value(
        data,
        "price.totalAmountDecimal",
        "price.total_amount",
        "price.total",
        "price.amount",
        "pricing.totalAmountDecimal",
        "pricing.total_amount",
        "pricing.total",
        "pricing.amount",
        "totalAmountDecimal",
        "total_amount",
        "total",
        "amount",
    )
    if amount_value is None:
        return None

    try:
        amount = Decimal(str(amount_value))
    except (InvalidOperation, ValueError):
        return None

    currency = first_value(
        data,
        "price.currency",
        "price.currency_code",
        "price.currencyCode",
        "pricing.currency",
        "pricing.currency_code",
        "pricing.currencyCode",
        "currency",
        "currency_code",
        "currencyCode",
    )
    normalized_amount = float(amount.quantize(Decimal("0.01")))
    return {
        "amount": normalized_amount,
        "currency": currency,
        "display": f"{currency} {normalized_amount:.2f}" if currency else f"{normalized_amount:.2f}",
    }


def airline_info(code: Any, name: Any = None, airline_labels: dict[str, str] | None = None) -> dict[str, Any]:
    normalized_code = str(code).strip() if code not in (None, "") else None
    label = name or (airline_labels or {}).get(normalized_code, UNKNOWN_LABEL)
    return {"code": normalized_code, "label": label}


def normalize_trip_offer_summary(item: dict[str, Any], airline_labels: dict[str, str] | None = None) -> dict[str, Any]:
    legs = _extract_offer_legs(item)
    first_leg = legs[0] if legs else {}
    last_leg = legs[-1] if legs else {}
    marketing_code = first_value(
        first_leg,
        "carrier.marketing",
        "carrier.mktg_carrier",
        "carrier.operating",
    )
    departure_at = normalize_datetime(
        first_value(
            first_leg,
            "departure_info.scheduled_time",
            "departure_info.dt",
        )
    )
    arrival_at = normalize_datetime(
        first_value(
            last_leg,
            "arrival_info.scheduled_time",
            "arrival_info.arr_date",
        )
    )
    duration_minutes = _to_int(
        first_value(
            item,
            "total_journey_time",
            "duration_minutes",
            "durationMinutes",
        )
    )
    if duration_minutes is None:
        duration_minutes = sum(_to_int(leg.get("duration_minutes")) or 0 for leg in legs) or None

    stops = _to_int(first_value(item, "stops", "num_stops", "stops_count", "stopsCount"))
    if stops is None and legs:
        stops = max(len(legs) - 1, 0)

    airline = airline_info(marketing_code, airline_labels=airline_labels)
    return {
        "price": normalize_price(item),
        "airline_name": airline["label"],
        "departure_at": departure_at,
        "arrival_at": arrival_at,
        "stops": stops,
        "flight_duration": normalize_duration(duration_minutes),
    }


def normalize_offer_detail(data: dict[str, Any]) -> dict[str, Any]:
    payload = unwrap_data(data)
    offer = first_value(payload, "offer") if isinstance(first_value(payload, "offer"), dict) else payload
    fare_details = first_value(offer, "fare_details", "fareDetails") or {}
    rules = fare_details.get("rules", {})
    rule_refund = rules.get("refund")
    rule_change = rules.get("change")

    baggage_allowance = first_value(offer, "baggage_allowance", "baggageAllowance") or {}
    conditions = first_value(offer, "conditions") or {}
    created_at = normalize_datetime(first_value(offer, "created_at", "createdAt", "created"))
    expires_at = normalize_datetime(first_value(offer, "expires_at", "expiresAt", "expiry_at", "expiryAt"))

    return {
        "data": {
            "policy": {
                "refund": rule_refund,
                "change": rule_change,
            },
            "baggage_allowance": baggage_allowance,
            "conditions": conditions,
            "created_at": created_at,
            "expires_at": expires_at,
        }
    }

def normalize_booking(data: dict[str, Any],
                      method="GET") -> dict[str, Any]:
    payload = unwrap_data(data)
    if method == "GET":
        payload = payload.get("reservation", {})

    passengers = mapping_passengers(passengers=payload.get("passengers", []))
    contact = payload.get("contact", {})
    ticketing = payload.get("ticketing", {})

    return {
        "booking_reference": payload.get('booking_ref'),
        "summary": {
            "pnr": payload.get("pnr"),
            "status": payload.get("status"),
            "status_code": payload.get("StatusCode"),
            "created_at": normalize_datetime(payload.get("created_at")),

            "contact": {
                "email": contact.get("email"),
                "phone": contact.get("phone")
            },

            "passengers": passengers,

            "ticketing": {
                "status": ticketing.get("status"),
                "time_limit": normalize_datetime(ticketing.get("time_limit")),
                "ticket_numbers": ticketing.get("ticket_numbers"),
            }
        }
    }


def unwrap_data(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    payload = first_value(data, "data", "result", "offer", "booking", "reservation")
    return payload if isinstance(payload, dict) else data

def _extract_offer_legs(item: dict[str, Any]) -> list[dict[str, Any]]:
    segment_list = first_value(item, "segments.segment_list")
    if not isinstance(segment_list, list):
        return []

    legs: list[dict[str, Any]] = []
    for segment in segment_list:
        if not isinstance(segment, dict):
            continue
        leg_data = segment.get("leg_data")
        if isinstance(leg_data, list):
            legs.extend(leg for leg in leg_data if isinstance(leg, dict))
    return legs

def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_duration(duration_minutes: int | None) -> dict[str, Any] | None:
    if duration_minutes is None:
        return None
    hours, minutes = divmod(duration_minutes, 60)
    return {
        "duration_minutes": duration_minutes,
        "display": f"{hours}h {minutes:02d}m",
    }

def _get_path(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current

def mapping_passengers(passengers: list) -> list:
    data_mapping = []
    for passenger in passengers:
        data_mapping.append(         {
                    "pax_id": passenger.get("pax_id"),
                    "type": passenger.get("type"),
                    "first_name": passenger.get("first_name"),
                    "last_name": passenger.get("first_name"),
                    "name": passenger.get("name"),
                    "title": passenger.get("title"),
                    "dob": passenger.get("dob"),
                    "nationality": passenger.get("nationality"),
                    "passport_no": passenger.get("passport_no"),
                })
    return data_mapping
