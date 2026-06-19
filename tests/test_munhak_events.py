from collectors.munhak_events import Event, parse_kopis_xml, collect_events
from datetime import date, timedelta


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<dbs>
  <db>
    <mt20id>PF260001</mt20id>
    <prfnm>플레이브 단독 콘서트</prfnm>
    <prfpdfrom>{start}</prfpdfrom>
    <prfpdto>{end}</prfpdto>
    <fcltynm>인천문학경기장 주경기장</fcltynm>
    <genrenm>대중음악</genrenm>
  </db>
  <db>
    <mt20id>PF260099</mt20id>
    <prfnm>딴 동네 뮤지컬</prfnm>
    <prfpdfrom>{start}</prfpdfrom>
    <prfpdto>{end}</prfpdto>
    <fcltynm>서울예술의전당</fcltynm>
    <genrenm>뮤지컬</genrenm>
  </db>
</dbs>"""


def _dot(d):
    return d.strftime("%Y.%m.%d")


def test_parse_filters_to_munhak_venue_only():
    today = date.today()
    xml = SAMPLE_XML.format(start=_dot(today), end=_dot(today + timedelta(days=1))).encode("utf-8")
    events = parse_kopis_xml(xml)
    # 서울예술의전당은 걸러지고 문학경기장만 남는다
    assert len(events) == 1
    assert events[0].title == "플레이브 단독 콘서트"
    assert events[0].genre == "대중음악"
    assert events[0].source == "kopis"
    assert "PF260001" in events[0].ticket_url


def test_collect_filters_to_7_days():
    today = date.today()
    near = Event("이번주 공연", today.isoformat(), today.isoformat(), "대중음악", "u", "kopis")
    far = Event(
        "3개월 뒤 공연",
        (today + timedelta(days=90)).isoformat(),
        (today + timedelta(days=90)).isoformat(),
        "대중음악", "u", "kopis",
    )
    result = collect_events([near, far])
    assert len(result) == 1
    assert result[0].title == "이번주 공연"


def test_collect_deduplicates():
    today = date.today().isoformat()
    e1 = Event("같은 공연", today, today, "대중음악", "a", "kopis")
    e2 = Event("같은 공연", today, today, "대중음악", "b", "kopis")
    result = collect_events([e1, e2])
    assert len(result) == 1
