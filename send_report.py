"""
report.md를 읽어 카카오톡(나에게 보내기)으로 전송한다.

이 프로젝트의 새 구조:
  Claude가 매주 공연 일정 + 세븐일레븐 핫템을 직접 조사해 report.md에 작성하고
  git에 push하면, GitHub Actions가 이 스크립트로 report.md를 그대로 전송한다.
  (데이터 수집/판단은 Claude가 하고, CI는 '전송'만 담당)
"""
import os
import subprocess
from pathlib import Path

from notifier.kakao import refresh_access_token, send_message

REPORT_PATH = Path(__file__).parent / "report.md"


def _update_github_secret(secret_name: str, value: str) -> None:
    gh_pat = os.environ.get("GH_PAT", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not gh_pat or not repo:
        print(f"[경고] GH_PAT/GITHUB_REPOSITORY 없음 → {secret_name} 자동 갱신 스킵")
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


def main() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit("report.md 가 비어 있습니다. 전송할 내용이 없습니다.")

    client_id = os.environ["KAKAO_CLIENT_ID"]
    client_secret = os.environ["KAKAO_CLIENT_SECRET"]
    refresh_token = os.environ["KAKAO_REFRESH_TOKEN"]

    print("카카오 토큰 갱신 중...")
    token_data = refresh_access_token(client_id, client_secret, refresh_token)
    access_token = token_data["access_token"]
    new_refresh = token_data.get("refresh_token", refresh_token)
    if new_refresh != refresh_token:
        _update_github_secret("KAKAO_REFRESH_TOKEN", new_refresh)

    print("\n--- 전송할 내용 (report.md) ---")
    print(text)
    print("------------------------------\n")

    send_message(access_token, text)
    print("카카오톡 전송 완료!")


if __name__ == "__main__":
    main()
