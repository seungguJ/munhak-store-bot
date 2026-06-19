import os
from datetime import date, timedelta

from collectors.munhak_events import Event, collect_events, fetch_kopis
from collectors.seven_eleven_official import collect_official_hot_items
from notifier.kakao import refresh_access_token, send_message

WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


def _date_label(start: str, end: str) -> str:
    """'2026-06-20(토)' 또는 기간이면 '2026-06-20(토)~06-22(월)'."""
    def one(iso):
        try:
            d = date.fromisoformat(iso)
            return f"{iso}({WEEKDAYS[d.weekday()]})"
        except ValueError:
            return iso
    if end and end != start:
        try:
            e = date.fromisoformat(end)
            return f"{one(start)}~{e.strftime('%m-%d')}({WEEKDAYS[e.weekday()]})"
        except ValueError:
            return one(start)
    return one(start)


def _rank_tier(rank: int) -> tuple:
    """순위별 (이모지, 발주 권고). 1~2위 적극, 3~4위 추가, 그 외 소량."""
    if rank <= 2:
        return "🔴", "적극 발주"
    if rank <= 4:
        return "🟠", "추가 발주"
    return "🟡", "소량 테스트"


def format_message(this_week: list, upcoming: list, hot_items: list, signal: str = "blog") -> str:
    today = date.today()
    end = today + timedelta(days=6)
    lines = [
        f"📅 [문학경기장 이번 주 일정] {today.strftime('%Y.%m.%d')}~{end.strftime('%m.%d')}",
        "",
    ]

    if this_week:
        lines.append("🎤 이번 주 공연/행사")
        for e in this_week:
            lines.append(f"• {_date_label(e.date, e.end_date)} [{e.genre}] {e.title}")
            if e.ticket_url:
                lines.append(f"  {e.ticket_url}")
    else:
        lines.append("🎤 이번 주 공연/행사: 예정된 이벤트 없음")

    if upcoming:
        lines.append("")
        lines.append("📣 다가오는 대형 공연 (미리 발주 준비)")
        for e in upcoming:
            d_day = (date.fromisoformat(e.date) - today).days
            lines.append(f"• D-{d_day} {_date_label(e.date, e.end_date)} [{e.genre}] {e.title}")
            if e.ticket_url:
                lines.append(f"  {e.ticket_url}")

    signal_label = "검색 트렌드" if signal == "datalab" else "블로그 화제도"
    lines += [
        "",
        "━━━━━━━━━━━━━━━━━",
        "🏪 세븐일레븐 이번 주 발주 추천",
        f"(공식 행사상품 × {signal_label})",
        "",
    ]

    if hot_items:
        for i, item in enumerate(hot_items, 1):
            emoji, rec = _rank_tier(i)
            lines.append(f"{emoji} {i}. {item.name} [{item.promo_type} 행사]")
            lines.append(f"     {signal_label} {i}위 · {rec}")
            lines.append("")
    else:
        lines.append("이번 주 수집된 행사상품 없음")

    lines += [
        "━━━━━━━━━━━━━━━━━",
        "발주 가이드: 🔴적극 🟠추가 🟡소량",
        "행사: 1+1·2+1은 마진 기회 — 회전 빠른 품목 우선",
    ]

    return "\n".join(lines).rstrip()


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
    kopis_service_key = os.environ["KOPIS_SERVICE_KEY"]

    print("카카오 토큰 갱신 중...")
    token_data = refresh_access_token(kakao_client_id, kakao_client_secret, kakao_refresh_token)
    access_token = token_data["access_token"]
    new_refresh = token_data.get("refresh_token", kakao_refresh_token)

    if new_refresh != kakao_refresh_token:
        _update_github_secret("KAKAO_REFRESH_TOKEN", new_refresh)

    print("문학경기장 공연 일정 수집 중 (KOPIS, 90일)...")
    raw_events = fetch_kopis(kopis_service_key, days=90)
    all_events = collect_events(raw_events, days=90)
    today = date.today()
    week_end = today + timedelta(days=7)
    this_week = [e for e in all_events if date.fromisoformat(e.date) <= week_end]
    upcoming = [e for e in all_events if date.fromisoformat(e.date) > week_end]
    print(f"  → 이번 주 {len(this_week)}개 / 다가오는 공연 {len(upcoming)}개")

    print("세븐일레븐 공식 행사상품 + 인기도 분석 중...")
    hot_items, signal = collect_official_hot_items(naver_client_id, naver_client_secret, top_n=5)
    print(f"  → {len(hot_items)}개 추천 (신호: {signal})")

    message = format_message(this_week, upcoming, hot_items, signal)
    print("\n--- 전송할 메시지 ---")
    print(message)
    print("-------------------\n")

    send_message(access_token, message)
    print("카카오톡 전송 완료!")


if __name__ == "__main__":
    main()
