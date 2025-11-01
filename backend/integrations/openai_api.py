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

        prompt = f"""당신은 네이버 플레이스 로컬 서치 최적화 전문가입니다.
입력은 오직 3개입니다: category(업종), location(지역), specialty(특성: 콤마 구분).
이 3개만으로, 실제 모바일 검색에서 자주 쓰일 **자연스러운 한국어** 키워드 34개를 생성하세요.

📍 **기본 정보**
업종: {category}
지역: {location}
{specialty_emphasis}
{modifier_examples if modifier_examples else ''}

📚 **생성 예시 (Few-Shot Learning - 반드시 학습하세요!):**

[Good Example - Level 5 롱테일]
✅ "강남역 10번출구 근처에서 브런치 먹기 좋은 조용한 카페"
   → 구체적 위치 + "에서" 조사 + 목적("먹기 좋은") + 분위기
✅ "부산 중구 혼자 가기 좋은 떡볶이집 추천"
   → 자연스러운 어순, 조사 생략 가능, 구어체
✅ "서울 강남구 안과 주말 진료 잘하는 병원" (specialty=안과)
   → specialty "안과"를 정확히 포함, 다른 전문분야 사용 안함
❌ "강남역 브런치 카페 추천 베스트 맛집"
   → 조사 없음, 키워드만 나열, 부자연스러움
❌ "서울 강남구 안과 치료 잘보는 **피부과**" (specialty=안과인데 피부과 사용)
   → specialty에 없는 다른 전문분야 사용, 절대 금지!

[Good Example - Level 4 니치]
✅ "경성대 근처 가성비 좋은 분식당"
   → 랜드마크 + 수식어 + 자연스러운 표현
✅ "홍대입구역에서 평일 점심 혼밥"
   → 지하철역 + 시간대 + 상황
❌ "홍대 점심 혼밥 맛집"
   → 조사 없음, 단순 나열

[Good Example - Level 3 중간]
✅ "강남역에서 펌 잘하는 미용실"
   → 조사 "에서" + 동사 "잘하는"
✅ "부산의 유명한 돼지갈비 맛집"
   → 관형격 조사 "의" + 형용사
✅ "제주도 흑돼지 맛있는 곳"
   → 동의어 사용 ("맛집" 대신 "맛있는 곳")
❌ "강남역 펌 미용실"
   → 명사만 조합, 부자연스러움

[Good Example - Level 2 vs Level 1 차별화]
Level 2 (2개):
✅ "부산 돼지갈비", "부산의 흑돼지 맛집"
   → specialty 포함, 명확히 다른 구조

Level 1 (2개):
✅ "돼지갈비 맛집", "흑돼지"
   → 지역 제거, 전국 단위 키워드, Level 2와 완전히 다름

❌ 잘못된 예:
Level 2: "부산 돼지갈비"
Level 1: "부산 돼지갈비 맛집"
→ Level 1이 Level 2의 확장형, 차별화 실패!

[내부 자동 추론 규칙 – 모델이 스스로 수행]
1) 지리 계층 확장:
   - location을 광역/구·동/상권/역세권으로 분해/변형.
   - 잘 알려진 상권·역 이름을 location에서 자연스럽게 축약(예: "부산 수영구 대연동"→"부산","수영구","대연동","경성대").
   - "근처/역/역세권/사거리/로데오" 같은 일반화 표현을 일부 혼합.

2) 의도 버킷 채우기(균형 분포):
   - 가격/가성비, 좌석/룸/단체, 주차/대중교통 접근, 영업시간/야간/24시, 예약/대기,
     포장/배달, 리뷰/평점, 데이트/가족/회식 중 최소 각 1회 이상 반영.
   - 조사 생략·구어체·숫자(24시)·붙여쓰기/띄어쓰기 변형 허용(가성비좋은/가성비 좋은).

3) 특성 주입 (CRITICAL - 절대 규칙):
   - specialty가 제공된 경우:
     * **모든 Level의 모든 키워드**는 specialty 항목 중 **정확히 1개 이상 반드시 포함**
     * **specialty에 없는 다른 전문분야 절대 사용 금지**
     * 예: specialty="안과"인 경우 → "피부과", "내과", "예방접종" 등 다른 전문분야 사용 금지
   - specialty가 없는 경우: 업종 일반 강점(맛있는/잘하는/가성비/조용한 등) 사용.

4) 안전/정책:
   - 채용/알바/무료/과도한 할인율 등 정책 리스크 표현 제외.
   - 중복 패턴 과다 반복 금지(동일 접두/접미 2회 초과 불가).

5) **한국어 조사 필수 사용 (CRITICAL!):**
   - "에서" (장소): "강남역에서", "홍대에서", "부산에서"
   - "의" (소유/관형): "강남의 맛집", "홍대의 카페", "부산의 명소"
   - "로" (방향/수단): "데이트로 좋은", "혼밥으로 추천"
   - "에" (위치): "강남에 있는", "역 근처에 위치한"
   - **목표: 전체 키워드의 40% 이상 조사 포함 필수!**

6) **동의어 적극 활용:**
   - 맛집 → 맛있는 곳, 잘하는 곳, 유명한 곳, 추천하는 곳
   - 추천 → 좋은, 괜찮은, 인기 있는, 유명한
   - 전문 → 잘하는, 유명한, 특화된, 실력 있는

📊 **5단계 난이도별 키워드 생성**

**Level 5 (롱테일 - 가장 쉬움) - 15개:**
- 자연스러운 구체적 검색어 (3-7단어, 유연하게)
- {f'⚠️ CRITICAL: 반드시 특징({", ".join(specialty_list)}) 중 1개 이상 포함! (60% 이상 = 15개 중 9개 이상)' if specialty_list else '구체적 목적/상황/대상 조합'}
- 조사 적극 사용, 질문형 가능 ("어디?", "추천해요")
- 다양한 구조 예시:
  * "{location}에서 {specialty} 잘하는 {category}"
  * "{location} {specialty} 치료 추천 {category}"
  * "{location} {specialty} {category} 주말 진료"
{f'- ✅ 올바른 예 (specialty={specialty_list[0] if specialty_list else ""}): "{location}에서 {specialty_list[0] if specialty_list else ""} 잘보는 {category}", "{location} {specialty_list[0] if specialty_list else ""} 전문 {category}"' if specialty_list else ''}
{f'- ❌ 잘못된 예: "{location}에서 **다른전문분야** 잘보는 {category}" (specialty에 없는 전문분야 사용 금지!)' if specialty_list else ''}

**Level 4 (니치) - 10개:**
- 자연스러운 니치 검색어 (2-5단어, 유연하게)
- {f'특징({", ".join(specialty_list)}) 포함 권장 (70% 이상)' if specialty_list else '2-3개 특성 조합'}
- 랜드마크, 지하철역, 시간대 자연스럽게 활용
- 다양한 구조 예시:
  * "경성대 근처 {specialty_list[0] if specialty_list else category}"
  * "{location}역에서 {specialty_list[0] if specialty_list else category} 잘하는 곳"
  * "평일 점심 {specialty_list[0] if specialty_list else category} {location}"
- 예: "경성대 근처 {specialty_list[0] if specialty_list else category}"

**Level 3 (중간) - 5개:** ⭐ **조사 필수 사용!**
- 자연스러운 중간 검색어 (2-4단어)
- {f'특징({", ".join(specialty_list)}) 포함 필수 (80% 이상)' if specialty_list else '지역 + 특징 + 업종'}
- **절대 금지**: 명사만 나열 ("부산 분식 맛집" ❌)
- **5가지 구조 패턴 중 선택 (각각 다르게!):**
  1. "{location}에서 {specialty} 잘하는 곳"
  2. "{location} {specialty} 맛있는 {category}"
  3. "{location}의 유명한 {specialty} {category}"
  4. "{specialty} 전문 {category} {location}"
  5. "{location} {specialty} {category} 추천"
- 동의어 사용: 맛집 → 맛있는 곳, 잘하는 곳, 유명한 곳
- 예: "{location}에서 {specialty_list[0] if specialty_list else '맛있는'} {category}"

**Level 2 (경쟁) - 2개:**
- 핵심 키워드 (2-3단어)
- {f'광역 지역 + 특징({", ".join(specialty_list)}) 필수 (100%)' if specialty_list else '광역 지역 + 업종'}
- 조사 사용 가능 ("의", "에서")
- 예: {self._get_level2_examples(location, category, specialty_list)}
- ❌ 절대 금지: 특징 누락, Level 1과 동일한 키워드

**Level 1 (최상위 - 가장 어려움) - 2개:**
- 초경쟁 키워드 (1-3단어, Level 2보다 광범위)
- {f'특징({", ".join(specialty_list)}) 중심 키워드 (100% 필수)' if specialty_list else '업종 중심 키워드'}
- **지역 제거 또는 최소화** (전국 단위 검색어)
- Level 2와 **완전히 다른 키워드** 필수!
- 예: {self._get_level1_examples(location, category, specialty_list)}
- ❌ 절대 금지: Level 2의 확장형 키워드

⚠️ **반드시 지켜야 할 규칙:**
1. **Specialty 포함 기준 (단계적):**
   - Level 1-2: 100% 필수 (specialty 없이 생성 절대 불가)
   - Level 3: 80% 이상 (5개 중 4개 이상 포함)
   - Level 4: 70% 이상 (10개 중 7개 이상 포함)
   - Level 5: 60% 이상 (15개 중 9개 이상 포함)
2. 모든 키워드는 실제 사용자가 검색할 법한 **자연스러운 표현** 사용
3. **조사 사용 목표**: 전체 키워드의 40% 이상 조사 포함
4. 동일한 패턴 반복 금지 (특징 조합을 다양하게 사용)
5. Level 1과 Level 2는 **완전히 다른 키워드**여야 함

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
