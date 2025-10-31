#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 플레이스 최적화 서비스 - FastAPI 백엔드 V3
전략적 키워드 분석 시스템 - 검색광고 API 통합
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
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
                cumulative_visitors=phase.cumulative_visitors
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
        count = await engine.get_naver_competition("강남역 카페")
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


# ========== 기존 가이드 API (호환성 유지) ==========

OPTIMIZATION_GUIDES = {
    "business_name": {
        "section": "business_name",
        "title": "업체명 최적화",
        "content": """
### 원칙
- 공식 상호명 사용 (사업자등록증)
- 브랜드 일관성 유지
- 검색 가능성 고려

### 금지사항
❌ 키워드 나열
❌ 과도한 특수문자
❌ 허위 정보
        """,
        "priority": "high"
    }
}


@app.get("/api/guides")
async def get_optimization_guides():
    """최적화 가이드 조회"""
    return {"guides": list(OPTIMIZATION_GUIDES.values())}


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
