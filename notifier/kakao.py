import json
import requests


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    resp = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


MAX_LEN = 1900  # 카카오 텍스트 메시지 한도(2000)보다 여유를 둠


def split_text(text: str, max_len: int = MAX_LEN) -> list:
    """긴 메시지를 줄 단위로 잘라 max_len 이하 청크 리스트로 반환."""
    chunks = []
    current = ""
    for line in text.split("\n"):
        # 한 줄이 한도를 넘으면 강제로 잘라 넣는다
        while len(line) > max_len:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:max_len])
            line = line[max_len:]
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


def _send_one(access_token: str, text: str) -> None:
    template = {
        "object_type": "text",
        "text": text,
        "link": {"web_url": "https://www.kakaocorp.com", "mobile_web_url": "https://www.kakaocorp.com"},
    }
    resp = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template)},
        timeout=10,
    )
    if resp.status_code != 200 or resp.json().get("result_code") != 0:
        raise Exception(f"카카오 메시지 전송 실패: {resp.status_code} {resp.text}")


def send_message(access_token: str, text: str) -> bool:
    """2000자 한도를 고려해 긴 메시지는 여러 개로 나눠 전송한다."""
    for chunk in split_text(text):
        _send_one(access_token, chunk)
    return True
