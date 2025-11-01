#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
요식업 경쟁도 통계 데이터 로더
정부 통계 기반 실제 음식점 경쟁 데이터 제공
"""

import os
import csv
from typing import Optional, Dict
from pathlib import Path


class RestaurantStatsLoader:
    """요식업 경쟁도 통계 데이터 로더 (CSV 기반)"""

    def __init__(self):
        self.stats_data = {}
        self._load_csv()

    def _load_csv(self):
        """CSV 파일을 메모리에 로드"""
        csv_path = Path(__file__).parent.parent / "data" / "restaurant_competition_stats.csv"

        if not csv_path.exists():
            print(f"⚠️ CSV 파일 없음: {csv_path}")
            return

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sido = row['시도']
                    sigungu = row['시군구']

                    # 시도별 딕셔너리 초기화
                    if sido not in self.stats_data:
                        self.stats_data[sido] = {}

                    # 시군구 데이터 저장
                    self.stats_data[sido][sigungu] = {
                        "총_음식점수": int(row['총_음식점수']),
                        "인구수": int(row['인구수']),
                        "인구만명당음식점수": float(row['인구만명당음식점수']),
                        "경쟁강도_0to100": float(row['경쟁강도_0to100']),
                        "경쟁강도_등급": row['경쟁강도_등급'],
                        "음식점다양성_0to100": float(row['음식점다양성_0to100']),
                        "음식점종류수": int(row['음식점종류수']),
                        "최종_경쟁강도_지수": float(row['최종_경쟁강도_지수'])
                    }

            print(f"✅ CSV 로드 성공: {len(self.stats_data)}개 시도, 총 {sum(len(v) for v in self.stats_data.values())}개 시군구")

        except Exception as e:
            print(f"❌ CSV 로드 실패: {e}")

    def get_competition(self, location: str) -> Optional[Dict]:
        """
        지역명으로 경쟁도 데이터 조회

        Args:
            location: 지역명 (예: "서울 강남구", "강남구", "부산 중구")

        Returns:
            경쟁도 데이터 딕셔너리 또는 None
        """
        if not self.stats_data:
            return None

        # 지역명 파싱
        parts = location.split()

        if len(parts) >= 2:
            # "서울 강남구" 형태
            sido_input = parts[0]
            sigungu_input = parts[1]
        else:
            # "강남구" 형태 - 전체 시도에서 검색
            sigungu_input = parts[0]
            sido_input = None

        # 정확한 매칭 시도
        if sido_input:
            sido_normalized = self._normalize_sido(sido_input)
            if sido_normalized and sido_normalized in self.stats_data:
                if sigungu_input in self.stats_data[sido_normalized]:
                    return self.stats_data[sido_normalized][sigungu_input]

        # 시군구만으로 전체 검색 (모호한 경우 첫 매칭 반환)
        for sido, regions in self.stats_data.items():
            if sigungu_input in regions:
                return regions[sigungu_input]

        # 퍼지 매칭 (부분 일치)
        if sido_input:
            sido_normalized = self._normalize_sido(sido_input)
            if sido_normalized and sido_normalized in self.stats_data:
                for sigungu, data in self.stats_data[sido_normalized].items():
                    if sigungu_input in sigungu or sigungu in sigungu_input:
                        return data

        return None

    def _normalize_sido(self, sido: str) -> Optional[str]:
        """시도명 정규화 (약칭 → 정식 명칭)"""
        # 광역시/특별시/도 매핑
        mappings = {
            "서울": "서울특별시",
            "부산": "부산광역시",
            "대구": "대구광역시",
            "인천": "인천광역시",
            "광주": "광주광역시",
            "대전": "대전광역시",
            "울산": "울산광역시",
            "세종": "세종특별자치시",
            "경기": "경기도",
            "강원": "강원특별자치도",
            "충북": "충청북도",
            "충남": "충청남도",
            "전북": "전북특별자치도",
            "전남": "전라남도",
            "경북": "경상북도",
            "경남": "경상남도",
            "제주": "제주특별자치도"
        }

        # 이미 정식 명칭인 경우
        if sido in self.stats_data:
            return sido

        # 약칭 → 정식 명칭 변환
        for short, full in mappings.items():
            if short in sido:
                if full in self.stats_data:
                    return full

        return None

    def is_supported_category(self, category: str) -> bool:
        """
        요식업 카테고리 여부 확인

        Args:
            category: 업종명

        Returns:
            True if 요식업, False otherwise
        """
        food_categories = ["음식점", "카페", "맛집", "레스토랑", "식당", "베이커리", "디저트"]
        return any(food_cat in category for food_cat in food_categories)


# 싱글톤 인스턴스 (메모리 효율)
_loader_instance = None


def get_restaurant_stats_loader() -> RestaurantStatsLoader:
    """싱글톤 인스턴스 반환"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = RestaurantStatsLoader()
    return _loader_instance


# 사용 예시
if __name__ == "__main__":
    loader = RestaurantStatsLoader()

    # 테스트 케이스
    test_locations = [
        "서울 강남구",
        "강남구",
        "부산 중구",
        "제주 제주시",
        "경기 수원시 팔달구"
    ]

    print("\n📊 테스트 결과:")
    print("-" * 60)

    for loc in test_locations:
        data = loader.get_competition(loc)
        if data:
            print(f"✅ {loc:20s} → 경쟁강도: {data['경쟁강도_0to100']:.1f}, 등급: {data['경쟁강도_등급']}")
        else:
            print(f"❌ {loc:20s} → 데이터 없음")
