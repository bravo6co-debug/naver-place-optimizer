#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전략적 키워드 분석 엔진
- 5단계 난이도 시스템
- OpenAI GPT-4 통합
- 네이버 검색 API 통합
- 트래픽 기반 전략 수립
"""

import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import httpx
from integrations.mois_population_api import get_region_population
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class KeywordLevel(Enum):
    """키워드 난이도 5단계"""
    LEVEL_5_LONGTAIL = 5  # 롱테일 (가장 쉬움)
    LEVEL_4_NICHE = 4  # 니치
    LEVEL_3_MEDIUM = 3  # 중간
    LEVEL_2_COMPETITIVE = 2  # 경쟁
    LEVEL_1_TOP = 1  # 최상위 (가장 어려움)


@dataclass
class KeywordMetrics:
    """키워드 지표"""
    keyword: str
    level: int
    estimated_monthly_searches: int
    competition_score: int  # 0-100
    naver_result_count: int
    difficulty_score: int  # 0-100
    recommended_rank_target: str  # "Top 1-3", "Top 5", etc.
    estimated_timeline: str  # "1-2주", "1개월", etc.
    estimated_traffic: int  # 예상 일방문자 수
    conversion_rate: float  # 예상 전환율


@dataclass
class StrategyPhase:
    """전략 단계"""
    phase: int
    name: str
    duration: str
    target_level: int
    target_keywords_count: int
    strategies: List[str]
    goals: List[str]
    expected_daily_visitors: int


class StrategicKeywordEngine:
    """전략적 키워드 분석 엔진"""

    # 업종별 기본 데이터
    CATEGORY_DATA = {
        "음식점": {
            "usage_rate": 0.70,
            "search_rate": 0.35,
            "conversion_rate": 0.08,
            "base_keywords": ["맛집", "식당", "음식점"],
            "modifiers": {
                "목적": ["데이트", "회식", "혼밥", "가족모임", "점심", "저녁", "야식"],
                "특징": ["분위기좋은", "가성비", "웨이팅맛집", "숨은맛집", "로컬맛집", "인기"],
                "메뉴": ["메뉴추천", "시그니처", "인기메뉴"],
                "시간": ["점심", "저녁", "브런치", "새벽"],
                "가격": ["저렴한", "가성비", "합리적인", "가격대"],
            },
            "longtail_patterns": [
                "{지역} {목적} {특징} 맛집",
                "{지역} {특징} {메뉴} 맛집 추천",
                "{지역} 근처 {목적} 하기좋은 식당",
                "{지역} {시간} {특징} 맛집 베스트",
            ]
        },
        "카페": {
            "usage_rate": 0.80,
            "search_rate": 0.40,
            "conversion_rate": 0.10,
            "base_keywords": ["카페", "커피숍", "디저트카페"],
            "modifiers": {
                "목적": ["공부", "작업", "데이트", "회의", "혼카페", "독서"],
                "특징": ["조용한", "넓은", "감성", "뷰맛집", "인스타감성", "힙한", "루프탑"],
                "메뉴": ["커피맛집", "디저트맛집", "브런치", "베이커리"],
                "시설": ["콘센트많은", "와이파이좋은", "주차가능한", "애견동반"],
                "분위기": ["아늑한", "모던한", "빈티지", "북카페"],
            },
            "longtail_patterns": [
                "{지역} {목적} 하기좋은 카페",
                "{지역} {특징} {분위기} 카페 추천",
                "{지역} {시설} {목적} 카페",
                "{지역} {메뉴} 맛있는 카페 베스트",
            ]
        },
        "미용실": {
            "usage_rate": 0.50,
            "search_rate": 0.45,
            "conversion_rate": 0.12,
            "base_keywords": ["미용실", "헤어샵", "헤어살롱"],
            "modifiers": {
                "서비스": ["커트", "펌", "염색", "클리닉", "두피케어"],
                "특징": ["가성비", "실력좋은", "친절한", "예약필수", "인기"],
                "대상": ["남자", "여자", "학생", "직장인"],
                "스타일": ["단발", "중단발", "롱", "파마", "매직"],
                "가격": ["저렴한", "가성비좋은", "합리적"],
            },
            "longtail_patterns": [
                "{지역} {대상} {서비스} 잘하는 미용실",
                "{지역} {특징} {서비스} 미용실 추천",
                "{지역} {스타일} {서비스} 헤어샵",
                "{지역} 근처 {가격} {대상} 미용실",
            ]
        },
        "병원": {
            "usage_rate": 0.40,
            "search_rate": 0.60,
            "conversion_rate": 0.15,
            "base_keywords": ["병원", "의원", "클리닉"],
            "modifiers": {
                "진료과": ["내과", "정형외과", "피부과", "치과", "한의원", "소아과"],
                "특징": ["친절한", "꼼꼼한", "실력좋은", "예약가능", "야간진료"],
                "증상": ["통증", "감기", "검진", "치료"],
                "시간": ["야간", "주말", "공휴일", "24시간"],
                "서비스": ["검진", "예방접종", "건강검진", "정밀검사"],
            },
            "longtail_patterns": [
                "{지역} {진료과} {특징} 병원",
                "{지역} {증상} 잘보는 {진료과}",
                "{지역} {시간} 진료 병원 추천",
                "{지역} 근처 {서비스} 잘하는 병원",
            ]
        },
        "학원": {
            "usage_rate": 0.30,
            "search_rate": 0.70,
            "conversion_rate": 0.05,
            "base_keywords": ["학원", "교습소", "학습센터"],
            "modifiers": {
                "과목": ["수학", "영어", "국어", "과학", "논술"],
                "대상": ["초등", "중등", "고등", "재수", "성인"],
                "특징": ["소규모", "일대일", "관리잘하는", "성적올리는", "입시전문"],
                "목적": ["내신", "수능", "특목고", "입시"],
                "방식": ["과외", "그룹", "온라인", "방문"],
            },
            "longtail_patterns": [
                "{지역} {대상} {과목} 학원 추천",
                "{지역} {목적} {특징} 학원",
                "{지역} {과목} {방식} 학원 베스트",
                "{지역} 근처 {대상} {과목} 잘가르치는 학원",
            ]
        },
        "헬스장": {
            "usage_rate": 0.25,
            "search_rate": 0.50,
            "conversion_rate": 0.10,
            "base_keywords": ["헬스장", "피트니스", "체육관"],
            "modifiers": {
                "서비스": ["PT", "GX", "필라테스", "요가", "크로스핏"],
                "특징": ["24시간", "여성전용", "시설좋은", "가성비", "샤워실"],
                "대상": ["여성", "남성", "초보자", "다이어트"],
                "시설": ["기구", "샤워실", "락커", "주차", "넓은"],
                "가격": ["저렴한", "무료체험", "이벤트", "할인"],
            },
            "longtail_patterns": [
                "{지역} {특징} 헬스장 추천",
                "{지역} {서비스} 잘하는 피트니스",
                "{지역} {대상} {목적} 헬스장",
                "{지역} 근처 {가격} {시설} 헬스장",
            ]
        }
    }

    # 지역 인구 데이터는 MOIS API 사용 (integrations/mois_population_api.py 참조)

    def __init__(self, openai_api_key: Optional[str] = None, naver_client_id: Optional[str] = None, naver_client_secret: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.naver_client_id = naver_client_id or os.getenv("NAVER_CLIENT_ID")
        self.naver_client_secret = naver_client_secret or os.getenv("NAVER_CLIENT_SECRET")

        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

    def estimate_monthly_searches(self, location: str, category: str) -> int:
        """지역 인구 기반 월간 검색량 추정"""
        # 인구 데이터 조회 (MOIS API 사용)
        population = get_region_population(location)  # API로 실시간 조회

        # 업종 데이터 조회
        cat_data = self.CATEGORY_DATA.get(category, {
            "usage_rate": 0.5,
            "search_rate": 0.3
        })

        # 공식: 인구 × 이용률 × 검색률 / 12
        monthly_searches = int(population * cat_data["usage_rate"] * cat_data["search_rate"] / 12)

        return monthly_searches

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_naver_competition(
        self,
        keyword: str,
        region: Optional[str] = None,
        category: Optional[str] = None
    ) -> int:
        """네이버 검색 API로 경쟁도 측정"""
        if not self.naver_client_id or not self.naver_client_secret:
            # API 키 없으면 추정값 반환
            return self._estimate_competition(keyword, region, category)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openapi.naver.com/v1/search/local.json",
                    headers={
                        "X-Naver-Client-Id": self.naver_client_id,
                        "X-Naver-Client-Secret": self.naver_client_secret
                    },
                    params={"query": keyword, "display": 1}
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("total", 0)
                else:
                    return self._estimate_competition(keyword, region, category)
        except Exception:
            return self._estimate_competition(keyword, region, category)

    def _detect_category_from_keyword(self, keyword: str) -> Optional[str]:
        """키워드에서 업종 자동 감지"""
        keyword_lower = keyword.lower()

        # 각 카테고리의 base_keywords로 매칭
        for category, data in self.CATEGORY_DATA.items():
            base_keywords = data.get("base_keywords", [])
            if any(bk in keyword_lower for bk in base_keywords):
                return category

        return None

    def _estimate_competition(
        self,
        keyword: str,
        region: Optional[str] = None,
        category: Optional[str] = None
    ) -> int:
        """
        향상된 경쟁도 추정 (API 실패 시 폴백)

        개선사항:
        - 인구 데이터 기반 지역별 가중치
        - 업종별 시장 포화도 반영
        - 고경쟁 키워드 패턴 감지
        - 키워드 특성 분석 (단순 단어 수 이상)
        """
        base_score = 1000

        # 1. 키워드 길이 기반 특성 분석 (개선된 버전)
        word_count = len(keyword.split())
        length_multiplier = {
            1: 50,    # "맛집" -> 매우 높은 경쟁
            2: 10,    # "강남 맛집" -> 높은 경쟁
            3: 3,     # "강남역 맛집 추천" -> 중간 경쟁
            4: 1,     # "강남역 근처 데이트 맛집" -> 낮은 경쟁
        }.get(word_count, 0.5 if word_count > 4 else 50)

        # 2. 고경쟁 키워드 패턴 감지 (가산 방식으로 변경)
        high_competition_patterns = {
            '맛집': 2.0, '카페': 1.8, '추천': 1.3, 'best': 1.5, '순위': 1.4,
            '인기': 1.2, '유명': 1.2, '핫플': 1.5, '웨이팅': 1.3,
            '병원': 1.5, '피부과': 1.4, '성형외과': 1.6, '치과': 1.4,
            '한의원': 1.3, '미용실': 1.3, '네일': 1.2, '헬스장': 1.2,
            '학원': 1.3, '과외': 1.2, '영어': 1.3,
        }

        keyword_multiplier = 1.0
        for pattern, multiplier in high_competition_patterns.items():
            if pattern in keyword.lower():
                keyword_multiplier += (multiplier - 1)  # 가산 방식

        # 3. 지역 인구 기반 가중치 (인구 API 데이터 활용)
        region_multiplier = 1.0
        if region:
            try:
                population = get_region_population(region)
                # 인구 기반 시장 규모 가중치 (보정된 값)
                if population >= 500000:      # 대형 구 (50만 이상)
                    region_multiplier = 2.5
                elif population >= 300000:    # 중형 구 (30만 이상)
                    region_multiplier = 1.8
                elif population >= 100000:    # 소형 구 (10만 이상)
                    region_multiplier = 1.3
                else:                         # 소규모 지역
                    region_multiplier = 0.8
            except Exception:
                region_multiplier = 1.5  # 기본값 (중간 규모 가정)

        # 4. 업종별 가중치 (시장 포화도 + 온라인 검색 강도)
        industry_multiplier = 1.0
        detected_category = category or self._detect_category_from_keyword(keyword)

        if detected_category and detected_category in self.CATEGORY_DATA:
            cat_data = self.CATEGORY_DATA[detected_category]
            usage_rate = cat_data.get("usage_rate", 0.5)      # 시장 사용률
            search_rate = cat_data.get("search_rate", 0.5)    # 온라인 검색 비율

            # 사용률이 높을수록 경쟁 증가, 검색률이 높을수록 온라인 경쟁 증가 (조정된 공식)
            industry_multiplier = 0.5 + (usage_rate * 1.2) + (search_rate * 0.8)
            # 예: 카페 (0.5 + 0.8 * 1.2 + 0.4 * 0.8) = 1.78
            # 예: 헬스장 (0.5 + 0.25 * 1.2 + 0.5 * 0.8) = 1.2
        else:
            # 카테고리 감지 실패 시 기본값
            industry_multiplier = 1.2

        # 5. 최종 경쟁도 계산
        estimated = int(
            base_score *
            length_multiplier *
            keyword_multiplier *
            region_multiplier *
            industry_multiplier
        )

        # 상한선/하한선 설정 (합리적 범위 유지)
        estimated = max(50, min(estimated, 100000))

        return estimated

    async def generate_keywords_with_gpt(self, category: str, location: str, specialty: Optional[str] = None) -> List[Dict]:
        """GPT-4로 전략적 키워드 생성"""
        if not self.openai_client:
            return self._generate_fallback_keywords(category, location)

        # 업종별 데이터 가져오기
        cat_data = self.CATEGORY_DATA.get(category, {})
        modifiers = cat_data.get("modifiers", {})

        # 프롬프트에 실제 검색 패턴 예시 추가
        modifier_examples = ""
        if modifiers:
            modifier_examples = "\n\n업종별 실제 검색 패턴:\n"
            for mod_type, mod_values in list(modifiers.items())[:3]:
                modifier_examples += f"- {mod_type}: {', '.join(mod_values[:5])}\n"

        prompt = f"""당신은 네이버 플레이스 검색 최적화 전문가입니다. 실제 사용자들이 검색하는 자연스러운 키워드를 생성해주세요.

