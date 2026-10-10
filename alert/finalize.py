"""루틴이 push 전에 실행: 인파·등급을 결정론적으로 채우고 스키마 검증.

    python -m alert.finalize [data/events.json]
"""
import datetime as dt
import sys

from alert import store
from alert.grading import base_grade, crowd_per_day, final_grade

KST = dt.timezone(dt.timedelta(hours=9))


def finalize(data, venues, today):
    for e in data["events"]:
        venue = venues.get(e["venue_id"])
        if venue is None:
            raise ValueError("행사장 목록에 없는 venue_id: %s (%s)" % (e["venue_id"], e["title"]))
        crowd = e["crowd_estimate"]
        capacity = crowd.get("capacity_override", venue["capacity"])
        crowd["per_day"] = crowd_per_day(capacity, crowd["fill_rate"])
        e["grade"] = final_grade(base_grade(crowd["per_day"], venue["weight"]), e["grade_adjust"])
        if e["status"] == "scheduled" and dt.date.fromisoformat(e["end"]) < today:
            e["status"] = "done"
    data["events"].sort(key=lambda e: (e["start"], e["id"]))
    store.validate(data)
    return data


def main(argv):
    path = argv[1] if len(argv) > 1 else store.EVENTS_PATH
    data = store.load_json(path)
    now = dt.datetime.now(KST)
    data["updated_at"] = now.isoformat(timespec="seconds")
    try:
        finalize(data, store.load_venues(), now.date())
    except (ValueError, store.ValidationError) as err:
        print("[finalize] 실패: %s" % err, file=sys.stderr)
        return 1
    store.save_json(path, data)
    print("[finalize] OK: 행사 %d건" % len(data["events"]))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
