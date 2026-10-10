"""실제 사례 회귀 테스트: 2026-10-09 리센느 (연수 능허대 문화축제, 연수한마음공원).

- 9/15 첫 보도 → 주 1회(월) 루틴이면 9/21에 발견 → D-18
- 처음 버전은 연수한마음공원이 행사장 목록에 없어 놓쳤던 사례
"""
import copy
import datetime as dt
from pathlib import Path

from alert import store
from alert.finalize import finalize
from alert.rules import change_alerts, reminder_alerts
from collectors.kopis import match_venue

FIXTURE = Path(__file__).parent / "fixtures" / "rescene_2026-10-09.json"
VENUES = store.load_venues()
ANNOUNCED = dt.date(2026, 9, 15)


def routine_output(today):
    return finalize(copy.deepcopy(store.load_json(FIXTURE)), VENUES, today)


def next_weekly_run(day, weekday=0):
    """루틴은 매주 월요일(weekday=0) 실행."""
    return day + dt.timedelta(days=(weekday - day.weekday()) % 7)


def test_venue_is_watched():
    assert "yeonsu-hanmaum" in VENUES
    assert VENUES["yeonsu-hanmaum"]["distance_km"] <= 3
    assert match_venue("연수한마음공원 일대", list(VENUES.values())) == "yeonsu-hanmaum"


def test_graded_s():
    e = routine_output(dt.date(2026, 9, 21))["events"][0]
    assert e["crowd_estimate"]["per_day"] == 40000
    assert e["grade"] == "S"


def test_weekly_routine_finds_it_with_enough_lead_time():
    found = next_weekly_run(ANNOUNCED)
    assert found == dt.date(2026, 9, 21)
    assert (dt.date(2026, 10, 9) - found).days >= 7  # D-7 리마인드보다 먼저 발견


def test_new_event_push_on_discovery_day():
    today = dt.date(2026, 9, 21)
    alerts = change_alerts({"events": []}, routine_output(today), VENUES, today)
    assert len(alerts) == 1
    assert alerts[0]["title"] == "🆕 [S] 제14회 연수 능허대 문화축제 (리센느·에일리·신인선 축하공연)"
    assert "연수한마음공원" in alerts[0]["body"]
    assert "4.0만" in alerts[0]["body"]


def test_reminders_d7_and_d1():
    events = routine_output(dt.date(2026, 9, 21))["events"]
    d7 = reminder_alerts(events, VENUES, dt.date(2026, 10, 2))
    d1 = reminder_alerts(events, VENUES, dt.date(2026, 10, 8))
    assert [a["title"][:6] for a in d7] == ["📦 D-7 "]
    assert "생수 ×3" in d7[0]["body"]
    assert [a["title"][:4] for a in d1] == ["⏰ 내일"]
    assert "17:00-19:00" in d1[0]["body"]
    assert reminder_alerts(events, VENUES, dt.date(2026, 10, 5)) == []


def test_not_alerted_again_next_week():
    old = routine_output(dt.date(2026, 9, 21))
    new = routine_output(dt.date(2026, 9, 28))
    assert change_alerts(old, new, VENUES, dt.date(2026, 9, 28)) == []
