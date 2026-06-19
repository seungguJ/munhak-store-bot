from main import format_message
from collectors.munhak_events import Event
from collectors.seven_eleven import HotItem


def test_format_message_contains_key_sections():
    events = [
        Event("플레이브 콘서트", "2026-06-20", "2026-06-21", "대중음악", "https://kopis.or.kr/x", "kopis"),
    ]
    hot_items = [
        HotItem("허니버터 크림빵", 0.87, 4200, 87, "https://blog.naver.com/x", "적극 입고 (평소 2~3배)"),
    ]
    msg = format_message(events, hot_items)

    assert "문학경기장" in msg
    assert "플레이브 콘서트" in msg
    assert "대중음악" in msg
    assert "세븐일레븐" in msg
    assert "허니버터 크림빵" in msg
    assert "적극 입고" in msg


def test_format_message_empty_events():
    msg = format_message([], [])
    assert "이번 주 예정된 이벤트 없음" in msg


def test_format_message_weekday_korean():
    events = [Event("테스트 공연", "2026-06-19", "2026-06-19", "대중음악", "https://example.com", "kopis")]
    msg = format_message(events, [])
    assert "금" in msg  # 2026-06-19는 금요일


def test_format_message_date_range():
    events = [Event("이틀 공연", "2026-06-20", "2026-06-21", "대중음악", "", "kopis")]
    msg = format_message(events, [])
    assert "2026-06-20" in msg
    assert "06-21" in msg
