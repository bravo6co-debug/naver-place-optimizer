#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""경쟁도 분석 서비스"""

from typing import Optional, Dict
from integrations.naver_local_api import NaverLocalAPI
from integrations.naver_search_ad_api import NaverSearchAdAPI


class CompetitionAnalyzerService:
    """경쟁도 분석 서비스"""

    def __init__(
        self,
        local_api: Optional[NaverLocalAPI] = None,
        search_ad_api: Optional[NaverSearchAdAPI] = None
    ):
        self.local_api = local_api or NaverLocalAPI()
        self.search_ad_api = search_ad_api or NaverSearchAdAPI()

    async def analyze_competition(self, keyword: str) -> Dict:
        """
        키워드 경쟁도 분석 (우선순위: 검색광고 API → 로컬 API → 추정)

        Returns:
            {
                "result_count": 검색 결과 수,
                "competition_score": 경쟁도 점수 (0-100),
                "competition_level": 경쟁도 수준 ("높음", "중간", "낮음"),
                "data_source": 데이터 소스 ("api", "naver_local", "estimated")
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
                "data_source": "api"  # ✅ 최고 등급
            }

        # 2차: 네이버 로컬 API 폴백
        result_count = await self.local_api.get_competition_count(keyword)

        if result_count > 0:
            competition_score = self.local_api.calculate_competition_score(result_count)
            return {
                "result_count": result_count,
                "competition_score": competition_score,
                "competition_level": self._score_to_level(competition_score),
                "data_source": "naver_local"  # ✅ 2등급
            }

        # 3차: 추정 (최후 폴백)
        estimated_count = self.local_api._estimate_competition(keyword)
        competition_score = self.local_api.calculate_competition_score(estimated_count)
        return {
            "result_count": estimated_count,
            "competition_score": competition_score,
            "competition_level": self._score_to_level(competition_score),
            "data_source": "estimated"  # ✅ 최하위
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
