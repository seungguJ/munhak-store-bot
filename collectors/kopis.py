"""KOPIS 공연 후보 수집 (루틴 보조 도구).

인천(signgucode=28) 공연 중 data/venues.json 행사장에 해당하는 것만 JSON으로 출력.
판단(인기·인파·등급)은 하지 않는다 — 루틴이 이 후보를 보고 events.json을 작성한다.

    KOPIS_SERVICE_KEY=... python -m collectors.kopis [days=120]
"""
import datetime as dt
import json
import os
import sys
import xml.etree.ElementTree as ET

import requests

from alert import store

URL = "http://www.kopis.or.kr/openApi/restful/pblprfr"
DETAIL_URL = "https://www.kopis.or.kr/por/db/pblprfr/pblprfrView.do?mt20id={}"
INCHEON = "28"
ROWS = 100
MAX_PAGES = 20


def match_venue(facility, venues):
    for v in venues:  # venues.json 순서 = 매칭 우선순위
        if any(k in facility for k in v["kopis_keywords"]):
            return v["id"]
    return None


def _iso(kopis_date):
    return kopis_date.strip().replace(".", "-")


def parse_xml(xml_bytes, venues):
    """(행사장 매칭된 후보 목록, 전체 행 수)."""
    root = ET.fromstring(xml_bytes)
    rows = root.findall("db")
    out = []
    for db in rows:
        facility = (db.findtext("fcltynm") or "").strip()
        venue_id = match_venue(facility, venues)
        if not venue_id:
            continue
        kopis_id = (db.findtext("mt20id") or "").strip()
        out.append({
            "kopis_id": kopis_id,
            "title": (db.findtext("prfnm") or "").strip(),
            "venue_id": venue_id,
            "facility": facility,
            "start": _iso(db.findtext("prfpdfrom") or ""),
            "end": _iso(db.findtext("prfpdto") or ""),
            "genre": (db.findtext("genrenm") or "").strip(),
            "url": DETAIL_URL.format(kopis_id),
        })
    return out, len(rows)


def fetch(service_key, days, venues, today=None):
    """KOPIS는 1회 최대 31일 → 31일 창 × 페이지 순회."""
    today = today or dt.date.today()
    final = today + dt.timedelta(days=days)
    found = {}
    cursor = today
    while cursor <= final:
        end = min(cursor + dt.timedelta(days=30), final)
        for page in range(1, MAX_PAGES + 1):
            resp = requests.get(URL, params={
                "service": service_key,
                "stdate": cursor.strftime("%Y%m%d"),
                "eddate": end.strftime("%Y%m%d"),
                "cpage": page,
                "rows": ROWS,
                "signgucode": INCHEON,
            }, timeout=20)
            resp.raise_for_status()
            rows, count = parse_xml(resp.content, venues)
            for r in rows:
                found[r["kopis_id"]] = r
            if count < ROWS:
                break
        cursor = end + dt.timedelta(days=1)
    return sorted(found.values(), key=lambda r: r["start"])


def main(argv):
    days = int(argv[1]) if len(argv) > 1 else 120
    venues = list(store.load_venues().values())
    rows = fetch(os.environ["KOPIS_SERVICE_KEY"], days, venues)
    json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
