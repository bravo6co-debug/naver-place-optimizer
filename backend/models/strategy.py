#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""전략 관련 데이터 모델"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class StrategyPhase:
    """전략 단계"""
    phase: int
    name: str
    duration: str
    target_level: int
    target_keywords_count: int
    strategies: List[str]
    goals: List[str]
    expected_daily_visitors: int

    # V4 추가 필드 (동적 로드맵)
    priority_keywords: List[str] = field(default_factory=list)  # 우선 공략 키워드
    keyword_traffic_breakdown: Dict[str, int] = field(default_factory=dict)  # 키워드별 예상 유입
    difficulty_level: str = "보통"  # "쉬움", "보통", "어려움"
    cumulative_visitors: int = 0  # 누적 방문자 수
