# 백엔드 아키텍처 문서

## 개요

네이버 플레이스 최적화 도구의 백엔드는 모듈화된 구조로 설계되어 확장성과 유지보수성을 극대화했습니다.

## 디렉토리 구조

```
backend/
├── main_v2.py                    # FastAPI 엔트리포인트
├── strategic_keyword_engine.py   # 레거시 엔진 (호환성 유지)
├── requirements.txt              # Python 의존성
├── .env                          # 환경 변수
│
├── models/                       # 데이터 모델
│   ├── __init__.py
│   ├── keyword.py               # 키워드 관련 모델
│   ├── strategy.py              # 전략 관련 모델
│   └── business.py              # 비즈니스 정보 모델
│
├── services/                     # 비즈니스 로직
│   ├── __init__.py
│   ├── keyword_generator.py     # 키워드 생성 서비스
│   ├── search_volume_estimator.py  # 검색량 추정 서비스
│   ├── competition_analyzer.py  # 경쟁도 분석 서비스
│   └── strategy_planner.py      # 전략 수립 서비스
│
├── integrations/                 # 외부 API 통합
│   ├── __init__.py
│   ├── naver_search_ad_api.py   # 네이버 검색광고 API
│   ├── naver_local_api.py       # 네이버 로컬 검색 API
│   └── openai_api.py            # OpenAI GPT API
│
├── config/                       # 설정 및 데이터
│   ├── __init__.py
│   ├── category_loader.py       # 업종 데이터 로더
│   ├── NAVER_SEARCH_AD_API_GUIDE.md
│   └── categories/              # 업종별 JSON 데이터
│       ├── restaurant.json
│       ├── cafe.json
│       ├── salon.json
│       ├── hospital.json
│       ├── academy.json
│       └── gym.json
│
└── database/                     # 데이터베이스 (향후 구현)
    ├── keyword_cache.py         # 키워드 캐싱
    └── analytics.py             # 분석 데이터 저장
```

## 핵심 컴포넌트

### 1. Models (데이터 모델)

순수 데이터 구조만 정의. 비즈니스 로직 없음.

#### keyword.py
```python
- KeywordLevel: 키워드 레벨 (1-5)
- KeywordMetrics: 키워드 지표 (검색량, 경쟁도, 난이도 등)
- KeywordSuggestion: 키워드 제안
```

#### strategy.py
```python
- StrategyPhase: 전략 단계 (로드맵)
```

#### business.py
```python
- BusinessInfo: 비즈니스 정보
- CategoryData: 업종 데이터
```

### 2. Integrations (외부 API)

외부 API와의 통신만 담당. 비즈니스 로직 없음.

#### naver_search_ad_api.py
```python
- NaverSearchAdAPI
  ├── get_keyword_stats()      # 키워드 통계 조회
  ├── get_related_keywords()   # 연관 키워드 조회
  └── parse_keyword_data()     # 응답 데이터 파싱
```

**제공 데이터:**
- 월간 PC/모바일 검색량
- 월평균 클릭수
- 경쟁 정도 (높음/중간/낮음)
- 평균 CPC

#### naver_local_api.py
```python
- NaverLocalAPI
  ├── get_competition_count()  # 경쟁 업체 수 조회
  └── calculate_competition_score()  # 경쟁도 점수 계산
```

#### openai_api.py
```python
- OpenAIAPI
  ├── generate_keywords()      # GPT 키워드 생성
  └── _build_keyword_prompt()  # 프롬프트 구성
```

### 3. Services (비즈니스 로직)

핵심 비즈니스 로직. Integrations와 Models를 조합.

#### keyword_generator.py
```python
- KeywordGeneratorService
  ├── generate_keywords()           # 키워드 생성 (GPT 우선)
  ├── _generate_fallback_keywords() # 폴백 키워드 생성
  └── _apply_pattern()              # 패턴 적용
```

**키워드 생성 전략:**
1. OpenAI GPT로 생성 시도
2. 실패 시 패턴 기반 생성
3. 업종별 JSON 데이터 활용

#### search_volume_estimator.py
```python
- SearchVolumeEstimatorService
  ├── estimate_monthly_searches()   # 다단계 검색량 추정
  ├── _get_from_api()               # API에서 데이터 조회
  ├── _estimate_from_population()   # 인구 기반 추정
  └── apply_level_multiplier()      # 레벨별 조정
```

**추정 전략 (폴백):**
1. 네이버 검색광고 API (실제 데이터)
2. 지역 인구 × 이용률 × 검색률
3. 키워드 길이 기반 추정

#### competition_analyzer.py
```python
- CompetitionAnalyzerService
  ├── analyze_competition()         # 경쟁도 분석
  ├── _get_ad_competition_data()    # 광고 API 데이터
  └── calculate_difficulty_score()  # 난이도 점수 계산
```

**경쟁도 계산:**
- 네이버 로컬 검색 결과 수 (0-100 점수화)
- 검색광고 API 경쟁도 수준
- 평균 CPC

#### strategy_planner.py
```python
- StrategyPlannerService
  ├── generate_roadmap()      # 전략 로드맵 생성
  └── get_rank_target()       # 레벨별 목표 설정
```

**로드맵 단계:**
1. 롱테일 킬러 (1-2주, Level 5)
2. 니치 공략 (3-8주, Level 4)
3. 중위권 진입 (3-6개월, Level 3)
4. 상위권 도전 (6개월+, Level 2)

