#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""키워드 관련 데이터 모델"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class KeywordLevel(Enum):
    """키워드 난이도 5단계"""
    LEVEL_5_LONGTAIL = 5  # 롱테일 (가장 쉬움)
    LEVEL_4_NICHE = 4  # 니치
    LEVEL_3_MEDIUM = 3  # 중간
    LEVEL_2_COMPETITIVE = 2  # 경쟁
    LEVEL_1_TOP = 1  # 최상위 (가장 어려움)


@dataclass
class KeywordMetrics:
    """키워드 지표"""
    keyword: str
    level: int
    estimated_monthly_searches: int
    competition_score: int  # 0-100
    naver_result_count: int
    difficulty_score: int  # 0-100
    recommended_rank_target: str  # "Top 1-3", "Top 5", etc.
    estimated_timeline: str  # "1-2주", "1개월", etc.
    estimated_traffic: int  # 예상 일방문자 수
    conversion_rate: float  # 예상 전환율

    # 네이버 검색광고 API 데이터 (선택적)
    monthly_pc_searches: Optional[int] = None
    monthly_mobile_searches: Optional[int] = None
    monthly_avg_clicks: Optional[int] = None
    competition_level: Optional[str] = None  # "높음", "중간", "낮음"
    avg_cpc: Optional[int] = None  # 평균 클릭 비용


@dataclass
class KeywordSuggestion:
    """키워드 제안"""
    keyword: str
    level: int
    reason: str
    priority: int  # 1-10, 높을수록 우선순위 높음
