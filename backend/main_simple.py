#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 플레이스 최적화 서비스 - Simplified Backend
OpenAI API만 사용한 전략적 키워드 분석 시스템
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import sys
from dotenv import load_dotenv

# 현재 디렉토리를 sys.path에 추가 (integrations 모듈 import를 위해)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integrations.openai_api import OpenAIAPI

load_dotenv()

app = FastAPI(
    title="네이버 플레이스 최적화 API Simplified",
    description="OpenAI API 기반 전략적 키워드 분석 서비스",
    version="2.0.0-simple"
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

# OpenAI API 초기화
openai_api = OpenAIAPI()


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

def estimate_keyword_metrics(keyword: str, level: int, category: str, location: str) -> Dict[str, Any]:
    """
    키워드 레벨에 따라 합리적인 메트릭 추정
    (Naver Search Ad API 없이도 동작)
    """
    # Level별 기본 메트릭 범위
    LEVEL_METRICS = {
        5: {  # 롱테일 (가장 쉬운)
            "monthly_searches": (100, 500),
            "competition": (10, 30),
            "naver_results": (1000, 10000),
            "difficulty": (10, 30),
            "rank_target": "1-3위",
            "timeline": "1-2주",
            "daily_traffic": (1, 3),
            "conversion_rate": 0.08
        },
        4: {  # 준롱테일
            "monthly_searches": (500, 2000),
            "competition": (30, 50),
            "naver_results": (10000, 50000),
            "difficulty": (30, 50),
            "rank_target": "1-5위",
            "timeline": "2-4주",
            "daily_traffic": (2, 5),
            "conversion_rate": 0.06
        },
        3: {  # 중간
            "monthly_searches": (2000, 5000),
            "competition": (50, 70),
            "naver_results": (50000, 200000),
            "difficulty": (50, 70),
            "rank_target": "1-5위",
            "timeline": "1-2개월",
            "daily_traffic": (3, 8),
            "conversion_rate": 0.05
        },
        2: {  # 경쟁 키워드
            "monthly_searches": (5000, 10000),
            "competition": (70, 85),
            "naver_results": (200000, 500000),
            "difficulty": (70, 85),
            "rank_target": "3-5위",
            "timeline": "2-3개월",
            "daily_traffic": (5, 12),
            "conversion_rate": 0.04
        },
        1: {  # 최상위
            "monthly_searches": (10000, 50000),
            "competition": (85, 95),
            "naver_results": (500000, 2000000),
            "difficulty": (85, 95),
            "rank_target": "5-10위",
            "timeline": "3-6개월",
            "daily_traffic": (8, 20),
            "conversion_rate": 0.03
        }
    }

    metrics = LEVEL_METRICS.get(level, LEVEL_METRICS[3])

    # 키워드 길이에 따라 조정 (긴 키워드 = 더 쉬움)
    keyword_length = len(keyword)
    adjustment = 1.0
    if keyword_length > 20:  # 매우 긴 롱테일
        adjustment = 0.7
    elif keyword_length > 15:
        adjustment = 0.85

    return {
        "keyword": keyword,
        "level": level,
        "level_name": _get_level_name(level),
        "estimated_monthly_searches": int(metrics["monthly_searches"][1] * adjustment),
        "competition_score": int(metrics["competition"][1] * adjustment),
        "naver_result_count": int(metrics["naver_results"][1] * adjustment),
        "difficulty_score": int(metrics["difficulty"][1] * adjustment),
        "recommended_rank_target": metrics["rank_target"],
        "estimated_timeline": metrics["timeline"],
        "estimated_daily_traffic": metrics["daily_traffic"][1],
        "conversion_rate": metrics["conversion_rate"],
        "confidence": "Estimated" if level >= 3 else "Low Confidence"
    }


def _get_level_name(level: int) -> str:
    """레벨 이름 반환"""
    names = {
        5: "롱테일 (Long-tail)",
        4: "준롱테일 (Mid-tail)",
        3: "중간 경쟁 (Medium)",
        2: "경쟁 키워드 (Competitive)",
        1: "최상위 (Top-tier)"
    }
    return names.get(level, "알 수 없음")


def generate_strategy_roadmap(
    keywords_by_level: Dict[str, List[Dict]],
    current_visitors: int,
    target_visitors: int,
    category: str,
    specialty: str
) -> List[Dict[str, Any]]:
    """전략 로드맵 생성"""

    gap = target_visitors - current_visitors

    phases = []
    cumulative_visitors = current_visitors

    # Phase 1: Level 5 (롱테일) - 1-2개월
    level_5_keywords = keywords_by_level.get("level_5", [])
    if level_5_keywords:
        phase_traffic = sum(kw.get("estimated_daily_traffic", 0) for kw in level_5_keywords[:5])
        cumulative_visitors += phase_traffic

        receipt_count = 20  # 1-2개월 목표
        phases.append({
            "phase": 1,
            "name": "🎯 롱테일 키워드 선점 (빠른 성과)",
            "duration": "1-2개월",
            "target_level": 5,
            "target_level_name": "롱테일 (Long-tail)",
            "target_keywords_count": len(level_5_keywords),
            "strategies": [
                f"✅ {len(level_5_keywords)}개 롱테일 키워드 집중 공략",
                "✅ 영수증 리뷰 20개 확보 (주 2-3개)",
                "✅ 프로필 완성도 100% 달성",
                "✅ 키워드를 자연스럽게 포함한 리뷰 작성"
            ],
            "goals": [
                f"📍 Level 5 키워드 상위 3위 달성",
                f"📈 일방문자 +{phase_traffic}명 달성 (총 {cumulative_visitors}명)",
                "⭐ 평점 4.5+ 유지"
            ],
            "expected_daily_visitors": phase_traffic,
            "priority_keywords": [kw["keyword"] for kw in level_5_keywords[:5]],
            "keyword_traffic_breakdown": {kw["keyword"]: kw.get("estimated_daily_traffic", 0) for kw in level_5_keywords[:5]},
            "difficulty_level": "쉬움",
            "cumulative_visitors": cumulative_visitors,
            "receipt_review_target": receipt_count,
            "weekly_review_target": 3,
            "consistency_importance": "⚠️ 주 2-3개 꾸준한 리뷰가 핵심입니다 (한 번에 몰아서 작성 금지)",
            "receipt_review_keywords": [kw["keyword"] for kw in level_5_keywords[:5]],
            "review_quality_standard": {
                "min_text_length": 50,
                "min_photos": 2,
                "keyword_count": 2,
                "must_include_receipt_photo": True
            },
            "review_incentive_plan": "리뷰 작성 시 다음 방문 10% 할인 쿠폰 제공",
            "keyword_mention_strategy": {
                "frequency": "리뷰당 2-3개 키워드 자연스럽게 포함",
                "placement": "리뷰 중간과 마지막에 자연스럽게 배치",
                "natural_tip": "검색어처럼 쓰지 말고, 문장 속에 녹여서 작성",
                "example": f"주말에 {specialty} 찾다가 발견했는데, 정말 만족스러웠어요!"
            },
            "info_trust_checklist": [
                "✅ 대표 사진 10장 이상 등록",
                "✅ 메뉴/가격 정확히 입력",
                "✅ 영업시간 정확히 설정",
                "✅ 편의시설 체크 완료"
            ],
            "review_templates": {
                "short": f"{specialty} 너무 좋았어요! 재방문 의사 있습니다.",
                "medium": f"주말에 {specialty} 찾다가 발견했는데, 분위기도 좋고 서비스도 친절했어요. 추천합니다!",
                "long": f"친구랑 {category} 찾다가 우연히 방문했는데, {specialty} 때문에 정말 만족스러웠어요. 다음에도 꼭 올 것 같아요. 위치도 좋고, 주차도 편했습니다!"
            }
        })

    # Phase 2: Level 4 (준롱테일) - 2-3개월
    level_4_keywords = keywords_by_level.get("level_4", [])
    if level_4_keywords:
        phase_traffic = sum(kw.get("estimated_daily_traffic", 0) for kw in level_4_keywords[:4])
        cumulative_visitors += phase_traffic

        receipt_count = 30
        phases.append({
            "phase": 2,
            "name": "📈 준롱테일 키워드 확장",
            "duration": "2-3개월",
            "target_level": 4,
            "target_level_name": "준롱테일 (Mid-tail)",
            "target_keywords_count": len(level_4_keywords),
            "strategies": [
                f"✅ {len(level_4_keywords)}개 준롱테일 키워드 공략",
                "✅ 영수증 리뷰 30개 추가 확보 (주 2-3개)",
                "✅ 기존 Level 5 키워드 순위 유지",
                "✅ 사진 업데이트 (월 5장)"
            ],
            "goals": [
                f"📍 Level 4 키워드 상위 5위 달성",
                f"📈 일방문자 +{phase_traffic}명 달성 (총 {cumulative_visitors}명)",
                "⭐ 리뷰 수 50개 돌파"
            ],
            "expected_daily_visitors": phase_traffic,
            "priority_keywords": [kw["keyword"] for kw in level_4_keywords[:4]],
            "keyword_traffic_breakdown": {kw["keyword"]: kw.get("estimated_daily_traffic", 0) for kw in level_4_keywords[:4]},
            "difficulty_level": "보통",
            "cumulative_visitors": cumulative_visitors,
            "receipt_review_target": receipt_count,
            "weekly_review_target": 3,
            "consistency_importance": "⚠️ 주 2-3개 꾸준한 리뷰가 핵심입니다",
            "receipt_review_keywords": [kw["keyword"] for kw in level_4_keywords[:4]],
            "review_quality_standard": {
                "min_text_length": 70,
                "min_photos": 3,
                "keyword_count": 2,
                "must_include_receipt_photo": True
            },
            "review_incentive_plan": "리뷰 작성 시 음료 1잔 무료 제공",
            "keyword_mention_strategy": {
                "frequency": "리뷰당 2-3개 키워드 자연스럽게 포함",
                "placement": "리뷰 시작과 중간에 자연스럽게 배치",
                "natural_tip": "검색어처럼 쓰지 말고, 경험을 설명하며 키워드 포함",
                "example": f"이 지역에서 {specialty} 하는 곳 찾기 힘든데, 여기는 정말 좋았어요!"
            },
            "info_trust_checklist": [
                "✅ 신규 메뉴 추가",
                "✅ 시즌 사진 업데이트",
                "✅ 리뷰 응답률 90% 유지"
            ],
            "review_templates": {
                "short": f"{specialty} 최고! 재방문 예정입니다.",
                "medium": f"{category} 찾다가 발견했는데, {specialty} 덕분에 정말 만족했어요. 재방문 의사 100%!",
                "long": f"주말에 가족과 방문했는데, {specialty} 정말 좋았어요. {category}도 훌륭하고, 직원분들도 친절하셨습니다. 다음엔 친구들과도 올 계획이에요!"
            }
        })

    # Phase 3: Level 3 (중간 경쟁) - 3-4개월
    level_3_keywords = keywords_by_level.get("level_3", [])
    if level_3_keywords:
        phase_traffic = sum(kw.get("estimated_daily_traffic", 0) for kw in level_3_keywords[:3])
        cumulative_visitors += phase_traffic

        receipt_count = 40
        phases.append({
            "phase": 3,
            "name": "🔥 중간 경쟁 키워드 진출",
            "duration": "3-4개월",
            "target_level": 3,
            "target_level_name": "중간 경쟁 (Medium)",
            "target_keywords_count": len(level_3_keywords),
            "strategies": [
                f"✅ {len(level_3_keywords)}개 중간 경쟁 키워드 공략",
                "✅ 영수증 리뷰 40개 추가 확보 (주 2-3개)",
                "✅ 블로그 리뷰 10개 유도",
                "✅ 인스타그램 태그 노출 확대"
            ],
            "goals": [
                f"📍 Level 3 키워드 상위 5위 달성",
                f"📈 일방문자 +{phase_traffic}명 달성 (총 {cumulative_visitors}명)",
                "⭐ 리뷰 수 100개 돌파"
            ],
            "expected_daily_visitors": phase_traffic,
            "priority_keywords": [kw["keyword"] for kw in level_3_keywords[:3]],
            "keyword_traffic_breakdown": {kw["keyword"]: kw.get("estimated_daily_traffic", 0) for kw in level_3_keywords[:3]},
            "difficulty_level": "보통",
            "cumulative_visitors": cumulative_visitors,
            "receipt_review_target": receipt_count,
            "weekly_review_target": 3,
            "consistency_importance": "⚠️ 주 2-3개 꾸준한 리뷰가 핵심입니다",
            "receipt_review_keywords": [kw["keyword"] for kw in level_3_keywords[:3]],
            "review_quality_standard": {
                "min_text_length": 100,
                "min_photos": 3,
                "keyword_count": 3,
                "must_include_receipt_photo": True
            },
            "review_incentive_plan": "리뷰 작성 시 포인트 적립 (10% 할인)",
            "keyword_mention_strategy": {
                "frequency": "리뷰당 3개 키워드 자연스럽게 포함",
                "placement": "리뷰 전체에 골고루 분산",
                "natural_tip": "스토리텔링 방식으로 경험을 공유하며 키워드 포함",
                "example": f"{category} 찾다가 발견한 곳인데, {specialty} 덕분에 정말 만족했어요!"
            },
            "info_trust_checklist": [
                "✅ 메뉴 업데이트",
                "✅ 고객 문의 24시간 내 응답",
                "✅ SNS 활동 강화"
            ],
            "review_templates": {
                "short": f"{specialty} 정말 좋았어요!",
                "medium": f"{category} 중에서 {specialty} 하는 곳은 여기가 최고인 것 같아요. 재방문 의사 있습니다!",
                "long": f"친구 추천으로 방문했는데, {specialty} 정말 훌륭했어요. {category}도 기대 이상이고, 분위기도 아늑해서 데이트나 모임 장소로 완벽합니다. 적극 추천해요!"
            }
        })

    # Phase 4: Level 2+1 (경쟁 + 최상위) - 4-6개월
    level_2_keywords = keywords_by_level.get("level_2", [])
    level_1_keywords = keywords_by_level.get("level_1", [])

    if level_2_keywords or level_1_keywords:
        phase_traffic = sum(kw.get("estimated_daily_traffic", 0) for kw in level_2_keywords[:2]) + \
                       sum(kw.get("estimated_daily_traffic", 0) for kw in level_1_keywords[:1])
        cumulative_visitors += phase_traffic

        receipt_count = 50
        all_keywords = level_2_keywords + level_1_keywords
        phases.append({
            "phase": 4,
            "name": "👑 최상위 키워드 진입",
            "duration": "4-6개월",
            "target_level": 2,
            "target_level_name": "경쟁 + 최상위",
            "target_keywords_count": len(level_2_keywords) + len(level_1_keywords),
            "strategies": [
                f"✅ Level 2 키워드 {len(level_2_keywords)}개 + Level 1 키워드 {len(level_1_keywords)}개 공략",
                "✅ 영수증 리뷰 50개 추가 확보 (주 3개)",
                "✅ 블로그 리뷰 20개 유도",
                "✅ 인플루언서 협업 검토"
            ],
            "goals": [
                f"📍 Level 2 키워드 5-10위 달성",
                f"📍 Level 1 키워드 10위권 진입",
                f"📈 목표 일방문자 {target_visitors}명 달성!",
                "⭐ 리뷰 수 150개 돌파"
            ],
            "expected_daily_visitors": phase_traffic,
            "priority_keywords": [kw["keyword"] for kw in (level_2_keywords[:2] + level_1_keywords[:1])],
            "keyword_traffic_breakdown": {kw["keyword"]: kw.get("estimated_daily_traffic", 0)
                                         for kw in (level_2_keywords[:2] + level_1_keywords[:1])},
            "difficulty_level": "어려움",
            "cumulative_visitors": cumulative_visitors,
            "receipt_review_target": receipt_count,
            "weekly_review_target": 3,
            "consistency_importance": "⚠️ 주 3개 이상 꾸준한 리뷰가 핵심입니다 (장기전 필수)",
            "receipt_review_keywords": [kw["keyword"] for kw in all_keywords[:5]],
            "review_quality_standard": {
                "min_text_length": 150,
                "min_photos": 4,
                "keyword_count": 3,
                "must_include_receipt_photo": True
            },
            "review_incentive_plan": "리뷰 작성 시 VIP 멤버십 제공",
            "keyword_mention_strategy": {
                "frequency": "리뷰당 3-4개 키워드 자연스럽게 포함",
                "placement": "리뷰 전체에 자연스럽게 분산 (스토리텔링)",
                "natural_tip": "개인 경험을 상세히 공유하며 키워드를 자연스럽게 녹여내기",
                "example": f"이 지역에서 {specialty} 찾기 정말 힘든데, 여기는 기대 이상이었어요!"
            },
            "info_trust_checklist": [
                "✅ 월간 이벤트 진행",
                "✅ 단골 고객 혜택 제공",
                "✅ SNS 광고 집행",
                "✅ 언론 보도 자료 배포"
            ],
            "review_templates": {
                "short": f"{specialty} 최고의 선택!",
                "medium": f"{category} 중 최고라고 자신 있게 말할 수 있어요. {specialty} 정말 만족스럽고, 직원분들도 친절했습니다!",
                "long": f"몇 군데 다녀본 중에 여기가 최고예요. {specialty} 정말 훌륭하고, {category}도 기대 이상입니다. 분위기, 서비스, 품질 모두 완벽해서 가족 모임 장소로도 강력 추천합니다!"
            }
        })

    return phases


# ========== API 엔드포인트 ==========

@app.post("/api/v2/analyze")
async def analyze_strategic(request: StrategicAnalysisRequest):
    """전략적 키워드 분석 (OpenAI API Only)"""

    try:
        # 1. OpenAI로 고품질 키워드 생성 (이미 GPT-4o + enhanced prompt로 업그레이드됨)
        keywords = openai_api.generate_keywords(
            category=request.business_type,
            location=request.location,
            specialty=request.specialty
        )

        if not keywords:
            raise HTTPException(status_code=500, detail="키워드 생성에 실패했습니다")

        # 2. 키워드별 메트릭 추정 (API 없이도 합리적인 추정)
        keywords_by_level = {
            "level_5": [],
            "level_4": [],
            "level_3": [],
            "level_2": [],
            "level_1": []
        }

        for kw in keywords:
            level = kw.get("level", 3)
            metrics = estimate_keyword_metrics(
                keyword=kw["keyword"],
                level=level,
                category=request.business_type,
                location=request.location
            )
            keywords_by_level[f"level_{level}"].append(metrics)

        # 3. 전략 로드맵 생성
        roadmap = generate_strategy_roadmap(
            keywords_by_level=keywords_by_level,
            current_visitors=request.current_daily_visitors or 0,
            target_visitors=request.target_daily_visitors or 100,
            category=request.business_type,
            specialty=request.specialty or ""
        )

        # 4. 응답 구성
        total_keywords = len(keywords)
        gap = (request.target_daily_visitors or 100) - (request.current_daily_visitors or 0)
        total_expected_traffic = sum(phase["expected_daily_visitors"] for phase in roadmap)
        achievement_rate = min(100, (total_expected_traffic / gap * 100) if gap > 0 else 100)

        response = {
            "business_info": {
                "type": request.business_type,
                "location": request.location,
                "specialty": request.specialty or ""
            },
            "total_keywords": total_keywords,
            "keywords_by_level": keywords_by_level,
            "strategy_roadmap": roadmap,
            "summary": {
                "current_daily_visitors": request.current_daily_visitors or 0,
                "target_daily_visitors": request.target_daily_visitors or 100,
                "gap": gap,
                "total_expected_traffic": total_expected_traffic,
                "achievement_rate": round(achievement_rate, 1),
                "total_phases": len(roadmap),
                "recommended_timeline": f"{len(roadmap) * 2}-{len(roadmap) * 3}개월",
                "data_sources": [
                    "GPT-4o (OpenAI) - 고품질 키워드 생성",
                    "통계 기반 메트릭 추정 (Level별 평균값)",
                    "전략적 로드맵 자동 생성"
                ]
            }
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@app.get("/api/guides")
async def get_optimization_guides(business_type: str = "공통"):
    """업종별 최적화 가이드 조회"""

    # 간단한 가이드 데이터 (실제로는 더 많은 내용 포함 가능)
    guides = {
        "receipt_review": {
            "section": "receipt_review",
            "title": "영수증 리뷰 전략",
            "content": """### 최우선 전략
✅ 네이버 알고리즘 최우선 반영 (2025년 하반기 이후)
✅ 주 2-3개 영수증 리뷰 확보 목표
✅ 키워드를 자연스럽게 포함한 리뷰 작성

### 실행 방법
1. 현장 POP/QR 코드로 리뷰 유도
2. 리뷰 작성 시 할인/적립 혜택 제공
3. 꾸준한 리뷰 확보가 핵심 (한 번에 몰아서 작성 금지)
4. 리뷰 품질 관리 (텍스트 50자 이상, 사진 2장 이상)

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
✅ 편의시설 체크
✅ 전화번호 & 예약 링크

### 사진 전략
- 대표 메뉴/서비스 3장 이상
- 인테리어/외관 3장 이상
- 주차장/편의시설 2장 이상
- 조명 밝게, 고해상도 필수

### 업데이트 주기
- 월 1회 이상 사진 업데이트
- 시즌 메뉴/이벤트 즉시 반영""",
            "priority": "high"
        },
        "keyword_optimization": {
            "section": "keyword_optimization",
            "title": "키워드 최적화",
            "content": """### 키워드 선정 전략
✅ 롱테일 키워드부터 공략 (빠른 성과)
✅ 자연스러운 검색어 패턴 사용
✅ 지역명 + 특징 + 업종 조합

### 키워드 삽입 방법
- 업체 소개글에 자연스럽게 포함
- 리뷰에 2-3개 키워드 자연스럽게 삽입
- 대표 키워드 5개 설정 (네이버 플레이스 관리)

### 주의사항
❌ 키워드 도배 금지
❌ 부자연스러운 키워드 나열 금지""",
            "priority": "medium"
        }
    }

    return {
        "guides": list(guides.values()),
        "business_type": business_type
    }


@app.get("/api/seo-guide")
async def get_seo_guide():
    """네이버 플레이스 SEO 가이드 조회"""

    seo_guide = {
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
                            "GPS 기반 실시간 위치 반영"
                        ]
                    },
                    {
                        "name": "정보의 충실성",
                        "icon": "✅",
                        "description": "업체 정보의 정확도와 완성도",
                        "details": [
                            "스마트플레이스 필수 항목 완성도",
                            "사진 10장 이상 (고해상도, 다양한 앵글)",
                            "메뉴판/가격표 최신 상태 유지",
                            "영업시간 정확도"
                        ]
                    }
                ]
            }
        },
        "best_practices": {
            "section": "best_practices",
            "title": "최적화 모범 사례",
            "priority": "high",
            "content": {
                "intro": "실제로 효과가 검증된 최적화 방법들을 소개합니다.",
                "practices": [
                    {
                        "name": "영수증 리뷰 전략",
                        "description": "주 2-3개 꾸준한 영수증 리뷰 확보",
                        "benefits": ["빠른 순위 상승", "신뢰도 향상", "AI 알고리즘 우대"]
                    },
                    {
                        "name": "롱테일 키워드 우선 공략",
                        "description": "경쟁이 낮은 구체적 키워드부터 시작",
                        "benefits": ["빠른 성과", "낮은 비용", "점진적 확장"]
                    },
                    {
                        "name": "프로필 완성도 100%",
                        "description": "모든 항목을 정확하고 상세하게 작성",
                        "benefits": ["정보 신뢰도 상승", "노출 빈도 증가", "전환율 향상"]
                    }
                ]
            }
        }
    }

    return {
        "guide": seo_guide,
        "version": "2.0",
        "last_updated": "2025-11-11"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))

    return {
        "status": "healthy",
        "version": "2.0.0-simple",
        "engine": "OpenAI API Only (Simplified)",
        "openai": "configured" if openai_configured else "not_configured",
        "features": [
            "✅ GPT-4o 고품질 키워드 생성",
            "✅ 통계 기반 메트릭 추정",
            "✅ 전략적 로드맵 자동 생성",
            "❌ Naver Search Ad API (제거됨)",
            "❌ 인구통계 API (제거됨)",
            "❌ 복잡한 경쟁도 분석 (제거됨)"
        ]
    }


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "네이버 플레이스 최적화 서비스 (Simplified)",
        "version": "2.0.0-simple",
        "description": "OpenAI API만 사용한 전략적 키워드 분석",
        "endpoints": {
            "strategic_analysis": "POST /api/v2/analyze",
            "optimization_guides": "GET /api/guides",
            "seo_guide": "GET /api/seo-guide",
            "health": "GET /health"
        },
        "improvements": [
            "✅ GPT-4o (gpt-4o-mini → gpt-4o)",
            "✅ 강화된 프롬프트 (290줄, 좋은/나쁜 예시 추가)",
            "✅ 나쁜 키워드 필터링 (_filter_bad_keywords)",
            "✅ 단순화된 백엔드 (복잡한 API 제거)",
            "✅ 합리적인 메트릭 추정 (API 비용 절감)"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting Simplified Backend on port {port}")
    print("✅ Using OpenAI API Only (GPT-4o)")
    print("❌ Removed: Naver Search Ad API, Population API, Complex Services")
    uvicorn.run("main_simple:app", host="0.0.0.0", port=port, reload=True)
