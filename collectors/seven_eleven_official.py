"""
세븐일레븐 공식몰 행사상품 수집 + 인기도 측정.

기존 방식(블로그 제목 정규식 추출)은 상품명이 부정확했다.
여기서는 세븐일레븐 공식몰(7-eleven.co.kr) 행사상품 목록에서
'정확한 상품명'을 직접 가져온 뒤, 각 상품의 검색 인기도를 측정한다.

인기도 신호 우선순위:
  1) 네이버 DataLab 검색어 트렌드 (앱에 DataLab API 활성화 시) — 실제 검색 관심도
  2) 폴백: 네이버 블로그 검색 결과 total 건수 — 기존 검색 키로 즉시 동작
"""
from dataclasses import dataclass
import json
import re
import requests
from bs4 import BeautifulSoup

PRESENT_URL = "https://www.7-eleven.co.kr/product/presentList.asp"
DATALAB_URL = "https://openapi.naver.com/v1/datalab/search"
BLOG_URL = "https://openapi.naver.com/v1/search/blog.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# 공식몰 행사 탭 → 사람이 읽을 라벨
PROMO_TABS = {"1": "1+1", "2": "2+1", "3": "증정", "4": "할인"}

# DataLab 정규화용 고정 기준 키워드(항상 어느 정도 검색되는 안정적 단어).
# 각 배치 결과를 이 단어 기준으로 나눠 배치 간 비교가 가능하게 만든다.
DATALAB_ANCHOR = "편의점"


@dataclass
class OfficialProduct:
    name: str          # 정제된 상품명 (검색/표시용)
    raw_name: str      # 공식몰 원본 (브랜드)상품명+용량
    promo_type: str    # "1+1" / "2+1" / "증정" / "할인"
    popularity: float  # 인기도 점수 (신호별 스케일 다름, 정렬용)


def clean_name(raw: str) -> str:
    """'빙그레)래핑카우8포션치즈120g' -> '래핑카우8포션치즈'.

    브랜드 접두사 'XXX)'와 용량 꼬리(120g, 190ml 등), 괄호 부연을 제거한다.
    """
    n = re.sub(r"^[^)]{1,8}\)", "", raw)                       # 브랜드) 제거
    n = re.sub(r"\d+(\.\d+)?\s*(g|ml|kg|L|개|포션|입|매|p|P)\b.*$", "", n)  # 용량 꼬리
    n = re.sub(r"\(.*?\)", "", n)                              # (부연) 제거
    return n.strip()


def fetch_official_products() -> list:
    """공식몰 행사상품 4개 탭에서 (정제명, 원본명, 행사타입) 수집."""
    products = []
    seen = set()
    for tab, label in PROMO_TABS.items():
        try:
            resp = requests.get(
                PRESENT_URL,
                headers=HEADERS,
                params={"pTab": tab, "intPageSize": 100},
                timeout=15,
            )
            html = resp.content.decode("utf-8", "replace")
            soup = BeautifulSoup(html, "html.parser")
            for el in soup.select(".name"):
                raw = el.get_text(strip=True)
                name = clean_name(raw)
                if not name or len(name) < 2 or name in seen:
                    continue
                seen.add(name)
                products.append(OfficialProduct(
                    name=name, raw_name=raw, promo_type=label, popularity=0.0,
                ))
        except Exception as e:
            print(f"[7-eleven] 탭 {label} 수집 실패: {e}")
    return products


def _datalab_batch(client_id: str, client_secret: str, names: list) -> dict:
    """이름 묶음 + 앵커를 한 번에 조회해 {이름: 앵커대비 비율} 반환.

    DataLab은 한 요청 내 최대 5개 그룹, 응답 비율은 요청 내 최댓값=100으로
    선형 스케일된다. 같은 요청에 앵커를 넣고 (상품평균/앵커평균)을 쓰면
    스케일 상수가 약분되어 배치 간 비교가 가능해진다.
    """
    from datetime import date, timedelta
    end = date.today()
    start = end - timedelta(days=30)
    groups = [{"groupName": n, "keywords": [n]} for n in names]
    groups.append({"groupName": "_anchor", "keywords": [DATALAB_ANCHOR]})

    resp = requests.post(
        DATALAB_URL,
        headers={
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "startDate": start.strftime("%Y-%m-%d"),
            "endDate": end.strftime("%Y-%m-%d"),
            "timeUnit": "week",
            "keywordGroups": groups,
        }),
        timeout=15,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])

    def avg(title):
        for r in results:
            if r["title"] == title:
                pts = [p["ratio"] for p in r["data"]]
                return sum(pts) / len(pts) if pts else 0.0
        return 0.0

    anchor = avg("_anchor") or 1e-9
    return {n: avg(n) / anchor for n in names}


def measure_with_datalab(client_id: str, client_secret: str, products: list) -> bool:
    """DataLab 검색 트렌드로 popularity 채움. 성공 시 True, 미활성/실패 시 False."""
    names = [p.name for p in products]
    scores = {}
    try:
        for i in range(0, len(names), 4):  # 그룹 4개 + 앵커 1개 = 5개 한도
            scores.update(_datalab_batch(client_id, client_secret, names[i:i + 4]))
    except Exception as e:
        print(f"[datalab] 미사용(앱에 DataLab API 미활성?): {e}")
        return False
    for p in products:
        p.popularity = round(scores.get(p.name, 0.0), 4)
    return True


def measure_with_blog(client_id: str, client_secret: str, products: list) -> None:
    """폴백: 각 상품명의 블로그 검색 total 건수를 인기도로 사용."""
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    for p in products:
        try:
            # 일반명("맛있는우유")의 타 매장 언급을 배제하려고 세븐일레븐으로 스코핑
            resp = requests.get(
                BLOG_URL, headers=headers,
                params={"query": f"세븐일레븐 {p.name}", "display": 1}, timeout=10,
            )
            p.popularity = float(resp.json().get("total", 0))
        except Exception as e:
            print(f"[blog] '{p.name}' 건수 조회 실패: {e}")
            p.popularity = 0.0


def collect_official_hot_items(client_id: str, client_secret: str, top_n: int = 5) -> tuple:
    """공식 행사상품 수집 → 인기도 측정 → 상위 N개 반환.

    반환: (상위 OfficialProduct 리스트, 사용한 신호 라벨)
    """
    products = fetch_official_products()
    if not products:
        return [], "none"

    signal = "datalab"
    if not measure_with_datalab(client_id, client_secret, products):
        measure_with_blog(client_id, client_secret, products)
        signal = "blog"

    products.sort(key=lambda p: p.popularity, reverse=True)
    return products[:top_n], signal
