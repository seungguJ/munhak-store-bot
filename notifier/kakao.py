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


def send_message(access_token: str, text: str) -> bool:
    template = {
        "object_type": "text",
        "text": text[:2000],
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
    return True
