from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.common.constant import (
    AIRLINE_LABELS,
    CABIN_LABELS,
    PAYMENT_METHOD_LABELS,
    UNKNOWN_LABEL,
)


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


def duration_minutes_from_datetimes(departure_at: Any, arrival_at: Any) -> int | None:
    departure = _coerce_datetime(departure_at)
    arrival = _coerce_datetime(arrival_at)
    if departure is None or arrival is None:
        return None

    delta_minutes = int((arrival - departure).total_seconds() // 60)
    return delta_minutes if delta_minutes >= 0 else None


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


def airline_info(code: Any, name: Any = None) -> dict[str, Any]:
    normalized_code = str(code).strip() if code not in (None, "") else None
    label = name or AIRLINE_LABELS.get(normalized_code, UNKNOWN_LABEL)
    return {"code": normalized_code, "label": label}


def cabin_info(code: Any) -> dict[str, Any]:
    normalized_code = str(code).strip() if code not in (None, "") else None
    return {
        "code": normalized_code,
        "label": CABIN_LABELS.get(normalized_code, UNKNOWN_LABEL),
    }


def normalize_airport(data: Any, default_code: Any = None) -> dict[str, Any]:
    code = first_value(data, "code", "airport_code", "iata", "iata_code") or default_code
    name = first_value(data, "name", "airport_name", "label")
    city = first_value(data, "city", "city_name")
    country = first_value(data, "country", "country_name")
    return {
        "code": code,
        "name": name or code,
        "city": city,
        "country": country,
    }


def normalize_segment(segment: dict[str, Any]) -> dict[str, Any]:
    departure_data = first_value(segment, "departure", "origin", "from") or {}
    arrival_data = first_value(segment, "arrival", "destination", "to") or {}
    departure_at = normalize_datetime(
        first_value(segment, "departure_at", "departureAt", "departure_time", "departureTime", "departure.datetime")
        or first_value(departure_data, "datetime", "time", "at")
    )
    arrival_at = normalize_datetime(
        first_value(segment, "arrival_at", "arrivalAt", "arrival_time", "arrivalTime", "arrival.datetime")
        or first_value(arrival_data, "datetime", "time", "at")
    )
    marketing_code = first_value(segment, "airline_code", "airlineCode", "carrier_code", "carrierCode", "airline.code")
    marketing_name = first_value(segment, "airline_name", "airlineName", "carrier_name", "carrierName", "airline.name")
    return {
        "flight_number": first_value(segment, "flight_number", "flightNumber", "number"),
        "airline": airline_info(marketing_code, marketing_name),
        "origin": normalize_airport(departure_data, first_value(segment, "origin_code", "from_code")),
        "destination": normalize_airport(arrival_data, first_value(segment, "destination_code", "to_code")),
        "departure_at": departure_at,
        "arrival_at": arrival_at,
        "duration_minutes": first_value(segment, "duration_minutes", "durationMinutes")
                            or duration_minutes_from_datetimes(departure_at, arrival_at),
        "cabin": cabin_info(first_value(segment, "cabin", "cabin_code", "cabinCode")),
    }


def normalize_flight_item(item: dict[str, Any]) -> dict[str, Any]:
    segments = _extract_segments(item)
    normalized_segments = [normalize_segment(segment) for segment in segments]
    first_segment = normalized_segments[0] if normalized_segments else None
    last_segment = normalized_segments[-1] if normalized_segments else None
    departure_at = first_segment["departure_at"] if first_segment else normalize_datetime(
        first_value(item, "departure_at", "departureAt"))
    arrival_at = last_segment["arrival_at"] if last_segment else normalize_datetime(
        first_value(item, "arrival_at", "arrivalAt"))
    airline = first_segment["airline"] if first_segment else airline_info(
        first_value(item, "airline_code", "airlineCode"), first_value(item, "airline_name", "airlineName"))
    cabin = cabin_info(first_value(item, "cabin", "cabin_code", "cabinCode"))
    normalized_price = normalize_price(item)
    stops = first_value(item, "stops", "stops_count", "stopsCount")
    if stops is None:
        stops = max(len(normalized_segments) - 1, 0)

    result = {
        "offer_id": first_value(item, "offer_id", "offerId", "id"),
        "airline": airline,
        "cabin": cabin,
        "origin": first_segment["origin"] if first_segment else normalize_airport(first_value(item, "origin") or {},
                                                                                  first_value(item, "origin_code",
                                                                                              "originCode")),
        "destination": last_segment["destination"] if last_segment else normalize_airport(
            first_value(item, "destination") or {}, first_value(item, "destination_code", "destinationCode")),
        "departure_at": departure_at,
        "arrival_at": arrival_at,
        "duration_minutes": first_value(item, "duration_minutes", "durationMinutes")
                            or duration_minutes_from_datetimes(departure_at, arrival_at),
        "stops": int(stops) if isinstance(stops, (int, float, str)) and str(stops).isdigit() else stops,
        "price": normalized_price,
        "segments": normalized_segments,
        "raw": item,
    }
    return result


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


def normalize_code_label(code: Any, labels: dict[str, str], fallback_label: Any = None) -> dict[str, Any]:
    normalized_code = str(code).strip() if code not in (None, "") else None
    label = labels.get(normalized_code) or fallback_label or (UNKNOWN_LABEL if normalized_code else None)
    return {
        "code": normalized_code,
        "label": label,
    }


def normalize_conditions(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    return {
        "advance_purchase_days": _to_int(first_value(data, "advance_purchase_days", "advancePurchaseDays")),
        "min_stay_days": _to_int(first_value(data, "min_stay_days", "minStayDays")),
        "max_stay_days": _to_int(first_value(data, "max_stay_days", "maxStayDays")),
    }


def normalize_payment_requirements(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    accepted_methods = [
        normalize_code_label(method, PAYMENT_METHOD_LABELS)
        for method in _ensure_list(first_value(data, "accepted_methods", "acceptedMethods"))
    ]
    return {
        "accepted_methods": accepted_methods,
        "time_limit": normalize_datetime(first_value(data, "time_limit", "timeLimit")),
        "instant_ticketing_required": bool(first_value(data, "instant_ticketing_required", "instantTicketingRequired")),
    }


def normalize_fare_rules(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    return {
        "refund": normalize_policy(data, "refund"),
        "change": normalize_policy(data, "change"),
        "no_show": normalize_policy(data, "no_show", "noShow"),
    }


def normalize_policy(data: Any, *paths: str) -> dict[str, Any] | None:
    policy = first_value(data, *paths)
    if not isinstance(policy, dict):
        return None
    allowed = first_value(policy, "allowed")
    penalty = normalize_price(first_value(policy, "penalty") or {})
    result: dict[str, Any] = {}
    if isinstance(allowed, bool):
        result["allowed"] = allowed
    if penalty is not None:
        result["penalty"] = penalty
    return result or None


def normalize_baggage(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    return {
        "checked": normalize_baggage_item(first_value(data, "checked")),
        "carry_on": normalize_baggage_item(first_value(data, "carry_on", "carryOn")),
    }


def normalize_baggage_item(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    quantity = _to_int(first_value(data, "quantity", "pieces"))
    max_weight = _to_int(first_value(data, "max_weight_kg", "maxWeightKg"))
    parsed_max_weight = _parse_weight_kg(first_value(data, "MaxWeight", "max_weight", "weight"))
    return {
        "quantity": quantity,
        "max_weight_kg": max_weight if max_weight not in (None, 0) else parsed_max_weight,
    }


def normalize_booking(data: dict[str, Any]) -> dict[str, Any]:
    payload = unwrap_data(data)
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


def _extract_segments(item: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("segments", "legs", "slices", "itinerary.segments", "journey.segments"):
        value = first_value(item, key)
        if isinstance(value, list):
            return [segment for segment in value if isinstance(segment, dict)]
    itineraries = _ensure_list(first_value(item, "itineraries", "journeys"))
    if itineraries:
        segments: list[dict[str, Any]] = []
        for itinerary in itineraries:
            if isinstance(itinerary, dict):
                segments.extend(_extract_segments(itinerary))
        return segments
    return []


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _coerce_datetime(value: Any) -> datetime | None:
    normalized = normalize_datetime(value)
    if normalized is None:
        return None
    if len(normalized) == 10:
        try:
            return datetime.strptime(normalized, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            return None
    try:
        return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_weight_kg(value: Any) -> int | None:
    if value in (None, ""):
        return None
    match = re.search(r"(\d+)", str(value))
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


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
