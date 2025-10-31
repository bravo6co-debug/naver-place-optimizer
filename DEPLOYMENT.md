# 🚀 네이버 플레이스 최적화 서비스 - 배포 가이드

## 📋 목차
- [배포 방식 선택](#배포-방식-선택)
- [Vercel + Railway 배포 (추천)](#vercel--railway-배포-추천)
- [환경 변수 설정](#환경-변수-설정)
- [배포 후 확인](#배포-후-확인)
- [문제 해결](#문제-해결)

---

## 배포 방식 선택

### ⭐ 추천: Vercel + Railway
- **비용**: 월 $5 (Railway만 유료)
- **난이도**: ⭐ 매우 쉬움
- **장점**: 자동 CI/CD, 무료 도메인, HTTPS 자동
- **예상 시간**: 10분

### 대안: Render (올인원)
- **비용**: 무료 또는 월 $21+
- **난이도**: ⭐⭐ 쉬움
- **장점**: 한 곳에서 모두 관리
- **단점**: 무료 티어는 슬립 모드 있음

---

## Vercel + Railway 배포 (추천)

### 1️⃣ **사전 준비**

#### GitHub에 코드 푸시
```bash
git init
git add .
git commit -m "feat: 네이버 플레이스 최적화 v2.0 완성"
git remote add origin https://github.com/YOUR_USERNAME/naver-place-optimizer.git
git push -u origin master
```

#### API 키 확인
다음 API 키들을 준비하세요:
- OpenAI API Key
- Naver Client ID & Secret (로컬 API)
- Naver Search Ad API Key, Secret, Customer ID

---

### 2️⃣ **Backend 배포 (Railway)**

#### A. Railway 가입 및 프로젝트 생성
1. [Railway](https://railway.app)에 GitHub 계정으로 가입
2. **New Project** → **Deploy from GitHub repo** 선택
3. `naver-place-optimizer` 레포지토리 선택

#### B. 배포 설정
1. **Root Directory**: `backend` 입력
2. **Start Command**: 자동 감지 (Procfile 사용)
3. Python 버전은 자동으로 3.11 선택

#### C. 환경 변수 설정
Railway 프로젝트 → **Variables** 탭에서 추가:

```env
OPENAI_API_KEY=sk-your-openai-key
NAVER_CLIENT_ID=your-naver-client-id
NAVER_CLIENT_SECRET=your-naver-client-secret
NAVER_API_KEY=your-search-ad-api-key
NAVER_SECRET_KEY=your-search-ad-secret
NAVER_CUSTOMER_ID=your-customer-id
PORT=8000
ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

⚠️ **중요**: `ALLOWED_ORIGINS`는 나중에 Vercel 도메인으로 업데이트

#### D. 배포 URL 확인
- Railway가 자동으로 배포하고 URL 제공
- 예: `https://naver-place-optimizer-production.up.railway.app`
- 이 URL을 복사해두세요!

#### E. 배포 확인
```bash
curl https://your-backend.up.railway.app/health
# 응답: {"status":"healthy","version":"3.0.0",...}
```

---

### 3️⃣ **Frontend 배포 (Vercel)**

#### A. Vercel 가입 및 프로젝트 생성
1. [Vercel](https://vercel.com)에 GitHub 계정으로 가입
2. **Add New Project** → `naver-place-optimizer` 선택

#### B. 배포 설정
1. **Framework Preset**: Vite 자동 감지
2. **Root Directory**: `frontend` 입력
3. **Build Command**: `npm run build` (자동 설정됨)
4. **Output Directory**: `dist` (자동 설정됨)

#### C. 환경 변수 설정
Vercel 프로젝트 → **Settings** → **Environment Variables**:

```env
VITE_API_URL=https://your-backend.up.railway.app
```

⚠️ Railway에서 받은 백엔드 URL을 입력하세요!

#### D. 배포 실행
- **Deploy** 클릭
- 2-3분 후 배포 완료
- 제공된 URL (예: `https://naver-place-optimizer.vercel.app`) 확인

---

### 4️⃣ **CORS 설정 업데이트 (Railway)**

#### Railway로 돌아가서:
1. **Variables** 탭 열기
2. `ALLOWED_ORIGINS` 값을 Vercel URL로 업데이트:
   ```
   https://naver-place-optimizer.vercel.app
   ```
3. Railway가 자동으로 재배포 (1-2분 소요)

---

### 5️⃣ **배포 완료! 🎉**

✅ **Frontend**: `https://your-app.vercel.app`
✅ **Backend**: `https://your-app.up.railway.app`

---

## 환경 변수 설정

### Backend (.env)
```env
# OpenAI API
OPENAI_API_KEY=sk-...

# Naver Local API
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...

# Naver Search Ad API
NAVER_API_KEY=...
NAVER_SECRET_KEY=...
NAVER_CUSTOMER_ID=...

# Server
PORT=8000
ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

### Frontend (.env)
```env
VITE_API_URL=https://your-backend.up.railway.app
```

---

## 배포 후 확인

### 1. Health Check
```bash
curl https://your-backend.up.railway.app/health
```

예상 응답:
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "engine": "UnifiedKeywordEngine V3",
  "openai": "configured",
  "naver_local": "configured",
  "naver_search_ad": "configured"
}
```

### 2. Frontend 접속
1. Vercel URL로 접속
2. 3개 탭 확인:
   - 🚀 전략적 분석
   - 📖 최적화 가이드
   - 🔍 SEO 가이드

### 3. API 연동 테스트
- "전략적 분석" 탭에서 업종 선택 후 분석 실행
- 키워드 생성 및 로드맵이 정상 표시되면 성공!

---

## 문제 해결

### Backend 배포 실패
**증상**: Railway 배포 로그에 에러
**해결**:
1. `backend/requirements.txt` 확인
2. Python 버전 확인 (3.11)
3. Railway 로그에서 구체적 에러 확인

### Frontend 빌드 실패
**증상**: Vercel 빌드 에러
**해결**:
1. `npm run build` 로컬에서 테스트
2. TypeScript 에러 확인
3. Vercel 로그 확인

### CORS 에러
**증상**: Frontend에서 API 호출 시 CORS 에러
**해결**:
1. Railway `ALLOWED_ORIGINS`에 Vercel URL 추가
2. 재배포 후 확인

### API 키 에러
**증상**: OpenAI 또는 Naver API 에러
**해결**:
1. Railway 환경 변수 재확인
2. API 키 유효성 확인
3. API 할당량 확인

---

## 💰 예상 비용

| 서비스 | 무료 티어 | 유료 플랜 | 추천 |
|--------|-----------|-----------|------|
| **Vercel** | 월 100GB 대역폭 | $20/월 (Pro) | 무료로 시작 |
| **Railway** | $5 크레딧 (1회) | $5/월 (500시간) | 유료 필수 |
| **OpenAI** | 사용량 기반 | $0.01/1K tokens | - |
| **Naver API** | 무료 (일일 제한) | - | - |
| **총 예상** | - | **$5~10/월** | - |

---

## 🔧 커스텀 도메인 연결 (선택)

### Vercel
1. Vercel 프로젝트 → **Settings** → **Domains**
2. 도메인 입력 (예: `place.yourdomain.com`)
3. DNS 레코드 추가 (Vercel이 안내)

### Railway
1. Railway 프로젝트 → **Settings** → **Public Networking**
2. **Custom Domain** 추가
3. DNS CNAME 레코드 설정

---

## 📚 추가 리소스

- [Vercel 문서](https://vercel.com/docs)
- [Railway 문서](https://docs.railway.app)
- [Vite 프로덕션 빌드](https://vitejs.dev/guide/build.html)
- [FastAPI 배포](https://fastapi.tiangolo.com/deployment/)

---

## 🆘 지원

문제 발생 시:
1. GitHub Issues 생성
2. 배포 로그 첨부
3. 에러 메시지 포함

---

**🎊 배포 완료! 이제 네이버 플레이스 최적화 서비스를 전 세계에서 사용할 수 있습니다!**
