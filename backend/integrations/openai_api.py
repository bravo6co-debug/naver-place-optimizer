#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI GPT API 통합
키워드 생성 및 전략 제안
"""

import os
import json
from typing import Optional, List, Dict
from openai import OpenAI


class OpenAIAPI:
    """OpenAI GPT API 클라이언트"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def generate_keywords(
        self,
        category: str,
        location: str,
        specialty: Optional[str] = None,
        modifier_examples: Optional[str] = None
    ) -> List[Dict]:
        """
        GPT를 사용한 키워드 생성

        Args:
            category: 업종
            location: 지역
            specialty: 특징/전문분야
            modifier_examples: 업종별 수식어 예시

        Returns:
            생성된 키워드 리스트
        """
        if not self.client:
            return []

        prompt = self._build_keyword_prompt(category, location, specialty, modifier_examples)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # ✅ GPT-4 full version으로 변경 (정확도 향상)
                messages=[
                    {"role": "system", "content": "You are a Naver Place SEO expert. Always respond in Korean with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # ✅ 창의성 증가
                max_tokens=3500  # ✅ 토큰 증가 (35개 키워드 생성)
            )

            content = response.choices[0].message.content
            keywords = self._parse_json_response(content)

            # ✅ 1단계: 형편없는 키워드 필터링 (자동 제거)
            keywords = self._filter_bad_keywords(keywords, category, location)

            # ✅ 2단계: specialty 포함 여부 검증 (경고 + 제거)
            if specialty:
                keywords = self.validate_specialty_inclusion(keywords, specialty)

            return keywords

        except Exception as e:
            print(f"OpenAI API 호출 실패: {e}")
            return []

    def _get_level2_examples(self, location: str, category: str, specialty_list: list) -> str:
        """Level 2 키워드 예시 생성"""
        base_location = location.split()[0] if " " in location else location

        if specialty_list:
            return f'"{base_location} {specialty_list[0]} 맛집", "{base_location} {specialty_list[0]}"'
        else:
            return f'"{base_location} {category}"'

    def _get_level1_examples(self, location: str, category: str, specialty_list: list) -> str:
        """Level 1 키워드 예시 생성 - Level 2와 차별화"""
        if specialty_list:
            # Level 1: 지역 제거, specialty 중심
            if len(specialty_list) > 1:
                return f'"{specialty_list[0]} 맛집", "{specialty_list[1]}"'
            else:
                return f'"{specialty_list[0]} 맛집", "{specialty_list[0]} {category}"'
        else:
            return f'"{category}", "{category} 추천"'

    def _build_keyword_prompt(
        self,
        category: str,
        location: str,
        specialty: Optional[str],
        modifier_examples: Optional[str]
    ) -> str:
        """키워드 생성 프롬프트 구성"""

        # specialty 파싱: 컴마로 구분된 여러 특징 처리
        specialty_list = []
        if specialty:
            specialty_list = [s.strip() for s in specialty.split(',') if s.strip()]

        # specialty 필수 강조
        specialty_emphasis = ""
        if specialty_list:
            if len(specialty_list) == 1:
                specialty_emphasis = f"""
🎯 **핵심 차별화 요소 (MANDATORY)**: {specialty_list[0]}
⚠️ **중요**: 모든 키워드에 이 특징({specialty_list[0]})을 필수로 포함하거나, 이 특징과 관련된 검색 의도를 반영해야 합니다.

예시:
- "{location} {specialty_list[0]} {category}" ✓
- "{location} {specialty_list[0]} 전문 {category}" ✓
- "{location} {category}" ✗ (특징 누락)
"""
            else:
                specialty_str = ', '.join(specialty_list)
                specialty_emphasis = f"""
🎯 **핵심 차별화 요소 (MANDATORY)**: {specialty_str}
⚠️ **중요**: 이 업체는 여러 특징을 가지고 있습니다. 키워드 생성 시 다음 전략을 사용하세요:

1. **개별 특징 활용**: 각 특징을 개별적으로 키워드에 포함
   - 예: "{location} {specialty_list[0]} {category}"
   - 예: "{location} {specialty_list[1]} {category}"

2. **특징 조합 활용**: 2-3개 특징을 조합하여 차별화
   - 예: "{location} {specialty_list[0]} {specialty_list[1]} {category}"
   - 예: "{location} {' '.join(specialty_list[:2])} {category}"

3. **자연스러운 표현**: 실제 검색어처럼 자연스럽게
   - 예: "{location} {specialty_list[0]}도 되고 {specialty_list[1]}도 되는 {category}"

⚠️ **필수**: 각 키워드는 최소 1개 이상의 특징을 반드시 포함해야 합니다.
"""
        else:
            specialty_emphasis = """
⚠️ **특징이 제공되지 않았습니다.** 업종의 일반적인 차별화 요소를 고려하여 키워드를 생성하세요.
"""

        specialty_str = ', '.join(specialty_list) if specialty_list else "없음"

        prompt = f"""당신은 네이버 플레이스 검색 최적화 전문가입니다.
**실제 사람들이 검색하는** 키워드를 생성하세요.

**사용자 입력:**
- category: {category}
- location: {location}
- specialty: {specialty_str}

{specialty_emphasis}

**출력 형식**: JSON 객체 (코드블록 없이 순수 JSON)
키: `longtail_keywords`, `mid_keywords`, `category_keywords`, `top_keywords`

---

## ✅ 좋은 키워드 (GOOD - 이렇게 생성하세요!)

**롱테일 (자연스러운 검색어):**
- ✅ "강남역 데이트하기 좋은 {specialty} 카페"
- ✅ "강남 조용한 공부 카페 {specialty} 되는 곳"
- ✅ "신논현역 근처 {specialty} 맛집 카페 추천"
- ✅ "강남역 3번출구 {specialty} 카페 어디있어요"

**니치 (실전 조합):**
- ✅ "강남역 {specialty} 카페"
- ✅ "강남 {specialty} 카페 추천"
- ✅ "신논현 {specialty} 맛집"

---

## ❌ 나쁜 키워드 (BAD - 절대 생성 금지!)

**일반적이고 형편없는 키워드:**
- ❌ "{location} 최고 {category}" (너무 추상적)
- ❌ "{location} 프리미엄 {category}" (의미 없음)
- ❌ "{location} 고급 {category}" (실제 검색 안 함)
- ❌ "{location} 전문 {category}" (너무 일반적)
- ❌ "{location} 유명한 {category}" (구체성 없음)

**specialty 없는 키워드:**
- ❌ "{location} {category}" (specialty 누락)
- ❌ "{location} {category} 추천" (specialty 없음)

---

## 📋 생성 요구사항

**longtail_keywords** (정확히 15개):
- 실제 사람들이 검색하는 **자연스러운 문장**
- 목적 포함 (데이트, 공부, 회의, 혼자, 가족 등)
- 세부 지역 사용 (강남역, 신논현역, 압구정 등)
- 조사 포함 ("-하기 좋은", "-되는 곳", "어디있어요" 등)
- **specialty 필수 포함**

**예시:**
- "{location}역 데이트하기 좋은 {specialty} {category}"
- "{location} 조용한 {specialty} {category} 추천"
- "{location}역 근처 {specialty} 맛집 {category} 어디?"

**mid_keywords** (정확히 10개):
- 중간 길이 실전 키워드
- 세부 지역 + specialty + category 조합
- **specialty 필수 포함**

**예시:**
- "{location}역 {specialty} {category}"
- "{location} {specialty} 맛집"
- "{location} {specialty} {category} 추천"

**category_keywords** (정확히 7개):
- 업종 관련 키워드
- specialty 포함한 업종 조합
- 동의어, 하위 업종

**예시:**
- "{specialty} {category}"
- "{specialty} 전문 {category}"
- "{category} (동의어)"

**top_keywords** (정확히 3개):
- 광범위한 상위 키워드
- specialty 포함 가능 (선택)

**예시:**
- "{category}"
- "{specialty} {category}"
- "광역지역 {category}"

---

## 🎯 핵심 규칙

1. **specialty 필수 포함** (longtail, mid, category에 특히 중요)
2. **실제 검색어** 생성 ("최고", "프리미엄" 같은 쓰레기 금지)
3. **세부 지역 사용** (강남역, 신논현역, 압구정 등)
4. **목적 키워드** 포함 (데이트, 공부, 회의 등)
5. **자연스러운 조사** 포함 (-하기 좋은, -되는 곳 등)
6. **총 35개 정확히** 생성 (15+10+7+3)

---

**출력 예시** (category=카페, location=서울 강남구, specialty=브런치, 애견동반):
{{
  "longtail_keywords": [
    "강남역 데이트하기 좋은 브런치 카페",
    "강남 조용한 공부 카페 애견동반 되는 곳",
    "신논현역 근처 브런치 맛집 카페 추천",
    "강남역 3번출구 애견동반 카페 어디있어요",
    "압구정 브런치 맛있는 강아지 동반 카페",
    "강남 혼자 가기 좋은 브런치 카페 애견 가능",
    "강남역 주차 가능한 애견동반 브런치 카페",
    "신논현 반려견 동반 브런치 맛집 추천",
    "강남 애견 카페 브런치 하기 좋은 곳",
    "강남역 근처 강아지 데리고 갈 수 있는 브런치 카페",
    "압구정로데오 브런치 카페 애견동반 되나요",
    "강남 브런치 맛집 강아지 동반 가능한 곳",
    "신논현역 도보 5분 애견동반 브런치 카페",
    "강남 인스타 감성 브런치 카페 애견 가능",
    "강남역 테라스 있는 애견동반 브런치 카페"
  ],
  "mid_keywords": [
    "강남역 브런치 카페",
    "강남 애견동반 카페",
    "신논현 브런치 맛집",
    "강남역 애견 카페",
    "압구정 브런치 카페",
    "강남 강아지 동반 카페",
    "강남역 브런치 맛집",
    "신논현 애견동반 카페",
    "강남 브런치 애견 카페",
    "압구정 애견동반 브런치"
  ],
  "category_keywords": [
    "브런치 카페",
    "애견동반 카페",
    "강아지 카페",
    "반려견 카페",
    "펫프렌들리 카페",
    "브런치 맛집",
    "커피숍"
  ],
  "top_keywords": [
    "카페",
    "브런치",
    "애견 카페"
  ]
}}

**중요**: 반드시 순수 JSON만 출력하세요. 설명이나 주석 없이!"""

        return prompt

    def _parse_json_response(self, content: str) -> List[Dict]:
        """GPT 응답에서 JSON 파싱 (새 형식 → 기존 level 형식 변환)"""
        try:
            # 코드 블록 제거
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            # 새 형식인지 확인 (longtail_keywords, mid_keywords 등의 키 존재)
            if isinstance(data, dict) and "longtail_keywords" in data:
                # 새 형식 → 기존 level 형식으로 변환
                keywords = []

                # longtail_keywords → Level 5
                for kw in data.get("longtail_keywords", []):
                    keywords.append({"keyword": kw, "level": 5, "reason": "롱테일 검색어"})

                # mid_keywords → Level 4
                for kw in data.get("mid_keywords", []):
                    keywords.append({"keyword": kw, "level": 4, "reason": "니치 검색어"})

                # category_keywords → Level 3
                for kw in data.get("category_keywords", []):
                    keywords.append({"keyword": kw, "level": 3, "reason": "카테고리 검색어"})

                # top_keywords → Level 2, Level 1로 분할
                top_kws = data.get("top_keywords", [])
                if len(top_kws) >= 2:
                    keywords.append({"keyword": top_kws[0], "level": 2, "reason": "상위 검색어"})
                    keywords.append({"keyword": top_kws[1], "level": 1, "reason": "최상위 검색어"})
                elif len(top_kws) == 1:
                    keywords.append({"keyword": top_kws[0], "level": 2, "reason": "상위 검색어"})

                return keywords

            # 기존 형식 (list of dicts with level)
            return data

        except Exception as e:
            print(f"JSON 파싱 실패: {e}")
            return []

    def generate_related_keywords(
        self,
        category: str,
        specialty: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        GPT를 사용한 연관 키워드 생성 (조합하지 않고 연관어만)

        Args:
            category: 업종 (예: "카페", "병원")
            specialty: 특징/전문분야 (콤마로 구분, 예: "브런치, 애견동반")

        Returns:
            연관 키워드 딕셔너리
            {
                "category_related": ["커피숍", "디저트카페", "베이커리카페", "티하우스", "북카페"],
                "specialty1_related": ["브런치맛집", "아침식사", "모닝식사", "조식", "브런치메뉴"],
                "specialty2_related": ["반려동물", "강아지동반", "펫프렌들리", "애견카페", "반려견"]
            }
        """
        if not self.client:
            return {}

        specialty_list = []
        if specialty:
            specialty_list = [s.strip() for s in specialty.split(',') if s.strip()]

        specialty_str = ', '.join(specialty_list) if specialty_list else "없음"

        prompt = f"""당신은 네이버 플레이스 검색 최적화 전문가입니다.
주어진 업종과 특성에 대한 **연관 키워드**만 생성하세요. (조합하지 말 것!)

**입력:**
- category: {category}
- specialty: {specialty_str}

**출력 형식**: JSON 객체 (코드블록 없이 순수 JSON)

**규칙:**
1. category에 대한 연관 키워드 5개 생성 → "category_related" 키
   - 동의어, 하위 업종, 유사 업종 포함
   - 예: category="카페" → ["커피숍", "디저트카페", "베이커리카페", "티하우스", "북카페"]

2. specialty가 있으면 각 특성마다 연관 키워드 5개씩 생성 → "specialty1_related", "specialty2_related" 등의 키
   - 동의어, 관련 표현, 검색 의도 키워드 포함
   - 예: specialty="브런치" → ["브런치맛집", "아침식사", "모닝식사", "조식", "브런치메뉴"]
   - 예: specialty="애견동반" → ["반려동물", "강아지동반", "펫프렌들리", "애견카페", "반려견"]

3. **중요**: 조합하지 말고 단일 키워드만 생성할 것!
   - ✅ Good: "브런치맛집", "강아지동반"
   - ❌ Bad: "브런치 강아지동반 카페", "홍대 브런치"

**출력 예시 1** (category=카페, specialty=브런치, 애견동반):
{{
  "category_related": ["커피숍", "디저트카페", "베이커리카페", "티하우스", "북카페"],
  "specialty1_related": ["브런치맛집", "아침식사", "모닝식사", "조식", "브런치메뉴"],
  "specialty2_related": ["반려동물", "강아지동반", "펫프렌들리", "애견카페", "반려견동반"]
}}

**출력 예시 2** (category=병원, specialty=안과):
{{
  "category_related": ["의료기관", "종합병원", "클리닉", "의원", "진료소"],
  "specialty1_related": ["안과의원", "눈병원", "시력교정", "라식", "안과진료"]
}}

**출력 예시 3** (category=카페, specialty 없음):
{{
  "category_related": ["커피숍", "디저트카페", "베이커리카페", "티하우스", "북카페"]
}}

이제 입력된 정보로 연관 키워드를 생성하세요:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Naver Place SEO expert. Always respond in Korean with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            content = response.choices[0].message.content

            # 코드 블록 제거
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            related_keywords = json.loads(content.strip())
            return related_keywords

        except Exception as e:
            print(f"연관 키워드 생성 실패: {e}")
            return {}

    def _filter_bad_keywords(
        self,
        keywords: List[Dict],
        category: str,
        location: str
    ) -> List[Dict]:
        """
        형편없는 키워드 패턴 자동 제거

        Args:
            keywords: 생성된 키워드 리스트
            category: 업종
            location: 지역

        Returns:
            필터링된 키워드 리스트
        """
        # 쓰레기 단어 목록 (실제로 사람들이 검색 안 하는 단어들)
        BAD_WORDS = [
            "최고", "프리미엄", "고급", "베테랑", "숙련",
            "전문가", "명인", "달인", "장인"
        ]

        # 너무 일반적인 패턴
        BAD_PATTERNS = [
            f"{location} {category}",  # specialty 없는 기본 조합
            f"{location} 유명한 {category}",
            f"{location} 인기 {category}",
        ]

        filtered = []
        removed_count = 0

        for kw in keywords:
            keyword_text = kw.get('keyword', '')
            level = kw.get('level', 5)

            # 쓰레기 단어 포함 여부 확인
            has_bad_word = any(bad_word in keyword_text for bad_word in BAD_WORDS)

            # 나쁜 패턴 정확히 일치 확인
            is_bad_pattern = keyword_text in BAD_PATTERNS

            # Level 3-5는 specialty 필수 (specialty 없으면 너무 일반적)
            # Level 1-2는 광범위해도 OK
            is_too_generic = (level >= 3) and (keyword_text == f"{location} {category}" or keyword_text == f"{location} {category} 추천")

            if has_bad_word:
                print(f"❌ [필터링] '{keyword_text}' - 쓰레기 단어 포함")
                removed_count += 1
                continue

            if is_bad_pattern:
                print(f"❌ [필터링] '{keyword_text}' - 나쁜 패턴")
                removed_count += 1
                continue

            if is_too_generic:
                print(f"❌ [필터링] '{keyword_text}' - 너무 일반적 (Level {level})")
                removed_count += 1
                continue

            # 통과한 키워드만 추가
            filtered.append(kw)

        if removed_count > 0:
            print(f"✅ 총 {removed_count}개 형편없는 키워드 제거됨")

        return filtered

    def validate_specialty_inclusion(
        self,
        keywords: List[Dict],
        specialty: Optional[str]
    ) -> List[Dict]:
        """
        specialty가 제공된 경우 키워드에 포함 여부 검증 (단계적 기준)

        Args:
            keywords: 생성된 키워드 리스트
            specialty: 특징/전문분야

        Returns:
            검증된 키워드 리스트 (경고 포함)
        """
        if not specialty:
            return keywords

        specialty_list = [s.strip() for s in specialty.split(',') if s.strip()]
        if not specialty_list:
            return keywords

        # Level별 specialty 포함 카운트
        level_stats = {1: {"total": 0, "with_specialty": 0},
                       2: {"total": 0, "with_specialty": 0},
                       3: {"total": 0, "with_specialty": 0},
                       4: {"total": 0, "with_specialty": 0},
                       5: {"total": 0, "with_specialty": 0}}

        validated = []
        for kw in keywords:
            keyword_text = kw.get('keyword', '')
            level = kw.get('level', 5)

            # specialty 포함 여부 확인
            has_specialty = any(spec.lower() in keyword_text.lower() for spec in specialty_list)

            level_stats[level]["total"] += 1
            if has_specialty:
                level_stats[level]["with_specialty"] += 1

            # Level 1-2는 100% 필수
            if not has_specialty and level <= 2:
                print(f"⚠️ [CRITICAL] Level {level} 키워드 '{keyword_text}'에 특징({', '.join(specialty_list)}) 누락 (필수!)")

            validated.append(kw)

        # Level별 포함률 검증
        thresholds = {1: 1.0, 2: 1.0, 3: 0.8, 4: 0.7, 5: 0.6}
        for level, stats in level_stats.items():
            if stats["total"] > 0:
                rate = stats["with_specialty"] / stats["total"]
                threshold = thresholds[level]
                if rate < threshold:
                    print(f"⚠️ Level {level} specialty 포함률: {rate:.1%} (목표: {threshold:.0%}) - {stats['with_specialty']}/{stats['total']}개")

        return validated
