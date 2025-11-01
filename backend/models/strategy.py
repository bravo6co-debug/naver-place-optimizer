#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""전략 관련 데이터 모델
Updated: 2025-11-01 - Force cache clear for V5 fields
"""

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

    # V5 Simplified 필드 - 영수증 리뷰 집중 전략
    receipt_review_target: int = 0  # 목표 개수
    weekly_review_target: int = 0  # 주간 목표 (최신성 강조)
    consistency_importance: str = ""  # 꾸준함 강조 메시지

    receipt_review_keywords: List[str] = field(default_factory=list)  # 삽입할 키워드
    review_quality_standard: Dict[str, any] = field(default_factory=dict)  # 품질 기준
    review_incentive_plan: str = ""  # 인센티브

    keyword_mention_strategy: Dict[str, str] = field(default_factory=dict)  # 키워드 언급 방법
    info_trust_checklist: List[str] = field(default_factory=list)  # 정보 신뢰도 체크리스트

    review_templates: Dict[str, str] = field(default_factory=dict)  # 키워드 삽입 템플릿
