#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""키워드 생성 서비스"""

import random
from typing import List, Dict, Optional
from integrations.openai_api import OpenAIAPI
from config.category_loader import CategoryLoader


class KeywordGeneratorService:
    """키워드 생성 서비스"""

    def __init__(self, openai_api: Optional[OpenAIAPI] = None):
        self.openai_api = openai_api or OpenAIAPI()
        self.category_loader = CategoryLoader()

    async def generate_keywords(
        self,
        category: str,
        location: str,
        specialty: Optional[str] = None
    ) -> List[Dict]:
        """
        2단계 키워드 생성 프로세스

        Stage 1: GPT로 연관 키워드만 생성 (조합 없이)
        Stage 2: 연관 키워드를 조합 규칙으로 결합

        Args:
            category: 업종
            location: 지역
            specialty: 특징/전문분야

        Returns:
            키워드 리스트 (총 30개: Level 5=10, 4=8, 3=6, 2=4, 1=2)
        """
        # Stage 1: GPT로 연관 키워드 생성
        related_keywords = self.openai_api.generate_related_keywords(
            category=category,
            specialty=specialty
        )

        # Stage 2: 연관 키워드를 조합하여 최종 키워드 생성
        if related_keywords:
            keywords = self._combine_keywords_by_level(
                location=location,
                category=category,
                specialty=specialty,
                related_keywords=related_keywords
            )
        else:
            # Fallback: 연관 키워드 생성 실패 시 기본 키워드 사용
            print("⚠️ 연관 키워드 생성 실패, 기본 키워드 사용")
            keywords = self._generate_generic_keywords(category, location, specialty)

        # Level별 키워드 개수 제한
        keywords = self._limit_keywords_per_level(keywords)

        return keywords

    def _combine_keywords_by_level(
        self,
        location: str,
        category: str,
        specialty: Optional[str],
        related_keywords: Dict[str, List[str]]
    ) -> List[Dict]:
        """
        연관 키워드를 조합하여 레벨별 키워드 생성

        Args:
            location: 지역
            category: 업종
            specialty: 특징/전문분야
            related_keywords: 연관 키워드 딕셔너리

        Returns:
            레벨별 키워드 리스트
        """
        keywords = []
        location_parts = location.split()

        # 연관 키워드 추출
        category_related = related_keywords.get("category_related", [category])
        specialty_list = []
        if specialty:
            specialty_list = [s.strip() for s in specialty.split(',') if s.strip()]

        # specialty별 연관 키워드 수집
        all_specialty_related = []
        for i, spec in enumerate(specialty_list, 1):
            spec_key = f"specialty{i}_related"
            if spec_key in related_keywords:
                all_specialty_related.extend(related_keywords[spec_key])
            else:
                all_specialty_related.append(spec)  # 기본값으로 specialty 자체 사용

        # Level 5 (롱테일) - 10개: 복잡한 조합 + 조사
        level5_patterns = [
            lambda loc, cat, spec: f"{loc} {spec} {cat} 추천해줘",
            lambda loc, cat, spec: f"{loc}에 있는 {spec} {cat} 어디가 좋을까",
            lambda loc, cat, spec: f"{loc} {spec} 잘하는 {cat} 찾아요",
            lambda loc, cat, spec: f"{loc} {spec} {cat} 후기 좋은 곳",
            lambda loc, cat, spec: f"{loc}에서 {spec} 되는 {cat} 추천",
            lambda loc, cat, spec: f"{loc} {spec} 전문 {cat} 어디?",
            lambda loc, cat, spec: f"{loc} {spec} {cat} 가격 저렴한 곳",
            lambda loc, cat, spec: f"{loc} 근처 {spec} {cat} 괜찮은데",
            lambda loc, cat, spec: f"{loc} {spec} {cat} 예약 가능한 곳",
            lambda loc, cat, spec: f"{loc}에 {spec} {cat} 있나요"
        ]

        for i in range(10):
            if all_specialty_related:
                spec = all_specialty_related[i % len(all_specialty_related)]
                cat = category_related[i % len(category_related)]
                pattern = level5_patterns[i % len(level5_patterns)]
                keywords.append({
                    "keyword": pattern(location, cat, spec),
                    "level": 5,
                    "reason": f"롱테일: {spec} + {cat}"
                })
            else:
                cat = category_related[i % len(category_related)]
                keywords.append({
                    "keyword": f"{location} {cat} 추천 후기",
                    "level": 5,
                    "reason": "기본 롱테일"
                })

        # Level 4 (니치) - 8개: 중간 조합
        for i in range(8):
            if all_specialty_related:
                spec = all_specialty_related[i % len(all_specialty_related)]
                cat = category_related[i % len(category_related)]
                if i % 2 == 0:
                    keywords.append({
                        "keyword": f"{location} {spec} {cat} 추천",
                        "level": 4,
                        "reason": f"니치: {spec}"
                    })
                else:
                    keywords.append({
                        "keyword": f"{location} {spec} 잘하는 {cat}",
                        "level": 4,
                        "reason": f"니치: {spec} 품질"
                    })
            else:
                cat = category_related[i % len(category_related)]
                keywords.append({
                    "keyword": f"{location} {cat} 추천",
                    "level": 4,
                    "reason": "기본 니치"
                })

        # Level 3 (중간) - 6개: 간단한 조합
        for i in range(6):
            if all_specialty_related:
                spec = all_specialty_related[i % len(all_specialty_related)]
                cat = category_related[i % len(category_related)]
                keywords.append({
                    "keyword": f"{location} {spec} {cat}",
                    "level": 3,
                    "reason": f"중간: 지역+특성+업종"
                })
            else:
                cat = category_related[i % len(category_related)]
                keywords.append({
                    "keyword": f"{location} {cat}",
                    "level": 3,
                    "reason": "기본 중간"
                })

        # Level 2 (경쟁) - 4개: 지역 + specialty/category
        base_location = location_parts[0] if len(location_parts) >= 2 else location

        if all_specialty_related:
            for i in range(4):
                spec = all_specialty_related[i % len(all_specialty_related)]
                if i % 2 == 0:
                    keywords.append({
                        "keyword": f"{base_location} {spec}",
                        "level": 2,
                        "reason": f"경쟁: 광역+특성"
                    })
                else:
                    cat = category_related[0]
                    keywords.append({
                        "keyword": f"{base_location} {spec} {cat}",
                        "level": 2,
                        "reason": f"경쟁: 광역+특성+업종"
                    })
        else:
            for i in range(4):
                cat = category_related[i % len(category_related)]
                keywords.append({
                    "keyword": f"{base_location} {cat}",
                    "level": 2,
                    "reason": "경쟁: 광역+업종"
                })

        # Level 1 (최상위) - 2개: specialty 또는 category만
        if all_specialty_related:
            keywords.append({
                "keyword": all_specialty_related[0],
                "level": 1,
                "reason": "최상위: 특성 단독"
            })
            if len(all_specialty_related) > 1:
                keywords.append({
                    "keyword": all_specialty_related[1],
                    "level": 1,
                    "reason": "최상위: 특성 단독"
                })
            else:
                keywords.append({
                    "keyword": category,
                    "level": 1,
                    "reason": "최상위: 업종 단독"
                })
        else:
            keywords.append({
                "keyword": category,
                "level": 1,
                "reason": "최상위: 업종 단독"
            })
            if len(category_related) > 1:
                keywords.append({
                    "keyword": category_related[1],
                    "level": 1,
                    "reason": "최상위: 업종 관련어"
                })
            else:
                keywords.append({
                    "keyword": category_related[0],
                    "level": 1,
                    "reason": "최상위: 업종 관련어"
                })

        return keywords

    def _limit_keywords_per_level(self, keywords: List[Dict]) -> List[Dict]:
        """
        Level별 키워드 개수 제한

        Args:
            keywords: 키워드 리스트

        Returns:
            제한된 키워드 리스트
        """
        level_limits = {
            5: 10,  # 롱테일
            4: 8,   # 니치
            3: 6,   # 중간
            2: 4,   # 경쟁
            1: 2    # 최상위
        }

        # Level별로 그룹화
        keywords_by_level = {}
        for kw in keywords:
            level = kw.get("level", 3)
            if level not in keywords_by_level:
                keywords_by_level[level] = []
            keywords_by_level[level].append(kw)

        # Level별 제한 적용
        limited_keywords = []
        for level in [5, 4, 3, 2, 1]:
            if level in keywords_by_level:
                limit = level_limits[level]
                limited_keywords.extend(keywords_by_level[level][:limit])

        return limited_keywords

    def _generate_generic_keywords(
        self,
        category: str,
        location: str,
        specialty: Optional[str] = None
    ) -> List[Dict]:
        """
        커스텀 업종용 기본 키워드 생성 (specialty 우선 반영, 다중 특징 지원)

        Args:
            category: 업종
            location: 지역
            specialty: 특징/전문분야 (컴마로 구분된 여러 특징 가능)

        Returns:
            기본 키워드 리스트 (35개)
        """
        location_parts = location.split()
        keywords = []

        # specialty 파싱: 컴마로 구분된 여러 특징 처리
        specialty_list = []
        if specialty:
            specialty_list = [s.strip() for s in specialty.split(',') if s.strip()]

        # 일반적인 수식어들
        generic_modifiers = ["추천", "잘하는곳", "가격", "후기", "위치", "영업시간", "전화번호"]
        purposes = ["근처", "예약", "상담", "방문"]
        qualities = ["좋은", "유명한", "저렴한", "괜찮은"]

        # Level 5 - 롱테일 (15개) - specialty 필수
        for i in range(15):
            if specialty_list:
                # 다중 특징 처리
                if len(specialty_list) >= 2 and i % 4 == 0:
                    # 2개 특징 조합
                    specs = random.sample(specialty_list, min(2, len(specialty_list)))
                    spec_str = ' '.join(specs)
                    kw = f"{location} {spec_str} {category} {random.choice(purposes)}"
                    reason = f"'{'+'.join(specs)}' 복합 특징"
                else:
                    # 개별 특징 사용
                    spec = random.choice(specialty_list)
                    if i % 3 == 0:
                        kw = f"{location} {spec} {random.choice(qualities)} {category}"
                    elif i % 3 == 1:
                        kw = f"{location} {spec} {category} {random.choice(purposes)}"
                    else:
                        kw = f"{location} {spec} {category} {random.choice(generic_modifiers)}"
                    reason = f"'{spec}' 특징 반영"
            else:
                if i < 5:
                    kw = f"{location} {random.choice(qualities)} {category} {random.choice(generic_modifiers)}"
                elif i < 10:
                    kw = f"{location} {category} {random.choice(purposes)} {random.choice(generic_modifiers)}"
                else:
                    kw = f"{location} {category} {random.choice(generic_modifiers)} {random.choice(qualities)}"
                reason = "커스텀 업종"

            keywords.append({
                "keyword": kw,
                "level": 5,
                "reason": f"롱테일 키워드 ({reason})"
            })

        # Level 4 - 니치 (10개) - specialty 필수
        if specialty_list:
            for mod in generic_modifiers[:7]:
                spec = random.choice(specialty_list)
                keywords.append({
                    "keyword": f"{location} {spec} {category} {mod}",
                    "level": 4,
                    "reason": f"'{spec}' 특징 니치 키워드"
                })
            for qual in qualities[:3]:
                spec = random.choice(specialty_list)
                keywords.append({
                    "keyword": f"{location} {spec} {qual} {category}",
                    "level": 4,
                    "reason": f"'{spec}' + 품질 키워드"
                })
        else:
            for mod in generic_modifiers[:7]:
                keywords.append({
                    "keyword": f"{location} {category} {mod}",
                    "level": 4,
                    "reason": "니치 키워드 (커스텀 업종)"
                })
            for qual in qualities[:3]:
                keywords.append({
                    "keyword": f"{location} {qual} {category}",
                    "level": 4,
                    "reason": "니치 키워드 (커스텀 업종)"
                })

        # Level 3 - 중간 (5개) - specialty 필수
        if specialty_list:
            # 다중 특징을 순차적으로 사용
            specs_to_use = specialty_list * 2  # 5개 키워드에 충분하도록 반복
            keywords.extend([
                {"keyword": f"{location} {specs_to_use[0]} {category}", "level": 3, "reason": f"지역 + '{specs_to_use[0]}' + 업종"},
                {"keyword": f"{location} {specs_to_use[1]} {category} 추천", "level": 3, "reason": f"'{specs_to_use[1]}' 추천 키워드"},
                {"keyword": f"{location} {specs_to_use[2]} {category} 가격", "level": 3, "reason": f"'{specs_to_use[2]}' 가격 키워드"},
                {"keyword": f"{location} {specs_to_use[3]} {category} 후기", "level": 3, "reason": f"'{specs_to_use[3]}' 후기 키워드"},
                {"keyword": f"{location} {specs_to_use[4]} {category} 예약", "level": 3, "reason": f"'{specs_to_use[4]}' 예약 키워드"}
            ])
        else:
            keywords.extend([
                {"keyword": f"{location} {category}", "level": 3, "reason": "기본 키워드"},
                {"keyword": f"{location} {category} 추천", "level": 3, "reason": "추천 키워드"},
                {"keyword": f"{location} {category} 가격", "level": 3, "reason": "가격 키워드"},
                {"keyword": f"{location} {category} 후기", "level": 3, "reason": "후기 키워드"},
                {"keyword": f"{location} {category} 예약", "level": 3, "reason": "예약 키워드"}
            ])

        # Level 2 - 경쟁 (2개) - specialty 우선 반영
        if specialty_list:
            # specialty 있으면 specialty 기반 Level 2 (2개만)
            if len(location_parts) >= 2:
                keywords.extend([
                    {"keyword": f"{location_parts[0]} {specialty_list[0]} 맛집", "level": 2, "reason": f"광역 + '{specialty_list[0]}' 경쟁"},
                    {"keyword": f"{location_parts[0]} {specialty_list[1] if len(specialty_list) > 1 else specialty_list[0]}", "level": 2, "reason": f"광역 + specialty 경쟁"}
                ])
            else:
                keywords.extend([
                    {"keyword": f"{location} {specialty_list[0]}", "level": 2, "reason": f"지역 + '{specialty_list[0]}' 경쟁"},
                    {"keyword": f"{location} {specialty_list[1] if len(specialty_list) > 1 else specialty_list[0]} 맛집", "level": 2, "reason": f"specialty 맛집"}
                ])
        else:
            # specialty 없으면 기존 로직 (category 사용, 2개만)
            if len(location_parts) >= 2:
                keywords.extend([
                    {"keyword": f"{location_parts[0]} {category}", "level": 2, "reason": "광역 경쟁 키워드"},
                    {"keyword": f"{location_parts[0]} {category} 추천", "level": 2, "reason": "광역 추천 키워드"}
                ])
            else:
                keywords.extend([
                    {"keyword": f"{location} {category} 유명한", "level": 2, "reason": "경쟁 키워드"},
                    {"keyword": f"{location} {category} 인기", "level": 2, "reason": "경쟁 키워드"}
                ])

        # Level 1 - 최상위 (2개) - specialty 필수 반영
        if specialty_list:
            # specialty 있으면 specialty 우선
            if len(location_parts) >= 2:
                keywords.append({
                    "keyword": f"{location_parts[0]} {specialty_list[0]}",
                    "level": 1,
                    "reason": f"광역 + specialty({specialty_list[0]}) 최상위"
                })
            if len(specialty_list) > 1:
                keywords.append({
                    "keyword": f"{location_parts[0] if len(location_parts) >= 2 else location} {specialty_list[1]}",
                    "level": 1,
                    "reason": f"광역 + specialty({specialty_list[1]}) 최상위"
                })
            else:
                # specialty가 1개만 있으면 specialty만 사용
                keywords.append({
                    "keyword": specialty_list[0],
                    "level": 1,
                    "reason": f"specialty({specialty_list[0]}) 단독 최상위"
                })
        else:
            # specialty 없으면 기존 로직 (category 사용)
            if len(location_parts) >= 2:
                keywords.append({
                    "keyword": f"{location_parts[0]} {category}",
                    "level": 1,
                    "reason": "광역 초경쟁 키워드"
                })
            keywords.append({
                "keyword": category,
                "level": 1,
                "reason": "최상위 키워드"
            })

        return keywords
