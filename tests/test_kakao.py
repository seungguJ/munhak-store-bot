import pytest
import responses
import requests
from notifier.kakao import refresh_access_token, send_message, split_text


def test_split_text_short_stays_single():
    chunks = split_text("짧은 메시지", max_len=1900)
    assert chunks == ["짧은 메시지"]


def test_split_text_long_splits_on_line_boundary():
    text = "\n".join(f"line {i}" for i in range(1000))
    chunks = split_text(text, max_len=100)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)
    # 합치면 원본과 동일(줄 순서 보존)
    assert "\n".join(chunks).replace("\n", "") == text.replace("\n", "")


@responses.activate
def test_refresh_access_token_success():
    responses.add(
        responses.POST,
        "https://kauth.kakao.com/oauth/token",
        json={"access_token": "new_access_token", "refresh_token": "new_refresh_token"},
        status=200,
    )
    result = refresh_access_token(
        client_id="test_id",
        client_secret="test_secret",
        refresh_token="old_refresh_token",
    )
    assert result["access_token"] == "new_access_token"
    assert result["refresh_token"] == "new_refresh_token"


@responses.activate
def test_send_message_success():
    responses.add(
        responses.POST,
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        json={"result_code": 0},
        status=200,
    )
    result = send_message(access_token="test_token", text="테스트 메시지")
    assert result is True


@responses.activate
def test_send_message_failure_raises():
    responses.add(
        responses.POST,
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        json={"msg": "unauthorized"},
        status=401,
    )
    with pytest.raises(Exception, match="카카오 메시지 전송 실패"):
        send_message(access_token="bad_token", text="테스트")
