#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 키워드 분석 엔진 V3
- 새로운 모듈 구조 사용
- 네이버 검색광고 API 우선 사용
- 다단계 폴백 시스템
- 레거시 호환성 유지
Updated: 2025-11-01 - Railway deployment fix
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# 새로운 모듈 임포트
from models.keyword import KeywordMetrics, KeywordLevel
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


# 레거시 호환성을 위한 별칭
# KeywordMetrics, KeywordLevel은 models.keyword에서 import됨 (Line 19)
# StrategyPhase는 models.strategy에서 import됨 (Line 20)
StrategyPhase = StrategyPhaseModel


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
        self.competition_analyzer = CompetitionAnalyzerService(self.search_ad_api)
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

    async def prefetch_api_data(self, keywords_data: List[Dict], location: str, category: str):
        """
        Level 1-2 키워드의 API 데이터를 배치로 미리 가져오기

        Args:
            keywords_data: 생성된 키워드 리스트
            location: 지역
            category: 업종
        """
        # Level 1-2 키워드만 추출
        level12_keywords = [kw["keyword"] for kw in keywords_data if kw["level"] <= 2]

        if not level12_keywords:
            return

        print(f"🚀 배치 API 호출: Level 1-2 키워드 {len(level12_keywords)}개")

        # 배치 API 호출
        stats_list = self.volume_estimator.search_ad_api.get_keyword_stats(level12_keywords)

        # 결과를 캐시에 저장
        for stat in stats_list:
            parsed = self.volume_estimator.search_ad_api.parse_keyword_data(stat)
            if parsed:
                keyword = parsed["keyword"]
                self.volume_estimator._batch_cache[keyword] = parsed
                print(f"   ✅ 캐시 저장: {keyword}")

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
        # ✅ Level 1-2는 API 우선 (재시도 활성화)
        volume_data = await self.volume_estimator.estimate_monthly_searches(
            keyword=keyword,
            category=category,
            location=location,
            level=level,
            force_api=(level <= 2)  # ✅ Level 1-2는 API 재시도 활성화
        )

        # 레벨별 검색량 조정
        base_searches = volume_data["total"]
        estimated_searches = self.volume_estimator.apply_level_multiplier(base_searches, level)

        # 2. 경쟁도 분석 (location, category, level 전달)
        # ✅ Level 1-2만 네이버 검색 결과 조회, Level 3-5는 생략
        competition_data = await self.competition_analyzer.analyze_competition(
            keyword=keyword,
            location=location,
            category=category,
            level=level,  # ✅ 키워드 레벨 전달
            fetch_naver_results=(level <= 2)  # ✅ Level 1-2만 네이버 결과 조회
        )

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

        # 6. 최종 데이터 등급 결정 (검색량 vs 경쟁도 중 낮은 등급 선택)
        # 등급 우선순위: api(S) > restaurant_stats(A) > estimated(B) > estimated_b~f(C~F)
        volume_source = volume_data["source"]
        competition_source = competition_data["data_source"]

        # 두 소스 중 신뢰도가 낮은 것을 최종 등급으로 설정
        source_priority = {
            "api": 6,                      # S급 (검색광고 API)
            "restaurant_stats": 5,          # A급 (정부 통계)
            "restaurant_stats_fallback": 5, # A급 (폴백)
            "estimated": 4,                 # B급 (추정 - 실제 인구)
            "estimated_b": 3,               # C급 (추정 - 50만+ 인구)
            "estimated_c": 2,               # D급 (추정 - 20~50만 인구)
            "estimated_d": 1,               # E급 (추정 - 10~20만 인구)
            "estimated_e": 0,               # F급 (추정 - 5~10만 인구)
            "estimated_f": 0                # F급 (추정 - 5만 미만 인구)
        }

        volume_priority = source_priority.get(volume_source, 0)
        competition_priority = source_priority.get(competition_source, 0)

        # 낮은 등급을 최종 data_source로 선택
        if volume_priority < competition_priority:
            final_data_source = volume_source
        else:
            final_data_source = competition_source

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
            # V3 추가 정보 (최종 데이터 등급)
            data_source=final_data_source,
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
        category: str,
        analyzed_keywords: Optional[List[KeywordMetrics]] = None,
        specialty: Optional[str] = None
    ) -> List[StrategyPhase]:
        """
        전략 로드맵 생성 (레거시 호환 메서드)

        Args:
            current_daily_visitors: 현재 일방문자
            target_daily_visitors: 목표 일방문자
            category: 업종
            analyzed_keywords: 분석된 키워드 목록 (V4+)
            specialty: 특징/전문분야 (specialty 포함 키워드 우선)

        Returns:
            StrategyPhase 리스트
        """
        phases = self.strategy_planner.generate_roadmap(
            current_daily_visitors=current_daily_visitors,
            target_daily_visitors=target_daily_visitors,
            category=category,
            analyzed_keywords=analyzed_keywords,
            specialty=specialty
        )

        # StrategyPhase는 이제 models.strategy.StrategyPhase의 별칭이므로 변환 불필요
        # V5 필드를 포함한 모든 필드가 자동으로 유지됨
        return phases


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
        if metrics.monthly_pc_searches is not None:
            # PC/Mobile 검색량 표시 (숫자 또는 "Fail")
            if isinstance(metrics.monthly_pc_searches, str):
                print(f"  PC: {metrics.monthly_pc_searches}, 모바일: {metrics.monthly_mobile_searches}")
            else:
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
