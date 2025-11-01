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
            return self._parse_json_response(content)

        except Exception as e:
            print(f"OpenAI API 호출 실패: {e}")
            return []

    def _build_keyword_prompt(
        self,
        category: str,
        location: str,
        specialty: Optional[str],
        modifier_examples: Optional[str]
    ) -> str:
        """키워드 생성 프롬프트 구성"""

        # specialty 필수 강조
        specialty_emphasis = ""
        if specialty:
            specialty_emphasis = f"""
🎯 **핵심 차별화 요소 (MANDATORY)**: {specialty}
⚠️ **중요**: 모든 키워드에 이 특징({specialty})을 필수로 포함하거나, 이 특징과 관련된 검색 의도를 반영해야 합니다.

예시:
- "{location} {specialty} {category}" ✓
- "{location} {specialty} 전문 {category}" ✓
- "{location} {category}" ✗ (특징 누락)
"""
        else:
            specialty_emphasis = """
⚠️ **특징이 제공되지 않았습니다.** 업종의 일반적인 차별화 요소를 고려하여 키워드를 생성하세요.
"""

        prompt = f"""당신은 네이버 플레이스 검색 최적화 전문가입니다. 실제 사용자들이 검색하는 자연스러운 키워드를 생성해주세요.

📍 **기본 정보**
업종: {category}
지역: {location}
{specialty_emphasis}
{modifier_examples if modifier_examples else ''}

🔍 **검색 의도 반영 요소**
- 목적 (데이트, 회식, 공부, 운동 등)
- 시간대 (아침, 점심, 저녁, 야간 등)
- 대상 (혼자, 가족, 친구, 연인 등)
- 상황 (기념일, 비오는날, 주말, 평일 등)

📊 **5단계 난이도별 키워드 생성**

**Level 5 (롱테일 - 가장 쉬움) - 15개:**
- 매우 구체적인 검색어 (4-6단어)
- {f'"{specialty}" 특징 + 목적/상황/대상 조합 필수' if specialty else '구체적 목적/상황/대상 조합'}
- 예: "{location} {specialty if specialty else category} 데이트 추천 분위기 좋은"

**Level 4 (니치) - 10개:**
- 구체적 니즈 반영 (3-4단어)
- {f'"{specialty}" 특징 + 1-2개 수식어' if specialty else '2-3개 특성 조합'}
- 예: "{location} {specialty if specialty else category} 가성비 좋은"

**Level 3 (중간) - 5개:**
- 일반적 조합 (2-3단어)
- {f'지역 + "{specialty}" + 업종' if specialty else '지역 + 특징 + 업종'}
- 예: "{location} {specialty if specialty else '맛있는'} {category}"

**Level 2 (경쟁) - 3개:**
- 핵심 키워드 (2단어)
- {f'광역 지역 + "{specialty}"' if specialty else '광역 지역 + 업종/특징'}
- 예: "{location.split()[0] if ' ' in location else location} {specialty if specialty else category}"

**Level 1 (최상위 - 가장 어려움) - 2개:**
- 초경쟁 키워드 (1-2단어)
- 광역 지역 + 업종
- 예: "{location.split()[0] if ' ' in location else location} {category}"

⚠️ **반드시 지켜야 할 규칙:**
1. Level 5, 4, 3에서는 특징({specialty if specialty else '차별화 요소'})을 **필수**로 포함
2. 모든 키워드는 실제 사용자가 검색할 법한 자연스러운 표현 사용
3. 동일한 패턴 반복 금지 (다양한 조합 사용)

📤 **JSON 형식으로 반환:**
[
  {{"keyword": "정확한 키워드", "level": 5, "reason": "구체적인 선정 이유"}},
  ...
]

총 35개의 키워드를 생성해주세요."""

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
