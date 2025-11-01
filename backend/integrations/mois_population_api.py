#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
행정안전부 주민등록인구 통계 API 클라이언트
"""

import os
import httpx
import xml.etree.ElementTree as ET
from typing import Dict, Optional
from datetime import datetime, timedelta


class MOISPopulationAPI:
    """행정안전부 인구 통계 API"""

    BASE_URL = "https://apis.data.go.kr/1741000/RegistrationPopulationByRegion"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MOIS_API_KEY")
        self._cache: Dict[str, tuple] = {}  # {region: (population, timestamp)}
        self._cache_duration = timedelta(hours=24)  # 24시간 캐시

    def get_population(self, region: str) -> Optional[int]:
        """
        지역별 인구 조회

        Args:
            region: "서울 강남구" 형식의 지역명

        Returns:
            인구 수 (없으면 None)
        """
        if not self.api_key:
            return None

        # 캐시 확인
        if region in self._cache:
            population, timestamp = self._cache[region]
            if datetime.now() - timestamp < self._cache_duration:
                return population

        try:
            # 지역명 파싱: "서울 강남구" -> city="서울", district="강남구"
            parts = region.split()
            if len(parts) != 2:
                return None

            city, district = parts

            # API 호출
            params = {
                "serviceKey": self.api_key,
                "pageNo": "1",
                "numOfRows": "1000",
                "type": "xml"
            }

            response = httpx.get(
                f"{self.BASE_URL}/getRegistrationPopulationByRegionService",
                params=params,
                timeout=10.0
            )

            if response.status_code != 200:
                print(f"⚠️ MOIS API 오류: HTTP {response.status_code}")
                return None

            # XML 파싱
            root = ET.fromstring(response.content)

            # 결과 코드 확인
            result_code = root.find('.//resultCode')
            if result_code is not None and result_code.text != "00":
                result_msg = root.find('.//resultMsg')
                print(f"⚠️ MOIS API 오류: {result_msg.text if result_msg is not None else 'Unknown'}")
                return None

            # 데이터 검색
            for item in root.findall('.//item'):
                region_name = item.find('admNm')  # 행정구역명
                population = item.find('totPpltn')  # 총인구

                if region_name is not None and population is not None:
                    # "서울특별시 강남구" -> "서울 강남구"로 매칭
                    api_region = region_name.text.replace("특별시", "").replace("광역시", "").replace("시", "").strip()

                    if city in api_region and district in api_region:
                        pop_value = int(population.text)
                        # 캐시 저장
                        self._cache[region] = (pop_value, datetime.now())
                        return pop_value

            print(f"⚠️ MOIS API: {region} 데이터 없음")
            return None

        except Exception as e:
            print(f"⚠️ MOIS API 호출 실패: {str(e)}")
            return None

    def get_population_batch(self, regions: list[str]) -> Dict[str, int]:
        """
        여러 지역 인구 일괄 조회

        Args:
            regions: 지역명 리스트

        Returns:
            {region: population} 딕셔너리
        """
        result = {}
        for region in regions:
            pop = self.get_population(region)
            if pop is not None:
                result[region] = pop
        return result


# 기본 폴백 데이터 (API 실패 시 사용)
DEFAULT_POPULATION = {
    "서울 강남구": 560000,
    "서울 서초구": 420000,
    "서울 송파구": 660000,
    "서울 강북구": 320000,
    "서울 영등포구": 390000,
    "서울 마포구": 380000,
    "부산 해운대구": 410000,
    "부산 부산진구": 380000,
    "부산 동래구": 270000,
    "대구 수성구": 420000,
    "인천 남동구": 520000,
    "광주 서구": 310000,
    "대전 유성구": 350000,
    "울산 남구": 340000,
    "경기 수원시": 1200000,
    "경기 성남시": 950000,
    "경기 고양시": 1050000,
}


def get_region_population(region: str, api_key: Optional[str] = None) -> int:
    """
    지역 인구 조회 (API 우선, 폴백 지원)

    Args:
        region: 지역명 (예: "서울 강남구")
        api_key: MOIS API 키 (선택)

    Returns:
        인구 수
    """
    # API 시도
    if api_key or os.getenv("MOIS_API_KEY"):
        api = MOISPopulationAPI(api_key)
        population = api.get_population(region)
        if population is not None:
            return population

    # 폴백: 기본 데이터
    if region in DEFAULT_POPULATION:
        return DEFAULT_POPULATION[region]

    # 기본값: 30만 (중소도시 평균)
    print(f"⚠️ {region} 인구 데이터 없음 → 기본값 300,000 사용")
    return 300000
