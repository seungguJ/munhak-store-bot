import pytest
import responses
import requests
from notifier.kakao import refresh_access_token, send_message


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
