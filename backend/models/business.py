#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""비즈니스 관련 데이터 모델"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BusinessInfo:
    """비즈니스 정보"""
    category: str  # 업종
    location: str  # 지역
    specialty: Optional[str] = None  # 특징/전문분야
    current_daily_visitors: Optional[int] = None  # 현재 일방문자
    target_daily_visitors: Optional[int] = None  # 목표 일방문자


@dataclass
class CategoryData:
    """업종 데이터"""
    name: str
    usage_rate: float  # 이용률
    search_rate: float  # 검색률
    conversion_rate: float  # 전환율
    base_keywords: list[str]  # 기본 키워드
    modifiers: dict[str, list[str]]  # 수식어
    longtail_patterns: list[str]  # 롱테일 패턴
