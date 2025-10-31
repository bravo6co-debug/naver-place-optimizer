#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 플레이스 최적화 서비스 - FastAPI 백엔드
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os

# 기존 키워드 분석기 임포트
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from keyword_analyzer import KeywordAnalyzer

app = FastAPI(
    title="네이버 플레이스 최적화 API",
    description="업종별 키워드 분석 및 최적화 가이드 제공",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청/응답 모델
class KeywordRequest(BaseModel):
    business_type: str
    location: str


class BusinessInfo(BaseModel):
    type: str
    location: str
    city: str
    district: str


class KeywordResponse(BaseModel):
    business_info: BusinessInfo
    competition_level: str
    keywords: Dict[str, List[str]]
    recommendations: List[str]


class OptimizationGuide(BaseModel):
    section: str
    title: str
    content: str
    priority: str


# 최적화 가이드 데이터
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

### 좋은 예시
✅ "브라보치킨 해운대점"
✅ "카페 문라이트 강남"
        """,
        "priority": "high"
    },
    "category": {
        "section": "category",
        "title": "카테고리 선택",
        "content": """
### 선택 전략
1. 주업종 정확히 선택
2. 부업종 2-3개 추가
3. 경쟁사 카테고리 분석

### 업종별 가이드
- 음식점: 음식 종류 → 세부 메뉴
- 카페: 카페 → 디저트/브런치
- 서비스업: 핵심 서비스 → 추가 서비스
        """,
        "priority": "high"
    },
    "description": {
        "section": "description",
        "title": "업체 소개글 작성",
        "content": """
### 작성 공식
[첫 문장] 핵심 차별화 포인트 (20자)
[2-3문장] 주요 메뉴/서비스 (50-80자)
[마지막] 위치/접근성 정보 (30-50자)

### 작성 원칙
- 간결성: 100-200자
- 키워드 2-3개 자연스럽게 포함
- 차별화 포인트 강조
        """,
        "priority": "high"
    },
    "photos": {
        "section": "photos",
        "title": "사진 등록 전략",
        "content": """
### 필수 사진 (우선순위)
1. 대표 사진 (1장) - 고해상도
2. 메뉴/제품 (5-10장)
3. 내부 인테리어 (3-5장)
4. 외관 (2-3장)

### 품질 체크
- 밝고 선명
- 흔들림 없음
- 실제 색감
- 워터마크 제거
        """,
        "priority": "medium"
    },
    "hours": {
        "section": "hours",
        "title": "영업시간 및 정보",
        "content": """
### 정확한 정보 입력
- 요일별 영업시간
- 브레이크타임
- 정기휴무
- 임시휴무 즉시 업데이트

### 추가 정보
- 주차 가능 여부
- 예약 방법
- WiFi 제공
- 반려동물 동반
        """,
        "priority": "medium"
    },
    "menu": {
        "section": "menu",
        "title": "메뉴/가격 정보",
        "content": """
### 메뉴 등록 원칙
1. 대표메뉴 우선 (베스트 5개)
2. 정확한 가격
3. 메뉴 설명 (재료, 특징)
4. 사진 첨부 (각 메뉴당 1장)

### 업데이트
- 가격 변경 즉시 반영
- 신메뉴 추가
- 단종 메뉴 삭제
        """,
        "priority": "high"
    },
    "reviews": {
        "section": "reviews",
        "title": "리뷰 관리",
        "content": """
### 리뷰 수집 전략
✅ 서비스 품질로 자연스럽게 유도
✅ QR코드 영수증 삽입
❌ 금전적 보상 (위법)
❌ 허위 리뷰

### 리뷰 응답
- 긍정 리뷰: 24시간 내 응답
- 부정 리뷰: 12시간 내 응답
- 응답률 90% 이상 목표
        """,
        "priority": "high"
    },
    "seo": {
        "section": "seo",
        "title": "검색 최적화",
        "content": """
### 네이버 알고리즘 요소
1. 관련성: 키워드 최적화
2. 거리: 정확한 위치
3. 인기도: 리뷰 수/평점
4. 최신성: 주 1회 업데이트
5. 완성도: 프로필 100% 작성

### 주간 루틴
- 월: 공지사항 등록
- 수: 리뷰 응답
- 금: 사진/메뉴 업데이트
- 일: 통계 확인
        """,
        "priority": "medium"
    }
}


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "네이버 플레이스 최적화 API",
        "version": "1.0.0",
        "endpoints": {
            "keyword_analysis": "/api/analyze",
            "optimization_guides": "/api/guides",
            "business_types": "/api/business-types"
        }
    }


@app.post("/api/analyze", response_model=KeywordResponse)
async def analyze_keywords(request: KeywordRequest):
    """키워드 분석 API"""
    try:
        analyzer = KeywordAnalyzer(request.business_type, request.location)
        result = analyzer.analyze()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/guides")
async def get_optimization_guides():
    """최적화 가이드 조회"""
    return {"guides": list(OPTIMIZATION_GUIDES.values())}


@app.get("/api/guides/{section}")
async def get_guide_by_section(section: str):
    """특정 섹션 가이드 조회"""
    if section not in OPTIMIZATION_GUIDES:
        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다")
    return OPTIMIZATION_GUIDES[section]


@app.get("/api/business-types")
async def get_business_types():
    """지원 업종 목록"""
    return {
        "business_types": list(KeywordAnalyzer.BUSINESS_KEYWORDS.keys())
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
