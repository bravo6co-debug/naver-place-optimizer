#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""검색량 추정 서비스"""

from typing import Optional, Dict
from integrations.naver_search_ad_api import NaverSearchAdAPI
from integrations.mois_population_api import get_region_population, get_population_grade
from config.category_loader import CategoryLoader


class SearchVolumeEstimatorService:
    """검색량 추정 서비스 - 다단계 폴백"""

    def __init__(self, search_ad_api: Optional[NaverSearchAdAPI] = None):
        self.search_ad_api = search_ad_api or NaverSearchAdAPI()
        self.category_loader = CategoryLoader()
        self._batch_cache = {}  # 배치 API 호출 결과 캐시

    async def estimate_monthly_searches(
        self,
        keyword: str,
        category: str,
        location: str,
        level: int = 3,  # ✅ 키워드 레벨 추가
        force_api: bool = False  # ✅ Level 1-2는 API 재시도 강화
    ) -> Dict:
        """
        검색량 추정 (다단계)

        Level 1: 네이버 검색광고 API (실제 데이터)
        Level 2: 지역 인구 기반 추정 (폴백)

        Args:
            keyword: 검색 키워드
            category: 업종
            location: 지역
            level: 키워드 레벨 (1-5)
            force_api: Level 1-2는 True로 설정하여 API 우선 시도

        Returns:
            {
                "total": 전체 검색량,
                "pc": PC 검색량,
                "mobile": 모바일 검색량,
                "source": "api" or "estimated"
            }
        """
        # ✅ Level 1-2만 API 호출 (총 4개 키워드)
        if force_api:
            api_data = self._get_from_api(keyword, retry=True)
            if api_data:
                print(f"✅ [{keyword}] 검색광고 API 데이터 사용: {api_data['monthly_total_searches']:,}회/월")
                return {
                    "total": api_data["monthly_total_searches"],
                    "pc": api_data["monthly_pc_searches"],
                    "mobile": api_data["monthly_mobile_searches"],
                    "source": "api"
                }
            else:
                # Level 1-2: API 실패 시 "Fail" 반환
                print(f"   ❌ [{keyword}] API 실패 - 'Fail' 표시")
                if level == 1:
                    # Level 1은 기본 검색량 사용하되 PC/Mobile은 Fail 표시
                    default_volume = 10000
                    return {
                        "total": default_volume,
                        "pc": "Fail",
                        "mobile": "Fail",
                        "source": "restaurant_stats_fallback"
                    }
                else:
                    # Level 2는 추정치 사용하되 PC/Mobile은 Fail 표시
                    estimated, grade = self._estimate_from_population(location, category)
                    return {
                        "total": estimated,
                        "pc": "Fail",
                        "mobile": "Fail",
                        "source": grade
                    }

        # Level 3-5: 인구 기반 추정 (PC/Mobile 상세 정보 없음)
        estimated, grade = self._estimate_from_population(location, category)
        print(f"⚠️ [{keyword}] API 데이터 없음 → 추정치 사용: {estimated:,}회/월 (등급: {grade})")
        return {
            "total": estimated,
            "pc": None,  # Level 3-5는 상세 정보 제공 안함
            "mobile": None,  # Level 3-5는 상세 정보 제공 안함
            "source": grade  # 인구 기반 등급 (estimated, estimated_b ~ estimated_f)
        }

    def _get_from_api(self, keyword: str, retry: bool = False) -> Optional[Dict]:
        """
        검색광고 API에서 데이터 가져오기 (캐시 우선)

        Args:
            keyword: 검색 키워드
            retry: Level 1-2 키워드는 True로 설정하여 재시도
        """
        # 캐시 확인 (배치 호출 결과)
        if keyword in self._batch_cache:
            print(f"   ✅ [{keyword}] 캐시된 API 데이터 사용")
            return self._batch_cache[keyword]

        max_attempts = 2 if retry else 1

        for attempt in range(max_attempts):
            try:
                stats = self.search_ad_api.get_keyword_stats([keyword])
                if stats and len(stats) > 0:
                    parsed = self.search_ad_api.parse_keyword_data(stats[0])

                    # parse_keyword_data가 None을 반환하면 (적은검색량 등) 실패 처리
                    if parsed is None:
                        if attempt == 0 and retry:
                            print(f"   [{keyword}] 적은검색량으로 파싱 실패, 재시도 중...")
                            continue
                        else:
                            print(f"   [{keyword}] 적은검색량 - API 데이터 사용 불가")
                            return None

                    if attempt > 0:
                        print(f"   [{keyword}] API 재시도 성공 ({attempt + 1}회차)")
                    return parsed
                else:
                    if attempt == 0 and retry:
                        print(f"   [{keyword}] API 응답 없음, 재시도 중...")
                    else:
                        print(f"   [{keyword}] API 응답 없음 (빈 리스트)")
            except Exception as e:
                if attempt == 0 and retry:
                    print(f"   [{keyword}] API 호출 실패, 재시도 중... ({e})")
                else:
                    print(f"   [{keyword}] 검색광고 API 호출 실패: {e}")

        return None

    def _estimate_from_population(self, location: str, category: str) -> tuple[int, str]:
        """
        지역 인구 기반 추정 (MOIS API 통합) + 데이터 소스 반환

        Returns:
            (검색량, 데이터 소스)
            데이터 소스: "estimated_b" ~ "estimated_f" (인구 규모별)
        """
        population, pop_source = get_region_population(location)

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

        # 인구 기반 등급 결정 (B~F급)
        if pop_source == "population_estimated":
            # 추정 인구인 경우 인구 규모에 따라 등급 세분화
            grade = get_population_grade(population)
        else:
            # 실제 인구 데이터인 경우 "estimated"로 반환 (호출자가 B급으로 처리)
            grade = "estimated"

        return monthly_searches, grade

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
