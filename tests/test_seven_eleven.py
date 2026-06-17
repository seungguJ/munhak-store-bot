import pytest
import responses
from collectors.seven_eleven import HotItem, score_items, fetch_naver_blog, fetch_youtube


def test_hotitem_dataclass():
    item = HotItem(
        product_name="허니버터 크림빵",
        score=0.87,
        instagram_likes=4200,
        blog_mentions=87,
        source_url="https://instagram.com/test",
        order_recommendation="적극 입고 (평소 2~3배)",
    )
    assert item.score == 0.87
    assert "적극" in item.order_recommendation


def test_score_items_ranking():
    raw = [
        {"name": "상품A", "instagram_likes": 5000, "blog_mentions": 100, "youtube_views": 10000, "tweet_count": 50, "url": "https://a.com"},
        {"name": "상품B", "instagram_likes": 100, "blog_mentions": 5, "youtube_views": 200, "tweet_count": 2, "url": "https://b.com"},
    ]
    result = score_items(raw)
    assert result[0].product_name == "상품A"
    assert result[0].score > result[1].score


def test_order_recommendation_tiers():
    raw = [
        {"name": "핫템", "instagram_likes": 10000, "blog_mentions": 200, "youtube_views": 50000, "tweet_count": 100, "url": ""},
        {"name": "보통템", "instagram_likes": 500, "blog_mentions": 20, "youtube_views": 1000, "tweet_count": 10, "url": ""},
        {"name": "저템", "instagram_likes": 10, "blog_mentions": 1, "youtube_views": 50, "tweet_count": 0, "url": ""},
    ]
    result = score_items(raw)
    assert "적극" in result[0].order_recommendation
