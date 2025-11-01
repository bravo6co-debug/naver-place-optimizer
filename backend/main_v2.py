#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 플레이스 최적화 서비스 - FastAPI 백엔드 V3
전략적 키워드 분석 시스템 - 검색광고 API 통합
Updated: 2025-11-01 - CORS fix deployed
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, AsyncGenerator
import os
import json
import asyncio
from dotenv import load_dotenv

from engine_v3 import UnifiedKeywordEngine, KeywordMetrics, StrategyPhase

load_dotenv()

app = FastAPI(
    title="네이버 플레이스 최적화 API v3",
    description="전략적 키워드 분석 및 로드맵 제공 - 검색광고 API 통합",
    version="3.0.0"
)

# CORS 설정
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 엔진 인스턴스 (V3 - 새로운 모듈 구조)
engine = UnifiedKeywordEngine()


# ========== 요청/응답 모델 ==========

class StrategicAnalysisRequest(BaseModel):
    business_type: str
    location: str
    specialty: Optional[str] = None
    current_daily_visitors: Optional[int] = 0
    target_daily_visitors: Optional[int] = 100


class KeywordMetricsResponse(BaseModel):
    keyword: str
    level: int
    level_name: str
    estimated_monthly_searches: int
    competition_score: int
    naver_result_count: int
    difficulty_score: int
    recommended_rank_target: str
    estimated_timeline: str
    estimated_daily_traffic: int
    conversion_rate: float
    confidence: str


class StrategyPhaseResponse(BaseModel):
    phase: int
    name: str
    duration: str
    target_level: int
    target_level_name: str
    target_keywords_count: int
    strategies: List[str]
    goals: List[str]
    expected_daily_visitors: int

    # V4 추가 필드
    priority_keywords: List[str] = []
    keyword_traffic_breakdown: Dict[str, int] = {}
    difficulty_level: str = "보통"
    cumulative_visitors: int = 0

    # V5 Simplified 추가 필드
    receipt_review_target: int = 0
    weekly_review_target: int = 0
    consistency_importance: str = ""
    receipt_review_keywords: List[str] = []
    review_quality_standard: Dict[str, Any] = {}
    review_incentive_plan: str = ""
    keyword_mention_strategy: Dict[str, str] = {}
    info_trust_checklist: List[str] = []
    review_templates: Dict[str, str] = {}


class StrategicAnalysisResponse(BaseModel):
    business_info: Dict[str, str]
    total_keywords: int
    keywords_by_level: Dict[str, List[KeywordMetricsResponse]]
    strategy_roadmap: List[StrategyPhaseResponse]
    summary: Dict[str, Any]


# ========== 헬퍼 함수 ==========

def get_level_name(level: int) -> str:
    """레벨 번호 → 이름"""
    names = {
        5: "롱테일 (가장 쉬움)",
        4: "니치",
        3: "중간",
        2: "경쟁",
        1: "최상위 (가장 어려움)"
    }
    return names.get(level, "알 수 없음")


def get_confidence_level(metrics: KeywordMetrics) -> str:
    """
    신뢰도 등급 (V3 개선)
    데이터 소스에 따라 신뢰도 차별화
    """
    # 데이터 소스 기반 신뢰도
    if metrics.data_source == "api":
        return "최고 (A+) - 실제 검색광고 데이터"
    elif metrics.data_source == "naver_local":
        return "높음 (A) - 네이버 로컬 데이터"

    # 추정치인 경우 점수 기반
    avg_score = (metrics.competition_score + metrics.difficulty_score) / 2
    if avg_score < 30:
        return "보통 (B) - AI 추정"
    elif avg_score < 60:
        return "낮음 (C) - AI 추정"
    else:
        return "매우 낮음 (D) - AI 추정"


# ========== API 엔드포인트 ==========

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "네이버 플레이스 최적화 API v3",
        "version": "3.0.0",
        "features": [
            "5단계 키워드 난이도 분석",
            "GPT-4 기반 키워드 생성",
            "네이버 검색광고 API (실제 검색량)",
            "네이버 로컬 API (경쟁도)",
            "다단계 폴백 시스템",
            "트래픽 기반 전략 로드맵",
            "목표 달성 시뮬레이션"
        ],
        "endpoints": {
            "strategic_analysis": "/api/v2/analyze",
            "optimization_guides": "/api/guides",
            "test_gpt": "/api/test/gpt"
        }
    }


