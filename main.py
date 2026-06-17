import os
from datetime import date, timedelta

from collectors.munhak_events import Event, collect_events, fetch_interpark, fetch_kbo, fetch_naver_search
from collectors.seven_eleven import HotItem, collect_hot_items
from notifier.kakao import refresh_access_token, send_message

WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


def format_message(events: list, hot_items: list) -> str:
    today = date.today()
    end = today + timedelta(days=6)
    lines = [
        f"📅 [문학경기장 이번 주 일정] {today.strftime('%Y.%m.%d')}~{end.strftime('%m.%d')}",
        "",
    ]

    concerts = [e for e in events if e.genre != "스포츠"]
    sports = [e for e in events if e.genre == "스포츠"]

    if concerts:
        lines.append("🎤 공연/행사")
        for e in concerts:
            weekday = ""
            try:
                d = date.fromisoformat(e.date)
                weekday = WEEKDAYS[d.weekday()]
            except ValueError:
                pass
            cap = f"좌석 약 {e.venue_capacity:,}석 | " if e.venue_capacity else ""
            date_str = f"{e.date}({weekday})" if weekday else e.date
            lines.append(f"• {date_str} {e.title} - {e.time}")
            lines.append(f"  {cap}{e.ticket_url}")
    else:
        lines.append("🎤 공연/행사: 이번 주 예정된 이벤트 없음")

    lines.append("")

    if sports:
        lines.append("⚾ SSG 랜더스 홈경기")
        for e in sports:
            weekday = ""
            try:
                d = date.fromisoformat(e.date)
                weekday = WEEKDAYS[d.weekday()]
            except ValueError:
                pass
            date_str = f"{e.date}({weekday})" if weekday else e.date
            lines.append(f"• {date_str} {e.title} - {e.time}")

    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━",
        "🏪 [세븐일레븐 이번 주 핫템]",
        "",
    ]

    if hot_items:
        lines.append("🔥 SNS 화제 상품")
        for i, item in enumerate(hot_items, 1):
            lines.append(f"{i}. {item.product_name} (블로그 {item.blog_mentions}건 | 인스타 {item.instagram_likes:,})")
            lines.append(f"   → 발주 추천: {item.order_recommendation}")
            if item.source_url:
                lines.append(f"   {item.source_url}")
    else:
        lines.append("이번 주 수집된 핫템 없음")

    return "\n".join(lines)


def _update_github_secret(secret_name: str, value: str):
    import subprocess
    gh_pat = os.environ.get("GH_PAT", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not gh_pat or not repo:
        print(f"[경고] GH_PAT 또는 GITHUB_REPOSITORY 없음 → {secret_name} 자동 갱신 스킵")
        return
    try:
        subprocess.run(
            ["gh", "secret", "set", secret_name, "--body", value, "--repo", repo],
            env={**os.environ, "GH_TOKEN": gh_pat},
            check=True,
            capture_output=True,
        )
        print(f"  → GitHub Secret '{secret_name}' 갱신 완료")
    except Exception as e:
        print(f"[경고] Secret 갱신 실패: {e}")


def main():
    kakao_client_id = os.environ["KAKAO_CLIENT_ID"]
    kakao_client_secret = os.environ["KAKAO_CLIENT_SECRET"]
    kakao_refresh_token = os.environ["KAKAO_REFRESH_TOKEN"]
    naver_client_id = os.environ["NAVER_CLIENT_ID"]
    naver_client_secret = os.environ["NAVER_CLIENT_SECRET"]
    youtube_api_key = os.environ["YOUTUBE_API_KEY"]
    twitter_bearer = os.environ.get("X_BEARER_TOKEN", "")

    print("카카오 토큰 갱신 중...")
    token_data = refresh_access_token(kakao_client_id, kakao_client_secret, kakao_refresh_token)
    access_token = token_data["access_token"]
    new_refresh = token_data.get("refresh_token", kakao_refresh_token)

    if new_refresh != kakao_refresh_token:
        _update_github_secret("KAKAO_REFRESH_TOKEN", new_refresh)

    print("문학경기장 이벤트 수집 중...")
    raw_events = (
        fetch_interpark()
        + fetch_kbo()
        + fetch_naver_search(naver_client_id, naver_client_secret)
    )
    events = collect_events(raw_events)
    print(f"  → {len(events)}개 이벤트 수집")

    print("세븐일레븐 핫템 분석 중...")
    hot_items = collect_hot_items(naver_client_id, naver_client_secret, youtube_api_key, twitter_bearer)
    print(f"  → {len(hot_items)}개 핫템 분석")

    message = format_message(events, hot_items)
    print("\n--- 전송할 메시지 ---")
    print(message)
    print("-------------------\n")

    send_message(access_token, message)
    print("카카오톡 전송 완료!")


if __name__ == "__main__":
    main()
