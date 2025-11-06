#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""업종 데이터 로더"""

import json
import os
from typing import Optional, Dict, List
from pathlib import Path


class CategoryLoader:
    """업종 데이터 로더 (JSON 기반)"""

    def __init__(self, categories_dir: Optional[str] = None):
        """
        초기화

        Args:
            categories_dir: 업종 데이터 디렉토리 경로
        """
        if categories_dir:
            self.categories_dir = Path(categories_dir)
        else:
            # 현재 파일 기준으로 categories 디렉토리 찾기
            current_dir = Path(__file__).parent
            self.categories_dir = current_dir / "categories"

        self._cache = {}

    def get_category(self, category_name: str) -> Optional[Dict]:
        """
        업종 데이터 조회 (유사 업종 매핑 + 범용 전략 폴백)

        Args:
            category_name: 업종 이름 (예: "음식점", "카페", "치킨집", "정형외과")

        Returns:
            업종 데이터 딕셔너리 또는 None
        """
        # 캐시 확인
        if category_name in self._cache:
            return self._cache[category_name]

        # 1차 매핑: 정확한 업종명
        exact_map = {
            "음식점": "restaurant.json",
            "카페": "cafe.json",
            "미용실": "salon.json",
            "병원": "hospital.json",
            "학원": "academy.json",
            "헬스장": "gym.json"
        }

        # 2차 매핑: 유사 업종 → 대표 업종
        similar_map = {
            # 음식점 관련
            "식당": "restaurant.json",
            "맛집": "restaurant.json",
            "레스토랑": "restaurant.json",
            "한식": "restaurant.json",
            "중식": "restaurant.json",
            "일식": "restaurant.json",
            "양식": "restaurant.json",
            "치킨": "restaurant.json",
            "치킨집": "restaurant.json",
            "피자": "restaurant.json",
            "피자집": "restaurant.json",
            "분식": "restaurant.json",
            "분식집": "restaurant.json",
            "고기집": "restaurant.json",
            "술집": "restaurant.json",
            "횟집": "restaurant.json",

            # 카페 관련
            "커피숍": "cafe.json",
            "디저트": "cafe.json",
            "디저트카페": "cafe.json",
            "베이커리": "cafe.json",
            "제과점": "cafe.json",

            # 미용실 관련
            "헤어샵": "salon.json",
            "네일샵": "salon.json",
            "피부관리": "salon.json",
            "네일아트": "salon.json",
            "왁싱": "salon.json",

            # 병원 관련
            "의원": "hospital.json",
            "클리닉": "hospital.json",
            "정형외과": "hospital.json",
            "치과": "hospital.json",
            "한의원": "hospital.json",
            "피부과": "hospital.json",
            "내과": "hospital.json",
            "소아과": "hospital.json",

            # 학원 관련
            "교습소": "academy.json",
            "과외": "academy.json",
            "영어학원": "academy.json",
            "수학학원": "academy.json",
            "음악학원": "academy.json",
            "미술학원": "academy.json",

            # 헬스장 관련
            "피트니스": "gym.json",
            "요가": "gym.json",
            "필라테스": "gym.json",
            "크로스핏": "gym.json",
            "pt": "gym.json",
            "PT": "gym.json"
        }

        # 1차 시도: 정확한 매핑
        filename = exact_map.get(category_name)

        # 2차 시도: 유사 업종 매핑
        if not filename:
            filename = similar_map.get(category_name)

        # 3차 폴백: 범용 전략 사용
        if not filename:
            filename = "_generic_strategies.json"
            print(f"ℹ️ '{category_name}' → 범용 전략 사용")

        filepath = self.categories_dir / filename

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[category_name] = data
                return data
        except FileNotFoundError:
            print(f"❌ 업종 데이터 파일을 찾을 수 없습니다: {filepath}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {filepath} - {e}")
            return None

    def list_categories(self) -> List[str]:
        """사용 가능한 업종 목록 반환"""
        categories = []

        if not self.categories_dir.exists():
            return categories

        for filepath in self.categories_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    categories.append(data.get("name"))
            except Exception:
                continue

        return categories

    def reload_category(self, category_name: str):
        """특정 업종 데이터 캐시 갱신"""
        if category_name in self._cache:
            del self._cache[category_name]
        return self.get_category(category_name)

    def clear_cache(self):
        """전체 캐시 초기화"""
        self._cache.clear()


# 사용 예시
if __name__ == "__main__":
    loader = CategoryLoader()

    # 업종 목록 조회
    categories = loader.list_categories()
    print(f"사용 가능한 업종: {categories}")

    # 특정 업종 데이터 로드
    cafe_data = loader.get_category("카페")
    if cafe_data:
        print(f"\n[{cafe_data['name']}]")
        print(f"기본 키워드: {cafe_data['base_keywords']}")
        print(f"수식어 종류: {list(cafe_data['modifiers'].keys())}")
