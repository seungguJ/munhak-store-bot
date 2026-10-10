# 선학역 행사 알림

선학역 근처 세븐일레븐 사장님 폰으로 **주변 콘서트·행사를 미리 알려주는 앱**입니다.
[munhak-store-bot](https://github.com/seungguJ/munhak-store-bot)의 확장판입니다.

```
Claude Code 루틴 (매일 06:30)  ──조사·판단──▶  data/events.json  ──push──▶  GitHub
                                                                          │
     ┌────────────────────────────────────────────────────────────────────┤
     ▼                                   ▼                                ▼
 Notify Changes                    Daily Reminders (08:00)          Deploy PWA
 🆕 새 행사 / ⬆️ 등급 상승 / ❌ 취소    📦 D-7 · ⏰ D-1 · 루틴 정지 감지      GitHub Pages
     └──────────── 웹푸시 ────────────┘                                │
                       ▼                                              ▼
                사장님 안드로이드 폰 (PWA: 행사 목록·등급·발주 추천)
```

- 설계: [docs/specs/2026-10-10-seonhak-event-alert-design.md](docs/specs/2026-10-10-seonhak-event-alert-design.md)
- 루틴 지시서: [ROUTINE.md](ROUTINE.md)
- 행사장 목록: [data/venues.json](data/venues.json) (거리·수용인원은 대략값, `capacity_verified: false`)

## 등급

`예상 인파 = 수용인원 × 채움률`, 원거리 행사장은 가중치 0.5를 곱함.
**S** ≥ 3만 · **A** ≥ 1만 · **B** ≥ 3천 · **C** 그 외 (C는 앱에만 표시, 푸시 없음).
Claude는 근거를 남기고 한 단계까지만 조정 가능. 계산은 `alert/grading.py`.

## 설치 (1회)

### 1. GitHub repo + Pages
```bash
gh repo create seonhak-event-alert --private --source . --push
```
repo → Settings → Pages → Source: **GitHub Actions**. (private repo의 Pages는 유료 플랜 필요 — 무료 계정이면 public으로)

### 2. VAPID 키
```bash
python scripts/gen_vapid.py
```
- `PUBLIC` → `web/config.js`의 `VAPID_PUBLIC_KEY`에 넣고 commit/push
- `PRIVATE` → Secret `VAPID_PRIVATE_KEY`
- Secret `VAPID_SUBJECT` = `mailto:<연락받을 이메일>`

### 3. 사장님 폰
1. 안드로이드 **크롬**에서 Pages 주소 열기 → 메뉴 → **홈 화면에 추가**
2. 앱 → ⚙︎ → **알림 켜기** → 허용
3. 화면의 **등록 코드 복사** → 관리자에게 전달
4. 관리자: Secret `PUSH_SUBSCRIPTIONS`에 `[<등록코드>]` 형태(JSON 배열)로 저장. 여러 폰이면 배열에 추가
5. Actions → **Daily Reminders** → Run workflow → mode `test` → 폰에 "✅ 알림 테스트"가 오면 완료

> 알림 받는 기기를 바꾸거나 크롬 데이터를 지우면 등록 코드가 바뀝니다. Actions 로그에 "만료된 구독" 경고가 나오면 3번을 다시 하세요.

### 4. Claude Code 루틴
Claude Code에서 `/schedule`로 클라우드 루틴 생성:
- 저장소: 이 repo / 주기: 매일 06:30 KST
- 프롬프트: `ROUTINE.md를 읽고 그대로 수행해줘.`
- 환경변수: `KOPIS_SERVICE_KEY` (munhak-store-bot과 같은 키)

루틴이 36시간 넘게 갱신하지 않으면 `routine-stale` 이슈가 자동 생성됩니다 (사장님에게는 알림 안 감).

## 개발

```bash
pip install -r requirements.txt
pytest -q
python -m alert.finalize data/events.json         # 등급 계산 + 검증
python -m alert.notify reminders                   # 구독 없으면 dry-run 출력
KOPIS_SERVICE_KEY=... python -m collectors.kopis   # 행사장 매칭 공연 후보
sh scripts/build_site.sh && python -m http.server 8765 -d _site   # PWA 미리보기
```
