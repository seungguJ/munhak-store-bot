from main import format_message
from collectors.munhak_events import Event
from collectors.seven_eleven import HotItem


def test_format_message_contains_key_sections():
    events = [
        Event("IU 콘서트", "2026-06-19", "19:00", "콘서트", 20000, "https://tickets.interpark.com/1", "interpark"),
        Event("SSG 랜더스 vs KIA", "2026-06-20", "18:30", "스포츠", 23000, "https://kbo.com", "kbo"),
    ]
    hot_items = [
        HotItem("허니버터 크림빵", 0.87, 4200, 87, "https://instagram.com/1", "적극 입고 (평소 2~3배)"),
    ]
    msg = format_message(events, hot_items)

    assert "문학경기장" in msg
    assert "IU 콘서트" in msg
    assert "SSG 랜더스" in msg
    assert "세븐일레븐" in msg
    assert "허니버터 크림빵" in msg
    assert "적극 입고" in msg


def test_format_message_empty_events():
    msg = format_message([], [])
    assert "이번 주 예정된 이벤트 없음" in msg


def test_format_message_weekday_korean():
    events = [Event("테스트", "2026-06-19", "19:00", "콘서트", None, "https://example.com", "test")]
    msg = format_message(events, [])
    assert "금" in msg  # 2026-06-19는 금요일
