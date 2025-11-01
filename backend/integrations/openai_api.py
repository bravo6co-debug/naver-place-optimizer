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
        """Level 1 키워드 예시 생성"""
        base_location = location.split()[0] if " " in location else location

        if specialty_list:
            second_specialty = specialty_list[1] if len(specialty_list) > 1 else specialty_list[0]
            return f'"{base_location} {specialty_list[0]}", "{base_location} {second_specialty}"'
        else:
            return f'"{base_location} {category}"'

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

        prompt = f"""당신은 네이버 플레이스 로컬 서치 최적화 전문가입니다.
입력은 오직 3개입니다: category(업종), location(지역), specialty(특성: 콤마 구분).
이 3개만으로, 실제 모바일 검색에서 자주 쓰일 한국어 키워드 34개를 생성하세요.

📍 **기본 정보**
업종: {category}
지역: {location}
{specialty_emphasis}
{modifier_examples if modifier_examples else ''}

[내부 자동 추론 규칙 – 모델이 스스로 수행]
1) 지리 계층 확장:
   - location을 광역/구·동/상권/역세권으로 분해/변형.
   - 잘 알려진 상권·역 이름을 location에서 자연스럽게 축약(예: "부산 수영구 대연동"→"부산","수영구","대연동","경성대").
   - “근처/역/역세권/사거리/로데오” 같은 일반화 표현을 일부 혼합.

2) 의도 버킷 채우기(균형 분포):
   - 가격/가성비, 좌석/룸/단체, 주차/대중교통 접근, 영업시간/야간/24시, 예약/대기,
     포장/배달, 리뷰/평점, 데이트/가족/회식 중 최소 각 1회 이상 반영.
   - 조사 생략·구어체·숫자(24시)·붙여쓰기/띄어쓰기 변형 허용(가성비좋은/가성비 좋은).

3) 특성 주입:
   - specialty가 제공된 경우: 모든 Level의 키워드는 specialty 항목 중 최소 1개 이상 반드시 포함.
   - specialty가 없는 경우: 업종 일반 강점(맛있는/잘하는/가성비/조용한 등) 사용.

4) 안전/정책:
   - 채용/알바/무료/과도한 할인율 등 정책 리스크 표현 제외.
   - 중복 패턴 과다 반복 금지(동일 접두/접미 2회 초과 불가).

📊 **5단계 난이도별 키워드 생성**

**Level 5 (롱테일 - 가장 쉬움) - 15개:**
- 매우 구체적인 검색어 (4-6단어)
- {f'특징({", ".join(specialty_list)}) + 목적/상황/대상 조합 필수' if specialty_list else '구체적 목적/상황/대상 조합'}
- 예: "{location} {specialty_list[0] if specialty_list else category} 데이트 추천 분위기 좋은"

**Level 4 (니치) - 10개:**
- 구체적 니즈 반영 (3-4단어)
- {f'특징({", ".join(specialty_list)}) 중 1-2개 + 수식어' if specialty_list else '2-3개 특성 조합'}
- 예: "{location} {specialty_list[0] if specialty_list else category} 가성비 좋은"

**Level 3 (중간) - 5개:**
- 일반적 조합 (2-3단어)
- {f'지역 + 특징({", ".join(specialty_list)}) + 업종' if specialty_list else '지역 + 특징 + 업종'}
- 예: "{location} {specialty_list[0] if specialty_list else '맛있는'} {category}"

**Level 2 (경쟁) - 2개:**
- 핵심 키워드 (2-3단어)
- {f'광역 지역 + 특징({", ".join(specialty_list)}) 필수!' if specialty_list else '광역 지역 + 업종'}
- 예: {self._get_level2_examples(location, category, specialty_list)}
- ❌ 절대 금지: 특징 누락 (specialty 있을 때)

**Level 1 (최상위 - 가장 어려움) - 2개:**
- 초경쟁 키워드 (1-2단어)
- {f'광역 지역 + 특징({", ".join(specialty_list)}) 필수!' if specialty_list else '광역 지역 + 업종'}
- 예: {self._get_level1_examples(location, category, specialty_list)}
- ❌ 절대 금지: 특징 누락 (specialty 있을 때)

⚠️ **반드시 지켜야 할 규칙:**
1. Level 1-5 모두 특징(specialty)이 있으면 **필수**로 포함 (특히 Level 1-2는 specialty만 사용!)
2. 모든 키워드는 실제 사용자가 검색할 법한 자연스러운 표현 사용
3. 동일한 패턴 반복 금지 (특징 조합을 다양하게 사용)

📤 **JSON 형식으로 반환:**
[
  {{"keyword": "정확한 키워드", "level": 5, "reason": "구체적인 선정 이유"}},
  ...
]

총 34개의 키워드를 생성해주세요."""

        return prompt

    def _parse_json_response(self, content: str) -> List[Dict]:
        """GPT 응답에서 JSON 파싱"""
        try:
            # 코드 블록 제거
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            keywords = json.loads(content.strip())
            return keywords

        except Exception as e:
            print(f"JSON 파싱 실패: {e}")
            return []

    def validate_specialty_inclusion(
        self,
        keywords: List[Dict],
        specialty: Optional[str]
    ) -> List[Dict]:
        """
        specialty가 제공된 경우 키워드에 포함 여부 검증

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

        validated = []
        for kw in keywords:
            keyword_text = kw.get('keyword', '')
            level = kw.get('level', 5)

            # specialty 포함 여부 확인
            has_specialty = any(spec.lower() in keyword_text.lower() for spec in specialty_list)

            if not has_specialty and level <= 3:
                # Level 1-3는 specialty 필수
                print(f"⚠️ [specialty 누락] Level {level} 키워드 '{keyword_text}'에 특징({', '.join(specialty_list)}) 누락")

            validated.append(kw)

        return validated
