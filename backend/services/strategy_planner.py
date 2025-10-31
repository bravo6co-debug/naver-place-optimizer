#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""전략 수립 서비스"""

from typing import List, Dict, Optional
from models.strategy import StrategyPhase
from models.keyword import KeywordMetrics
from config.category_loader import CategoryLoader
import json
import os


class StrategyPlannerService:
    """전략 수립 서비스"""

    def __init__(self):
        self.category_loader = CategoryLoader()
        self._load_generic_strategies()

    def _load_generic_strategies(self):
        """범용 전략 템플릿 로드"""
        generic_path = os.path.join(
            os.path.dirname(__file__),
            "../config/categories/_generic_strategies.json"
        )
        try:
            with open(generic_path, 'r', encoding='utf-8') as f:
                self.generic_strategies = json.load(f)
        except:
            self.generic_strategies = {
                "strategies": {},
                "goals": {}
            }

    def generate_roadmap(
        self,
        current_daily_visitors: int,
        target_daily_visitors: int,
        category: str,
        analyzed_keywords: Optional[List[KeywordMetrics]] = None
    ) -> List[StrategyPhase]:
        """
        목표 기반 전략 로드맵 생성 (V4: 동적 생성)

        Args:
            current_daily_visitors: 현재 일방문자
            target_daily_visitors: 목표 일방문자
            category: 업종
            analyzed_keywords: 분석된 키워드 리스트 (V4 신규)

        Returns:
            전략 단계 리스트
        """
        gap = target_daily_visitors - current_daily_visitors

        # 키워드 분석 데이터가 있으면 동적 생성, 없으면 레거시 방식
        if analyzed_keywords:
            return self._generate_dynamic_roadmap(gap, category, analyzed_keywords)
        else:
            return self._generate_legacy_roadmap(gap, category)

    def _generate_dynamic_roadmap(
        self,
        gap: int,
        category: str,
        analyzed_keywords: List[KeywordMetrics]
    ) -> List[StrategyPhase]:
        """
        실제 키워드 분석 결과 기반 동적 로드맵 생성

        Args:
            gap: 목표 트래픽 갭
            category: 업종
            analyzed_keywords: 분석된 키워드들

        Returns:
            동적 생성된 전략 단계 리스트
        """
        # 레벨별로 키워드 그룹화
        keywords_by_level = {1: [], 2: [], 3: [], 4: [], 5: []}
        for kw in analyzed_keywords:
            keywords_by_level[kw.level].append(kw)

        # 업종별 전략/목표 로드
        cat_data = self.category_loader.get_category(category)
        strategies_template = cat_data.get("strategies", {}) if cat_data else {}
        goals_template = cat_data.get("goals", {}) if cat_data else {}

        # 없으면 범용 템플릿 사용
        if not strategies_template:
            strategies_template = self.generic_strategies.get("strategies", {})
            goals_template = self.generic_strategies.get("goals", {})

        phases = []
        cumulative_traffic = 0
        phase_num = 1

        # 레벨 5부터 1까지 역순으로 Phase 생성 (롱테일 → 최상위)
        level_config = {
            5: {"name": "롱테일 킬러", "duration": "1-2주"},
            4: {"name": "니치 공략", "duration": "3-8주"},
            3: {"name": "중위권 진입", "duration": "3-6개월"},
            2: {"name": "상위권 도전", "duration": "6개월 이상"},
            1: {"name": "최상위 도전", "duration": "12개월 이상"}
        }

        for level in [5, 4, 3, 2, 1]:
            level_keywords = keywords_by_level[level]
            if not level_keywords:
                continue  # 해당 레벨 키워드 없으면 건너뛰기

            # 실제 트래픽 계산
            level_traffic = sum(kw.estimated_traffic for kw in level_keywords)
            cumulative_traffic += level_traffic

            # 우선순위 키워드 선정 (난이도 대비 효과 높은 순)
            priority_kws = self._select_priority_keywords(level_keywords, top_n=5)

            # 키워드별 트래픽 분해
            traffic_breakdown = {
                kw.keyword: kw.estimated_traffic
                for kw in sorted(level_keywords, key=lambda k: k.estimated_traffic, reverse=True)[:5]
            }

            # 난이도 계산
            avg_difficulty = sum(kw.difficulty_score for kw in level_keywords) / len(level_keywords)
            difficulty_level = self._get_difficulty_level(avg_difficulty)

            # 전략/목표 가져오기
            level_key = f"level_{level}"
            strategies = strategies_template.get(level_key, [
                f"Level {level} 키워드 최적화",
                "검색 노출 향상 전략",
                "리뷰 및 평점 관리",
                "지속적인 콘텐츠 업데이트"
            ])
            goals = goals_template.get(level_key, [
                f"Level {level} 키워드 상위 노출",
                "고객 만족도 향상",
                "지속적 트래픽 증가"
            ])

            phase = StrategyPhase(
                phase=phase_num,
                name=level_config[level]["name"],
                duration=level_config[level]["duration"],
                target_level=level,
                target_keywords_count=len(level_keywords),
                strategies=strategies,
                goals=goals,
                expected_daily_visitors=level_traffic,
                priority_keywords=[kw.keyword for kw in priority_kws],
                keyword_traffic_breakdown=traffic_breakdown,
                difficulty_level=difficulty_level,
                cumulative_visitors=cumulative_traffic
            )
            phases.append(phase)
            phase_num += 1

        return phases

    def _generate_legacy_roadmap(self, gap: int, category: str) -> List[StrategyPhase]:
        """
        레거시 방식: 고정 비율 기반 로드맵
        (하위 호환성 유지용)
        """
        phases = []

        # Phase 1: 롱테일 킬러 (1-2주)
        phases.append(StrategyPhase(
            phase=1,
            name="롱테일 킬러",
            duration="1-2주",
            target_level=5,
            target_keywords_count=15,
            strategies=[
                "소개글에 롱테일 키워드 자연스럽게 삽입",
                "메뉴명에 검색 키워드 활용",
                "사진 설명(alt)에 키워드 포함",
                "초기 리뷰 10개 확보"
            ],
            goals=[
                "각 키워드 Top 3 달성",
                "프로필 완성도 100%",
                "기본 트래픽 확보"
            ],
            expected_daily_visitors=int(gap * 0.15)
        ))

        # Phase 2: 니치 공략 (3-8주)
        phases.append(StrategyPhase(
            phase=2,
            name="니치 공략",
            duration="3-8주",
            target_level=4,
            target_keywords_count=10,
            strategies=[
                "블로그/SNS 연계 포스팅",
                "특화 메뉴 개발 및 홍보",
                "이벤트/프로모션 진행",
                "리뷰 50개 돌파"
            ],
            goals=[
                "각 키워드 Top 5 진입",
                "평점 4.5+ 유지",
                "재방문율 향상"
            ],
            expected_daily_visitors=int(gap * 0.35)
        ))

        # Phase 3: 중위권 진입 (3-6개월)
        phases.append(StrategyPhase(
            phase=3,
            name="중위권 진입",
            duration="3-6개월",
            target_level=3,
            target_keywords_count=5,
            strategies=[
                "리뷰 100개 이상 확보",
                "정기 업데이트 (주 2회)",
                "지역 커뮤니티 활동",
                "입소문 마케팅 강화"
            ],
            goals=[
                "각 키워드 Top 10 안착",
                "월간 방문자 1000+",
                "단골 고객 확보"
            ],
            expected_daily_visitors=int(gap * 0.70)
        ))

        # Phase 4: 상위권 도전 (6개월+)
        phases.append(StrategyPhase(
            phase=4,
            name="상위권 도전",
            duration="6개월 이상",
            target_level=2,
            target_keywords_count=3,
            strategies=[
                "브랜드 인지도 강화",
                "프리미엄 서비스 차별화",
                "미디어 노출 (기사, 방송)",
                "충성 고객 커뮤니티 운영"
            ],
            goals=[
                "지역 대표 업체로 인식",
                "리뷰 500개 이상",
                "매출 안정화"
            ],
            expected_daily_visitors=gap
        ))

        return phases

    def _select_priority_keywords(
        self,
        keywords: List[KeywordMetrics],
        top_n: int = 5
    ) -> List[KeywordMetrics]:
        """
        우선순위 키워드 선정 (ROI 기반)

        Args:
            keywords: 키워드 리스트
            top_n: 선정할 개수

        Returns:
            우선순위 키워드 리스트
        """
        # ROI = 예상 트래픽 / max(난이도, 1)
        scored_keywords = []
        for kw in keywords:
            roi = kw.estimated_traffic / max(kw.difficulty_score, 1)
            scored_keywords.append((kw, roi))

        # ROI 높은 순으로 정렬
        scored_keywords.sort(key=lambda x: x[1], reverse=True)

        return [kw for kw, _ in scored_keywords[:top_n]]

    def _get_difficulty_level(self, avg_difficulty: float) -> str:
        """난이도 점수 → 레벨 변환"""
        if avg_difficulty < 30:
            return "쉬움"
        elif avg_difficulty < 60:
            return "보통"
        else:
            return "어려움"

    def get_rank_target(self, level: int) -> tuple[str, str, float]:
        """
        레벨별 목표 순위 및 타임라인

        Returns:
            (목표 순위, 예상 기간, 트래픽 전환율)
        """
        targets = {
            5: ("Top 1-3", "1-2주", 0.25),
            4: ("Top 5", "1개월", 0.15),
            3: ("Top 10", "2-3개월", 0.10),
            2: ("Top 20", "6개월", 0.05),
            1: ("노출 목표", "장기", 0.02)
        }

        return targets.get(level, ("Top 10", "2개월", 0.10))
