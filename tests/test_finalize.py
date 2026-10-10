import datetime as dt

import pytest

from alert import store
from alert.finalize import finalize

TODAY = dt.date(2026, 10, 10)


def raw(make_event, **kw):
    e = make_event(**kw)
    del e["grade"]
    e["crowd_estimate"] = {k: v for k, v in e["crowd_estimate"].items() if k != "per_day"}
    return e


def test_computes_crowd_and_grade(make_event, make_data):
    data = make_data([raw(make_event, crowd_estimate={"fill_rate": 0.5})])
    out = finalize(data, store.load_venues(), TODAY)
    e = out["events"][0]
    assert e["crowd_estimate"]["per_day"] == 24500  # 49000 * 0.5
    assert e["grade"] == "A"
    store.validate(out)


def test_capacity_override_and_far_weight(make_event, make_data):
    e = raw(make_event, venue_id="aetteul",
            crowd_estimate={"fill_rate": 1.0, "capacity_override": 20000})
    out = finalize(make_data([e]), store.load_venues(), TODAY)
    # 20000 * 가중치 0.5 = 10000 → A
    assert out["events"][0]["grade"] == "A"


def test_grade_adjust_applied(make_event, make_data):
    e = raw(make_event, crowd_estimate={"fill_rate": 0.5}, grade_adjust=1)
    out = finalize(make_data([e]), store.load_venues(), TODAY)
    assert out["events"][0]["grade"] == "S"


def test_past_event_marked_done(make_event, make_data):
    e = raw(make_event, start="2026-10-01", end="2026-10-02")
    out = finalize(make_data([e]), store.load_venues(), TODAY)
    assert out["events"][0]["status"] == "done"


def test_unknown_venue_rejected(make_event, make_data):
    with pytest.raises(ValueError):
        finalize(make_data([raw(make_event, venue_id="nowhere")]), store.load_venues(), TODAY)


def test_old_done_events_pruned(make_event, make_data):
    events = [raw(make_event, id="kopis-OLD", start="2026-09-01", end="2026-09-01"),
              raw(make_event, id="kopis-RECENT", start="2026-09-20", end="2026-09-20")]
    out = finalize(make_data(events), store.load_venues(), TODAY)
    assert [e["id"] for e in out["events"]] == ["kopis-RECENT"]
