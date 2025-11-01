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
        키워드 생성 (GPT 우선, 폴백은 패턴 기반)

        Args:
            category: 업종
            location: 지역
            specialty: 특징/전문분야

        Returns:
            키워드 리스트
        """
        # 업종 데이터 로드 (없으면 커스텀 업종으로 처리)
        cat_data = self.category_loader.get_category(category)

        # GPT로 키워드 생성 시도
        if cat_data:
            modifiers = cat_data.get("modifiers", {})
            modifier_examples = self._build_modifier_examples(modifiers)
        else:
            # 커스텀 업종 - GPT가 스스로 패턴을 생성하도록 함
            modifier_examples = ""

        keywords = self.openai_api.generate_keywords(
            category=category,
            location=location,
            specialty=specialty,
            modifier_examples=modifier_examples
        )

        # GPT 실패 시 폴백 (카테고리 데이터가 있는 경우만)
        if not keywords and cat_data:
            keywords = self._generate_fallback_keywords(category, location, cat_data, specialty)
        elif not keywords:
            # 커스텀 업종이고 GPT도 실패한 경우 - 기본 키워드 생성
            keywords = self._generate_generic_keywords(category, location, specialty)

        return keywords

    def _build_modifier_examples(self, modifiers: Dict) -> str:
        """수식어 예시 문자열 생성"""
        if not modifiers:
            return ""

        examples = "\n\n업종별 실제 검색 패턴:\n"
        for mod_type, mod_values in list(modifiers.items())[:3]:
            examples += f"- {mod_type}: {', '.join(mod_values[:5])}\n"

        return examples

    def _generate_fallback_keywords(
        self,
        category: str,
        location: str,
        cat_data: Dict,
        specialty: Optional[str] = None
    ) -> List[Dict]:
        """패턴 기반 폴백 키워드 생성 (specialty 우선 반영, 다중 특징 지원)"""
        base_keywords = cat_data.get("base_keywords", [category])
        modifiers = cat_data.get("modifiers", {})
        patterns = cat_data.get("longtail_patterns", [])
        location_parts = location.split()

        keywords = []

        # specialty 파싱: 컴마로 구분된 여러 특징 처리
        specialty_list = []
        if specialty:
            specialty_list = [s.strip() for s in specialty.split(',') if s.strip()]

        # Level 5 - 롱테일 (15개) - specialty 필수 포함
        for i in range(15):
            if patterns and modifiers and specialty_list:
                # 다중 특징 조합 전략
                if len(specialty_list) >= 2 and i % 3 == 0:
                    # 2개 특징 조합
                    specs = random.sample(specialty_list, min(2, len(specialty_list)))
                    spec_str = ' '.join(specs)
                    pattern = random.choice(patterns)
                    keyword = self._apply_pattern(pattern, location, modifiers)
                    keyword = keyword.replace(location, f"{location} {spec_str}", 1)
                    keywords.append({
                        "keyword": keyword,
                        "level": 5,
                        "reason": f"'{'+'.join(specs)}' 복합 특징 롱테일"
                    })
                else:
                    # 개별 특징 사용
                    spec = random.choice(specialty_list)
                    pattern = random.choice(patterns)
                    keyword = self._apply_pattern(pattern, location, modifiers)
                    keyword = keyword.replace(location, f"{location} {spec}", 1)
                    keywords.append({
                        "keyword": keyword,
                        "level": 5,
                        "reason": f"'{spec}' 특징 반영 롱테일"
                    })
            elif specialty_list:
                # specialty + 기본 조합
                spec = random.choice(specialty_list)
                base = random.choice(base_keywords)
                mod_keys = list(modifiers.keys()) if modifiers else ["추천", "베스트"]
                mod = random.choice(mod_keys) if isinstance(mod_keys[0], str) else "추천"
                keywords.append({
                    "keyword": f"{location} {spec} {base} {mod}",
                    "level": 5,
                    "reason": f"'{spec}' 특징 + {mod}"
                })
            else:
                # specialty 없는 경우 기존 로직
                base = random.choice(base_keywords)
                keywords.append({
                    "keyword": f"{location} {base} 추천 베스트",
                    "level": 5,
                    "reason": "롱테일 키워드"
                })

        # Level 4 - 니치 (10개) - specialty 필수 포함
        for i in range(10):
            if specialty_list and modifiers:
                # 다중 특징 중 랜덤 선택 + 수식어
                spec = random.choice(specialty_list)
                mod_type = random.choice(list(modifiers.keys()))
                mod_value = random.choice(modifiers[mod_type])
                base = random.choice(base_keywords)
                keywords.append({
                    "keyword": f"{location} {spec} {mod_value} {base}",
                    "level": 4,
                    "reason": f"'{spec}' + {mod_type}"
                })
            elif specialty_list:
                # specialty만 포함
                spec = random.choice(specialty_list)
                base = random.choice(base_keywords)
                keywords.append({
                    "keyword": f"{location} {spec} {base}",
                    "level": 4,
                    "reason": f"'{spec}' 특징 니치 키워드"
                })
            elif modifiers:
                # specialty 없는 경우 기존 로직
                mod_types = list(modifiers.keys())
                if len(mod_types) >= 2:
                    selected_types = random.sample(mod_types, 2)
                    mod1 = random.choice(modifiers[selected_types[0]])
                    mod2 = random.choice(modifiers[selected_types[1]])
                    base = random.choice(base_keywords)
                    keywords.append({
                        "keyword": f"{location} {mod1} {mod2} {base}",
                        "level": 4,
                        "reason": f"{selected_types[0]}+{selected_types[1]} 조합"
                    })
                else:
                    base = random.choice(base_keywords)
                    keywords.append({
                        "keyword": f"{location} {base} 추천",
                        "level": 4,
                        "reason": "니치 키워드"
                    })

        # Level 3 - 중간 (5개) - specialty 필수 포함
        for i, base in enumerate(base_keywords[:5]):
            if specialty_list:
                # 다중 특징 중 순차적으로 선택
                spec = specialty_list[i % len(specialty_list)]
                keywords.append({
                    "keyword": f"{location} {spec} {base}",
                    "level": 3,
                    "reason": f"지역 + '{spec}' + 업종"
                })
            elif modifiers:
                # specialty 없는 경우 기존 로직
                mod_type = random.choice(list(modifiers.keys()))
                mod_value = random.choice(modifiers[mod_type])
                keywords.append({
                    "keyword": f"{location} {mod_value} {base}",
                    "level": 3,
                    "reason": f"{mod_type} 반영"
                })
            else:
                keywords.append({
                    "keyword": f"{location} {base}",
                    "level": 3,
                    "reason": "중간 키워드"
                })

        # Level 2 - 경쟁 (3개) - specialty 우선 반영
        if specialty_list:
            # specialty 있으면 specialty 기반 Level 2
            if len(location_parts) >= 2:
                for spec in specialty_list[:3]:
                    keywords.append({
                        "keyword": f"{location_parts[0]} {spec} 맛집",
                        "level": 2,
                        "reason": f"광역 + specialty({spec}) 경쟁"
                    })
            else:
                for spec in specialty_list[:3]:
                    keywords.append({
                        "keyword": f"{location} {spec}",
                        "level": 2,
                        "reason": f"지역 + specialty({spec}) 경쟁"
                    })
        else:
            # specialty 없으면 기존 로직
            if len(location_parts) >= 2:
                for base in base_keywords[:3]:
                    keywords.append({
                        "keyword": f"{location_parts[0]} {base}",
                        "level": 2,
                        "reason": "광역 경쟁 키워드"
                    })
            else:
                for base in base_keywords[:3]:
                    keywords.append({
                        "keyword": f"{location} {base}",
                        "level": 2,
                        "reason": "경쟁 키워드"
                    })

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

        # Level 2 - 경쟁 (3개) - specialty 우선 반영
        if specialty_list:
            # specialty 있으면 specialty 기반 Level 2
            specs_for_level2 = specialty_list * 2  # 3개 키워드에 충분하도록 반복
            if len(location_parts) >= 2:
                keywords.extend([
                    {"keyword": f"{location_parts[0]} {specs_for_level2[0]} 맛집", "level": 2, "reason": f"광역 + '{specs_for_level2[0]}' 경쟁"},
                    {"keyword": f"{location_parts[0]} {specs_for_level2[1]}", "level": 2, "reason": f"광역 + '{specs_for_level2[1]}' 경쟁"},
                    {"keyword": f"{location_parts[0]} {specs_for_level2[2]} 추천", "level": 2, "reason": f"광역 + '{specs_for_level2[2]}' 추천"}
                ])
            else:
                keywords.extend([
                    {"keyword": f"{location} {specs_for_level2[0]}", "level": 2, "reason": f"지역 + '{specs_for_level2[0]}' 경쟁"},
                    {"keyword": f"{location} {specs_for_level2[1]} 맛집", "level": 2, "reason": f"'{specs_for_level2[1]}' 맛집"},
                    {"keyword": f"{location} {specs_for_level2[2]} 추천", "level": 2, "reason": f"'{specs_for_level2[2]}' 추천"}
                ])
        else:
            # specialty 없으면 기존 로직 (category 사용)
            if len(location_parts) >= 2:
                keywords.extend([
                    {"keyword": f"{location_parts[0]} {category}", "level": 2, "reason": "광역 경쟁 키워드"},
                    {"keyword": f"{location_parts[0]} {category} 추천", "level": 2, "reason": "광역 추천 키워드"},
                    {"keyword": f"{location_parts[0]} {category} 잘하는곳", "level": 2, "reason": "광역 품질 키워드"}
                ])
            else:
                keywords.extend([
                    {"keyword": f"{location} {category} 유명한", "level": 2, "reason": "경쟁 키워드"},
                    {"keyword": f"{location} {category} 인기", "level": 2, "reason": "경쟁 키워드"},
                    {"keyword": f"{location} {category} 베스트", "level": 2, "reason": "경쟁 키워드"}
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

    def _apply_pattern(self, pattern: str, location: str, modifiers: Dict) -> str:
        """패턴에 실제 값을 적용"""
        keyword = pattern.replace("{지역}", location)

        for mod_type, mod_values in modifiers.items():
            placeholder = f"{{{mod_type}}}"
            if placeholder in keyword:
                keyword = keyword.replace(placeholder, random.choice(mod_values))

        return keyword
