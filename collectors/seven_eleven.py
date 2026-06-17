from dataclasses import dataclass
from typing import Optional
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


@dataclass
class HotItem:
    product_name: str
    score: float
    instagram_likes: int
    blog_mentions: int
    source_url: str
    order_recommendation: str


def _recommendation(score: float) -> str:
    if score >= 0.8:
        return "적극 입고 (평소 2~3배)"
    if score >= 0.5:
        return "추가 발주 추천"
    if score >= 0.3:
        return "소량 테스트 입고"
    return "관망"


def score_items(raw_items: list) -> list:
    if not raw_items:
        return []

    def safe_max(key):
        vals = [r[key] for r in raw_items]
        return max(vals) or 1

    max_ig = safe_max("instagram_likes")
    max_blog = safe_max("blog_mentions")
    max_yt = safe_max("youtube_views")
    max_tw = safe_max("tweet_count")

    results = []
    for r in raw_items:
        score = (
            0.40 * (r["instagram_likes"] / max_ig)
            + 0.30 * (r["blog_mentions"] / max_blog)
            + 0.20 * (r["youtube_views"] / max_yt)
            + 0.10 * (r["tweet_count"] / max_tw)
        )
        results.append(HotItem(
            product_name=r["name"],
            score=round(score, 3),
            instagram_likes=r["instagram_likes"],
            blog_mentions=r["blog_mentions"],
            source_url=r.get("url", ""),
            order_recommendation=_recommendation(score),
        ))
    return sorted(results, key=lambda x: x.score, reverse=True)[:5]


def fetch_naver_blog(client_id: str, client_secret: str) -> list:
    keywords = ["세븐일레븐 추천", "편의점 신상", "세븐일레븐 신상"]
    counts = {}
    urls = {}

    for kw in keywords:
        try:
            resp = requests.get(
                "https://openapi.naver.com/v1/search/blog.json",
                headers={
                    "X-Naver-Client-Id": client_id,
                    "X-Naver-Client-Secret": client_secret,
                },
                params={"query": kw, "display": 30, "sort": "date"},
                timeout=10,
            )
            for item in resp.json().get("items", []):
                title = re.sub(r"<[^>]+>", "", item.get("title", "")).strip()
                desc = re.sub(r"<[^>]+>", "", item.get("description", "")).strip()
                combined = title + " " + desc
                products = re.findall(
                    r"[가-힣A-Za-z0-9\s]{3,15}(?:빵|음료|과자|아이스크림|도시락|샌드위치|떡볶이|김밥|컵라면|맥주|소주|콜라|사이다)",
                    combined,
                )
                for p in products:
                    p = p.strip()
                    if p:
                        counts[p] = counts.get(p, 0) + 1
                        urls[p] = item.get("link", "")
        except Exception as e:
            print(f"[naver_blog] 수집 실패 ({kw}): {e}")

    return [
        {"name": k, "instagram_likes": 0, "blog_mentions": v, "youtube_views": 0, "tweet_count": 0, "url": urls.get(k, "")}
        for k, v in sorted(counts.items(), key=lambda x: -x[1])[:20]
    ]


def fetch_youtube(api_key: str) -> list:
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "key": api_key,
                "q": "세븐일레븐 신상 추천",
                "part": "snippet",
                "type": "video",
                "order": "viewCount",
                "maxResults": 10,
                "publishedAfter": _two_weeks_ago_iso(),
            },
            timeout=10,
        )
        items = resp.json().get("items", [])
        result = []
        for item in items:
            video_id = item["id"].get("videoId", "")
            title = item["snippet"].get("title", "")
            stats_resp = requests.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"key": api_key, "id": video_id, "part": "statistics"},
                timeout=10,
            )
            stats = stats_resp.json().get("items", [{}])[0].get("statistics", {})
            view_count = int(stats.get("viewCount", 0))
            result.append({
                "name": title[:20],
                "instagram_likes": 0,
                "blog_mentions": 0,
                "youtube_views": view_count,
                "tweet_count": 0,
                "url": f"https://youtube.com/watch?v={video_id}",
            })
        return result
    except Exception as e:
        print(f"[youtube] 수집 실패: {e}")
        return []


def fetch_twitter(bearer_token: str) -> list:
    try:
        resp = requests.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers={"Authorization": f"Bearer {bearer_token}"},
            params={"query": "세븐일레븐 (추천 OR 신상 OR 맛있) lang:ko", "max_results": 50, "tweet.fields": "text"},
            timeout=10,
        )
        tweets = resp.json().get("data", [])
        counts = {}
        for tw in tweets:
            text = tw.get("text", "")
            products = re.findall(
                r"[가-힣A-Za-z0-9\s]{3,15}(?:빵|음료|과자|아이스크림|도시락|샌드위치|떡볶이|김밥|컵라면|맥주|소주|콜라|사이다)",
                text,
            )
            for p in products:
                p = p.strip()
                if p:
                    counts[p] = counts.get(p, 0) + 1
        return [
            {"name": k, "instagram_likes": 0, "blog_mentions": 0, "youtube_views": 0, "tweet_count": v, "url": ""}
            for k, v in sorted(counts.items(), key=lambda x: -x[1])[:10]
        ]
    except Exception as e:
        print(f"[twitter] 수집 실패: {e}")
        return []


def _two_weeks_ago_iso() -> str:
    from datetime import datetime, timedelta, timezone
    dt = datetime.now(timezone.utc) - timedelta(days=14)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def collect_hot_items(
    naver_client_id: str,
    naver_client_secret: str,
    youtube_api_key: str,
    twitter_bearer_token: str,
) -> list:
    blog_items = fetch_naver_blog(naver_client_id, naver_client_secret)
    yt_items = fetch_youtube(youtube_api_key)
    tw_items = fetch_twitter(twitter_bearer_token)

    merged = {}
    for item in blog_items + yt_items + tw_items:
        name = item["name"]
        if name not in merged:
            merged[name] = {"name": name, "instagram_likes": 0, "blog_mentions": 0, "youtube_views": 0, "tweet_count": 0, "url": item.get("url", "")}
        merged[name]["blog_mentions"] += item["blog_mentions"]
        merged[name]["youtube_views"] += item["youtube_views"]
        merged[name]["tweet_count"] += item["tweet_count"]

    return score_items(list(merged.values()))
