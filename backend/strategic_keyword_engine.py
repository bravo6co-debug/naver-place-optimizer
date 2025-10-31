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

    # 지역 인구 데이터 (주요 지역만, 실제로는 DB 또는 API 사용)
    POPULATION_DATA = {
        "서울 강남구": 560000,
        "서울 서초구": 420000,
        "서울 송파구": 660000,
        "서울 강북구": 320000,
        "부산 해운대구": 410000,
        "부산 부산진구": 380000,
    }

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
        # 인구 데이터 조회
        population = self.POPULATION_DATA.get(location, 100000)  # 기본값 10만

        # 업종 데이터 조회
        cat_data = self.CATEGORY_DATA.get(category, {
            "usage_rate": 0.5,
            "search_rate": 0.3
        })

        # 공식: 인구 × 이용률 × 검색률 / 12
        monthly_searches = int(population * cat_data["usage_rate"] * cat_data["search_rate"] / 12)

        return monthly_searches

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_naver_competition(self, keyword: str) -> int:
        """네이버 검색 API로 경쟁도 측정"""
        if not self.naver_client_id or not self.naver_client_secret:
            # API 키 없으면 추정값 반환
            return self._estimate_competition(keyword)

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
                    return self._estimate_competition(keyword)
        except Exception:
            return self._estimate_competition(keyword)

    def _estimate_competition(self, keyword: str) -> int:
        """경쟁도 추정 (API 없을 때)"""
        # 키워드 길이 기반 간단 추정
        word_count = len(keyword.split())

        if word_count >= 4:
            return 100  # 롱테일
        elif word_count == 3:
            return 500
        elif word_count == 2:
            return 5000
        else:
            return 50000

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

        # 네이버 경쟁도
        naver_results = await self.get_naver_competition(keyword)

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

        # Phase 1: 롱테일 킬러 (1-2주)
        phases.append(StrategyPhase(
            phase=1,
            name="롱테일 킬러",
            duration="1-2주",
            target_level=5,
            target_keywords_count=15,
            strategies=[
                "소개글에 롱테일 키워드 자연스럽게 삽입",
                "메뉴명에 검색 키워드 활용",
                "사진 설명(alt)에 키워드 포함",
                "초기 리뷰 10개 확보"
            ],
            goals=[
                "각 키워드 Top 3 달성",
                "프로필 완성도 100%",
                "기본 트래픽 확보"
            ],
            expected_daily_visitors=int(gap * 0.15)
        ))

        # Phase 2: 니치 공략 (3-8주)
        phases.append(StrategyPhase(
            phase=2,
            name="니치 공략",
            duration="3-8주",
            target_level=4,
            target_keywords_count=10,
            strategies=[
                "블로그/SNS 연계 포스팅",
                "특화 메뉴 개발 및 홍보",
                "이벤트/프로모션 진행",
                "리뷰 50개 돌파"
            ],
            goals=[
                "각 키워드 Top 5 진입",
                "평점 4.5+ 유지",
                "재방문율 향상"
            ],
            expected_daily_visitors=int(gap * 0.35)
        ))

        # Phase 3: 중위권 진입 (3-6개월)
        phases.append(StrategyPhase(
            phase=3,
            name="중위권 진입",
            duration="3-6개월",
            target_level=3,
            target_keywords_count=5,
            strategies=[
                "리뷰 100개 이상 확보",
                "정기 업데이트 (주 2회)",
                "지역 커뮤니티 활동",
                "입소문 마케팅 강화"
            ],
            goals=[
                "각 키워드 Top 10 안착",
                "월간 방문자 1000+",
                "단골 고객 확보"
            ],
            expected_daily_visitors=int(gap * 0.70)
        ))

        # Phase 4: 상위권 도전 (6개월+)
        phases.append(StrategyPhase(
            phase=4,
            name="상위권 도전",
            duration="6개월 이상",
            target_level=2,
            target_keywords_count=3,
            strategies=[
                "브랜드 인지도 강화",
                "프리미엄 서비스 차별화",
                "미디어 노출 (기사, 방송)",
                "충성 고객 커뮤니티 운영"
            ],
            goals=[
                "지역 대표 업체로 인식",
                "리뷰 500개 이상",
                "매출 안정화"
            ],
            expected_daily_visitors=gap
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
