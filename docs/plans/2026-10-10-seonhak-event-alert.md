# 선학역 행사 알림 앱 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 선학역 반경 2~3km 행사를 Claude Code 루틴이 매일 조사해 `data/events.json`에 기록하면, GitHub Actions가 사장님 안드로이드 폰(PWA)으로 웹푸시를 보내고 PWA가 행사·등급·발주 추천을 보여준다.

**Architecture:** 루틴(조사·판단) → `alert.finalize`(등급 결정론적 계산 + 스키마 검증) → push → Actions(`alert.notify changes` / `alert.notify reminders`) → pywebpush. PWA는 GitHub Pages 정적 사이트로 `data/events.json`을 읽는다.

**Tech Stack:** Python 3.11(CI)/3.8 호환 코드, requests, jsonschema, pywebpush, pytest / Vanilla HTML·JS·Service Worker / GitHub Actions, GitHub Pages

Spec: `docs/specs/2026-10-10-seonhak-event-alert-design.md`

---

## File Structure

| 파일 | 책임 |
|---|---|
| `data/venues.json` | 행사장 고정 목록 (id, 이름, KOPIS 키워드, 거리, 가중치, 수용인원, 지도 검색어) |
| `data/events.json` | 루틴이 갱신하는 행사 목록 (PWA·Actions 공용) |
| `schema/events.schema.json` | events.json JSON Schema |
| `alert/store.py` | JSON 읽기/쓰기, venues 조회, 스키마 검증 |
| `alert/grading.py` | 예상 인파·등급 계산 (spec §6) |
| `alert/finalize.py` | CLI: events.json에 per_day·grade 채우고 검증 (루틴이 push 전 실행) |
| `alert/rules.py` | 알림 판정 순수 함수: `change_alerts(old, new, today)`, `reminder_alerts(events, today)`, `is_stale(data, now)` |
| `alert/push.py` | 웹푸시 전송 (구독 만료 감지, 구독 없으면 dry-run) |
| `alert/notify.py` | CLI: `changes OLD NEW` / `reminders` / `stale` |
| `collectors/kopis.py` | CLI: 인천 KOPIS 공연 중 행사장 키워드 매칭 후보를 JSON으로 출력 (루틴 보조) |
| `web/*` | PWA (index.html, app.js, style.css, sw.js, manifest.json, icon.svg, config.js) |
| `.github/workflows/*.yml` | test / notify-changes / daily / pages |
| `ROUTINE.md` | 루틴 프롬프트 (조사 절차·기준·금지사항) |
| `scripts/gen_vapid.py` | VAPID 키 생성 (로컬 1회) |

## Tasks

### Task 1: 프로젝트 골격 + 행사장/스키마 데이터
- Create: `requirements.txt`, `.gitignore`, `data/venues.json`, `data/events.json`(빈 목록), `schema/events.schema.json`, `alert/__init__.py`, `alert/store.py`
- Test: `tests/test_store.py` — 빈 events.json 통과, 필수 필드 누락/잘못된 grade 실패, `venue_by_id` 조회
- [ ] 실패 테스트 작성 → 실행(FAIL) → 구현 → PASS → commit

### Task 2: 등급 계산 (`alert/grading.py`)
- `crowd_per_day(capacity, fill_rate) -> int`, `base_grade(adjusted_crowd) -> str` (S≥30000, A≥10000, B≥3000, C), `final_grade(base, adjust)` (adjust ∈ {-1,0,1}, S/C 경계 clamp)
- Test: `tests/test_grading.py` — 경계값 30000/29999, 가중치 0.5 적용, adjust clamp
- [ ] TDD 사이클 → commit

### Task 3: finalize CLI (`alert/finalize.py`)
- `finalize(data, venues) -> data`: 각 이벤트에 `crowd_estimate.per_day`(capacity_override 우선), `grade` 계산, 행사장 목록 밖 venue_id면 ValueError
- `python -m alert.finalize data/events.json` → 파일 갱신 후 검증, 실패 시 exit 1
- Test: `tests/test_finalize.py`
- [ ] TDD 사이클 → commit

### Task 4: 알림 판정 (`alert/rules.py`)
- `change_alerts(old, new, today)`: 새 id(B 이상, scheduled, 종료일≥today) → 🆕 / 등급 상승 → ⬆️ / cancelled 전환 → ❌
- `reminder_alerts(events, today)`: start-today == 7 → 📦 D-7, ==1 → ⏰ D-1 (B 이상, scheduled)
- `is_stale(data, now, hours=36)`
- 알림 dict: `{"title", "body", "url"}` (url = `./#event=<id>`)
- Test: `tests/test_rules.py`
- [ ] TDD 사이클 → commit

### Task 5: 푸시 전송 + notify CLI (`alert/push.py`, `alert/notify.py`)
- `send_all(alerts, subscriptions, vapid_private_key, subject) -> list[expired_endpoint]` (pywebpush, 404/410 → expired)
- notify: env `PUSH_SUBSCRIPTIONS`(JSON 배열), `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`; 구독 없으면 출력만(dry-run). 만료 있으면 exit 2 (Action 로그로 알림)
- Test: `tests/test_push.py` (webpush mock), `tests/test_notify.py` (dry-run 출력)
- [ ] TDD 사이클 → commit

### Task 6: KOPIS 수집기 (`collectors/kopis.py`)
- 인천(signgucode=28) 공연을 31일 창 × 페이지로 조회, `fcltynm`이 venues의 `kopis_keywords`에 매칭되면 후보 `{kopis_id, title, venue_id, start, end, genre, url}`
- Test: `tests/test_kopis.py` — XML fixture 파싱/매칭
- [ ] TDD 사이클 → commit

### Task 7: PWA (`web/`)
- 홈(D-day 순 카드), 상세(`#event=<id>`), 설정(알림 켜기 → 구독 JSON 표시·복사, 테스트 알림)
- sw.js: precache 셸, events.json network-first, `push` → showNotification, `notificationclick` → url 열기
- [ ] 로컬 서버로 렌더 확인(샘플 데이터) → commit

### Task 8: GitHub Actions
- `test.yml`(push/PR pytest), `notify-changes.yml`(events.json push → 이전 버전과 비교 후 푸시), `daily.yml`(08:00 KST 리마인드 + stale 이슈), `pages.yml`(web+data → Pages)
- [ ] YAML 작성 → commit

### Task 9: 루틴 프롬프트 + 문서
- `ROUTINE.md`(조사 절차, 등급 조정 규칙, 스키마 예시, finalize 실행 필수, 금지사항), `README.md`(설치·Secrets·사장님 폰 설정·루틴 생성), `scripts/gen_vapid.py`
- [ ] 작성 → commit

## 실행 후 사용자 작업 (자동화 불가)
1. GitHub repo 생성·push, Pages 활성화 (Source: GitHub Actions)
2. VAPID 키 생성 → `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` Secret, 공개키는 `web/config.js`
3. 사장님 폰에서 PWA 설치 → 알림 켜기 → 구독 JSON을 `PUSH_SUBSCRIPTIONS` Secret에 등록
4. `/schedule`로 루틴 생성 (매일 06:30 KST, 프롬프트: "ROUTINE.md를 읽고 따르라", env `KOPIS_SERVICE_KEY`)
