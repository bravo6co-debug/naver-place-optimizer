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
        키워드 경쟁도 분석

        Returns:
            {
                "result_count": 검색 결과 수,
                "competition_score": 경쟁도 점수 (0-100),
                "competition_level": 경쟁도 수준 ("높음", "중간", "낮음"),
                "avg_cpc": 평균 클릭 비용 (원)
            }
        """
        # 네이버 로컬 검색 결과 수
        result_count = await self.local_api.get_competition_count(keyword)
        competition_score = self.local_api.calculate_competition_score(result_count)

        # 검색광고 API에서 추가 정보
        ad_data = await self._get_ad_competition_data(keyword)

        return {
            "result_count": result_count,
            "competition_score": competition_score,
            "competition_level": ad_data.get("competition_level", self._score_to_level(competition_score)),
            "avg_cpc": ad_data.get("avg_cpc", 0)
        }

    async def _get_ad_competition_data(self, keyword: str) -> Dict:
        """검색광고 API에서 경쟁 데이터 가져오기"""
        try:
            stats = self.search_ad_api.get_keyword_stats([keyword])
            if stats and len(stats) > 0:
                parsed = self.search_ad_api.parse_keyword_data(stats[0])
                return {
                    "competition_level": parsed.get("competition_level"),
                    "avg_cpc": parsed.get("avg_cpc", 0)
                }
        except Exception:
            pass

        return {}

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
