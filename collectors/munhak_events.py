"""
인천문학경기장 공연/행사 일정 수집기.

데이터 소스: KOPIS(공연예술통합전산망) OpenAPI 공연목록 조회.
- 공식 등록 공연 데이터라 공연명/날짜가 정확하다.
- 오늘부터 +7일 이내, 인천문학경기장(시설명에 "문학" 포함)만, 중복 제거.
"""
from dataclasses import dataclass
import requests
import xml.etree.ElementTree as ET
from datetime import date, timedelta

KOPIS_URL = "http://www.kopis.or.kr/openApi/restful/pblprfr"
VENUE_KEYWORD = "문학"  # 인천문학경기장 / 인천문학경기장 주경기장
DETAIL_URL = "https://www.kopis.or.kr/por/db/pblprfr/pblprfrView.do?mt20id={}"


@dataclass
class Event:
    title: str
    date: str        # 시작일 YYYY-MM-DD
    end_date: str    # 종료일 YYYY-MM-DD
    genre: str
    ticket_url: str
    source: str


def _to_iso(kopis_date: str) -> str:
    """'2026.06.20' -> '2026-06-20'. 실패 시 빈 문자열."""
    parts = kopis_date.strip().split(".")
    if len(parts) == 3:
        return f"{parts[0]}-{parts[1]}-{parts[2]}"
    return ""


def parse_kopis_xml(xml_bytes: bytes) -> list:
    """KOPIS 공연목록 XML을 Event 리스트로 변환 (시설 필터 적용)."""
    events = []
    root = ET.fromstring(xml_bytes)
    for db in root.findall("db"):
        fclty = (db.findtext("fcltynm") or "").strip()
        if VENUE_KEYWORD not in fclty:
            continue
        title = (db.findtext("prfnm") or "").strip()
        start = _to_iso(db.findtext("prfpdfrom") or "")
        end = _to_iso(db.findtext("prfpdto") or "")
        genre = (db.findtext("genrenm") or "공연").strip()
        mt20id = (db.findtext("mt20id") or "").strip()
        ticket_url = DETAIL_URL.format(mt20id) if mt20id else ""
        if title and start:
            events.append(Event(
                title=title,
                date=start,
                end_date=end or start,
                genre=genre,
                ticket_url=ticket_url,
                source="kopis",
            ))
    return events


def _fetch_kopis_window(service_key: str, start: date, end: date, retries: int = 2) -> list:
    """한 번의 KOPIS 조회 (KOPIS는 1회 최대 31일까지만 허용). 실패 시 재시도."""
    last_err = None
    for _ in range(retries + 1):
        try:
            resp = requests.get(
                KOPIS_URL,
                params={
                    "service": service_key,
                    "stdate": start.strftime("%Y%m%d"),
                    "eddate": end.strftime("%Y%m%d"),
                    "cpage": 1,
                    "rows": 100,
                    "shprfnmfct": "인천문학경기장",  # 공연시설명 서버측 필터
                },
                timeout=20,
            )
            resp.raise_for_status()
            return parse_kopis_xml(resp.content)
        except Exception as e:
            last_err = e
    print(f"[kopis] 구간 조회 실패 ({start}~{end}): {last_err}")
    return []


def fetch_kopis(service_key: str, days: int = 90) -> list:
    """오늘~+days 기간의 인천문학경기장 공연을 KOPIS에서 수집.

    KOPIS는 1회 조회 최대 31일이라 31일씩 나눠 조회 후 합친다.
    한 구간이 실패해도 나머지 구간은 계속 수집한다.
    """
    today = date.today()
    events = []
    cursor = today
    final = today + timedelta(days=days)
    while cursor <= final:
        window_end = min(cursor + timedelta(days=30), final)
        events.extend(_fetch_kopis_window(service_key, cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return events


def collect_events(events: list, days: int = 7) -> list:
    """오늘~+days 이내로 거르고, (제목,시작일) 중복 제거 후 날짜순 정렬."""
    today = date.today()
    window_end = today + timedelta(days=days)
    seen = set()
    result = []
    for e in events:
        try:
            start = date.fromisoformat(e.date)
            end = date.fromisoformat(e.end_date)
        except ValueError:
            continue
        # 공연 기간이 7일 창과 겹치는지 (종료>=오늘, 시작<=오늘+7)
        if end < today or start > window_end:
            continue
        key = (e.title, e.date)
        if key in seen:
            continue
        seen.add(key)
        result.append(e)
    return sorted(result, key=lambda e: e.date)
