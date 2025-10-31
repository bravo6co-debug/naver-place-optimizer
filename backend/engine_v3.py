#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 키워드 분석 엔진 V3
- 새로운 모듈 구조 사용
- 네이버 검색광고 API 우선 사용
- 다단계 폴백 시스템
- 레거시 호환성 유지
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# 새로운 모듈 임포트
from models.keyword import KeywordMetrics as KeywordMetricsModel
from models.strategy import StrategyPhase as StrategyPhaseModel
from services.keyword_generator import KeywordGeneratorService
from services.search_volume_estimator import SearchVolumeEstimatorService
from services.competition_analyzer import CompetitionAnalyzerService
from services.strategy_planner import StrategyPlannerService
from integrations.naver_search_ad_api import NaverSearchAdAPI
from integrations.naver_local_api import NaverLocalAPI
from integrations.openai_api import OpenAIAPI
from config.category_loader import CategoryLoader

load_dotenv()


# 레거시 호환성을 위한 클래스 (strategic_keyword_engine.py와 동일)
class KeywordLevel(Enum):
    """키워드 난이도 5단계"""
    LEVEL_5_LONGTAIL = 5
    LEVEL_4_NICHE = 4
    LEVEL_3_MEDIUM = 3
    LEVEL_2_COMPETITIVE = 2
    LEVEL_1_TOP = 1


@dataclass
class KeywordMetrics:
    """키워드 지표 (레거시 호환)"""
    keyword: str
    level: int
    estimated_monthly_searches: int
    competition_score: int
    naver_result_count: int
    difficulty_score: int
    recommended_rank_target: str
    estimated_timeline: str
    estimated_traffic: int
    conversion_rate: float
    # V3 추가 필드
    data_source: str = "estimated"  # "api", "naver_local", "estimated"
    monthly_pc_searches: Optional[int] = None
    monthly_mobile_searches: Optional[int] = None


@dataclass
class StrategyPhase:
    """전략 단계 (레거시 호환)"""
    phase: int
    name: str
    duration: str
    target_level: int
    target_keywords_count: int
    strategies: List[str]
    goals: List[str]
    expected_daily_visitors: int


