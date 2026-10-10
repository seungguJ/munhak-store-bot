"""GitHub Actions에서 실행하는 알림 CLI.

    python -m alert.notify changes OLD.json NEW.json   # events.json push 시
    python -m alert.notify reminders [events.json]     # 매일 D-7 / D-1
    python -m alert.notify stale [events.json]         # 루틴 정지 감지 (exit 3)
    python -m alert.notify suggestions [events.json]   # 목록 밖 행사장 후보 (있으면 exit 4)
    python -m alert.notify test                        # 설치 확인용 테스트 알림

환경변수: PUSH_SUBSCRIPTIONS(JSON 배열), VAPID_PRIVATE_KEY, VAPID_SUBJECT(mailto:...)
구독이 없으면 보낼 내용만 출력한다(dry-run). 만료 구독이 있으면 exit 2.
"""
import datetime as dt
import json
import os
import sys

from alert import store
from alert.push import send_all
from alert.rules import change_alerts, is_stale, reminder_alerts

KST = dt.timezone(dt.timedelta(hours=9))
EMPTY = {"events": []}


def _load(path):
    return store.load_json(path) if os.path.exists(path) else EMPTY


def deliver(alerts):
    for a in alerts:
        print("· %s | %s" % (a["title"], a["body"]))
    if not alerts:
        print("보낼 알림 없음")
        return 0
    subs = json.loads(os.environ.get("PUSH_SUBSCRIPTIONS") or "[]")
    if not subs:
        print("[dry-run] PUSH_SUBSCRIPTIONS 없음 → 전송 생략")
        return 0
    expired = send_all(alerts, subs, os.environ["VAPID_PRIVATE_KEY"], os.environ["VAPID_SUBJECT"])
    if expired:
        print("::warning::만료된 구독 %d개 — 휴대폰에서 알림을 다시 켜고 Secret 갱신 필요: %s"
              % (len(expired), expired))
        return 2
    print("전송 완료: 알림 %d건 × 구독 %d개" % (len(alerts), len(subs)))
    return 0


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    now = dt.datetime.now(KST)
    venues = store.load_venues()
    if cmd == "changes":
        return deliver(change_alerts(_load(argv[2]), store.load_json(argv[3]), venues, now.date()))
    path = argv[2] if len(argv) > 2 else store.EVENTS_PATH
    if cmd == "reminders":
        return deliver(reminder_alerts(store.load_json(path)["events"], venues, now.date()))
    if cmd == "stale":
        data = store.load_json(path)
        if is_stale(data, now):
            print("루틴이 %s 이후 갱신하지 않음" % data["updated_at"])
            return 3
        print("정상: 마지막 갱신 %s" % data["updated_at"])
        return 0
    if cmd == "suggestions":
        items = store.load_json(path)["venue_suggestions"]
        if not items:
            return 0
        print("루틴이 data/venues.json에 없는 장소의 행사를 발견했습니다. 추가할지 검토하세요.\n")
        for v in items:
            print("- **%s**: %s %s" % (v["name"], v["reason"], v.get("source", "")))
        return 4
    if cmd == "test":
        return deliver([{"title": "✅ 알림 테스트", "body": "선학역 행사 알림이 정상 연결됐어요.", "url": "./"}])
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
