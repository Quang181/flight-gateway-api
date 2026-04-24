from __future__ import annotations

import json
from pathlib import Path


def get_default_airline_labels_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "airlines.json"


def load_airline_labels(path: str | Path) -> dict[str, str]:
    json_path = Path(path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    labels: dict[str, str] = {}

    if isinstance(payload, dict):
        for raw_code, raw_name in payload.items():
            code = str(raw_code).strip().upper()
            name = str(raw_name).strip()
            if code and name:
                labels[code] = name
        return labels

    for item in payload:
        if isinstance(item, dict):
            code = str(item.get("code", "")).strip().upper()
            name = str(item.get("name", "")).strip()
            if code and name:
                labels[code] = name

    return labels