### 4. Config (설정 및 데이터)

#### category_loader.py
```python
- CategoryLoader
  ├── get_category()      # 업종 데이터 조회
  ├── list_categories()   # 사용 가능한 업종 목록
  └── clear_cache()       # 캐시 초기화
```

#### categories/*.json
업종별 세분화된 데이터:
```json
{
  "name": "카페",
  "usage_rate": 0.80,
  "search_rate": 0.40,
  "conversion_rate": 0.10,
  "base_keywords": ["카페", "커피숍"],
  "modifiers": {
    "목적": ["공부", "작업", "데이트"],
    "특징": ["조용한", "넓은", "감성"],
    "메뉴": ["커피맛집", "디저트맛집"]
  },
  "longtail_patterns": [
    "{지역} {목적} 하기좋은 카페"
  ]
}
```

## 데이터 흐름

### 키워드 분석 요청 흐름

```
[Client Request]
      ↓
[FastAPI Endpoint] (main_v2.py)
      ↓
[KeywordGeneratorService]
      ├─→ [OpenAIAPI] (GPT 키워드 생성)
      └─→ [CategoryLoader] (업종 데이터)
      ↓
[SearchVolumeEstimatorService]
      ├─→ [NaverSearchAdAPI] (실제 검색량)
      └─→ fallback: 인구 기반 추정
      ↓
[CompetitionAnalyzerService]
      ├─→ [NaverLocalAPI] (경쟁 업체 수)
      └─→ [NaverSearchAdAPI] (경쟁도, CPC)
      ↓
[StrategyPlannerService]
      ↓
[KeywordMetrics 생성]
      ↓
[Response to Client]
```

## API 키 우선순위

### 검색량 데이터
1. **네이버 검색광고 API** (최우선)
   - 실제 월간 검색량
   - PC/모바일 분리
2. 지역 인구 기반 추정
3. 키워드 길이 기반 추정

### 경쟁도 데이터
1. **네이버 검색광고 API**
   - 경쟁 수준 (높음/중간/낮음)
   - 평균 CPC
2. **네이버 로컬 검색 API**
   - 검색 결과 업체 수
3. 키워드 길이 기반 추정

## 캐싱 전략 (향후 구현)

### 캐싱 대상
- 검색광고 API 결과: 24시간
- 로컬 검색 API 결과: 1주일
- 업종 데이터: 앱 재시작 시까지

### 캐시 키 설계
```python
cache_key = f"keyword:{keyword}:location:{location}:date:{YYYYMMDD}"
```

## 환경 변수

### 필수
```env
OPENAI_API_KEY=sk-...          # GPT 키워드 생성용
```

### 선택 (정확도 향상)
```env
# 네이버 로컬 검색 (경쟁 업체 수)
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...

# 네이버 검색광고 (실제 검색량, 경쟁도)
NAVER_SEARCH_AD_CUSTOMER_ID=cus-...
NAVER_SEARCH_AD_API_KEY=...
NAVER_SEARCH_AD_SECRET_KEY=...
```

## 확장 포인트

### 단기 (현재 구현 완료)
- ✅ 모듈화된 구조
- ✅ 업종 데이터 JSON 외부화
- ✅ 네이버 검색광고 API 연동
- ✅ 다단계 폴백 시스템

### 중기 (향후 구현)
- ⬜ 캐싱 시스템 (Redis)
- ⬜ 데이터베이스 연동 (PostgreSQL)
- ⬜ 분석 데이터 저장
- ⬜ A/B 테스트 시스템

### 장기
- ⬜ 머신러닝 기반 검색량 예측
- ⬜ 실시간 경쟁도 모니터링
- ⬜ 사용자별 맞춤 전략
- ⬜ 네이버 데이터랩 API 연동

## 주요 개선 사항

### AS-IS (기존)
```python
# strategic_keyword_engine.py (680줄 단일 파일)
- 모든 로직이 한 곳에 집중
- 업종 데이터 하드코딩
- API 통합 없음
- 추정치만 사용
```

### TO-BE (개선)
```python
# 모듈별 분리 (20+ 파일)
- 관심사 분리 (SoC)
- 업종 데이터 JSON 외부화
- 네이버 검색광고 API 통합
- 실제 데이터 우선, 폴백 시스템
```

## 의존성

```txt
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.1
openai==1.3.5
python-dotenv==1.0.0
tenacity==8.2.3
pydantic==2.5.0
```

## 개발 가이드

### 새 업종 추가
1. `config/categories/새업종.json` 생성
2. `category_loader.py`의 `filename_map`에 추가
3. 서버 재시작

### 새 API 통합
1. `integrations/`에 새 클라이언트 생성
2. `services/`에서 활용
3. `.env`에 API 키 추가

### 테스트
```bash
# 개별 모듈 테스트
cd backend
python -m integrations.naver_search_ad_api
python -m services.keyword_generator

# 서버 실행
uvicorn main_v2:app --reload
```

## 참고 문서

- [네이버 검색광고 API 가이드](./config/NAVER_SEARCH_AD_API_GUIDE.md)
- [네이버 개발자 센터](https://developers.naver.com/)
- [OpenAI API 문서](https://platform.openai.com/docs)
