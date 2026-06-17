import pytest
import responses
from collectors.munhak_events import fetch_interpark, fetch_kbo, collect_events, Event
from datetime import date


def test_event_dataclass():
    event = Event(
        title="IU 콘서트",
        date="2026-06-19",
        time="19:00",
        genre="콘서트",
        venue_capacity=20000,
        ticket_url="https://tickets.interpark.com/test",
        source="interpark",
    )
    assert event.title == "IU 콘서트"
    assert event.genre == "콘서트"


@responses.activate
def test_fetch_interpark_returns_list():
    html = """
    <html><body>
    <div class="RKBody">
      <ul class="RKList">
        <li>
          <a href="/product/NewProduct.asp?NO=123456">
            <strong class="RKName">테스트 콘서트</strong>
          </a>
          <span class="RKDate">2026.06.20 ~ 2026.06.21</span>
          <span class="RKPlace">인천문학경기장</span>
        </li>
      </ul>
    </div>
    </body></html>
    """
    responses.add(
        responses.GET,
        "https://tickets.interpark.com/contents/Search?SearchWord=%EC%9D%B8%EC%B2%9C%EB%AC%B8%ED%95%99%EA%B2%BD%EA%B8%B0%EC%9E%A5",
        body=html,
        status=200,
    )
    result = fetch_interpark()
    assert isinstance(result, list)


def test_collect_events_deduplicates():
    events = [
        Event("IU 콘서트", "2026-06-19", "19:00", "콘서트", 20000, "https://a.com", "interpark"),
        Event("IU 콘서트", "2026-06-19", "19:00", "콘서트", 20000, "https://b.com", "melon"),
    ]
    result = collect_events(events)
    assert len(result) == 1
