#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 로컬 검색 API 통합
경쟁 업체 수 파악

⚠️ DEPRECATED: 이 모듈은 더 이상 사용되지 않습니다.
네이버 로컬 API는 경쟁도 측정에 부정확하여 폐기되었습니다.
대신 restaurant_stats_loader.py (정부 통계 CSV)를 사용하세요.
"""

import os
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from integrations.mois_population_api import get_region_population


class NaverLocalAPI:
    """네이버 로컬 검색 API 클라이언트"""

    BASE_URL = "https://openapi.naver.com/v1/search/local.json"

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.getenv("NAVER_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("NAVER_CLIENT_SECRET")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_competition_count(
        self,
        keyword: str,
        region: Optional[str] = None,
        category: Optional[str] = None
    ) -> int:
        """
        키워드로 검색되는 업체 수 조회

        Args:
            keyword: 검색 키워드
            region: 지역명 (예: "서울 강남구")
            category: 업종 (예: "카페")

        Returns:
            검색 결과 업체 수
        """
        if not self.client_id or not self.client_secret:
            return self._estimate_competition(keyword, region, category)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.BASE_URL,
                    headers={
                        "X-Naver-Client-Id": self.client_id,
                        "X-Naver-Client-Secret": self.client_secret
                    },
                    params={"query": keyword, "display": 1}
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("total", 0)
                else:
                    return self._estimate_competition(keyword, region, category)

        except Exception as e:
            print(f"네이버 로컬 API 오류: {e}")
            return self._estimate_competition(keyword, region, category)

    def _estimate_competition(
        self,
        keyword: str,
        region: Optional[str] = None,
        category: Optional[str] = None
    ) -> int:
        """
        향상된 경쟁도 추정 (API 실패 시 폴백)

        Args:
            keyword: 검색 키워드
            region: 지역명 (예: "서울 강남구")
            category: 업종 (예: "카페")

        Returns:
            추정 경쟁 업체 수
        """
        base_score = 1000

        # 1. 키워드 길이 기반 특성 분석
        word_count = len(keyword.split())
        length_multiplier = {
            1: 50,    # "맛집" -> 매우 높은 경쟁
            2: 10,    # "강남 맛집" -> 높은 경쟁
            3: 3,     # "강남역 맛집 추천" -> 중간 경쟁
            4: 1,     # "강남역 근처 데이트 맛집" -> 낮은 경쟁
        }.get(word_count, 0.5 if word_count > 4 else 50)

        # 2. 고경쟁 키워드 패턴 감지 (가산 방식)
        high_competition_patterns = {
            '맛집': 2.0, '카페': 1.8, '추천': 1.3, 'best': 1.5, '순위': 1.4,
            '인기': 1.2, '유명': 1.2, '핫플': 1.5, '웨이팅': 1.3,
            '병원': 1.5, '피부과': 1.4, '성형외과': 1.6, '치과': 1.4,
            '한의원': 1.3, '미용실': 1.3, '네일': 1.2, '헬스장': 1.2,
            '학원': 1.3, '과외': 1.2, '영어': 1.3,
        }

        keyword_multiplier = 1.0
        for pattern, multiplier in high_competition_patterns.items():
            if pattern in keyword.lower():
                keyword_multiplier += (multiplier - 1)  # 가산 방식

        # 3. 지역 인구 기반 가중치
        region_multiplier = 1.0
        if region:
            try:
                population = get_region_population(region)
                if population >= 500000:
                    region_multiplier = 2.5
                elif population >= 300000:
                    region_multiplier = 1.8
                elif population >= 100000:
                    region_multiplier = 1.3
                else:
                    region_multiplier = 0.8
            except Exception:
                region_multiplier = 1.5

        # 4. 업종별 가중치 (간단한 버전)
        industry_multiplier = 1.0
        if category:
            category_weights = {
                '음식점': 1.8, '카페': 1.78, '미용실': 1.4,
                '병원': 1.6, '학원': 1.5, '헬스장': 1.2
            }
            industry_multiplier = category_weights.get(category, 1.2)
        else:
            industry_multiplier = 1.2

        # 5. 최종 경쟁도 계산
        estimated = int(
            base_score *
            length_multiplier *
            keyword_multiplier *
            region_multiplier *
            industry_multiplier
        )

        # 상한선/하한선 설정
        estimated = max(50, min(estimated, 100000))

        return estimated

    def calculate_competition_score(self, result_count: int) -> int:
        """
        검색 결과 수를 경쟁도 점수(0-100)로 변환

        Args:
            result_count: 검색 결과 수

        Returns:
            경쟁도 점수 (0-100)
        """
        if result_count < 100:
            return 10
        elif result_count < 1000:
            return 30
        elif result_count < 10000:
            return 50
        elif result_count < 100000:
            return 70
        else:
            return 90
