from dataclasses import dataclass
from typing import Optional
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
VENUE_KEYWORDS = ["인천문학", "문학경기장", "인천 문학"]


@dataclass
class Event:
    title: str
    date: str        # "YYYY-MM-DD"
    time: str        # "HH:MM" or ""
    genre: str       # 콘서트/스포츠/행사/기타
    venue_capacity: Optional[int]
    ticket_url: str
    source: str


def fetch_interpark() -> list:
    url = (
        "https://tickets.interpark.com/contents/Search"
        "?SearchWord=%EC%9D%B8%EC%B2%9C%EB%AC%B8%ED%95%99%EA%B2%BD%EA%B8%B0%EC%9E%A5"
    )
    events = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "lxml")
        for item in soup.select("li"):
            place = item.select_one(".RKPlace")
            if not place:
                continue
            if not any(kw in place.text for kw in VENUE_KEYWORDS):
                continue
            name_el = item.select_one(".RKName")
            date_el = item.select_one(".RKDate")
            link_el = item.select_one("a")
            if not name_el:
                continue
            title = name_el.text.strip()
            raw_date = date_el.text.strip() if date_el else ""
            date_match = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", raw_date)
            event_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else ""
            href = link_el["href"] if link_el else ""
            ticket_url = href if href.startswith("http") else f"https://tickets.interpark.com{href}"
            events.append(Event(
                title=title,
                date=event_date,
                time="",
                genre="콘서트",
                venue_capacity=None,
                ticket_url=ticket_url,
                source="interpark",
            ))
    except Exception as e:
        print(f"[interpark] 수집 실패: {e}")
    return events


def fetch_kbo() -> list:
    url = "https://www.koreabaseball.com/Schedule/Schedule.aspx"
    events = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "lxml")
        for row in soup.select("table.tbl tr"):
            cols = row.select("td")
            if len(cols) < 5:
                continue
            home_team = cols[3].text.strip() if len(cols) > 3 else ""
            stadium = cols[4].text.strip() if len(cols) > 4 else ""
            if "SSG" not in home_team and not any(kw in stadium for kw in VENUE_KEYWORDS):
                continue
            date_el = cols[0] if cols else None
            raw_date = date_el.text.strip() if date_el else ""
            date_match = re.search(r"(\d{2})\.(\d{2})", raw_date)
            year = date.today().year
            event_date = f"{year}-{date_match.group(1)}-{date_match.group(2)}" if date_match else ""
            away = cols[2].text.strip() if len(cols) > 2 else "?"
            time_el = cols[1] if len(cols) > 1 else None
            event_time = time_el.text.strip() if time_el else "18:30"
            events.append(Event(
                title=f"SSG 랜더스 vs {away}",
                date=event_date,
                time=event_time,
                genre="스포츠",
                venue_capacity=23000,
                ticket_url="https://www.koreabaseball.com/Schedule/Schedule.aspx",
                source="kbo",
            ))
    except Exception as e:
        print(f"[kbo] 수집 실패: {e}")
    return events


def fetch_naver_search(client_id: str, client_secret: str) -> list:
    url = "https://openapi.naver.com/v1/search/news.json"
    events = []
    try:
        resp = requests.get(
            url,
            headers={
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            },
            params={"query": "인천 문학경기장 공연", "display": 10, "sort": "date"},
            timeout=10,
        )
        for item in resp.json().get("items", []):
            title = re.sub(r"<[^>]+>", "", item.get("title", "")).strip()
            link = item.get("link", "")
            events.append(Event(
                title=title,
                date="",
                time="",
                genre="기타",
                venue_capacity=None,
                ticket_url=link,
                source="naver",
            ))
    except Exception as e:
        print(f"[naver] 수집 실패: {e}")
    return events


def collect_events(events: list) -> list:
    seen = set()
    result = []
    for e in events:
        key = (e.title, e.date)
        if key not in seen:
            seen.add(key)
            result.append(e)
    return sorted(result, key=lambda e: e.date or "9999")
