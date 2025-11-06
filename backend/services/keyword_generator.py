#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""키워드 생성 서비스"""

import random
from typing import List, Dict, Optional
from integrations.openai_api import OpenAIAPI
from integrations.naver_search_ad_api import NaverSearchAdAPI
from config.category_loader import CategoryLoader


class KeywordGeneratorService:
    """키워드 생성 서비스"""

    def __init__(self, openai_api: Optional[OpenAIAPI] = None, naver_ad_api: Optional[NaverSearchAdAPI] = None):
        self.openai_api = openai_api or OpenAIAPI()
        self.naver_ad_api = naver_ad_api or NaverSearchAdAPI()
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

        # Level 2 (경쟁) - 4개: 3가지 조합 (지역 + 특징 + 업종)
        base_location = location_parts[0] if len(location_parts) >= 2 else location
        detail_location = location_parts[1] if len(location_parts) >= 2 else location

        if all_specialty_related:
            # ✅ 3-way combinations ONLY (specialty required)
            # 1. 광역지역 + 특징 + 업종
            spec = all_specialty_related[0]
            if category.lower() in spec.lower():
                # specialty에 이미 업종 포함 (예: "해변카페")
                keywords.append({
                    "keyword": f"{base_location} {spec}",
                    "level": 2,
                    "reason": "경쟁: 광역+특성 (업종 포함)"
                })
            else:
                keywords.append({
                    "keyword": f"{base_location} {spec} {category}",
                    "level": 2,
                    "reason": "경쟁: 광역+특성+업종"
                })

            # 2. 상세지역 + 특징 + 업종
            spec2 = all_specialty_related[1 % len(all_specialty_related)]
            if category.lower() in spec2.lower():
                keywords.append({
                    "keyword": f"{detail_location} {spec2}",
                    "level": 2,
                    "reason": "경쟁: 상세지역+특성 (업종 포함)"
                })
            else:
                keywords.append({
                    "keyword": f"{detail_location} {spec2} {category}",
                    "level": 2,
                    "reason": "경쟁: 상세지역+특성+업종"
                })

            # 3. 전체지역명 + 특징 + 업종 (full location)
            spec3 = all_specialty_related[2 % len(all_specialty_related)]
            if category.lower() in spec3.lower():
                keywords.append({
                    "keyword": f"{location} {spec3}",
                    "level": 2,
                    "reason": "경쟁: 전체지역+특성 (업종 포함)"
                })
            else:
                keywords.append({
                    "keyword": f"{location} {spec3} {category}",
                    "level": 2,
                    "reason": "경쟁: 전체지역+특성+업종"
                })

            # 4. 상세지역 + 특징2 + 업종 (variant)
            spec4 = all_specialty_related[3 % len(all_specialty_related)]
            if category.lower() in spec4.lower():
                keywords.append({
                    "keyword": f"{detail_location} {spec4}",
                    "level": 2,
                    "reason": "경쟁: 상세지역+특성2 (업종 포함)"
                })
            else:
                keywords.append({
                    "keyword": f"{detail_location} {spec4} {category}",
                    "level": 2,
                    "reason": "경쟁: 상세지역+특성2+업종"
                })
        else:
            # specialty 없을 경우: 지역+업종관련어 조합
            keywords.extend([
                {"keyword": f"{base_location} {category_related[0]} {category}", "level": 2, "reason": "경쟁: 광역+관련어+업종"},
                {"keyword": f"{detail_location} {category_related[0]} {category}", "level": 2, "reason": "경쟁: 상세지역+관련어+업종"},
                {"keyword": f"{location} {category_related[1 % len(category_related)]} {category}", "level": 2, "reason": "경쟁: 전체지역+관련어+업종"},
                {"keyword": f"{base_location} {category_related[2 % len(category_related)]} {category}", "level": 2, "reason": "경쟁: 광역+관련어2+업종"}
            ])

        # Level 1 (최상위) - 2개: 2가지 조합 또는 1가지 단독, 검색량 기반 우선순위
        level1_candidates = []

        # ✅ Level 2 키워드 수집 (중복 방지용)
        level2_keywords = {kw["keyword"] for kw in keywords if kw["level"] == 2}

        # 후보 생성: 1-way (broadest) 및 2-way combinations
        # 1. 업종 단독 (1-way, 가장 광범위)
        level1_candidates.append({
            "keyword": category,
            "level": 1,
            "reason": "최상위: 업종 단독 (1-way, broadest)"
        })

        # 2. 광역지역 + 업종 (2-way)
        level1_candidates.append({
            "keyword": f"{base_location} {category}",
            "level": 1,
            "reason": "최상위: 광역+업종 (2-way)"
        })

        # 3. 특징 + 업종 (2-way)
        if all_specialty_related:
            for i, spec in enumerate(all_specialty_related[:3]):
                # specialty 관련어에 이미 category가 포함되어 있으면 단독 사용
                if category.lower() in spec.lower():
                    level1_candidates.append({
                        "keyword": spec,
                        "level": 1,
                        "reason": f"최상위: 특성 단독 (업종 포함, 1-way)"
                    })
                else:
                    level1_candidates.append({
                        "keyword": f"{spec} {category}",
                        "level": 1,
                        "reason": f"최상위: 특성+업종 (2-way)"
                    })

        # 4. 업종 관련어 (1-way)
        for cat in category_related[:2]:
            level1_candidates.append({
                "keyword": cat,
                "level": 1,
                "reason": "최상위: 업종관련어 (1-way)"
            })

        # ✅ Level 2와 중복되는 키워드 제거
        level1_candidates = [
            kw for kw in level1_candidates
            if kw["keyword"] not in level2_keywords
        ]

        # 검색량 기반 정렬로 상위 2개 선택
        sorted_level1 = self._sort_by_search_volume(level1_candidates)
        keywords.extend(sorted_level1[:2])

        return keywords

    def _sort_by_search_volume(self, candidates: List[Dict]) -> List[Dict]:
        """
        검색량 기반으로 키워드 정렬

        Args:
            candidates: 후보 키워드 리스트

        Returns:
            검색량 순으로 정렬된 키워드 리스트
        """
        if not candidates:
            return candidates

        # 네이버 검색광고 API가 인증되지 않았으면 원본 순서 반환
        if not self.naver_ad_api.is_authenticated:
            print("⚠️ 네이버 검색광고 API 미인증 - Level 1 검색량 정렬 생략")
            return candidates

        try:
            # 키워드 목록 추출
            keyword_texts = [kw["keyword"] for kw in candidates]

            # 검색량 조회
            stats = self.naver_ad_api.get_keyword_stats(keyword_texts)

            # 검색량 매핑 생성
            search_volumes = {}
            for stat in stats:
                parsed = self.naver_ad_api.parse_keyword_data(stat)
                if parsed:
                    search_volumes[parsed["keyword"]] = parsed["monthly_total_searches"]

            # 검색량 정보 추가 및 정렬
            for candidate in candidates:
                kw_text = candidate["keyword"]
                volume = search_volumes.get(kw_text, 0)
                candidate["search_volume"] = volume

            # 검색량 기준 내림차순 정렬
            sorted_candidates = sorted(
                candidates,
                key=lambda x: x.get("search_volume", 0),
                reverse=True
            )

            # 정렬 결과 로깅
            print(f"   📊 Level 1 검색량 정렬 완료:")
            for i, kw in enumerate(sorted_candidates[:5], 1):
                volume = kw.get("search_volume", 0)
                print(f"      {i}. {kw['keyword']}: {volume:,}회/월")

            return sorted_candidates

        except Exception as e:
            print(f"⚠️ 검색량 정렬 실패: {e} - 원본 순서 반환")
            return candidates

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
