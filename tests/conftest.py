import copy

import pytest

BASE_EVENT = {
    "id": "kopis-PF000001",
    "title": "테스트 콘서트",
    "category": "concert",
    "venue_id": "munhak-main",
    "start": "2026-11-14",
    "end": "2026-11-15",
    "show_times": ["18:00"],
    "status": "scheduled",
    "popularity": {"sold_out": True, "extra_shows": False, "evidence": ["매진"]},
    "crowd_estimate": {"fill_rate": 1.0, "per_day": 49000},
    "grade_adjust": 0,
    "grade": "S",
    "peak_hours": ["16:00-18:00 입장 전"],
    "order_advice": [{"item": "생수", "multiplier": 3}],
    "sources": ["https://example.com"],
    "first_seen": "2026-10-01",
    "last_changed": "2026-10-01",
}


@pytest.fixture
def make_event():
    def _make(**overrides):
        e = copy.deepcopy(BASE_EVENT)
        e.update(overrides)
        return e
    return _make


@pytest.fixture
def make_data():
    def _make(events):
        return {"updated_at": "2026-10-10T06:30:00+09:00", "events": events, "venue_suggestions": []}
    return _make
