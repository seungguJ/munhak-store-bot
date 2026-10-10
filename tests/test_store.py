import pytest

from alert import store


def test_empty_events_file_is_valid():
    store.validate(store.load_json(store.EVENTS_PATH))


def test_valid_event_passes(make_event, make_data):
    store.validate(make_data([make_event()]))


def test_missing_field_fails(make_event, make_data):
    e = make_event()
    del e["venue_id"]
    with pytest.raises(store.ValidationError):
        store.validate(make_data([e]))


def test_order_advice_no_longer_allowed(make_event, make_data):
    with pytest.raises(store.ValidationError):
        store.validate(make_data([make_event(order_advice=[{"item": "생수", "multiplier": 3}])]))


def test_bad_grade_fails(make_event, make_data):
    with pytest.raises(store.ValidationError):
        store.validate(make_data([make_event(grade="SS")]))


def test_venue_by_id():
    venues = store.load_venues()
    assert venues["munhak-main"]["name"] == "인천문학경기장 주경기장"
    assert all("weight" in v for v in venues.values())
