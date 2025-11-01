#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""경쟁도 분석 서비스"""

from typing import Optional, Dict
from integrations.naver_search_ad_api import NaverSearchAdAPI
from integrations.restaurant_stats_loader import get_restaurant_stats_loader
from integrations.mois_population_api import get_region_population


class CompetitionAnalyzerService:
    """경쟁도 분석 서비스 (네이버 로컬 API 폐기, CSV 기반)"""

    def __init__(
        self,
        search_ad_api: Optional[NaverSearchAdAPI] = None
    ):
        self.search_ad_api = search_ad_api or NaverSearchAdAPI()
        self.restaurant_stats = get_restaurant_stats_loader()

    async def analyze_competition(
        self,
        keyword: str,
        location: str = "",
        category: str = ""
    ) -> Dict:
        """
        키워드 경쟁도 분석 (우선순위: 검색광고 API → CSV 통계 → 추정)

        Args:
            keyword: 검색 키워드
            location: 지역 (예: "서울 강남구")
            category: 업종 (예: "카페", "음식점")

        Returns:
            {
                "result_count": 검색 결과 수,
                "competition_score": 경쟁도 점수 (0-100),
                "competition_level": 경쟁도 수준 ("높음", "중간", "낮음"),
                "data_source": 데이터 소스 ("api", "restaurant_stats", "estimated")
            }
        """
        # ✅ 1차: 검색광고 API 우선 시도
        ad_data = await self._get_ad_competition_data(keyword)

        if ad_data and "competition_level" in ad_data:
            # 검색광고 API 3단계 경쟁도 사용
            competition_score = self._level_to_score(ad_data["competition_level"])
            return {
                "result_count": 0,  # API에서 제공 안함
                "competition_score": competition_score,  # ✅ 높음:85, 중간:60, 낮음:30
                "competition_level": ad_data["competition_level"],
                "data_source": "api"  # ✅ 최고 등급 (S급)
            }

        # ✅ 2차: 요식업 CSV 통계 데이터 (음식점/카페)
        if category and location:
            if self.restaurant_stats.is_supported_category(category):
                stats_data = self.restaurant_stats.get_competition(location)
                if stats_data:
                    competition_score = int(stats_data["경쟁강도_0to100"])
                    return {
                        "result_count": stats_data["총_음식점수"],
                        "competition_score": competition_score,
                        "competition_level": self._score_to_level(competition_score),
                        "data_source": "restaurant_stats"  # ✅ A급 (정부 통계)
                    }

        # ✅ 3차: 인구 기반 추정 (최후 폴백)
        estimated_score = self._estimate_competition(location, category)
        return {
            "result_count": 0,  # 추정값
            "competition_score": estimated_score,
            "competition_level": self._score_to_level(estimated_score),
            "data_source": "estimated"  # ✅ B~E급 (추정)
        }

    async def _get_ad_competition_data(self, keyword: str) -> Dict:
        """검색광고 API에서 경쟁 데이터 가져오기"""
        try:
            stats = self.search_ad_api.get_keyword_stats([keyword])
            if stats and len(stats) > 0:
                parsed = self.search_ad_api.parse_keyword_data(stats[0])
                return {
                    "competition_level": parsed.get("competition_level")
                }
        except Exception as e:
            print(f"   검색광고 API 경쟁도 조회 실패: {e}")

        return {}

    def _estimate_competition(self, location: str, category: str) -> int:
        """
        인구 기반 경쟁도 추정

        Args:
            location: 지역명
            category: 업종

        Returns:
            경쟁도 점수 (0-100)
        """
        if not location:
            return 50  # 기본값

        # 인구 기반 추정
        population = get_region_population(location)

        # 인구별 경쟁도 추정 (간단한 휴리스틱)
        if population >= 500000:  # 50만 이상
            base_score = 30
        elif population >= 200000:  # 20만 이상
            base_score = 40
        elif population >= 100000:  # 10만 이상
            base_score = 50
        elif population >= 50000:  # 5만 이상
            base_score = 60
        else:  # 5만 미만
            base_score = 70

        return base_score

    def _level_to_score(self, level: str) -> int:
        """
        검색광고 API 3단계 경쟁도 → 점수 변환

        Args:
            level: "높음", "중간", "낮음"

        Returns:
            경쟁도 점수 (0-100)
        """
        mapping = {
            "높음": 85,  # Level 1-2 키워드
            "중간": 60,  # Level 3 키워드
            "낮음": 30   # Level 4-5 키워드
        }
        return mapping.get(level, 60)  # 기본값 중간

    def _score_to_level(self, score: int) -> str:
        """경쟁도 점수를 수준으로 변환"""
        if score >= 70:
            return "높음"
        elif score >= 40:
            return "중간"
        else:
            return "낮음"

    def calculate_difficulty_score(
        self,
        competition_score: int,
        level: int,
        search_volume: int
    ) -> int:
        """
        난이도 점수 계산

        Args:
            competition_score: 경쟁도 점수 (0-100)
            level: 키워드 레벨 (1-5)
            search_volume: 검색량

        Returns:
            난이도 점수 (0-100)
        """
        # 경쟁도 60% + 키워드 레벨 30% + 검색량 10%
        level_score = 100 - (level * 20)
        volume_score = min(100, (search_volume / 10000) * 100)

        difficulty = int(
            (competition_score * 0.6) +
            (level_score * 0.3) +
            (volume_score * 0.1)
        )

        return min(100, max(0, difficulty))
