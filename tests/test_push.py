import json

from alert import push


class FakeResp:
    def __init__(self, status):
        self.status_code = status


def test_send_all_reports_expired(monkeypatch):
    calls = []

    def fake_webpush(subscription_info, data, vapid_private_key, vapid_claims, ttl):
        calls.append((subscription_info["endpoint"], json.loads(data)))
        if subscription_info["endpoint"] == "https://gone":
            raise push.WebPushException("gone", response=FakeResp(410))

    monkeypatch.setattr(push, "webpush", fake_webpush)
    subs = [{"endpoint": "https://ok", "keys": {}}, {"endpoint": "https://gone", "keys": {}}]
    alerts = [{"title": "t", "body": "b", "url": "./#event=x"}]
    expired = push.send_all(alerts, subs, "KEY", "mailto:a@b.c")
    assert expired == ["https://gone"]
    assert calls[0] == ("https://ok", alerts[0])


def test_send_all_reraises_other_errors(monkeypatch):
    def fake_webpush(**kw):
        raise push.WebPushException("boom", response=FakeResp(500))

    monkeypatch.setattr(push, "webpush", fake_webpush)
    try:
        push.send_all([{"title": "t", "body": "b", "url": "u"}],
                      [{"endpoint": "https://x", "keys": {}}], "KEY", "mailto:a@b.c")
    except push.WebPushException:
        return
    raise AssertionError("expected WebPushException")


def test_subject_https_url_reduced_to_origin():
    assert push.normalize_subject("https://seungguj.github.io/munhak-store-bot/") == "https://seungguj.github.io"
    assert push.normalize_subject("mailto:a@b.c") == "mailto:a@b.c"
    assert push.normalize_subject(" https://x.example.com ") == "https://x.example.com"
