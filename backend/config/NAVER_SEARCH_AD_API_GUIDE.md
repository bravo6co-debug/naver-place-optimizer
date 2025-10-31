# 네이버 검색광고 API 연동 가이드

## 개요

네이버 검색광고 API를 통해 실제 검색량, 경쟁도, CPC 데이터를 가져올 수 있습니다.

## API 신청 방법

### 1. 네이버 검색광고 계정 생성
1. [네이버 검색광고](https://searchad.naver.com/) 접속
2. 회원가입 및 로그인
3. 광고 계정 생성 (최소 입금 불필요)

### 2. API 권한 신청
1. 검색광고 관리 화면 > 도구 > API 관리
2. API 사용 신청
3. 고객 ID, API 키, Secret 키 발급
   - **고객 ID**: `cus-a001-01-000000000`
   - **API 키**: `01000000000abcd...`
   - **Secret 키**: `AQAAAAabcdef...`

### 3. 환경 변수 설정

`.env` 파일에 다음 정보 추가:

```env
# 네이버 검색광고 API
NAVER_SEARCH_AD_CUSTOMER_ID=cus-a001-01-000000000
NAVER_SEARCH_AD_API_KEY=01000000000abcd...
NAVER_SEARCH_AD_SECRET_KEY=AQAAAAabcdef...
```

## 사용 가능한 데이터

### 1. 키워드 통계 (Keyword Tool API)

#### 제공 데이터
- **월간 검색수**
  - PC 검색수
  - 모바일 검색수
- **월평균 클릭수**
  - PC 클릭수
  - 모바일 클릭수
- **월평균 클릭률 (CTR)**
- **경쟁 정도**
  - "높음" / "중간" / "낮음"
- **평균 클릭 비용 (CPC)**
  - 단위: 원

#### API 엔드포인트
```
GET https://api.naver.com/keywordstool
```

#### 요청 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| hintKeywords | string | Y | 조회할 키워드 (쉼표로 구분, 최대 5000개) |
| showDetail | int | N | 상세 정보 포함 (1) |
| device | string | N | 기기 필터 ("pc", "mobile") |
| month | int | N | 조회 개월 수 (1-12) |

#### 응답 예시
```json
{
  "keywordList": [
    {
      "relKeyword": "강남 카페",
      "monthlyPcQcCnt": 5000,
      "monthlyMobileQcCnt": 15000,
      "monthlyAvePcClkCnt": 400,
      "monthlyAveMobileClkCnt": 1200,
      "monthlyAvePcCtr": 8.0,
      "compIdx": "높음",
      "plAvgDepth": 350
    }
  ]
}
```

### 2. 연관 키워드 조회

동일한 API를 사용하여 입력한 키워드의 연관 키워드를 받을 수 있습니다.

## 코드 사용 예시

### 기본 사용법

```python
from integrations.naver_search_ad_api import NaverSearchAdAPI

# API 클라이언트 생성
api = NaverSearchAdAPI()

# 키워드 통계 조회
keywords = ["강남 카페", "강남역 브런치", "강남 맛집"]
stats = api.get_keyword_stats(keywords)

for stat in stats:
    parsed = api.parse_keyword_data(stat)
    print(f"키워드: {parsed['keyword']}")
    print(f"  월간 검색수: {parsed['monthly_total_searches']:,}")
    print(f"  경쟁도: {parsed['competition_level']}")
    print(f"  평균 CPC: {parsed['avg_cpc']}원")
```

### 서비스와 통합

```python
from services.search_volume_estimator import SearchVolumeEstimatorService

estimator = SearchVolumeEstimatorService()

# 자동으로 API 데이터 우선, 실패 시 추정값 사용
result = await estimator.estimate_monthly_searches(
    keyword="강남 카페",
    category="카페",
    location="서울 강남구"
)

print(f"검색량: {result['total']}")
print(f"데이터 소스: {result['source']}")  # "api" or "estimated"
```

## API 사용 시 주의사항

### 1. 비용
- **무료 할당량**: 월 1,000회 요청
- 초과 시 별도 요금 발생
- 캐싱을 통해 비용 절감 필요

### 2. 요청 제한
- 초당 10회 요청 제한
- 동시 요청 최대 3개
- 키워드 최대 5,000개/요청

### 3. 인증
- API 키는 매번 서명(Signature) 생성 필요
- 타임스탬프 기반 HMAC-SHA256 서명

### 4. 캐싱 전략
```python
# 24시간 캐싱 권장
- 검색량 데이터: 24시간
- 경쟁도 데이터: 1주일
```

## 폴백 전략

API가 실패하거나 키가 없는 경우:
1. **1차**: 네이버 로컬 검색 API (경쟁 업체 수)
2. **2차**: 지역 인구 기반 추정
3. **3차**: 키워드 길이 기반 추정

## 참고 자료

- [네이버 검색광고 API 문서](https://naver.github.io/searchad-apidoc/)
- [키워드 도구 API](https://naver.github.io/searchad-apidoc/#/guides/keyword-tool)
- [인증 가이드](https://naver.github.io/searchad-apidoc/#/guides/authentication)

## 문제 해결

### API 호출 실패
```
오류: 401 Unauthorized
해결: API 키와 Secret 키 확인, 서명 생성 로직 점검
```

### 빈 결과 반환
```
오류: keywordList가 비어있음
해결: 키워드가 너무 구체적이거나 검색량이 없을 수 있음
      -> 폴백 로직으로 자동 전환됨
```

### 요청 제한 초과
```
오류: 429 Too Many Requests
해결: 요청 간 딜레이 추가 (최소 100ms)
      캐싱 활성화
```
