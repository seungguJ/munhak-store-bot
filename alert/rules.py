"""알림 판정 순수 함수 (spec §7). 알림 = {"title", "body", "url"}."""
import datetime as dt

from alert.grading import rank

WEEKDAYS = "월화수목금토일"
PUSH_GRADES = {"S", "A", "B"}  # C등급은 앱에만 표시


def _date(iso):
    d = dt.date.fromisoformat(iso)
    return "%d/%d(%s)" % (d.month, d.day, WEEKDAYS[d.weekday()])


def _period(e):
    if e["end"] == e["start"]:
        return _date(e["start"])
    return "%s~%s" % (_date(e["start"]), _date(e["end"]))


def _crowd(n):
    if n >= 10000:
        return "%.1f만" % (n / 10000.0)
    return "{:,}".format(n)


def _alert(e, title, body):
    return {"title": title, "body": body, "url": "./#event=%s" % e["id"]}


def _summary(e, venues):
    return "%s · %s · 하루 %s 명 예상" % (
        _period(e), venues[e["venue_id"]]["name"], _crowd(e["crowd_estimate"]["per_day"]))


def _upcoming(e, today):
    return e["status"] == "scheduled" and dt.date.fromisoformat(e["end"]) >= today


def change_alerts(old, new, venues, today):
    before = {e["id"]: e for e in old["events"]}
    alerts = []
    for e in new["events"]:
        prev = before.get(e["id"])
        if prev is None:
            if _upcoming(e, today) and e["grade"] in PUSH_GRADES:
                alerts.append(_alert(e, "🆕 [%s] %s" % (e["grade"], e["title"]), _summary(e, venues)))
        elif e["status"] == "cancelled" and prev["status"] != "cancelled":
            alerts.append(_alert(e, "❌ 취소: %s" % e["title"], "%s · %s" % (
                _period(e), venues[e["venue_id"]]["name"])))
        elif _upcoming(e, today) and rank(e["grade"]) > rank(prev["grade"]) \
                and e["grade"] in PUSH_GRADES:
            reason = e["popularity"]["evidence"][-1] if e["popularity"]["evidence"] else ""
            body = _summary(e, venues) + (" · " + reason if reason else "")
            alerts.append(_alert(e, "⬆️ [%s→%s] %s" % (prev["grade"], e["grade"], e["title"]), body))
    return alerts


def reminder_alerts(events, venues, today):
    alerts = []
    for e in events:
        if e["status"] != "scheduled" or e["grade"] not in PUSH_GRADES:
            continue
        days = (dt.date.fromisoformat(e["start"]) - today).days
        if days == 7:
            advice = ", ".join("%s ×%g" % (a["item"], a["multiplier"]) for a in e["order_advice"])
            alerts.append(_alert(e, "📦 D-7 [%s] %s" % (e["grade"], e["title"]),
                                 "발주 준비: %s · %s" % (advice or "음료·간식 보강", _summary(e, venues))))
        elif days == 1:
            peak = " / ".join(e["peak_hours"])
            alerts.append(_alert(e, "⏰ 내일 [%s] %s" % (e["grade"], e["title"]),
                                 (peak + " · " if peak else "") + _summary(e, venues)))
    return alerts


def is_stale(data, now, hours=36):
    updated = dt.datetime.fromisoformat(data["updated_at"])
    return now - updated > dt.timedelta(hours=hours)
