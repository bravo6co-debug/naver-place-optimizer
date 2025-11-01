#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""검색량 추정 서비스"""

from typing import Optional, Dict
from integrations.naver_search_ad_api import NaverSearchAdAPI
from integrations.mois_population_api import get_region_population
from config.category_loader import CategoryLoader


class SearchVolumeEstimatorService:
    """검색량 추정 서비스 - 다단계 폴백"""

    def __init__(self, search_ad_api: Optional[NaverSearchAdAPI] = None):
        self.search_ad_api = search_ad_api or NaverSearchAdAPI()
        self.category_loader = CategoryLoader()

    async def estimate_monthly_searches(
        self,
        keyword: str,
        category: str,
        location: str
    ) -> Dict:
        """
        검색량 추정 (다단계)

        Level 1: 네이버 검색광고 API (실제 데이터)
        Level 2: 지역 인구 기반 추정 (폴백)

        Returns:
            {
                "total": 전체 검색량,
                "pc": PC 검색량,
                "mobile": 모바일 검색량,
                "source": "api" or "estimated"
            }
        """
        # Level 1: 검색광고 API 시도
        api_data = self._get_from_api(keyword)
        if api_data:
            print(f"✅ [{keyword}] 검색광고 API 데이터 사용: {api_data['monthly_total_searches']:,}회/월")
            return {
                "total": api_data["monthly_total_searches"],
                "pc": api_data["monthly_pc_searches"],
                "mobile": api_data["monthly_mobile_searches"],
                "source": "api"
            }

        # Level 2: 인구 기반 추정
        estimated = self._estimate_from_population(location, category)
        print(f"⚠️ [{keyword}] API 데이터 없음 → 추정치 사용: {estimated:,}회/월")
        return {
            "total": estimated,
            "pc": int(estimated * 0.3),  # PC 30%
            "mobile": int(estimated * 0.7),  # 모바일 70%
            "source": "estimated"
        }

    def _get_from_api(self, keyword: str) -> Optional[Dict]:
        """검색광고 API에서 데이터 가져오기"""
        try:
            stats = self.search_ad_api.get_keyword_stats([keyword])
            if stats and len(stats) > 0:
                parsed = self.search_ad_api.parse_keyword_data(stats[0])
                return parsed
            else:
                print(f"   [{keyword}] API 응답 없음 (빈 리스트)")
        except Exception as e:
            print(f"   [{keyword}] 검색광고 API 호출 실패: {e}")

        return None

    def _estimate_from_population(self, location: str, category: str) -> int:
        """지역 인구 기반 추정 (MOIS API 통합)"""
        population = get_region_population(location)

        cat_data = self.category_loader.get_category(category)
        if not cat_data:
            cat_data = {
                "usage_rate": 0.5,
                "search_rate": 0.3
            }

        usage_rate = cat_data.get("usage_rate", 0.5)
        search_rate = cat_data.get("search_rate", 0.3)

        # 공식: 인구 × 이용률 × 검색률 / 12
        monthly_searches = int(population * usage_rate * search_rate / 12)

        return monthly_searches

    def apply_level_multiplier(self, base_searches: int, level: int) -> int:
        """
        키워드 레벨별 검색량 조정

        Args:
            base_searches: 기본 검색량
            level: 키워드 레벨 (1-5)

        Returns:
            조정된 검색량
        """
        multipliers = {
            5: 0.01,  # 롱테일 1%
            4: 0.05,  # 니치 5%
            3: 0.15,  # 중간 15%
            2: 0.40,  # 경쟁 40%
            1: 1.00   # 최상위 100%
        }

        multiplier = multipliers.get(level, 0.1)
        return int(base_searches * multiplier)
