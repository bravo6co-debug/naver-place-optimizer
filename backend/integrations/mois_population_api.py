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
        self._cache_duration = timedelta(days=30)  # 30일 캐시 (인구는 월 1회만 업데이트)

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

            # API 호출 (공공데이터포털 표준 파라미터)
            # 인코딩된 키를 디코딩하여 params로 전달 (httpx가 자동으로 재인코딩)
            import urllib.parse
            decoded_key = urllib.parse.unquote_plus(self.api_key)

            params = {
                "serviceKey": decoded_key,  # 디코딩된 키 사용 (소문자 s로 시도)
                "pageNo": "1",
                "numOfRows": "1000"
            }

            response = httpx.get(
                f"{self.BASE_URL}/getRegistrationPopulationByRegion",
                params=params,
                timeout=3.0  # 3초로 단축 (공공 API 느림 고려)
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
# 2024년 기준 전국 주요 시군구 인구 데이터
DEFAULT_POPULATION = {
    # 서울특별시 (25구)
    "서울 강남구": 560000,
    "서울 서초구": 420000,
    "서울 송파구": 660000,
    "서울 강동구": 450000,
    "서울 강서구": 580000,
    "서울 양천구": 470000,
    "서울 영등포구": 390000,
    "서울 구로구": 420000,
    "서울 금천구": 240000,
    "서울 관악구": 510000,
    "서울 동작구": 400000,
    "서울 마포구": 380000,
    "서울 서대문구": 320000,
    "서울 은평구": 490000,
    "서울 노원구": 550000,
    "서울 도봉구": 340000,
    "서울 강북구": 320000,
    "서울 성북구": 460000,
    "서울 중랑구": 410000,
    "서울 동대문구": 360000,
    "서울 광진구": 360000,
    "서울 성동구": 310000,
    "서울 용산구": 240000,
    "서울 중구": 130000,
    "서울 종로구": 160000,

    # 부산광역시 (16구)
    "부산 해운대구": 410000,
    "부산 부산진구": 380000,
    "부산 북구": 300000,
    "부산 사상구": 230000,
    "부산 사하구": 330000,
    "부산 동래구": 270000,
    "부산 남구": 280000,
    "부산 연제구": 210000,
    "부산 수영구": 180000,
    "부산 금정구": 250000,
    "부산 강서구": 140000,
    "부산 동구": 95000,
    "부산 서구": 110000,
    "부산 영도구": 120000,
    "부산 중구": 45000,
    "부산 기장군": 180000,

    # 대구광역시 (8구)
    "대구 수성구": 420000,
    "대구 달서구": 580000,
    "대구 북구": 440000,
    "대구 동구": 340000,
    "대구 서구": 210000,
    "대구 남구": 160000,
    "대구 중구": 80000,
    "대구 달성군": 260000,

    # 인천광역시 (10구)
    "인천 남동구": 520000,
    "인천 부평구": 510000,
    "인천 서구": 550000,
    "인천 계양구": 320000,
    "인천 연수구": 340000,
    "인천 미추홀구": 410000,
    "인천 동구": 70000,
    "인천 중구": 140000,
    "인천 강화군": 70000,
    "인천 옹진군": 22000,

    # 광주광역시 (5구)
    "광주 북구": 450000,
    "광주 서구": 310000,
    "광주 남구": 220000,
    "광주 동구": 95000,
    "광주 광산구": 390000,

    # 대전광역시 (5구)
    "대전 유성구": 350000,
    "대전 서구": 480000,
    "대전 중구": 250000,
    "대전 동구": 230000,
    "대전 대덕구": 210000,

    # 울산광역시 (5구)
    "울산 남구": 340000,
    "울산 북구": 210000,
    "울산 동구": 170000,
    "울산 중구": 230000,
    "울산 울주군": 230000,

    # 세종특별자치시
    "세종": 380000,

    # 경기도 주요 시
    "경기 수원시": 1200000,
    "경기 성남시": 950000,
    "경기 고양시": 1050000,
    "경기 용인시": 1080000,
    "경기 부천시": 820000,
    "경기 안산시": 660000,
    "경기 안양시": 550000,
    "경기 남양주시": 720000,
    "경기 화성시": 950000,
    "경기 평택시": 580000,
    "경기 의정부시": 460000,
    "경기 시흥시": 490000,
    "경기 파주시": 480000,
    "경기 김포시": 520000,
    "경기 광명시": 280000,
    "경기 광주시": 420000,
    "경기 군포시": 280000,
    "경기 하남시": 300000,
    "경기 오산시": 230000,
    "경기 양주시": 230000,
    "경기 이천시": 220000,
    "경기 구리시": 190000,
    "경기 안성시": 190000,
    "경기 포천시": 150000,
    "경기 의왕시": 160000,
    "경기 여주시": 110000,
    "경기 동두천시": 95000,
    "경기 과천시": 56000,

    # 강원특별자치도
    "강원 춘천시": 280000,
    "강원 원주시": 360000,
    "강원 강릉시": 210000,
    "강원 동해시": 92000,
    "강원 태백시": 42000,
    "강원 속초시": 82000,
    "강원 삼척시": 65000,

    # 충청북도
    "충북 청주시": 850000,
    "충북 충주시": 210000,
    "충북 제천시": 135000,

    # 충청남도
    "충남 천안시": 680000,
    "충남 아산시": 330000,
    "충남 서산시": 180000,
    "충남 논산시": 120000,
    "충남 계룡시": 46000,
    "충남 당진시": 170000,

    # 전라북도
    "전북 전주시": 660000,
    "전북 익산시": 280000,
    "전북 군산시": 270000,
    "전북 정읍시": 110000,
    "전북 남원시": 82000,
    "전북 김제시": 85000,

    # 전라남도
    "전남 목포시": 230000,
    "전남 여수시": 280000,
    "전남 순천시": 280000,
    "전남 나주시": 120000,
    "전남 광양시": 160000,

    # 경상북도
    "경북 포항시": 500000,
    "경북 경주시": 250000,
    "경북 구미시": 410000,
    "경북 김천시": 140000,
    "경북 안동시": 160000,
    "경북 경산시": 280000,

    # 경상남도
    "경남 창원시": 1040000,
    "경남 김해시": 560000,
    "경남 진주시": 340000,
    "경남 양산시": 360000,
    "경남 거제시": 260000,
    "경남 통영시": 130000,
    "경남 사천시": 115000,
    "경남 밀양시": 105000,

    # 제주특별자치도
    "제주 제주시": 490000,
    "제주 서귀포시": 190000,
}


def get_region_population(region: str, api_key: Optional[str] = None) -> tuple[int, str]:
    """
    지역 인구 조회 (로컬 데이터 우선, API는 폴백) + 데이터 소스 반환

    Args:
        region: 지역명 (예: "서울 강남구")
        api_key: MOIS API 키 (선택)

    Returns:
        (인구 수, 데이터 소스)
        데이터 소스: "population_db" (A급), "population_api" (A급), "population_estimated" (B~F급)

    성능 최적화:
        - 1차: DEFAULT_POPULATION (146개 지역, < 1ms) → A급
        - 2차: MOIS API (타임아웃 3초) → A급
        - 3차: 기본값 300,000 → B~F급 (인구 규모별 차등)
    """
    # 1차: 로컬 데이터 우선 (즉시 응답) - A급
    if region in DEFAULT_POPULATION:
        return DEFAULT_POPULATION[region], "population_db"

    # 2차: API 시도 (로컬에 없는 경우만) - A급
    if api_key or os.getenv("MOIS_API_KEY"):
        api = MOISPopulationAPI(api_key)
        population = api.get_population(region)
        if population is not None:
            return population, "population_api"

    # 3차: 기본값 (중소도시 평균) - B~F급 (추정)
    print(f"⚠️ {region} 인구 데이터 없음 → 기본값 300,000 사용")
    return 300000, "population_estimated"


def get_population_grade(population: int) -> str:
    """
    인구 규모 기반 데이터 등급 반환

    Args:
        population: 인구 수

    Returns:
        등급: "B", "C", "D", "E", "F"

    등급 기준:
        - B급: 50만 이상 (대도시)
        - C급: 20만~50만 (중도시)
        - D급: 10만~20만 (소도시)
        - E급: 5만~10만 (군 지역)
        - F급: 5만 미만 (소규모)
    """
    if population >= 500000:
        return "estimated_b"  # 대도시
    elif population >= 200000:
        return "estimated_c"  # 중도시
    elif population >= 100000:
        return "estimated_d"  # 소도시
    elif population >= 50000:
        return "estimated_e"  # 군 지역
    else:
        return "estimated_f"  # 소규모
