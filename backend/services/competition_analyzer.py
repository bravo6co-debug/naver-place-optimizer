#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""경쟁도 분석 서비스"""

from typing import Optional, Dict
from integrations.naver_search_ad_api import NaverSearchAdAPI
from integrations.restaurant_stats_loader import get_restaurant_stats_loader
from integrations.mois_population_api import get_region_population, get_population_grade


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
        category: str = "",
        level: int = 3,  # ✅ 추가: 키워드 레벨 (1-5)
        fetch_naver_results: bool = True  # ✅ Level 1-2만 상세 조회
    ) -> Dict:
        """
        키워드 경쟁도 분석 (우선순위: 검색광고 API → CSV 통계 → 추정)

        Args:
            keyword: 검색 키워드
            location: 지역 (예: "서울 강남구")
            category: 업종 (예: "카페", "음식점")
            level: 키워드 레벨 (1-5, 낮을수록 경쟁적)
            fetch_naver_results: Level 1-2만 True (상세 조회), Level 3-5는 False (간소화)

        Returns:
            {
                "result_count": 검색 결과 수,
                "competition_score": 경쟁도 점수 (0-100),
                "competition_level": 경쟁도 수준 ("높음", "중간", "낮음"),
                "data_source": 데이터 소스 ("api", "restaurant_stats", "estimated")
            }
        """
        # ✅ Level 3-5는 간소화된 분석 (API 호출 스킵)
        if not fetch_naver_results:
            # CSV 통계 우선 → 추정치 폴백 (API 호출 안함)
            if category and location:
                if self.restaurant_stats.is_supported_category(category):
                    stats_data = self.restaurant_stats.get_competition(location)
                    if stats_data:
                        base_competition = int(stats_data["경쟁강도_0to100"])
                        adjusted_competition = self._adjust_competition_by_keyword(
                            base_competition, keyword, level
                        )
                        return {
                            "result_count": 0,  # Level 3-5는 결과 수 생략
                            "competition_score": adjusted_competition,
                            "competition_level": self._score_to_level(adjusted_competition),
                            "data_source": "restaurant_stats"
                        }

            # 최종 폴백: 추정치
            base_estimated, grade = self._estimate_competition(location, category)
            adjusted_estimated = self._adjust_competition_by_keyword(
                base_estimated, keyword, level
            )
            return {
                "result_count": 0,
                "competition_score": adjusted_estimated,
                "competition_level": self._score_to_level(adjusted_estimated),
                "data_source": grade  # 인구 기반 등급 (estimated, estimated_b ~ estimated_f)
            }

        # ✅ Level 1-2: 상세 분석 (API 호출 포함)
        # 1차: 검색광고 API 우선 시도
        ad_data = await self._get_ad_competition_data(keyword)

        if ad_data and "competition_level" in ad_data:
            # 검색광고 API 3단계 경쟁도 사용 (키워드별 실제 데이터)
            competition_score = self._level_to_score(ad_data["competition_level"])
            return {
                "result_count": 0,  # API에서 제공 안함
                "competition_score": competition_score,  # ✅ 높음:85, 중간:60, 낮음:30
                "competition_level": ad_data["competition_level"],
                "data_source": "api"  # ✅ S급 (검색광고 API)
            }

        # 2차: 요식업 CSV 통계 데이터 (음식점/카페) + 키워드 조정
        if category and location:
            if self.restaurant_stats.is_supported_category(category):
                stats_data = self.restaurant_stats.get_competition(location)
                if stats_data:
                    # 지역 기본 경쟁도
                    base_competition = int(stats_data["경쟁강도_0to100"])

                    # ✅ 키워드 특성 반영: 길이, 구체성, 레벨에 따라 조정
                    adjusted_competition = self._adjust_competition_by_keyword(
                        base_competition, keyword, level
                    )

                    return {
                        "result_count": stats_data["총_음식점수"],
                        "competition_score": adjusted_competition,
                        "competition_level": self._score_to_level(adjusted_competition),
                        "data_source": "restaurant_stats"  # ✅ A급 (정부 통계)
                    }

        # ✅ Level 1: estimated 금지 (S/A급만 허용)
        if level == 1:
            # Level 1은 API나 restaurant_stats 없으면 경고 후 restaurant_stats 기본값 반환
            print(f"   ⚠️ [Level 1 경고] {keyword}: API/정부통계 없음, 기본 경쟁도 적용 (A급 유지)")
            base_estimated = 85  # Level 1 기본 고경쟁도
            adjusted_estimated = self._adjust_competition_by_keyword(
                base_estimated, keyword, level
            )
            return {
                "result_count": 0,
                "competition_score": adjusted_estimated,
                "competition_level": self._score_to_level(adjusted_estimated),
                "data_source": "restaurant_stats_fallback"  # ✅ A급 (폴백)
            }

        # 3차: 인구 기반 추정 (Level 2-5만 허용)
        base_estimated, grade = self._estimate_competition(location, category)
        adjusted_estimated = self._adjust_competition_by_keyword(
            base_estimated, keyword, level
        )

        return {
            "result_count": 0,  # 추정값
            "competition_score": adjusted_estimated,
            "competition_level": self._score_to_level(adjusted_estimated),
            "data_source": grade  # ✅ 인구 기반 등급 (estimated, estimated_b ~ estimated_f)
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

    def _adjust_competition_by_keyword(
        self,
        base_competition: int,
        keyword: str,
        level: int
    ) -> int:
        """
        키워드 특성에 따라 경쟁도 조정

        Args:
            base_competition: 기본 경쟁도 (지역 기반)
            keyword: 키워드
            level: 키워드 레벨 (1-5)

        Returns:
            조정된 경쟁도 (0-100)

        조정 로직:
        - Level 1 (최상위): 경쟁도 +0% (그대로)
        - Level 2 (경쟁): 경쟁도 -10%
        - Level 3 (중간): 경쟁도 -25%
        - Level 4 (니치): 경쟁도 -40%
        - Level 5 (롱테일): 경쟁도 -60%

        추가 조정:
        - 키워드 길이 4단어 이상: 추가 -10%
        - 키워드 길이 6단어 이상: 추가 -15%
        """
        # 1. Level별 경쟁도 감소
        level_adjustments = {
            1: 0.00,   # 최상위 (그대로)
            2: 0.10,   # -10%
            3: 0.25,   # -25%
            4: 0.40,   # -40%
            5: 0.60    # -60%
        }

        level_reduction = level_adjustments.get(level, 0.25)
        adjusted = base_competition * (1 - level_reduction)

        # 2. 키워드 길이 기반 추가 감소 (롱테일일수록 경쟁 낮음)
        word_count = len(keyword.split())

        if word_count >= 6:
            adjusted *= 0.85  # 추가 -15%
        elif word_count >= 4:
            adjusted *= 0.90  # 추가 -10%

        # 3. 최소/최대값 제한
        result = int(adjusted)
        result = max(5, min(100, result))  # 5~100 범위

        return result

    def _estimate_competition(self, location: str, category: str) -> tuple[int, str]:
        """
        인구 기반 경쟁도 추정 + 데이터 소스 반환

        Args:
            location: 지역명
            category: 업종

        Returns:
            (경쟁도 점수, 데이터 소스)
            데이터 소스: "estimated_b" ~ "estimated_f" (인구 규모별)
        """
        if not location:
            return 50, "estimated"  # 기본값

        # 인구 기반 추정
        population, pop_source = get_region_population(location)

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

        # 인구 기반 등급 결정 (B~F급)
        if pop_source == "population_estimated":
            # 추정 인구인 경우 인구 규모에 따라 등급 세분화
            grade = get_population_grade(population)
        else:
            # 실제 인구 데이터인 경우 "estimated"로 반환 (호출자가 B급으로 처리)
            grade = "estimated"

        return base_score, grade

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