업종: {category}
지역: {location}
{f'특징: {specialty}' if specialty else ''}
{modifier_examples}

중요: 실제 사용자의 검색 의도를 반영해주세요.
- 목적 (데이트, 회식, 공부, 운동 등)
- 특징 (가성비, 분위기, 시설 등)
- 시간대 (아침, 점심, 저녁, 야간 등)
- 대상 (혼자, 가족, 친구, 연인 등)

5단계 난이도별로 키워드를 생성해주세요:

Level 5 (롱테일 - 가장 쉬움) - 15개:
- 매우 구체적인 검색어 (4-6단어)
- 사용자의 구체적인 의도와 상황 반영
- 예시:
  * 카페: "강남역 10번출구 조용한 노트북 작업 카페", "강남역 근처 데이트하기좋은 루프탑 카페"
  * 음식점: "강남역 점심 혼밥하기좋은 가성비 맛집", "강남역 저녁 회식 분위기좋은 한식당"
  * 미용실: "강남역 남자 가성비 커트 잘하는 미용실", "강남역 여자 단발 펌 전문 헤어샵"

Level 4 (니치) - 10개:
- 구체적 니즈 반영 (3-4단어)
- 2-3개의 특성 조합
- 예시:
  * 카페: "강남역 공부하기좋은 카페", "강남역 브런치 디저트 맛집"
  * 음식점: "강남역 가성비 점심맛집", "강남역 데이트 분위기좋은 식당"
  * 미용실: "강남역 남자 커트 전문", "강남역 펌 잘하는 헤어샵"

