from alert import store
from collectors.kopis import match_venue, parse_xml

XML = """<?xml version="1.0" encoding="UTF-8"?>
<dbs>
  <db><mt20id>PF1</mt20id><prfnm>PLAVE 월드투어 [인천]</prfnm><prfpdfrom>2026.11.14</prfpdfrom>
      <prfpdto>2026.11.15</prfpdto><fcltynm>인천문학경기장 (주경기장)</fcltynm><genrenm>대중음악</genrenm></db>
  <db><mt20id>PF2</mt20id><prfnm>동네 연극</prfnm><prfpdfrom>2026.11.01</prfpdfrom>
      <prfpdto>2026.11.30</prfpdto><fcltynm>부평아트센터 (달누리극장)</fcltynm><genrenm>연극</genrenm></db>
  <db><mt20id>PF3</mt20id><prfnm>아이스쇼</prfnm><prfpdfrom>2026.12.24</prfpdfrom>
      <prfpdto>2026.12.24</prfpdto><fcltynm>선학국제빙상경기장</fcltynm><genrenm>복합</genrenm></db>
</dbs>"""


def test_match_venue():
    venues = list(store.load_venues().values())
    assert match_venue("인천SSG랜더스필드", venues) == "landers-field"
    assert match_venue("인천문학경기장 (주경기장)", venues) == "munhak-main"
    assert match_venue("부평아트센터", venues) is None


def test_parse_xml_keeps_only_listed_venues():
    venues = list(store.load_venues().values())
    rows, count = parse_xml(XML.encode("utf-8"), venues)
    assert count == 3
    assert [r["kopis_id"] for r in rows] == ["PF1", "PF3"]
    assert rows[0] == {
        "kopis_id": "PF1", "title": "PLAVE 월드투어 [인천]", "venue_id": "munhak-main",
        "facility": "인천문학경기장 (주경기장)", "start": "2026-11-14", "end": "2026-11-15",
        "genre": "대중음악",
        "url": "https://www.kopis.or.kr/por/db/pblprfr/pblprfrView.do?mt20id=PF1",
    }