class UnifiedKeywordEngine:
    """통합 키워드 분석 엔진"""

    def __init__(self):
        """초기화 - 모든 서비스 인스턴스 생성"""
        # API 클라이언트
        self.search_ad_api = NaverSearchAdAPI()
        self.local_api = NaverLocalAPI()
        self.openai_api = OpenAIAPI()

        # 서비스
        self.keyword_generator = KeywordGeneratorService(self.openai_api)
        self.volume_estimator = SearchVolumeEstimatorService(self.search_ad_api)
        self.competition_analyzer = CompetitionAnalyzerService(self.local_api, self.search_ad_api)
        self.strategy_planner = StrategyPlannerService()

        # 설정 로더
        self.category_loader = CategoryLoader()

        # 레거시 호환성을 위한 속성
        self.openai_client = self.openai_api.client
        self.openai_api_key = self.openai_api.api_key
        self.naver_client_id = self.local_api.client_id
        self.naver_client_secret = self.local_api.client_secret

    async def generate_keywords_with_gpt(
        self,
        category: str,
        location: str,
        specialty: Optional[str] = None
    ) -> List[Dict]:
        """
        GPT로 키워드 생성 (레거시 호환 메서드)

        Args:
            category: 업종
            location: 지역
            specialty: 특징/전문분야

        Returns:
            [{"keyword": "...", "level": 5, "reason": "..."}]
        """
        return await self.keyword_generator.generate_keywords(
            category=category,
            location=location,
            specialty=specialty
        )

    async def analyze_keyword(
        self,
        keyword: str,
        level: int,
        location: str,
        category: str
    ) -> KeywordMetrics:
        """
        개별 키워드 분석 (레거시 호환 메서드)

        Args:
            keyword: 키워드
            level: 레벨 (1-5)
            location: 지역
            category: 업종

        Returns:
            KeywordMetrics 객체
        """
        # 1. 검색량 추정 (다단계 폴백)
        volume_data = await self.volume_estimator.estimate_monthly_searches(
            keyword=keyword,
            category=category,
            location=location
        )

        # 레벨별 검색량 조정
        base_searches = volume_data["total"]
        estimated_searches = self.volume_estimator.apply_level_multiplier(base_searches, level)

        # 2. 경쟁도 분석
        competition_data = await self.competition_analyzer.analyze_competition(keyword)

        # 3. 난이도 점수 계산
        difficulty_score = self.competition_analyzer.calculate_difficulty_score(
            competition_score=competition_data["competition_score"],
            level=level,
            search_volume=estimated_searches
        )

        # 4. 목표 및 타임라인
        rank_target, timeline, traffic_rate = self.strategy_planner.get_rank_target(level)

        # 5. 예상 트래픽
        cat_data = self.category_loader.get_category(category)
        conversion_rate = cat_data.get("conversion_rate", 0.08) if cat_data else 0.08
        conversion = conversion_rate * traffic_rate
        estimated_daily_traffic = int((estimated_searches / 30) * conversion)

        # KeywordMetrics 생성
        return KeywordMetrics(
            keyword=keyword,
            level=level,
            estimated_monthly_searches=estimated_searches,
            competition_score=competition_data["competition_score"],
            naver_result_count=competition_data["result_count"],
            difficulty_score=difficulty_score,
            recommended_rank_target=rank_target,
            estimated_timeline=timeline,
            estimated_traffic=estimated_daily_traffic,
            conversion_rate=conversion,
            # V3 추가 정보
            data_source=volume_data["source"],
            monthly_pc_searches=volume_data.get("pc"),
            monthly_mobile_searches=volume_data.get("mobile")
        )

    async def get_naver_competition(self, keyword: str) -> int:
        """
        네이버 경쟁도 조회 (레거시 호환 메서드)

        Args:
            keyword: 키워드

        Returns:
            검색 결과 수
        """
        return await self.local_api.get_competition_count(keyword)

    def generate_strategy_roadmap(
        self,
        current_daily_visitors: int,
        target_daily_visitors: int,
        category: str
    ) -> List[StrategyPhase]:
        """
        전략 로드맵 생성 (레거시 호환 메서드)

        Args:
            current_daily_visitors: 현재 일방문자
            target_daily_visitors: 목표 일방문자
            category: 업종

        Returns:
            StrategyPhase 리스트
        """
        phases = self.strategy_planner.generate_roadmap(
            current_daily_visitors=current_daily_visitors,
            target_daily_visitors=target_daily_visitors,
            category=category
        )

        # StrategyPhaseModel → StrategyPhase 변환 (레거시 호환)
        return [
            StrategyPhase(
                phase=p.phase,
                name=p.name,
                duration=p.duration,
                target_level=p.target_level,
                target_keywords_count=p.target_keywords_count,
                strategies=p.strategies,
                goals=p.goals,
                expected_daily_visitors=p.expected_daily_visitors
            )
            for p in phases
        ]


# 테스트 코드
if __name__ == "__main__":
    import asyncio

    async def test():
        print("=== UnifiedKeywordEngine V3 테스트 ===\n")

        engine = UnifiedKeywordEngine()

        # 1. 키워드 생성 테스트
        print("[1] 키워드 생성 테스트")
        keywords = await engine.generate_keywords_with_gpt("카페", "서울 강남구", "브런치 전문")

        if keywords:
            print(f"✅ 생성된 키워드: {len(keywords)}개")
            for kw in keywords[:3]:
                print(f"   Level {kw['level']}: {kw['keyword']}")
        else:
            print("⚠️ 키워드 생성 실패 (API 키 확인 필요)")

        print()

        # 2. 키워드 분석 테스트
        print("[2] 키워드 분석 테스트")
        test_keyword = "강남역 브런치 카페"
        metrics = await engine.analyze_keyword(
            test_keyword, 4, "서울 강남구", "카페"
        )

        print(f"키워드: {metrics.keyword}")
        print(f"  검색량: {metrics.estimated_monthly_searches:,}회/월")
        print(f"  데이터 소스: {metrics.data_source}")
        if metrics.monthly_pc_searches:
            print(f"  PC: {metrics.monthly_pc_searches:,}, 모바일: {metrics.monthly_mobile_searches:,}")
        print(f"  경쟁도: {metrics.competition_score}/100")
        print(f"  난이도: {metrics.difficulty_score}/100")
        print(f"  목표: {metrics.recommended_rank_target} ({metrics.estimated_timeline})")
        print()

        # 3. 전략 로드맵 테스트
        print("[3] 전략 로드맵 테스트")
        roadmap = engine.generate_strategy_roadmap(50, 200, "카페")
        print(f"총 {len(roadmap)}개 단계")
        for phase in roadmap:
            print(f"  Phase {phase.phase}: {phase.name} ({phase.duration})")

        print("\n=== 테스트 완료 ===")

    asyncio.run(test())