Level 3 (중간) - 5개:
- 일반적 조합 (2-3단어)
- 지역 + 특징 + 업종
- 예시:
  * 카페: "강남역 브런치카페", "강남역 감성카페"
  * 음식점: "강남역 점심맛집", "강남역 한식당"
  * 미용실: "강남역 가성비 미용실", "강남역 펌전문"

Level 2 (경쟁) - 3개:
- 핵심 키워드 (2단어)
- 광역 지역 + 업종/특징
- 예시:
  * 카페: "강남 브런치", "강남 카페추천"
  * 음식점: "강남 맛집", "강남 한식"
  * 미용실: "강남 미용실", "강남 커트"

Level 1 (최상위 - 가장 어려움) - 2개:
- 초경쟁 키워드 (1-2단어)
- 광역 지역 + 업종
- 예시: "강남 카페", "강남 맛집", "강남 미용실"

JSON 형식으로 반환:
[
  {{"keyword": "...", "level": 5, "reason": "선정 이유"}},
  ...
]

총 35개의 키워드를 생성해주세요 (Level 5: 15개, Level 4: 10개, Level 3: 5개, Level 2: 3개, Level 1: 2개)."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 비용 절감을 위해 mini 사용
                messages=[
                    {"role": "system", "content": "You are a Naver Place SEO expert. Always respond in Korean with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            content = response.choices[0].message.content

            # JSON 파싱
            import json
            # 코드 블록 제거
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            keywords = json.loads(content.strip())
            return keywords

        except Exception as e:
            print(f"GPT 키워드 생성 실패: {e}")
            return self._generate_fallback_keywords(category, location)

    def _generate_fallback_keywords(self, category: str, location: str) -> List[Dict]:
        """GPT 실패 시 폴백 키워드 생성 - 현실적인 패턴 기반"""
        import random

        cat_data = self.CATEGORY_DATA.get(category, {
            "base_keywords": [category],
            "modifiers": {},
            "longtail_patterns": []
        })

        base_keywords = cat_data.get("base_keywords", [category])
        modifiers = cat_data.get("modifiers", {})
        patterns = cat_data.get("longtail_patterns", [])
        location_parts = location.split()

        keywords = []

        # Level 5 - 롱테일 (15개): 매우 구체적인 검색어
        for _ in range(15):
            if patterns and modifiers:
                pattern = random.choice(patterns)
                # 패턴의 플레이스홀더를 실제 값으로 치환
                keyword = pattern.replace("{지역}", location)
                for mod_type, mod_values in modifiers.items():
                    placeholder = f"{{{mod_type}}}"
                    if placeholder in keyword:
                        keyword = keyword.replace(placeholder, random.choice(mod_values))

                keywords.append({
                    "keyword": keyword,
                    "level": 5,
                    "reason": "구체적 의도 반영 롱테일 키워드"
                })
            else:
                # 기본 패턴
                base = random.choice(base_keywords)
                keywords.append({
                    "keyword": f"{location} {base} 추천 베스트",
                    "level": 5,
                    "reason": "롱테일 키워드"
                })

        # Level 4 - 니치 (10개): 구체적 니즈
        for _ in range(10):
            if modifiers:
                # 랜덤하게 2개의 modifier 조합
                mod_types = list(modifiers.keys())
                if len(mod_types) >= 2:
                    selected_types = random.sample(mod_types, 2)
                    mod1 = random.choice(modifiers[selected_types[0]])
                    mod2 = random.choice(modifiers[selected_types[1]])
                    base = random.choice(base_keywords)
                    keywords.append({
                        "keyword": f"{location} {mod1} {mod2} {base}",
                        "level": 4,
                        "reason": f"{selected_types[0]}+{selected_types[1]} 조합 니치 키워드"
                    })
                else:
                    base = random.choice(base_keywords)
                    keywords.append({
                        "keyword": f"{location} {base} 추천",
                        "level": 4,
                        "reason": "니치 키워드"
                    })
            else:
                base = random.choice(base_keywords)
                keywords.append({
                    "keyword": f"{location} {base} 추천",
                    "level": 4,
                    "reason": "니치 키워드"
                })

        # Level 3 - 중간 (5개): 일반적 조합
        for base in base_keywords[:5]:
            if modifiers and len(list(modifiers.keys())) > 0:
                # 1개의 modifier만 사용
                mod_type = random.choice(list(modifiers.keys()))
                mod_value = random.choice(modifiers[mod_type])
                keywords.append({
                    "keyword": f"{location} {mod_value} {base}",
                    "level": 3,
                    "reason": f"{mod_type} 반영 중간 키워드"
                })
            else:
                keywords.append({
                    "keyword": f"{location} {base}",
                    "level": 3,
                    "reason": "중간 키워드"
                })

        # Level 2 - 경쟁 (3개): 핵심 키워드
        if len(location_parts) >= 2:
            for base in base_keywords[:3]:
                keywords.append({
                    "keyword": f"{location_parts[0]} {base}",
                    "level": 2,
                    "reason": "광역 지역 경쟁 키워드"
                })
        else:
            for base in base_keywords[:3]:
                keywords.append({
                    "keyword": f"{location} {base}",
                    "level": 2,
                    "reason": "경쟁 키워드"
                })

        # Level 1 - 최상위 (2개): 초경쟁 키워드
        if len(location_parts) >= 2:
            keywords.append({
                "keyword": f"{location_parts[0]} {category}",
                "level": 1,
                "reason": "광역 초경쟁 키워드"
            })
        keywords.append({
            "keyword": category,
            "level": 1,
            "reason": "최상위 초경쟁 키워드"
        })

        return keywords

    async def analyze_keyword(self, keyword: str, level: int, location: str, category: str) -> KeywordMetrics:
        """개별 키워드 분석"""
        # 검색량 추정
        base_searches = self.estimate_monthly_searches(location, category)

        # 레벨별 검색량 조정
        level_multipliers = {
            5: 0.01,  # 1%
            4: 0.05,  # 5%
            3: 0.15,  # 15%
            2: 0.40,  # 40%
            1: 1.00   # 100%
        }
        estimated_searches = int(base_searches * level_multipliers.get(level, 0.1))

        # 네이버 경쟁도 (지역 및 카테고리 컨텍스트 포함)
        naver_results = await self.get_naver_competition(keyword, location, category)

        # 경쟁도 점수 계산 (0-100)
        if naver_results < 100:
            competition_score = 10
        elif naver_results < 1000:
            competition_score = 30
        elif naver_results < 10000:
            competition_score = 50
        elif naver_results < 100000:
            competition_score = 70
        else:
            competition_score = 90

        # 난이도 점수 (경쟁도와 검색량 조합)
        difficulty_score = int((competition_score * 0.6) + ((100 - level * 20) * 0.4))

        # 목표 순위 및 타임라인
        targets = {
            5: ("Top 1-3", "1-2주", 0.25),
            4: ("Top 5", "1개월", 0.15),
            3: ("Top 10", "2-3개월", 0.10),
            2: ("Top 20", "6개월", 0.05),
            1: ("노출 목표", "장기", 0.02)
        }
        rank_target, timeline, traffic_rate = targets.get(level, ("Top 10", "2개월", 0.10))

        # 예상 트래픽 (검색량 × 전환율)
        cat_data = self.CATEGORY_DATA.get(category, {"conversion_rate": 0.08})
        conversion = cat_data["conversion_rate"] * traffic_rate
        estimated_daily_traffic = int((estimated_searches / 30) * conversion)

        return KeywordMetrics(
            keyword=keyword,
            level=level,
            estimated_monthly_searches=estimated_searches,
            competition_score=competition_score,
            naver_result_count=naver_results,
            difficulty_score=difficulty_score,
            recommended_rank_target=rank_target,
            estimated_timeline=timeline,
            estimated_traffic=estimated_daily_traffic,
            conversion_rate=conversion
        )

    def generate_strategy_roadmap(
        self,
        current_daily_visitors: int,
        target_daily_visitors: int,
        category: str
    ) -> List[StrategyPhase]:
        """목표 기반 전략 로드맵 생성"""

        gap = target_daily_visitors - current_daily_visitors

        phases = []

        # Phase 1: 롱테일 킬러 (1개월) - Level 5 (V5 Simplified)
        phases.append(StrategyPhase(
            phase=1,
            name="롱테일 킬러",
            duration="1개월",
            target_level=5,
            target_keywords_count=15,
            strategies=[
                "✅ [최우선] 영수증 리뷰 100개 확보: 현장 POP/QR 코드 리뷰 유도",
                "✅ [핵심] 롱테일 키워드 3개 이상 리뷰에 자연스럽게 삽입",
                "✅ [품질] 리뷰 기준: 텍스트 30자+ / 사진 1장+ (20% 비율) / 키워드 2개+",
                "✅ [최신성] 일 3-4개 신규 리뷰 유입 (꾸준함이 핵심)"
            ],
            goals=[
                "각 키워드 Top 3 달성",
                "프로필 완성도 100%",
                "기본 트래픽 확보"
            ]
        ))

        # Phase 2: 니치 공략 (2개월) - Level 4 (V5 Simplified)
        phases.append(StrategyPhase(
            phase=2,
            name="니치 공략",
            duration="2개월",
            target_level=4,
            target_keywords_count=10,
            strategies=[
                "✅ [최우선] 영수증 리뷰 300개 확보 (주 35개 목표)",
                "✅ [핵심] 롱테일 키워드 4개 이상 리뷰에 자연스럽게 삽입",
                "✅ [품질] 리뷰 기준: 텍스트 80자+ / 사진 3장+ / 키워드 4개+",
                "✅ [정보신뢰도] 플레이스 정보 완성도 100% 유지 (주 1회 점검)",
                "✅ [최신성] 일 5개 신규 리뷰 유입 (공백 없이 꾸준히)"
            ],
            goals=[
                "각 키워드 Top 5 진입",
                "리뷰 300개 이상 + 주 5회 유입",
                "재방문율 향상"
            ]
        ))

        # Phase 3: 중위권 진입 (3개월) - Level 3 (V5 Simplified)
        phases.append(StrategyPhase(
            phase=3,
            name="중위권 진입",
            duration="3개월",
            target_level=3,
            target_keywords_count=5,
            strategies=[
                "✅ [최우선] 영수증 리뷰 500개 확보 (주 39개 목표)",
                "✅ [핵심] 롱테일 키워드 5개 이상 리뷰에 자연스럽게 삽입",
                "✅ [품질] 리뷰 기준: 텍스트 100자+ / 사진 4장+ / 키워드 5개+",
                "✅ [최신성] 일 5-6개 신규 리뷰 유입 (공백 없이 꾸준히)"
            ],
            goals=[
                "각 키워드 Top 10 안착",
                "월간 방문자 1000+",
                "단골 고객 확보"
            ]
        ))

        # Phase 4: 상위권 도전 (6개월+) - Level 2 (V5 Simplified)
        phases.append(StrategyPhase(
            phase=4,
            name="상위권 도전",
            duration="6개월 이상",
            target_level=2,
            target_keywords_count=3,
            strategies=[
                "✅ [최우선] 영수증 리뷰 999개 유지 + 월별 유입 지속",
                "✅ [핵심] 중단위 키워드에 집중 (5개 이상 리뷰에 삽입)",
                "✅ [품질] 리뷰 기준: 텍스트 150자+ / 사진 5장+ / 키워드 5개+",
                "✅ [최신성] 매일 3개 이상 신규 리뷰 유입 (꾸준함이 핵심)"
            ],
            goals=[
                "지역 대표 업체로 인식",
                "리뷰 999개 유지",
                "매출 안정화"
            ]
        ))

        # Phase 5: 최상위 (1년+) - Level 1 (V5 Simplified)
        phases.append(StrategyPhase(
            phase=5,
            name="최상위",
            duration="1년 이상",
            target_level=1,
            target_keywords_count=2,
            strategies=[
                "✅ [최우선] 영수증 리뷰 2000개 이상 확보",
                "✅ [핵심] 단어 키워드 공략 (10개 이상 리뷰에 삽입)",
                "✅ [품질] 리뷰 기준: 텍스트 200자+ / 사진 5장+ / 키워드 10개+",
                "✅ [최신성] 매일 5개 이상 신규 리뷰 유입 (지속성 유지)"
            ],
            goals=[
                "지역 1위 업체 확립",
                "리뷰 2000개 이상",
                "브랜드 인지도 극대화"
            ]
        ))

        return phases


# 테스트 코드
if __name__ == "__main__":
    import asyncio

    async def test():
        engine = StrategicKeywordEngine()

        # 키워드 생성
        keywords = await engine.generate_keywords_with_gpt("카페", "서울 강남구", "브런치 전문")

        print("=== 생성된 키워드 ===")
        for kw in keywords[:5]:
            print(f"Level {kw['level']}: {kw['keyword']} - {kw['reason']}")

        # 키워드 분석
        if keywords:
            analysis = await engine.analyze_keyword(
                keywords[0]['keyword'],
                keywords[0]['level'],
                "서울 강남구",
                "카페"
            )
            print(f"\n=== 키워드 분석: {analysis.keyword} ===")
            print(f"검색량: {analysis.estimated_monthly_searches}/월")
            print(f"경쟁도: {analysis.competition_score}/100")
            print(f"목표: {analysis.recommended_rank_target} ({analysis.estimated_timeline})")
            print(f"예상 트래픽: {analysis.estimated_traffic}명/일")

        # 전략 로드맵
        roadmap = engine.generate_strategy_roadmap(50, 200, "카페")
        print(f"\n=== 전략 로드맵 (50명 → 200명) ===")
        for phase in roadmap:
            print(f"\n[Phase {phase.phase}: {phase.name}]")
            print(f"기간: {phase.duration}")
            print(f"목표 키워드: Level {phase.target_level} × {phase.target_keywords_count}개")
            print(f"예상 추가 유입: +{phase.expected_daily_visitors}명/일")

    asyncio.run(test())
