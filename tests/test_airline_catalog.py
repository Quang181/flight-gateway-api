import json

from app.infrastructure.airlines.catalog import load_airline_labels


def test_load_airline_labels_returns_code_to_name_mapping(tmp_path) -> None:
    json_path = tmp_path / "airlines.json"
    json_path.write_text(
        json.dumps(
            {
                "mh": "Malaysia Airlines",
                "AK": "AirAsia",
            }
        ),
        encoding="utf-8",
    )

    result = load_airline_labels(json_path)

    assert result == {
        "MH": "Malaysia Airlines",
        "AK": "AirAsia",
    }
