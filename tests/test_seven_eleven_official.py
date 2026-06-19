import responses
from collectors.seven_eleven_official import (
    OfficialProduct, clean_name, measure_with_blog, BLOG_URL,
)


def test_clean_name_strips_brand_and_volume():
    assert clean_name("빙그레)래핑카우8포션치즈120g") == "래핑카우8포션치즈"
    assert clean_name("남양)초코에몽190ml") == "초코에몽"
    assert clean_name("아미)에코얼음컵(레귤러)") == "에코얼음컵"
    assert clean_name("hy)쉼230ml") == "쉼"


@responses.activate
def test_measure_with_blog_sets_popularity_from_total():
    responses.add(
        responses.GET, BLOG_URL,
        json={"total": 4242, "items": []}, status=200,
    )
    products = [OfficialProduct("초코우유", "남양)초코우유200ml", "2+1", 0.0)]
    measure_with_blog("id", "secret", products)
    assert products[0].popularity == 4242.0


@responses.activate
def test_measure_with_blog_handles_failure_gracefully():
    responses.add(responses.GET, BLOG_URL, status=500)
    products = [OfficialProduct("딸기우유", "서울)딸기우유200ml", "할인", 0.0)]
    measure_with_blog("id", "secret", products)
    assert products[0].popularity == 0.0
