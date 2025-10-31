# 🚀 네이버 플레이스 최적화 서비스 - 빠른 시작

## 📋 목차
- [시스템 요구사항](#시스템-요구사항)
- [설치 방법](#설치-방법)
- [실행 방법](#실행-방법)
- [사용 방법](#사용-방법)
- [문제 해결](#문제-해결)

---

## 시스템 요구사항

### 필수
- Python 3.8 이상
- Node.js 18 이상
- npm 또는 yarn

### 권장
- Windows 10/11, macOS, Linux
- 최소 4GB RAM
- 인터넷 연결

---

## 설치 방법

### 1. 백엔드 (FastAPI) 설치

```bash
# backend 디렉토리로 이동
cd backend

# 가상환경 생성 (선택사항)
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 프론트엔드 (React) 설치

```bash
# frontend 디렉토리로 이동
cd frontend

# 패키지 설치
npm install
```

---

## 실행 방법

### 터미널 2개를 사용하여 백엔드와 프론트엔드를 각각 실행합니다.

### 터미널 1: 백엔드 실행

```bash
cd backend
python main.py
```

✅ **성공 메시지:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

백엔드가 `http://localhost:8000`에서 실행됩니다.

### 터미널 2: 프론트엔드 실행

```bash
cd frontend
npm run dev
```

✅ **성공 메시지:**
```
VITE v5.4.1  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

프론트엔드가 `http://localhost:5173`에서 실행됩니다.

---

## 사용 방법

### 1. 웹 브라우저 열기
브라우저에서 `http://localhost:5173` 접속

### 2. 키워드 분석 사용

1. **📊 키워드 분석** 탭 선택
2. **업종 선택** (음식점, 카페, 미용실 등)
3. **위치 입력** (예: 서울 강남구, 부산 해운대)
4. **🔍 분석하기** 버튼 클릭
5. 결과 확인:
   - 주력 키워드
   - 보조 키워드
   - 롱테일 키워드
   - 맞춤 추천사항

### 3. 최적화 가이드 확인

1. **📖 최적화 가이드** 탭 선택
2. 왼쪽 메뉴에서 원하는 주제 선택:
   - 업체명 최적화
   - 카테고리 선택
   - 업체 소개글 작성
   - 사진 등록 전략
   - 영업시간 및 정보
   - 메뉴/가격 정보
   - 리뷰 관리
   - 검색 최적화
3. 우선순위별 가이드 확인 (필수/권장/선택)

---

## API 엔드포인트

백엔드는 다음 API를 제공합니다:

### 키워드 분석
```
POST http://localhost:8000/api/analyze
Content-Type: application/json

{
  "business_type": "음식점",
  "location": "서울 강남구"
}
```

### 최적화 가이드 조회
```
GET http://localhost:8000/api/guides
```

### 특정 가이드 조회
```
GET http://localhost:8000/api/guides/{section}
```

### 지원 업종 목록
```
GET http://localhost:8000/api/business-types
```

### API 문서
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 문제 해결

### 백엔드 실행 오류

#### 1. 모듈을 찾을 수 없음
```bash
ModuleNotFoundError: No module named 'fastapi'
```
**해결:** 패키지를 다시 설치하세요
```bash
pip install -r requirements.txt
```

#### 2. 포트 충돌
```bash
ERROR: [Errno 10048] error while attempting to bind on address
```
**해결:** 8000번 포트를 사용하는 다른 프로그램을 종료하거나, 다른 포트로 실행
```bash
python main.py --port 8001
```

#### 3. keyword_analyzer 임포트 오류
**해결:** scripts 디렉토리가 올바른 위치에 있는지 확인

### 프론트엔드 실행 오류

#### 1. npm 패키지 오류
```bash
npm ERR! code ERESOLVE
```
**해결:** 강제 설치
```bash
npm install --force
```

#### 2. 포트 충돌
```bash
Port 5173 is already in use
```
**해결:** 다른 포트로 실행
```bash
npm run dev -- --port 3000
```

#### 3. API 연결 오류
**증상:** 키워드 분석 시 에러 발생
**해결:**
1. 백엔드가 실행 중인지 확인 (`http://localhost:8000/health`)
2. CORS 설정 확인
3. 브라우저 콘솔에서 에러 확인

### 공통 문제

#### 브라우저 캐시 문제
**해결:** 브라우저 캐시 삭제 (Ctrl + Shift + Delete)

#### 방화벽 문제
**해결:** 방화벽에서 8000, 5173 포트 허용

---

## 개발 모드 vs 프로덕션

### 개발 모드 (현재)
- 핫 리로딩 지원
- 상세한 에러 메시지
- 디버깅 용이

### 프로덕션 빌드
```bash
# 프론트엔드 빌드
cd frontend
npm run build

# 빌드된 파일은 frontend/dist 에 생성됨
```

---

## 추가 정보

### 프로젝트 구조
```
naver-place-optimizer/
├── backend/              # FastAPI 백엔드
│   ├── main.py          # 메인 API 서버
│   └── requirements.txt # Python 패키지
├── frontend/            # React 프론트엔드
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   └── index.css
│   └── package.json
├── scripts/             # 키워드 분석 스크립트
│   └── keyword_analyzer.py
└── references/          # 최적화 가이드 문서
    └── optimization_guide.md
```

### 기술 스택
- **백엔드:** Python 3.x, FastAPI, Uvicorn
- **프론트엔드:** React 18, TypeScript, Vite, Axios
- **스타일:** CSS3 (그라데이션, 애니메이션)

### 라이선스
© 2025 Bravo Six Corp.

---

## 지원

문제가 발생하면:
1. 이 가이드의 [문제 해결](#문제-해결) 섹션 확인
2. 백엔드 로그 확인 (터미널 1)
3. 브라우저 콘솔 확인 (F12)
4. GitHub Issues 등록

---

**즐거운 최적화 되세요! 🎯**
