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
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Naver Place SEO expert. Always respond in Korean with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            keywords = self._parse_json_response(content)

            # specialty 포함 여부 검증 (경고만 표시, 키워드는 유지)
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
사용자 입력에 맞는 **현실적이고 자연스러운** 키워드 목록을 생성하세요.

**사용자 입력:**
- category: {category}
- location: {location}
- specialty: {specialty_str}

**출력 형식**: JSON 객체 (코드블록 없이 순수 JSON). 키는 `longtail_keywords`, `mid_keywords`, `category_keywords`, `top_keywords`의 4가지이며, 각 값은 해당 유형의 키워드 문자열들을 요소로 갖는 배열입니다.

**longtail_keywords** (5~10개): 구체적인 **한국어 롱테일 검색어**로, 세부 지역명, 목적이나 질문 형태, 조사가 포함된 **자연스러운 문장**입니다. 구어체 표현도 허용됩니다. **각 키워드에는 specialty 목록 중 최소 하나의 요소를 포함**해야 하며 (동의어나 유사 표현으로 변형 가능), 명사만 나열하는 형태는 피해주세요.
  *예시*: "홍대 애견동반 브런치 카페 추천", "강남역에서 수면내시경 잘하는 내과 어디인가요"

**mid_keywords** (3~5개): **업종+지역** 또는 **지역+특성** 등의 조합으로 이루어진 키워드입니다. 일반적인 검색어 형태로 **짧게** 표현하되, 의미 전달을 위해 필요한 경우 일부 조사를 포함할 수 있습니다. 각 키워드 역시 **specialty 중 하나 이상을 포함**해야 합니다.
  *예시*: "홍대 애견동반 카페", "강남역 수면내시경 내과"

**category_keywords** (2~3개): 입력된 업종을 중심으로 한 **일반적인 키워드**입니다. 해당 업종의 흔한 **동의어**나 **하위 업종**(특정 특성을 포함한 업종)을 포함할 수 있습니다. 가능하면 specialty에 해당하는 요소를 포함한 조합을 사용하세요.
  *예시*: 카페 업종의 경우 ["브런치 카페", "애견동반 카페"] *(동일 업종의 동의어 "커피숍" 등도 고려 가능)*

**top_keywords** (1~2개): 가장 단순하고 핵심적인 **상위 키워드**입니다. 한두 단어로 구성하며 너무 구체적이지 않게 합니다. 전국 단위로 검색할 법한 **광범위한 업종 관련 용어**를 선택하세요 (필요에 따라 specialty를 포함할 수 있으나 생략 가능).
  *예시*: ["카페"], ["내과"]

**추가 규칙**:
- 모든 범주의 키워드에서 **specialty 목록의 최소 한 가지 특성**이 반드시 포함되어야 합니다. (특성을 나타내는 단어는 **동의어나 유사한 표현**으로 바꾸어 사용할 수 있습니다.)
- specialty에 없는 다른 전문분야나 특성은 절대 사용 금지
- 출력은 **항상 유효한 JSON 객체** 형식이어야 하며, 요구된 4개 키를 모두 포함해야 합니다.
- JSON 외의 불필요한 텍스트는 출력하지 마세요.

**출력 예시** (category=카페, location=홍대, specialty=애견동반, 브런치):
{{
  "longtail_keywords": [
    "홍대에 있는 애견동반 브런치 카페 추천해줘",
    "홍대 애견동반 카페 중에 브런치 맛있는 곳은?",
    "홍대 브런치 가능한 강아지동반 카페 어디 있을까?",
    "홍대 애견 동반 카페 찾아보기 (브런치 가능한 곳)",
    "홍대 브런치 카페 - 애견동반 되는데 어디가 좋지?"
  ],
  "mid_keywords": [
    "홍대 애견동반 카페",
    "홍대 브런치 카페",
    "홍대 애견 카페 브런치"
  ],
  "category_keywords": [
    "브런치 카페",
    "애견동반 카페",
    "커피숍"
  ],
  "top_keywords": [
    "카페",
    "애견 카페"
  ]
}}"""

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
