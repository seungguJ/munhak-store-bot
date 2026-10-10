import datetime as dt

from alert import store
from alert.rules import change_alerts, is_stale, reminder_alerts

TODAY = dt.date(2026, 10, 10)
V = store.load_venues()


def titles(alerts):
    return [a["title"] for a in alerts]


def test_new_event_alert(make_event, make_data):
    alerts = change_alerts(make_data([]), make_data([make_event()]), V, TODAY)
    assert len(alerts) == 1
    a = alerts[0]
    assert a["title"].startswith("🆕 [S]")
    assert "인천문학경기장 주경기장" in a["body"]
    assert "4.9만" in a["body"]
    assert a["url"] == "./#event=kopis-PF000001"


def test_new_c_grade_or_past_or_cancelled_not_alerted(make_event, make_data):
    events = [
        make_event(id="kopis-C", grade="C"),
        make_event(id="kopis-PAST", start="2026-10-01", end="2026-10-02"),
        make_event(id="kopis-X", status="cancelled"),
    ]
    assert change_alerts(make_data([]), make_data(events), V, TODAY) == []


def test_grade_up_alert(make_event, make_data):
    old = make_data([make_event(grade="A")])
    new = make_data([make_event(grade="S")])
    assert titles(change_alerts(old, new, V, TODAY)) == ["⬆️ [A→S] 테스트 콘서트"]


def test_grade_down_silent(make_event, make_data):
    old = make_data([make_event(grade="S")])
    new = make_data([make_event(grade="A")])
    assert change_alerts(old, new, V, TODAY) == []


def test_cancel_alert(make_event, make_data):
    old = make_data([make_event()])
    new = make_data([make_event(status="cancelled")])
    assert titles(change_alerts(old, new, V, TODAY)) == ["❌ 취소: 테스트 콘서트"]


def test_reminders_d7_and_d1(make_event):
    events = [
        make_event(id="kopis-A", start="2026-10-17", end="2026-10-17"),
        make_event(id="kopis-B", start="2026-10-11", end="2026-10-12"),
        make_event(id="kopis-C", start="2026-10-12", end="2026-10-12"),
        make_event(id="kopis-D", start="2026-10-11", end="2026-10-11", grade="C"),
    ]
    alerts = reminder_alerts(events, V, TODAY)
    assert [a["url"] for a in alerts] == ["./#event=kopis-A", "./#event=kopis-B"]
    assert alerts[0]["title"].startswith("📅 D-7")
    assert "발주" not in alerts[0]["body"]
    assert alerts[1]["title"].startswith("⏰ 내일")


def test_is_stale():
    data = {"updated_at": "2026-10-05T06:30:00+09:00"}
    kst = dt.timezone(dt.timedelta(hours=9))
    assert is_stale(data, dt.datetime(2026, 10, 13, 6, 0, tzinfo=kst)) is False
    assert is_stale(data, dt.datetime(2026, 10, 13, 7, 0, tzinfo=kst)) is True
