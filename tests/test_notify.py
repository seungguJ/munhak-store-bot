import json

from alert import notify


def write(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(p)


def test_changes_dry_run_prints(tmp_path, monkeypatch, capsys, make_event, make_data):
    monkeypatch.delenv("PUSH_SUBSCRIPTIONS", raising=False)
    old = write(tmp_path, "old.json", make_data([]))
    new = write(tmp_path, "new.json", make_data([make_event(start="2099-01-01", end="2099-01-01")]))
    assert notify.main(["notify", "changes", old, new]) == 0
    out = capsys.readouterr().out
    assert "[dry-run]" in out and "🆕 [S] 테스트 콘서트" in out


def test_missing_old_file_treated_as_empty(tmp_path, monkeypatch, capsys, make_event, make_data):
    monkeypatch.delenv("PUSH_SUBSCRIPTIONS", raising=False)
    new = write(tmp_path, "new.json", make_data([make_event(start="2099-01-01", end="2099-01-01")]))
    assert notify.main(["notify", "changes", str(tmp_path / "nope.json"), new]) == 0
    assert "🆕" in capsys.readouterr().out


def test_expired_subscription_exit_code(tmp_path, monkeypatch, make_event, make_data):
    monkeypatch.setenv("PUSH_SUBSCRIPTIONS", json.dumps([{"endpoint": "https://gone", "keys": {}}]))
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "KEY")
    monkeypatch.setenv("VAPID_SUBJECT", "mailto:a@b.c")
    monkeypatch.setattr(notify, "send_all", lambda *a: ["https://gone"])
    new = write(tmp_path, "new.json", make_data([make_event(start="2099-01-01", end="2099-01-01")]))
    assert notify.main(["notify", "changes", str(tmp_path / "nope.json"), new]) == 2


def test_stale_exit_code(tmp_path, make_data):
    data = make_data([])
    data["updated_at"] = "2000-01-01T00:00:00+09:00"
    assert notify.main(["notify", "stale", write(tmp_path, "e.json", data)]) == 3


def test_suggestions_exit_code_and_body(tmp_path, capsys, make_data):
    data = make_data([])
    assert notify.main(["notify", "suggestions", write(tmp_path, "a.json", data)]) == 0
    data["venue_suggestions"] = [{"name": "송도달빛축제공원", "reason": "구 축제 개최지", "source": "https://x"}]
    assert notify.main(["notify", "suggestions", write(tmp_path, "b.json", data)]) == 4
    assert "- **송도달빛축제공원**: 구 축제 개최지 https://x" in capsys.readouterr().out


def test_today_override_and_demo_url(tmp_path, monkeypatch, capsys):
    """데모: TODAY=2026-10-02 → 리센느 축제 D-7, 링크는 데모 화면으로."""
    from pathlib import Path
    from alert import store
    from alert.finalize import finalize
    import datetime as dt
    fixture = Path(__file__).parent / "fixtures" / "rescene_2026-10-09.json"
    data = finalize(store.load_json(fixture), store.load_venues(), dt.date(2026, 9, 21))
    path = write(tmp_path, "demo.json", data)
    monkeypatch.delenv("PUSH_SUBSCRIPTIONS", raising=False)
    monkeypatch.setenv("TODAY", "2026-10-02")
    monkeypatch.setenv("DEMO_QUERY", "demo=rescene&today=2026-10-02")
    sent = []
    monkeypatch.setattr(notify, "_print_alert", lambda a: sent.append(a))
    assert notify.main(["notify", "reminders", path]) == 0
    assert sent[0]["title"].startswith("📦 D-7 [S] 제14회 연수 능허대")
    assert sent[0]["url"] == "./?demo=rescene&today=2026-10-02#event=web-neungheodae-2026"
