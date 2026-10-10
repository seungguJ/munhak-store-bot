"""events.json / venues.json 입출력과 스키마 검증."""
import json
from pathlib import Path

import jsonschema
from jsonschema import ValidationError  # noqa: F401  (re-export)

ROOT = Path(__file__).resolve().parent.parent
EVENTS_PATH = ROOT / "data" / "events.json"
VENUES_PATH = ROOT / "data" / "venues.json"
SCHEMA_PATH = ROOT / "schema" / "events.schema.json"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_venues(path=VENUES_PATH):
    """{venue_id: venue} 딕셔너리."""
    return {v["id"]: v for v in load_json(path)["venues"]}


def validate(data):
    """스키마 위반 시 jsonschema.ValidationError."""
    jsonschema.validate(data, load_json(SCHEMA_PATH))