@app.post("/api/v2/analyze", response_model=StrategicAnalysisResponse)
async def strategic_analysis(request: StrategicAnalysisRequest):
    """전략적 키워드 분석 (V2)"""
    try:
        # 1. GPT로 키워드 생성
        keywords_data = await engine.generate_keywords_with_gpt(
            request.business_type,
            request.location,
            request.specialty
        )

        # 2. 각 키워드 분석
        analyzed_keywords = []
        for kw_data in keywords_data:
            metrics = await engine.analyze_keyword(
                kw_data['keyword'],
                kw_data['level'],
                request.location,
                request.business_type
            )

            analyzed_keywords.append({
                "metrics": metrics,
                "reason": kw_data.get('reason', '')
            })

        # 3. 레벨별로 그룹화
        keywords_by_level = {
            "level_5": [],
            "level_4": [],
            "level_3": [],
            "level_2": [],
            "level_1": []
        }

        for item in analyzed_keywords:
            metrics = item['metrics']
            level_key = f"level_{metrics.level}"

            keyword_response = KeywordMetricsResponse(
                keyword=metrics.keyword,
                level=metrics.level,
                level_name=get_level_name(metrics.level),
                estimated_monthly_searches=metrics.estimated_monthly_searches,
                competition_score=metrics.competition_score,
                naver_result_count=metrics.naver_result_count,
                difficulty_score=metrics.difficulty_score,
                recommended_rank_target=metrics.recommended_rank_target,
                estimated_timeline=metrics.estimated_timeline,
                estimated_daily_traffic=metrics.estimated_traffic,
                conversion_rate=round(metrics.conversion_rate * 100, 2),
                confidence=get_confidence_level(metrics)  # V3: metrics 객체 전달
            )

            keywords_by_level[level_key].append(keyword_response)

        # 4. 전략 로드맵 생성 (V4: 키워드 데이터 전달)
        keyword_metrics_list = [item['metrics'] for item in analyzed_keywords]
        roadmap = engine.generate_strategy_roadmap(
            request.current_daily_visitors,
            request.target_daily_visitors,
            request.business_type,
            analyzed_keywords=keyword_metrics_list  # V4 추가
        )

        roadmap_response = []
        for phase in roadmap:
            roadmap_response.append(StrategyPhaseResponse(
                phase=phase.phase,
                name=phase.name,
                duration=phase.duration,
                target_level=phase.target_level,
                target_level_name=get_level_name(phase.target_level),
                target_keywords_count=phase.target_keywords_count,
                strategies=phase.strategies,
                goals=phase.goals,
                expected_daily_visitors=phase.expected_daily_visitors,
                # V4 추가 필드
                priority_keywords=phase.priority_keywords,
                keyword_traffic_breakdown=phase.keyword_traffic_breakdown,
                difficulty_level=phase.difficulty_level,
                cumulative_visitors=phase.cumulative_visitors,
                # V5 Simplified 추가 필드
                receipt_review_target=phase.receipt_review_target,
                weekly_review_target=phase.weekly_review_target,
                consistency_importance=phase.consistency_importance,
                receipt_review_keywords=phase.receipt_review_keywords,
                review_quality_standard=phase.review_quality_standard,
                review_incentive_plan=phase.review_incentive_plan,
                keyword_mention_strategy=phase.keyword_mention_strategy,
                info_trust_checklist=phase.info_trust_checklist,
                review_templates=phase.review_templates
            ))

        # 5. 요약 정보
        total_traffic = sum([phase.expected_daily_visitors for phase in roadmap])
        summary = {
            "current_daily_visitors": request.current_daily_visitors,
            "target_daily_visitors": request.target_daily_visitors,
            "gap": request.target_daily_visitors - request.current_daily_visitors,
            "total_expected_traffic": total_traffic,
            "achievement_rate": round((total_traffic / max(request.target_daily_visitors - request.current_daily_visitors, 1)) * 100, 1),
            "total_phases": len(roadmap),
            "recommended_timeline": "6-12개월",
            "data_sources": [
                "OpenAI GPT-4 키워드 생성",
                "네이버 검색광고 API (실제 검색량)",
                "네이버 로컬 API (경쟁도)",
                "다단계 폴백 시스템"
            ]
        }

        return StrategicAnalysisResponse(
            business_info={
                "type": request.business_type,
                "location": request.location,
                "specialty": request.specialty or "일반"
            },
            total_keywords=len(analyzed_keywords),
            keywords_by_level=keywords_by_level,
            strategy_roadmap=roadmap_response,
            summary=summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@app.get("/api/test/gpt")
async def test_gpt():
    """GPT 연동 테스트"""
    if not engine.openai_client:
        return {
            "status": "error",
            "message": "OPENAI_API_KEY가 설정되지 않았습니다",
            "solution": "백엔드 .env 파일에 OPENAI_API_KEY를 추가하세요"
        }

    try:
        keywords = await engine.generate_keywords_with_gpt("카페", "서울 강남구")
        return {
            "status": "success",
            "message": "GPT-4 연동 성공",
            "sample_keywords": keywords[:3]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"GPT 호출 실패: {str(e)}"
        }


@app.get("/api/test/naver")
async def test_naver():
    """네이버 API 연동 테스트"""
    if not engine.naver_client_id or not engine.naver_client_secret:
        return {
            "status": "warning",
            "message": "네이버 API 키가 설정되지 않았습니다 (추정값으로 대체)",
            "solution": ".env 파일에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 추가"
        }

    try:
        count = await engine.get_naver_competition("강남역 카페", "서울 강남구", "카페")
        return {
            "status": "success",
            "message": "네이버 검색 API 연동 성공",
            "test_result": {
                "keyword": "강남역 카페",
                "result_count": count
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"네이버 API 호출 실패: {str(e)}"
        }


@app.get("/api/config/status")
async def config_status():
    """설정 상태 확인"""
    return {
        "openai_configured": bool(engine.openai_api_key),
        "naver_configured": bool(engine.naver_client_id and engine.naver_client_secret),
        "recommendations": [
            "GPT-4 사용을 위해 OPENAI_API_KEY 설정 권장 (필수)" if not engine.openai_api_key else "✅ OpenAI API 설정 완료",
            "정확한 경쟁도 측정을 위해 네이버 API 키 설정 권장 (선택)" if not engine.naver_client_id else "✅ 네이버 API 설정 완료"
        ]
    }


# ========== 업종별 최적화 가이드 ==========

BUSINESS_TYPE_GUIDES = {
    "공통": {
        "receipt_review": {
            "section": "receipt_review",
            "title": "영수증 리뷰 전략",
            "content": """### 최우선 전략
✅ 네이버 알고리즘 최우선 반영 (2024년 하반기 이후)
✅ 자동 생성 AI 리뷰 시스템 구축 필수
✅ 주 3~5개 이상 영수증 리뷰 확보 목표

### 실행 방법
1. 현장 POP/QR 코드로 리뷰 유도
2. 리뷰 작성 시 할인/적립 혜택 제공
3. 일 1-3개 꾸준한 리뷰 확보가 핵심
4. 리뷰 품질 관리 (텍스트 30자 이상, 사진 권장)

### 주의사항
❌ 과도한 보상 제공 (네이버 정책 위반)
❌ 대량 리뷰 작성 (스팸 감지 위험)""",
            "priority": "high"
        },
        "profile_complete": {
            "section": "profile_complete",
            "title": "프로필 완성도 100%",
            "content": """### 필수 항목
✅ 대표 사진 10장 이상
✅ 메뉴/서비스 상세 설명
✅ 영업시간 정확히 기재
✅ 편의시설 체크 (주차/무선인터넷/단체석/포장 가능)
✅ 전화번호 & 예약 링크

### 사진 전략
- 대표 메뉴/서비스 3장 이상
- 인테리어/외관 3장 이상
- 주차장/편의시설 2장 이상
- 조명 밝게, 고해상도 필수

### 업데이트 주기
- 월 1회 이상 사진 업데이트
- 시즌 메뉴/이벤트 즉시 반영
- 영업시간 변경 즉시 수정""",
            "priority": "high"
        },
        "review_management": {
            "section": "review_management",
            "title": "리뷰 관리 루틴",
            "content": """### 응답 원칙
✅ 신규 리뷰 24시간 내 답변
✅ 부정 리뷰도 정중히 응대 (해명보다 개선 의지)
✅ 월 평균 리뷰 10개 이상 유지

### 응답 템플릿
긍정 리뷰: "소중한 리뷰 감사합니다! 앞으로도 더 나은 서비스로 보답하겠습니다 😊"
부정 리뷰: "불편을 드려 죄송합니다. 말씀하신 부분 개선하도록 노력하겠습니다. 다시 한 번 방문 기회를 주시면 감사하겠습니다."

### 관리 루틴
- 매일 오전 리뷰 확인
- 주 1회 리뷰 트렌드 분석
- 월 1회 경쟁사 리뷰 벤치마킹""",
            "priority": "medium"
        }
    },
    "카페": {
        "business_name": {
            "section": "business_name",
            "title": "업체명 최적화",
            "content": """### 원칙
✅ "○○카페" 형식 권장
❌ 지역명 삽입 금지 (예: 강남○○카페 ❌)
❌ 키워드 나열 금지 (예: 브런치디저트○○ ❌)

### 좋은 예
✅ "루프탑카페"
✅ "북카페 ○○"
✅ "○○ 로스터스"

### 나쁜 예
❌ "강남역 맛집 브런치 카페"
❌ "커피&디저트전문점"
❌ "○○카페★강남점★"

### 검색 최적화
- 브랜드명 + 카페/커피 조합
- 특징이 있다면 추가 (예: 북카페, 루프탑카페)
- 영문과 한글 모두 등록""",
            "priority": "high"
        },
        "photo_strategy": {
            "section": "photo_strategy",
            "title": "사진 전략",
            "content": """### 필수 사진 구성
✅ 시그니처 메뉴 클로즈업 (3장 이상)
✅ 좌석 배치별 인테리어 (커플석, 단체석, 창가석)
✅ 외관 + 주차장

### 촬영 팁
- 자연광 활용 (오전 10-12시, 오후 2-4시)
- 메뉴 사진은 45도 각도
- 인테리어는 넓은 공간감 표현
- 손님 없는 시간대 촬영

### 업데이트 전략
- 시즌 메뉴 출시 시 즉시 업로드
- 월 1회 인테리어 변화 반영
- 날씨 좋은 날 외관 재촬영""",
            "priority": "high"
        },
        "keyword_strategy": {
            "section": "keyword_strategy",
            "title": "키워드 전략",
            "content": """### 핵심 키워드
1차: 시그니처 메뉴 (브런치, 디저트, 원두)
2차: 분위기 (감성카페, 데이트, 혼카페)
3차: 위치/주차 (○○역, 주차가능)

### 메뉴 설명에 포함
- "브런치 전문", "핸드드립 커피"
- "조용한 분위기", "인스타 감성"
- "주차 3시간 무료", "와이파이 무제한"

### 리뷰 유도 포인트
- 커피 맛 (원두, 로스팅)
- 디저트 비주얼 (케이크, 크루아상)
- 인테리어 무드 (감성, 아늑함)""",
            "priority": "medium"
        },
        "differentiation": {
            "section": "differentiation",
            "title": "차별화 전략",
            "content": """### 추가 정보
✅ 원두 로스팅 정보 추가
✅ 월별 시즌 메뉴 업데이트
✅ 테이크아웃 할인 정보 명시
✅ 단체석 예약 가능 여부

### 강조할 포인트
- 자체 로스팅 (있다면)
- 디저트 매장 제작 (있다면)
- 루프탑/테라스 (있다면)
- 반려동물 동반 가능 (있다면)

### 프로모션 예시
- 평일 오전 할인
- 테이크아웃 10% 할인
- 생일 쿠폰 제공
- 스탬프 적립 이벤트""",
            "priority": "low"
        }
    },
    "음식점": {
        "business_name": {
            "section": "business_name",
            "title": "업체명 최적화",
            "content": """### 원칙
✅ "○○식당" 또는 전문 요리명 (예: "○○갈비")
❌ 지역명 + 키워드 나열 금지

### 좋은 예
✅ "한우갈비 ○○"
✅ "○○ 일식당"
✅ "파스타 전문점 ○○"

### 나쁜 예
❌ "강남역맛집 ○○식당"
❌ "가성비최고 ○○"
❌ "○○고기★무한리필"

### 검색 최적화
- 전문 메뉴 + 식당/집 조합
- 한식/양식/일식/중식 명시
- 특화 메뉴 강조 (갈비, 파스타 등)""",
            "priority": "high"
        },
        "photo_strategy": {
            "section": "photo_strategy",
            "title": "사진 전략",
            "content": """### 필수 사진 구성
✅ 대표 메뉴 플레이팅 (조명 중요!)
✅ 반찬 구성
✅ 테이블 세팅 (룸/홀 구분)
✅ 외관 + 간판

### 촬영 팁
- 음식 사진은 자연광 필수
- 김이 모락모락 나는 순간 포착
- 색감 선명하게 (후보정 적절히)
- 그릇/접시 깨끗한 상태

### 메뉴판 사진
- 전체 메뉴 가격 명확히
- 세트 메뉴 구성 상세히
- 사이드 메뉴 별도 표시""",
            "priority": "high"
        },
        "keyword_strategy": {
            "section": "keyword_strategy",
            "title": "키워드 전략",
            "content": """### 핵심 키워드
1차: 대표 메뉴 (갈비, 파스타, 초밥)
2차: 가격대 (가성비, 1만원대)
3차: 특징 (단체석, 룸, 예약)

### 메뉴 설명에 포함
- "한우 1++등급", "직접 만든 수제 파스타"
- "1인분 12,000원 (가성비 좋음)"
- "단체석 20명까지", "프라이빗 룸 있음"

### 리뷰 유도 포인트
- 가성비 (양, 가격)
- 맛 (간, 신선도)
- 친절도 (직원, 사장님)
- 재방문 의사""",
            "priority": "medium"
        },
        "differentiation": {
            "section": "differentiation",
            "title": "차별화 전략",
            "content": """### 추가 정보
✅ 메뉴판 전체 사진 업로드 (가격 명확히)
✅ "점심 특선" "저녁 코스" 별도 등록
✅ 예약 가능 여부 명시
✅ 주차 대행 서비스 강조

### 강조할 포인트
- 원산지 표기 (국내산, 수입산)
- 조리 방식 (숯불, 직화, 무쇠팬)
- 특별 재료 (한우, 유기농)
- 코스 요리 (2인, 4인)

### 프로모션 예시
- 점심 특선 할인
- 예약 시 사이드 메뉴 서비스
- 생일 이벤트 (케이크/노래)
- 단체 예약 할인""",
            "priority": "low"
        }
    },
    "병원": {
        "business_name": {
            "section": "business_name",
            "title": "업체명 최적화",
            "content": """### 원칙
✅ "○○의원" / "○○병원"
❌ 진료과목 삽입 금지 (예: 피부과○○의원 ❌)
❌ 과대광고 금지 ("최고", "1등" 등)

### 좋은 예
✅ "○○내과의원"
✅ "○○정형외과"
✅ "○○치과"

### 나쁜 예
❌ "강남최고 ○○피부과"
❌ "1등 ○○치과의원"
❌ "○○전문병원★강남점"

### 의료법 준수
- 의료광고 심의 필수
- 과대광고 금지
- 거짓·과장 금지
- 비방 광고 금지""",
            "priority": "high"
        },
        "photo_strategy": {
            "section": "photo_strategy",
            "title": "사진 전략",
            "content": """### 필수 사진 구성
✅ 대기실 & 진료실 (청결감)
✅ 의료진 프로필 (신뢰감)
✅ 주차장 & 건물 외관
❌ 치료 전후 사진 금지 (의료법 위반)

### 촬영 팁
- 청결하고 밝은 분위기
- 최신 의료 장비 강조
- 넓고 쾌적한 대기실
- 접근성 좋은 주차장

### 의료법 준수 사항
❌ 환자 사진 금지
❌ 시술 전후 비교 금지
❌ 효과 과장 금지
✅ 시설/장비 사진만 가능""",
            "priority": "high"
        },
        "keyword_strategy": {
            "section": "keyword_strategy",
            "title": "키워드 전략",
            "content": """### 핵심 키워드
1차: 전문 진료과 (내과, 정형외과, 피부과)
2차: 장비/시설 (첨단, MRI, 물리치료)
3차: 편의성 (예약제, 야간진료, 주차)

### 진료과목 설명에 포함
- "○○ 전문의 진료"
- "첨단 MRI 장비 보유"
- "예약제 운영 (대기시간 최소화)"
- "야간진료 가능 (평일 오후 8시까지)"

### 리뷰 유도 포인트
- 대기시간 (빠른 진료)
- 의사 친절도 (상담, 설명)
- 치료 결과 (증상 완화)
- 시설 청결도""",
            "priority": "medium"
        },
        "compliance": {
            "section": "compliance",
            "title": "의료법 준수사항",
            "content": """### 금지사항
❌ 치료 전후 사진 금지
❌ 가격 할인 문구 금지
❌ "최고" "1등" 등 과대광고 금지
❌ 효과 보장 금지

### 허용사항
✅ 진료 시간 정확히 기재
✅ 주차 가능 여부 명시
✅ 예약 시스템 안내
✅ 의료진 경력 (학력, 경력)
✅ 보유 장비/시설

### 리뷰 관리 주의
- 리뷰 작성 유도 시 보상 금지
- 부정 리뷰에 정중히 응대
- 의료 분쟁 리뷰는 별도 대응
- 허위 리뷰 신고 적극 활용""",
            "priority": "high"
        }
    },
    "미용실": {
        "business_name": {
            "section": "business_name",
            "title": "업체명 최적화",
            "content": """### 원칙
✅ "○○헤어" / "○○살롱"
❌ 지역명 + 키워드 나열 금지

### 좋은 예
✅ "○○헤어살롱"
✅ "헤어살롱 ○○"
✅ "○○ 뷰티"

### 나쁜 예
❌ "강남역 염색펌 전문 ○○"
❌ "○○헤어★가성비최고"
❌ "염색10%할인 ○○헤어"

### 검색 최적화
- 브랜드명 + 헤어/살롱 조합
- 특화 시술 있다면 추가
- 영문 병기 권장""",
            "priority": "high"
        },
        "photo_strategy": {
            "section": "photo_strategy",
            "title": "사진 전략",
            "content": """### 필수 사진 구성
✅ 시술 전후 비교 (Before/After)
✅ 인테리어 (세면대, 거울, 대기공간)
✅ 디자이너 프로필
✅ 외관 + 주차장

### 촬영 팁
- 자연스러운 조명 (백색광)
- 시술 결과 선명하게
- 깨끗한 인테리어 강조
- 디자이너 작업 중 모습

### Before/After 주의
- 고객 동의 필수
- 과도한 보정 금지
- 실제 시술 결과만
- 다양한 스타일 제시""",
            "priority": "high"
        },
        "keyword_strategy": {
            "section": "keyword_strategy",
            "title": "키워드 전략",
            "content": """### 핵심 키워드
1차: 전문 시술 (염색, 펌, 클리닉)
2차: 디자이너 경력 (10년차, 원장)
3차: 특화 서비스 (두피케어, 트리트먼트)

### 프로필 설명에 포함
- "디자이너 경력 10년 이상"
- "염색/펌 전문"
- "두피 클리닉 프로그램 운영"
- "예약제 운영"

### 리뷰 유도 포인트
- 스타일링 만족도
- 상담 친절도
- 가격 투명성
- 재방문 의사""",
            "priority": "medium"
        },
        "differentiation": {
            "section": "differentiation",
            "title": "차별화 전략",
            "content": """### 추가 정보
✅ 디자이너별 전문 분야 명시
✅ 신규 고객 할인 정보
✅ 예약 필수 여부 명확히
✅ 주차 가능 시간대 안내

### 강조할 포인트
- 디자이너 수상 경력
- 사용 제품 브랜드 (케라스타즈 등)
- 특화 시술 (매직, 클리닉펌)
- 프리미엄 서비스 (샴푸바, 음료)

### 프로모션 예시
- 신규 고객 20% 할인
- 재방문 쿠폰 제공
- 포인트 적립 제도
- 생일 월 특별 할인""",
            "priority": "low"
        }
    },
    "학원": {
        "business_name": {
            "section": "business_name",
            "title": "업체명 최적화",
            "content": """### 원칙
✅ "○○학원" / "○○교육"
❌ 과대광고 금지 ("SKY 100%", "전원 합격" 등)

### 좋은 예
✅ "○○영어학원"
✅ "수학전문 ○○"
✅ "○○입시학원"

### 나쁜 예
❌ "SKY합격률100% ○○"
❌ "강남1등 ○○학원"
❌ "전국1위★○○"

### 검색 최적화
- 전문 과목 + 학원 조합
- 대상 학년 명시
- 특화 프로그램 강조""",
            "priority": "high"
        },
        "photo_strategy": {
            "section": "photo_strategy",
            "title": "사진 전략",
            "content": """### 필수 사진 구성
✅ 강의실 (깨끗, 밝음)
✅ 강사 프로필
✅ 교재/커리큘럼
✅ 자습실/독서실 (있다면)

### 촬영 팁
- 수업 중인 모습 (학생 얼굴 가림)
- 깨끗하고 밝은 강의실
- 최신 교재/교구
- 1:1 상담실

### 학생 사진 주의
- 학생/학부모 동의 필수
- 얼굴 모자이크 권장
- 성적표 등 개인정보 가림
- 합격 현수막 (동의 받은 것만)""",
            "priority": "high"
        },
        "keyword_strategy": {
            "section": "keyword_strategy",
            "title": "키워드 전략",
            "content": """### 핵심 키워드
1차: 전문 과목 (영어, 수학, 국어)
2차: 대상 학년 (초등, 중등, 고등)
3차: 특화 프로그램 (내신, 수능, 논술)

### 프로필 설명에 포함
- "중등 수학 전문"
- "소수정예 수업 (정원 10명)"
- "1:1 맞춤 관리"
- "자체 제작 교재"

### 리뷰 유도 포인트
- 성적 향상 (구체적 점수)
- 강사 실력 (설명, 열정)
- 관리 시스템 (출결, 과제)
- 학습 분위기""",
            "priority": "medium"
        },
        "differentiation": {
            "section": "differentiation",
            "title": "차별화 전략",
            "content": """### 추가 정보
✅ 커리큘럼 상세 설명
✅ 강사 경력 (대학, 전공, 경력)
✅ 합격률/성적 향상 사례 (과장 없이)
✅ 학부모 상담 시스템

### 강조할 포인트
- 강사 학력/경력
- 자체 개발 교재/시스템
- 소수정예/1:1 관리
- 자습실/독서실 운영

### 프로모션 예시
- 첫 수업 무료 체험
- 형제/자매 할인
- 조기 등록 할인
- 추천인 할인""",
            "priority": "low"
        }
    },
    "헬스장": {
        "business_name": {
            "section": "business_name",
            "title": "업체명 최적화",
            "content": """### 원칙
✅ "○○헬스장" / "○○피트니스"
❌ 지역명 + 키워드 나열 금지

### 좋은 예
✅ "○○헬스클럽"
✅ "피트니스 ○○"
✅ "○○짐"

### 나쁜 예
❌ "강남역 24시 헬스장"
❌ "PT전문★○○"
❌ "가성비최고 ○○헬스"

### 검색 최적화
- 브랜드명 + 헬스/피트니스 조합
- 특화 프로그램 있다면 추가
- 24시간 운영 시 명시""",
            "priority": "high"
        },
        "photo_strategy": {
            "section": "photo_strategy",
            "title": "사진 전략",
            "content": """### 필수 사진 구성
✅ 유산소 기구 구역
✅ 웨이트 트레이닝 구역
✅ GX룸/스튜디오
✅ 샤워실/락커룸
✅ PT 전용 공간

### 촬영 팁
- 청결하고 밝은 분위기
- 최신 운동 기구 강조
- 넓은 공간감 표현
- 회원 없는 시간대

### 장비 사진
- 브랜드 명시 (라이프피트니스 등)
- 다양한 기구 종류
- 유지/관리 상태 양호
- GX 프로그램 스케줄표""",
            "priority": "high"
        },
        "keyword_strategy": {
            "section": "keyword_strategy",
            "title": "키워드 전략",
            "content": """### 핵심 키워드
1차: PT 프로그램 (1:1, 그룹)
2차: 시설 (24시간, GX, 샤워실)
3차: 가격 (회원권, 이용권)

### 프로필 설명에 포함
- "24시간 무인 운영"
- "1:1 PT 프로그램"
- "GX 프로그램 30개 이상"
- "샤워실/락커 완비"

### 리뷰 유도 포인트
- PT 트레이너 실력
- 시설 청결도
- 기구 다양성
- 가성비""",
            "priority": "medium"
        },
        "differentiation": {
            "section": "differentiation",
            "title": "차별화 전략",
            "content": """### 추가 정보
✅ PT 트레이너 자격증/경력
✅ GX 프로그램 스케줄
✅ 회원권 가격 투명 공개
✅ 샤워실/락커 수 명시

### 강조할 포인트
- 24시간 무인 운영
- 프리미엄 장비 (라이프피트니스 등)
- 다양한 GX 프로그램
- 넓은 주차장

### 프로모션 예시
- 첫 달 50% 할인
- PT 10회 패키지 할인
- 친구 추천 이벤트
- 조기 등록 사은품""",
            "priority": "low"
        }
    }
}


@app.get("/api/guides")
async def get_optimization_guides(business_type: str = "공통"):
    """업종별 최적화 가이드 조회"""
    guides = BUSINESS_TYPE_GUIDES.get(business_type, BUSINESS_TYPE_GUIDES["공통"])
    return {"guides": list(guides.values()), "business_type": business_type}


# ========== 네이버 플레이스 SEO 가이드 ==========

SEO_GUIDE_DATA = {
    "ranking_factors": {
        "section": "ranking_factors",
        "title": "네이버 플레이스 순위 결정 요소",
        "priority": "high",
        "content": {
            "intro": "네이버 플레이스 검색 결과 순위는 이용자의 다양한 니즈를 고려하여 복합적으로 결정됩니다.",
            "factors": [
                {
                    "name": "유사도 (적합도·연관도)",
                    "icon": "🎯",
                    "description": "검색어와 업체 정보의 매칭 정도",
                    "details": [
                        "플레이스 업체 설명과 리뷰를 AI가 분석하여 의미 기반 매칭",
                        "관련 리뷰가 풍부할수록 다양한 검색 결과에 노출",
                        "대표 키워드(최대 5개)가 검색어와 일치도 높을수록 유리",
                        "소개글에 자연스럽게 녹인 키워드가 타깃 키워드로 작용"
                    ]
                },
                {
                    "name": "인기도",
                    "icon": "🔥",
                    "description": "카테고리 선호도 + 업체 인기도",
                    "details": [
                        "카테고리 선호도: 사용자가 검색하고 많이 찾은 카테고리 우선 노출",
                        "업체 인기도: 언급수, 이미지수, 클릭수, 저장수 등으로 결정",
                        "인기도가 높으면 거리가 멀어도 상단 노출 가능",
                        "최근 3개월 데이터 비중이 높음 (지속 관리 필수)"
                    ]
                },
                {
                    "name": "거리 (위치·거리)",
                    "icon": "📍",
                    "description": "사용자 위치와의 근접성",
                    "details": [
                        "사용자 위치에서 가까운 장소 우선 노출",
                        "지역명 검색 시 해당 지역 내 업체 우대",
                        "GPS 기반 실시간 위치 반영",
                        "반경 5km 이내 업체들 간 경쟁 치열"
                    ]
                },
                {
                    "name": "정보의 충실성",
                    "icon": "✅",
                    "description": "업체 정보의 정확도와 완성도",
                    "details": [
                        "스마트플레이스 10개 필수 항목 완성도 (업체명, 카테고리, 주소, 전화번호, 영업시간, 메뉴/가격, 사진, 소개, 편의시설, 예약/주문)",
                        "사진 20장 이상 (고해상도, 다양한 앵글)",
                        "메뉴판/가격표 최신 상태 유지",
                        "영업시간 정확도 (임시휴무, 정기휴무 즉시 반영)"
                    ]
                }
            ]
        }
    },
    "algorithm_updates": {
        "section": "algorithm_updates",
        "title": "2025년 네이버 알고리즘 변화",
        "priority": "high",
        "content": {
            "intro": "2025년 3월 네이버는 검색 알고리즘을 대대적으로 개편하며 AI 기반 평가를 강화했습니다.",
            "algorithms": [
                {
                    "name": "C-Rank (Content Rank)",
                    "icon": "📊",
                    "description": "콘텐츠의 전문성, 신뢰도, 품질 평가",
                    "components": [
                        "Content (콘텐츠): 원본성, 정보의 깊이, 최신성",
                        "Context (맥락): 주제 일관성, 사용자 의도 부합",
                        "Chain (연결): 외부 인용, 소셜 공유, 백링크 품질",
                        "체류 시간, 클릭률(CTR), 재방문율 반영"
                    ]
                },
                {
                    "name": "D.I.A. (Deep Intent Analysis)",
                    "icon": "🧠",
                    "description": "사용자 검색 의도 분석 및 행동 데이터 반영",
                    "components": [
                        "클릭률(CTR): 검색 결과에서 클릭 비율",
                        "스크롤 깊이: 페이지 내 콘텐츠 소비량",
                        "체류 시간: 플레이스 페이지 머무는 시간",
                        "댓글/공유 횟수: 사용자 참여도"
                    ]
                },
                {
                    "name": "LMM 기반 검색 (대규모 언어 모델)",
                    "icon": "🤖",
                    "description": "AI가 문맥 분석하여 신뢰도 높은 콘텐츠 우선 노출",
                    "components": [
                        "AI 자동 생성 글 탐지 및 순위 하락",
                        "광고성 도배 블로그 검색 결과 제외",
                        "의미 기반 매칭 강화 (단순 키워드 일치 넘어)",
                        "리뷰 텍스트의 진정성 평가"
                    ]
                },
                {
                    "name": "3개월 주기 순위 변동",
                    "icon": "🔄",
                    "description": "신규 가게 우대 정책 및 지속 관리 중요성",
                    "components": [
                        "신규 업체에 초기 3개월 가점 부여",
                        "기존 업체는 관리 소홀 시 순위 하락",
                        "주 1-2회 업데이트 권장 (소식, 사진, 메뉴)",
                        "장기 미관리 시 검색 노출 감소"
                    ]
                }
            ]
        }
    },
    "optimization_checklist": {
        "section": "optimization_checklist",
        "title": "실전 최적화 체크리스트",
        "priority": "high",
        "content": {
            "intro": "네이버 플레이스 상위 노출을 위한 단계별 실행 가이드입니다.",
            "categories": [
                {
                    "name": "기본 정보 완성도 100%",
                    "icon": "📝",
                    "checklist": [
                        {"item": "업체명: 공식 상호명 사용 (키워드 나열 금지)", "priority": "필수"},
                        {"item": "카테고리: 정확한 업종 분류 (최대 3개)", "priority": "필수"},
                        {"item": "대표 키워드: 5개 전략적 등록 (메뉴명, 서비스, 특징)", "priority": "필수"},
                        {"item": "소개글: 300자 이상 자세히 작성 (자연스러운 키워드 포함)", "priority": "필수"},
                        {"item": "영업시간: 정확히 입력 + 임시휴무 즉시 반영", "priority": "필수"},
                        {"item": "전화번호: 연결 가능한 번호 등록", "priority": "필수"},
                        {"item": "메뉴/가격표: 최신 상태 유지 (월 1회 점검)", "priority": "필수"},
                        {"item": "편의시설: 주차, 무선인터넷, 단체석, 포장 등 체크", "priority": "권장"},
                        {"item": "예약/주문 연동: 네이버 예약, 톡톡, 스마트콜 연결", "priority": "권장"},
                        {"item": "외부 채널: 블로그, SNS, 홈페이지 연결", "priority": "권장"}
                    ]
                },
                {
                    "name": "사진 전략 (20장 이상)",
                    "icon": "📷",
                    "checklist": [
                        {"item": "대표 메뉴/서비스: 3-5장 (클로즈업, 고해상도)", "priority": "필수"},
                        {"item": "인테리어: 5장 (입구, 홀, 좌석, 조명)", "priority": "필수"},
                        {"item": "외관: 2장 (간판, 건물 전경)", "priority": "필수"},
                        {"item": "주차장/편의시설: 2장", "priority": "권장"},
                        {"item": "분위기 사진: 3-5장 (실제 이용 장면)", "priority": "권장"},
                        {"item": "계절/시즌 사진: 월 1회 업데이트", "priority": "권장"},
                        {"item": "촬영 팁: 자연광 활용, 밝은 조명, 수평 유지", "priority": "선택"}
                    ]
                },
                {
                    "name": "리뷰 관리 루틴",
                    "icon": "⭐",
                    "checklist": [
                        {"item": "영수증 리뷰 유도: 현장 POP/QR 코드 설치", "priority": "필수"},
                        {"item": "리뷰 목표: 주 3-5개 이상 (일 1-3개 꾸준히)", "priority": "필수"},
                        {"item": "리뷰 응답: 신규 리뷰 24시간 내 답변", "priority": "필수"},
                        {"item": "부정 리뷰 대응: 정중히 응대 + 개선 의지 표현", "priority": "필수"},
                        {"item": "리뷰 평점: 4.5점 이상 유지 목표", "priority": "권장"},
                        {"item": "리뷰 길이: 50자 이상 상세한 리뷰 유도", "priority": "권장"}
                    ]
                },
                {
                    "name": "콘텐츠 업데이트",
                    "icon": "🔄",
                    "checklist": [
                        {"item": "소식 포스팅: 주 1-2회 (신메뉴, 이벤트, 소식)", "priority": "필수"},
                        {"item": "사진 업데이트: 월 1회 이상 새 사진 추가", "priority": "필수"},
                        {"item": "메뉴판 갱신: 가격/메뉴 변경 즉시 반영", "priority": "필수"},
                        {"item": "해시태그 활용: 포스팅에 관련 해시태그 3-5개", "priority": "권장"},
                        {"item": "블로그 연동: 자사 블로그 월 2회 작성 + 연결", "priority": "권장"},
                        {"item": "인스타그램/페이스북: SNS 활동 연동", "priority": "선택"}
                    ]
                },
                {
                    "name": "지속 관리",
                    "icon": "📈",
                    "checklist": [
                        {"item": "스마트플레이스 앱: 주 3회 이상 접속하여 관리", "priority": "필수"},
                        {"item": "통계 분석: 월 1회 방문자/검색어 분석", "priority": "권장"},
                        {"item": "경쟁사 모니터링: 월 1회 동일 업종 상위 업체 벤치마킹", "priority": "권장"},
                        {"item": "키워드 조정: 분기 1회 대표 키워드 재설정", "priority": "권장"},
                        {"item": "이벤트 진행: 분기 1회 리뷰 이벤트 (할인/적립)", "priority": "선택"}
                    ]
                }
            ]
        }
    },
    "industry_specific": {
        "section": "industry_specific",
        "title": "업종별 SEO 특화 전략",
        "priority": "medium",
        "content": {
            "intro": "각 업종별 특성에 맞춘 SEO 최적화 포인트입니다.",
            "industries": [
                {
                    "name": "카페",
                    "icon": "☕",
                    "keywords": ["브런치카페", "디저트카페", "루프탑카페", "북카페", "테라스카페"],
                    "photo_tips": [
                        "시그니처 메뉴 클로즈업 (라떼아트, 디저트)",
                        "좌석별 분위기 (커플석, 단체석, 창가석)",
                        "인테리어 포인트 (조명, 소품, 식물)"
                    ],
                    "keyword_strategy": "메뉴명 + 카페 (예: 아인슈페너카페, 크로플카페)",
                    "review_focus": "맛, 분위기, 주차, 콘센트 유무"
                },
                {
                    "name": "음식점",
                    "icon": "🍽️",
                    "keywords": ["맛집", "혼밥", "데이트", "회식", "가성비"],
                    "photo_tips": [
                        "대표 메뉴 3종 이상 (먹음직스러운 플레이팅)",
                        "음식 조리 과정 (주방, 그릴, 화덕)",
                        "테이블 세팅 전경"
                    ],
                    "keyword_strategy": "음식 종류 + 맛집 (예: 삼겹살맛집, 파스타맛집)",
                    "review_focus": "맛, 양, 서비스, 재방문 의사, 주차"
                },
                {
                    "name": "병원",
                    "icon": "🏥",
                    "keywords": ["진료", "치료", "전문의", "야간진료", "주말진료"],
                    "photo_tips": [
                        "대기실 (깨끗하고 밝은 분위기)",
                        "진료실/치료실 (최신 장비)",
                        "의료진 소개 (전문성 강조)"
                    ],
                    "keyword_strategy": "진료과 + 병원/의원 (예: 정형외과, 피부과)",
                    "review_focus": "의료진 친절도, 대기시간, 치료 효과, 시설",
                    "compliance": "의료법 준수 (과장 광고 금지, 치료 전후 사진 주의)"
                },
                {
                    "name": "미용실",
                    "icon": "✂️",
                    "keywords": ["헤어", "펌", "염색", "클리닉", "남성컷"],
                    "photo_tips": [
                        "스타일 포트폴리오 (비포/애프터)",
                        "인테리어 (세련된 좌석, 조명)",
                        "시술 과정 (염색, 펌 기계)"
                    ],
                    "keyword_strategy": "시술명 + 미용실 (예: 매직펌, 발라야쥬)",
                    "review_focus": "디자이너 실력, 상담, 가격, 재방문율"
                },
                {
                    "name": "학원",
                    "icon": "📚",
                    "keywords": ["입시", "내신", "수능", "과외", "1대1"],
                    "photo_tips": [
                        "강의실 (깨끗한 환경, 최신 시설)",
                        "교재/커리큘럼 (체계적 프로그램)",
                        "성적 향상 사례 (합격 현수막)"
                    ],
                    "keyword_strategy": "과목 + 학원 (예: 수학학원, 영어학원)",
                    "review_focus": "강사 실력, 성적 향상, 관리 시스템, 상담"
                },
                {
                    "name": "헬스장",
                    "icon": "💪",
                    "keywords": ["PT", "필라테스", "요가", "크로스핏", "다이어트"],
                    "photo_tips": [
                        "운동 기구 (최신 장비, 다양한 종류)",
                        "샤워실/탈의실 (청결함)",
                        "PT/그룹 수업 장면 (활기찬 분위기)"
                    ],
                    "keyword_strategy": "운동 종류 + 헬스장/센터 (예: PT헬스장, 필라테스)",
                    "review_focus": "시설, 트레이너, 가격, 운동 효과, 청결도"
                }
            ]
        }
    }
}


@app.get("/api/seo-guide")
async def get_seo_guide():
    """네이버 플레이스 SEO 가이드 조회"""
    return {
        "guide": SEO_GUIDE_DATA,
        "version": "1.0",
        "last_updated": "2025-03-01"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "engine": "UnifiedKeywordEngine V3",
        "openai": "configured" if engine.openai_api_key else "not_configured",
        "naver_local": "configured" if engine.naver_client_id else "not_configured",
        "naver_search_ad": "configured" if engine.search_ad_api.api_key else "not_configured"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main_v2:app", host="0.0.0.0", port=port, reload=True)
