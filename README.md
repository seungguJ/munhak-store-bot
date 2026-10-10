# 선학역 주변 행사 알림

인천 선학역 반경 2~3km 행사장(문학경기장, SSG랜더스필드, 선학체육관 등)의 콘서트·페스티벌·대회 일정을 모아
**예상 인파와 등급**을 매기고, 휴대폰으로 **푸시 알림**을 보내는 웹앱입니다.

```
Claude Code 루틴 (매주 월 06:30)   ──조사──▶  data/events.json  ──push──▶  GitHub
                                                                        │
      ┌─────────────────────────────────┬───────────────────────────────┤
      ▼                                 ▼                               ▼
 Notify Changes                  Daily Reminders (08:00 KST)       Deploy PWA
 🆕 새 행사 · ⬆️ 등급 상승 · ❌ 취소     📅 D-7 · ⏰ D-1 · 루틴 정지 감지     GitHub Pages
      └──────────── 웹푸시 ─────────────┘                               │
                        ▼                                               ▼
                    휴대폰 (PWA: 행사 목록 · 등급 · 예상 인파 · 지도)
```

## 구성

| 경로 | 내용 |
|---|---|
| `ROUTINE.md` | 매일 행사를 조사하는 Claude Code 루틴 지시서 |
| `data/venues.json` | 감시 대상 행사장 (거리·수용인원은 대략값) |
| `data/events.json` | 행사 목록 (루틴이 갱신, 앱이 읽음) |
| `schema/events.schema.json` | events.json 스키마 |
| `alert/` | 등급 계산, 알림 판정, 웹푸시 전송 |
| `collectors/kopis.py` | KOPIS 공연 후보 수집 |
| `web/` | PWA |

## 등급

`예상 인파 = 수용인원 × 채움률` (원거리 행사장은 × 0.5)

| 등급 | 하루 예상 인파 | 알림 |
|---|---|---|
| S | 3만 명 이상 | ✅ |
| A | 1만 명 이상 | ✅ |
| B | 3천 명 이상 | ✅ |
| C | 그 외 | 앱에만 표시 |

KBO 정규리그 경기는 제외합니다.

## 설정

### 1. GitHub Pages
Settings → Pages → Source: **GitHub Actions**

### 2. 웹푸시 키
```bash
python scripts/setup_push.py
```
Secret `VAPID_PRIVATE_KEY`·`VAPID_SUBJECT`를 등록하고 `web/config.js`에 공개키를 넣습니다. 이후 `web/config.js`를 commit/push.

### 3. 알림 받을 휴대폰 (안드로이드 크롬)
1. Pages 주소 열기 → 메뉴 → **홈 화면에 추가**
2. 앱 → ⚙︎ → **알림 켜기** → **등록 코드 복사**
3. Secret `PUSH_SUBSCRIPTIONS`에 `[<등록 코드>, ...]` (JSON 배열)로 저장
4. Actions → **Daily Reminders** → Run workflow → mode `test`로 수신 확인

Actions 로그에 "만료된 구독" 경고가 나오면 3번을 다시 진행합니다.

### 4. Claude Code 루틴
`/schedule`로 이 저장소 대상 클라우드 루틴 생성
- 주기: 매주 월요일 06:30 KST (큰 행사는 보통 2주~수개월 전에 발표됨. D-7/D-1 알림은 매일 Actions가 보냄)
- 프롬프트: `ROUTINE.md를 읽고 그대로 수행해줘.`
- 환경변수: `KOPIS_SERVICE_KEY`

루틴이 8일 넘게 갱신하지 않으면 `routine-stale` 이슈, 목록 밖 장소의 행사 후보가 있으면 `venue-suggestion` 이슈가 자동 생성됩니다.

## 개발

```bash
pip install -r requirements.txt
pytest -q
python -m alert.finalize data/events.json        # 등급 계산 + 스키마 검증
python -m alert.notify reminders                  # 구독이 없으면 dry-run
KOPIS_SERVICE_KEY=... python -m collectors.kopis  # 행사장 매칭 공연 후보
sh scripts/build_site.sh && python -m http.server 8765 -d _site
```
