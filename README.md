# Munhak Store Bot

인천 문학경기장 주변 편의점 운영을 위한 주간 자동 리포트 봇.

매주 월요일 08:00 KST에 카카오톡으로 다음 내용을 전송합니다:
- 문학경기장 이번 주 공연/경기 일정 (인터파크, KBO, 네이버)
- 세븐일레븐 SNS 화제 상품 Top 5 + 발주 추천

## 초기 설정

### 1. GitHub Repository 생성 후 Secrets 등록

GitHub → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 발급처 | 비고 |
|-------------|--------|------|
| `KAKAO_CLIENT_ID` | [카카오 개발자](https://developers.kakao.com) → 앱 → 플랫폼 키 → REST API 키 | |
| `KAKAO_CLIENT_SECRET` | 카카오 개발자 → 앱 → 플랫폼 키 → REST API 키 → 클라이언트 시크릿(카카오 로그인) | 활성화되어 있으면 필수 |
| `KAKAO_REFRESH_TOKEN` | 아래 토큰 발급 절차 참고 | 초기 1회 수동 발급 필요 |
| `NAVER_CLIENT_ID` | [네이버 개발자](https://developers.naver.com) → 검색 API 앱 등록 | 무료, 일 25,000건 |
| `NAVER_CLIENT_SECRET` | 네이버 개발자 | |
| `YOUTUBE_API_KEY` | [Google Cloud Console](https://console.cloud.google.com) → YouTube Data API v3 활성화 | 무료, 일 10,000 units |
| `KOPIS_SERVICE_KEY` | [KOPIS](https://www.kopis.or.kr) → OPEN API → 인증키 발급신청 | 무료, 공연 일정 핵심 소스 |
| `X_BEARER_TOKEN` | [Twitter Developer Portal](https://developer.twitter.com) → Bearer Token | 없으면 트위터 분석 자동 스킵 |
| `GH_PAT` | GitHub → Settings → Developer settings → Personal access tokens (Classic) → `repo` 권한 | 카카오 토큰 자동 갱신용 |

> 카카오 Redirect URI는 `앱 → 플랫폼 키 → REST API 키 → Redirect URI`에 `http://localhost:5000` 등록.
> Refresh Token 발급은 `python get_kakao_token.py` (로컬 전용 스크립트)로 자동화.

### 2. 카카오 Refresh Token 최초 발급

**Step 1.** 브라우저에서 아래 URL 접속 (`YOUR_CLIENT_ID` 교체):

```
https://kauth.kakao.com/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=https://localhost&response_type=code&scope=talk_message
```

카카오 로그인 후 `https://localhost/?code=XXXX...` 로 리다이렉트됨. URL에서 `code=` 이후 값 복사.

**Step 2.** 터미널에서 토큰 발급:

```bash
curl -X POST https://kauth.kakao.com/oauth/token \
  -d "grant_type=authorization_code" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=https://localhost" \
  -d "code=복사한_코드"
```

응답 JSON에서 `refresh_token` 값을 `KAKAO_REFRESH_TOKEN` secret에 등록.

### 3. GitHub에 코드 Push

```bash
git remote add origin https://github.com/YOUR_USERNAME/munhak-store-bot.git
git branch -M main
git push -u origin main
```

### 4. 수동 실행으로 테스트

GitHub → Actions → Weekly Munhak Store Report → Run workflow

카카오톡에 메시지가 도착하면 설정 완료.

## 로컬 테스트

```bash
pip install -r requirements.txt
pytest -v
```

## 자동 실행 일정

매주 **월요일 오전 8시 KST** (GitHub Actions cron: `0 23 * * 0`)

## 데이터 소스

| 정보 | 소스 |
|------|------|
| 공연/행사 일정 (이번 주 + 다가오는 90일) | KOPIS 공연예술통합전산망 (시설명: 인천문학경기장) |
| 편의점 트렌드 | 네이버 블로그/카페 + YouTube + Twitter(X) |
