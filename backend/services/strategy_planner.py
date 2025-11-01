#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""전략 수립 서비스"""

from typing import List, Dict, Optional, Any
from models.strategy import StrategyPhase
from models.keyword import KeywordMetrics
from config.category_loader import CategoryLoader
import json
import os


class StrategyPlannerService:
    """전략 수립 서비스"""

    def __init__(self):
        self.category_loader = CategoryLoader()
        self._load_generic_strategies()

    def _load_generic_strategies(self):
        """범용 전략 템플릿 로드"""
        generic_path = os.path.join(
            os.path.dirname(__file__),
            "../config/categories/_generic_strategies.json"
        )
        try:
            with open(generic_path, 'r', encoding='utf-8') as f:
                self.generic_strategies = json.load(f)
        except:
            self.generic_strategies = {
                "strategies": {},
                "goals": {}
            }

    def generate_roadmap(
        self,
        current_daily_visitors: int,
        target_daily_visitors: int,
        category: str,
        analyzed_keywords: Optional[List[KeywordMetrics]] = None,
        specialty: Optional[str] = None
    ) -> List[StrategyPhase]:
        """
        목표 기반 전략 로드맵 생성 (V4: 동적 생성)

        Args:
            current_daily_visitors: 현재 일방문자
            target_daily_visitors: 목표 일방문자
            category: 업종
            analyzed_keywords: 분석된 키워드 리스트 (V4 신규)
            specialty: 특징/전문분야 (specialty 포함 키워드 우선 선정)

        Returns:
            전략 단계 리스트
        """
        gap = target_daily_visitors - current_daily_visitors

        # 키워드 분석 데이터가 있으면 동적 생성, 없으면 레거시 방식
        if analyzed_keywords:
            return self._generate_dynamic_roadmap(gap, category, analyzed_keywords, specialty)
        else:
            return self._generate_legacy_roadmap(gap, category)

    def _generate_dynamic_roadmap(
        self,
        gap: int,
        category: str,
        analyzed_keywords: List[KeywordMetrics],
        specialty: Optional[str] = None
    ) -> List[StrategyPhase]:
        """
        실제 키워드 분석 결과 기반 동적 로드맵 생성

        Args:
            gap: 목표 트래픽 갭
            category: 업종
            analyzed_keywords: 분석된 키워드들

        Returns:
            동적 생성된 전략 단계 리스트
        """
        # 레벨별로 키워드 그룹화
        keywords_by_level = {1: [], 2: [], 3: [], 4: [], 5: []}
        for kw in analyzed_keywords:
            keywords_by_level[kw.level].append(kw)

        # 업종별 전략/목표 로드
        cat_data = self.category_loader.get_category(category)
        strategies_template = cat_data.get("strategies", {}) if cat_data else {}
        goals_template = cat_data.get("goals", {}) if cat_data else {}

        # 없으면 범용 템플릿 사용
        if not strategies_template:
            strategies_template = self.generic_strategies.get("strategies", {})
            goals_template = self.generic_strategies.get("goals", {})

        phases = []
        cumulative_traffic = 0
        phase_num = 1

        # 레벨 5부터 1까지 역순으로 Phase 생성 (롱테일 → 최상위)
        # V5 현실화: 영수증 리뷰 기반 실제 소요 기간
        level_config = {
            5: {"name": "롱테일 킬러", "duration": "1개월"},
            4: {"name": "니치 공략", "duration": "3-8주"},
            3: {"name": "중위권 진입", "duration": "3-6개월"},
            2: {"name": "상위권 도전", "duration": "6개월 이상"},
            1: {"name": "최상위 도전", "duration": "1년 이상"}
        }

        for level in [5, 4, 3, 2, 1]:
            level_keywords = keywords_by_level[level]
            if not level_keywords:
                continue  # 해당 레벨 키워드 없으면 건너뛰기

            # 실제 트래픽 계산
            level_traffic = sum(kw.estimated_traffic for kw in level_keywords)
            cumulative_traffic += level_traffic

            # 우선순위 키워드 선정 (난이도 대비 효과 높은 순 + specialty 우선)
            priority_kws = self._select_priority_keywords(level_keywords, top_n=5, specialty=specialty)

            # 키워드별 트래픽 분해
            traffic_breakdown = {
                kw.keyword: kw.estimated_traffic
                for kw in sorted(level_keywords, key=lambda k: k.estimated_traffic, reverse=True)[:5]
            }

            # 난이도 계산
            avg_difficulty = sum(kw.difficulty_score for kw in level_keywords) / len(level_keywords)
            difficulty_level = self._get_difficulty_level(avg_difficulty)

            # 전략/목표 가져오기
            level_key = f"level_{level}"
            strategies = strategies_template.get(level_key, [
                f"Level {level} 키워드 최적화",
                "검색 노출 향상 전략",
                "리뷰 및 평점 관리",
                "지속적인 콘텐츠 업데이트"
            ])
            goals = goals_template.get(level_key, [
                f"Level {level} 키워드 상위 노출",
                "고객 만족도 향상",
                "지속적 트래픽 증가"
            ])

            # V5: 영수증 리뷰 전략 생성
            receipt_strategy = self._generate_receipt_review_strategy_v5(level, priority_kws, category)

            phase = StrategyPhase(
                phase=phase_num,
                name=level_config[level]["name"],
                duration=level_config[level]["duration"],
                target_level=level,
                target_keywords_count=len(level_keywords),
                strategies=strategies,
                goals=goals,
                priority_keywords=[kw.keyword for kw in priority_kws],
                keyword_traffic_breakdown=traffic_breakdown,
                difficulty_level=difficulty_level,
                # V5 필드 추가
                receipt_review_target=receipt_strategy["target"],
                weekly_review_target=receipt_strategy["weekly_target"],
                consistency_importance=receipt_strategy["consistency"],
                receipt_review_keywords=receipt_strategy["keywords"],
                review_quality_standard=receipt_strategy["quality_standard"],
                review_incentive_plan=receipt_strategy["incentive"],
                keyword_mention_strategy=receipt_strategy["mention_strategy"],
                info_trust_checklist=receipt_strategy["trust_checklist"],
                review_templates=receipt_strategy["templates"]
            )
            phases.append(phase)
            phase_num += 1

        return phases

    def _generate_legacy_roadmap(self, gap: int, category: str) -> List[StrategyPhase]:
        """
        레거시 방식: 고정 비율 기반 로드맵 (V5 Simplified 적용)
        영수증 리뷰 + 키워드 전략 중심
        """
        phases = []

        # Phase 1: 롱테일 킬러 (1개월) - Level 5
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
                "✅ [최신성] 일 1개 신규 리뷰 유입 (꾸준함이 핵심)"
            ],
            goals=[
                "각 키워드 Top 1-3 진입",
                "프로필 완성도 100%",
                "리뷰 100개 이상 + 평점 4.5+"
            ],
            # V5 필드
            receipt_review_target=100,
            weekly_review_target=6,
            consistency_importance="일 1개 신규 리뷰 (꾸준함이 핵심, 1개월 목표)",
            receipt_review_keywords=[],
            review_quality_standard={
                "min_text_length": 30,
                "min_photos": 1,
                "photo_ratio": 0.2,
                "keyword_count": 2,
                "receipt_photo_warning": "⚠️ 영수증 사진 첨부 금지 (개인정보로 인식되어 자동 비노출)"
            },
            review_incentive_plan="영수증 리뷰 작성 시 다음 이용 10% 할인",
            keyword_mention_strategy={},
            info_trust_checklist=[],
            review_templates={}
        ))

        # Phase 2: 니치 공략 (3-8주) - Level 4
        phases.append(StrategyPhase(
            phase=2,
            name="니치 공략",
            duration="3-8주",
            target_level=4,
            target_keywords_count=10,
            strategies=[
                "✅ [최우선] 영수증 리뷰 300개 확보 (주 10개 목표)",
                "✅ [핵심] 롱테일 키워드 4개 이상 리뷰에 자연스럽게 삽입",
                "✅ [품질] 리뷰 기준: 텍스트 80자+ / 사진 3장+ / 키워드 4개+",
                "✅ [정보신뢰도] 플레이스 정보 완성도 100% 유지 (주 1회 점검)"
            ],
            goals=[
                "각 키워드 Top 5 진입",
                "평점 4.5+ 유지",
                "재방문율 향상"
            ]
        ))

        # Phase 3: 중위권 진입 (3-6개월) - Level 3
        phases.append(StrategyPhase(
            phase=3,
            name="중위권 진입",
            duration="3-6개월",
            target_level=3,
            target_keywords_count=5,
            strategies=[
                "✅ [최우선] 영수증 리뷰 999개 확보 (주 15개 목표)",
                "✅ [핵심] 롱테일 키워드 5개 이상 리뷰에 자연스럽게 삽입",
                "✅ [품질] 리뷰 기준: 텍스트 100자+ / 사진 4장+ / 키워드 5개+",
                "✅ [최신성] 매일 2개 이상 신규 리뷰 유입 (공백 없이 꾸준히)"
            ],
            goals=[
                "각 키워드 Top 10 안착",
                "월간 방문자 1000+",
                "단골 고객 확보"
            ]
        ))

        # Phase 4: 상위권 도전 (6개월+) - Level 2
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

        # Phase 5: 최상위 (1년+) - Level 1
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

    def _select_priority_keywords(
        self,
        keywords: List[KeywordMetrics],
        top_n: int = 5,
        specialty: Optional[str] = None
    ) -> List[KeywordMetrics]:
        """
        우선순위 키워드 선정 (ROI 기반 + specialty 우선)

        Args:
            keywords: 키워드 리스트
            top_n: 선정할 개수
            specialty: 특징 (specialty 포함 키워드 우선 선정)

        Returns:
            우선순위 키워드 리스트
        """
        # ROI = 예상 트래픽 / max(난이도, 1)
        scored_keywords = []
        for kw in keywords:
            roi = kw.estimated_traffic / max(kw.difficulty_score, 1)

            # specialty 포함 시 ROI 가중치 부여 (2배)
            if specialty and specialty in kw.keyword:
                roi *= 2.0

            scored_keywords.append((kw, roi))

        # ROI 높은 순으로 정렬
        scored_keywords.sort(key=lambda x: x[1], reverse=True)

        return [kw for kw, _ in scored_keywords[:top_n]]

    def _get_difficulty_level(self, avg_difficulty: float) -> str:
        """난이도 점수 → 레벨 변환"""
        if avg_difficulty < 30:
            return "쉬움"
        elif avg_difficulty < 60:
            return "보통"
        else:
            return "어려움"

    def _generate_receipt_review_strategy_v5(
        self,
        level: int,
        priority_keywords: List[KeywordMetrics],
        category: str
    ) -> Dict[str, Any]:
        """영수증 리뷰 전략 생성 (V5 Simplified)"""

        # 업종별 JSON에서 receipt_review_strategy 로드
        cat_data = self.category_loader.get_category(category)

        if cat_data and "receipt_review_strategy" in cat_data:
            level_key = f"level_{level}"
            strategy_data = cat_data["receipt_review_strategy"].get(level_key, {})

            # 키워드 추출 (상위 5개)
            review_keywords = [kw.keyword for kw in priority_keywords[:5]]

            # 키워드 언급 전략
            keyword_relevance = cat_data.get("keyword_relevance_strategy", {}).get(level_key, {})
            mention_strategy = {
                "frequency": keyword_relevance.get("mention_frequency", "리뷰당 2-3회"),
                "placement": "제목 1개 + 본문 첫 문장 1개 + 본문 중간 1개",
                "natural_tip": keyword_relevance.get("natural_insertion_tip", "자연스럽게"),
                "example": f"{review_keywords[0]} 다녀왔는데, 정말 좋았어요!" if review_keywords else "키워드 예시"
            }

            # 정보 신뢰도 체크리스트
            trust_strategy = cat_data.get("info_trust_strategy", {})
            trust_checklist = trust_strategy.get("critical_fields", [])

            # 리뷰 템플릿 생성
            templates = self._generate_review_templates_v5(review_keywords, category, level)

            return {
                "target": strategy_data.get("target_count", 100),
                "weekly_target": strategy_data.get("weekly_target", 7),
                "consistency": strategy_data.get("consistency_message", "꾸준히"),
                "keywords": review_keywords,
                "quality_standard": strategy_data.get("quality_standard", {}),
                "incentive": strategy_data.get("incentive", "할인 혜택"),
                "mention_strategy": mention_strategy,
                "trust_checklist": [f"✅ {field}" for field in trust_checklist],
                "templates": templates
            }

        # 폴백: 기본값 (V5 Simplified)
        consistency_messages = {
            5: "일 1개 신규 리뷰 (꾸준함이 핵심, 1개월 목표)",
            4: "일 1-2개 신규 리뷰 (1-2일 공백 없음, 2개월 목표)",
            3: "일 2-3개 신규 리뷰 (절대 공백 없음, 3개월 목표)",
            2: "일 2-3개 신규 리뷰 (최신성 유지, 지속)",
            1: "일 2-3개 신규 리뷰 (1등 유지, 지속)"
        }

        quality_standards = {
            5: {"min_text_length": 30, "min_photos": 1, "photo_ratio": 0.2, "keyword_count": 2,
                "receipt_photo_warning": "⚠️ 영수증 사진 첨부 금지 (개인정보로 인식되어 자동 비노출)"},
            4: {"min_text_length": 50, "min_photos": 1, "photo_ratio": 0.2, "keyword_count": 2,
                "receipt_photo_warning": "⚠️ 영수증 사진 첨부 금지 (개인정보로 인식되어 자동 비노출)"},
            3: {"min_text_length": 80, "min_photos": 1, "photo_ratio": 0.2, "keyword_count": 3,
                "receipt_photo_warning": "⚠️ 영수증 사진 첨부 금지 (개인정보로 인식되어 자동 비노출)"},
            2: {"min_text_length": 80, "min_photos": 1, "photo_ratio": 0.2, "keyword_count": 3,
                "receipt_photo_warning": "⚠️ 영수증 사진 첨부 금지 (개인정보로 인식되어 자동 비노출)"},
            1: {"min_text_length": 100, "min_photos": 1, "photo_ratio": 0.2, "keyword_count": 3,
                "receipt_photo_warning": "⚠️ 영수증 사진 첨부 금지 (개인정보로 인식되어 자동 비노출)"}
        }

        return {
            "target": {5: 100, 4: 300, 3: 999, 2: 999, 1: 2000}.get(level, 100),
            "weekly_target": {5: 6, 4: 12, 3: 19, 2: 19, 1: 19}.get(level, 6),
            "consistency": consistency_messages.get(level, "일 1개 신규 리뷰"),
            "keywords": [kw.keyword for kw in priority_keywords[:5]],
            "quality_standard": quality_standards.get(level, quality_standards[5]),
            "incentive": "영수증 리뷰 작성 시 할인",
            "mention_strategy": {},
            "trust_checklist": [],
            "templates": self._generate_review_templates_v5(
                [kw.keyword for kw in priority_keywords[:3]],
                category,
                level
            )
        }

    def _generate_review_templates_v5(
        self,
        keywords: List[str],
        category: str,
        level: int
    ) -> Dict[str, str]:
        """키워드 기반 영수증 리뷰 템플릿 생성"""

        if not keywords:
            keywords = ["지역명 업종"]

        kw1 = keywords[0] if len(keywords) > 0 else "키워드"
        kw2 = keywords[1] if len(keywords) > 1 else "키워드"
        kw3 = keywords[2] if len(keywords) > 2 else "키워드"

        # 업종별 표현
        if category == "음식점":
            action = "식사"
            good_point = "음식 맛/서비스/분위기"
        elif category == "카페":
            action = "방문"
            good_point = "커피/디저트/공간"
        elif category == "미용실":
            action = "시술"
            good_point = "실력/서비스/분위기"
        elif category == "병원":
            action = "진료"
            good_point = "진료/친절도/시설"
        elif category == "학원":
            action = "수강"
            good_point = "강의/커리큘럼/강사"
        elif category == "헬스장":
            action = "운동"
            good_point = "시설/프로그램/트레이너"
        else:
            action = "이용"
            good_point = "서비스/품질/분위기"

        # 짧은 리뷰 (50자 이내)
        short = f'"{kw1} {action}했는데, {good_point} 정말 좋았어요! 재방문 의사 있습니다 👍"'

        # 중간 리뷰 (100자 이내)
        medium = f'''"{kw1} 찾다가 발견한 곳인데 {kw2}도 만족스러웠어요.
{action} 시간도 적절하고 분위기도 좋아서 자주 올 것 같습니다.
사진은 {action}한 내용입니다."'''

        # 긴 리뷰 (150자 이내)
        long = f'''"{kw1} 검색해서 방문했습니다!

🕐 {action} 시간: 평일 낮 12시 40분
⭐ 평가: {kw2} 정말 만족

{kw3} 중에서도 여기가 제일 좋은 것 같아요. {good_point} 정말 훌륭하고 직원분들도 친절하셔서 기분 좋게 {action}했습니다. 다음에 또 오겠습니다!"'''

        return {
            "short": short,
            "medium": medium,
            "long": long
        }

    def get_rank_target(self, level: int) -> tuple[str, str, float]:
        """
        레벨별 목표 순위 및 타임라인

        Returns:
            (목표 순위, 예상 기간, 트래픽 전환율)
        """
        targets = {
            5: ("Top 1-3", "1-2주", 0.25),
            4: ("Top 5", "1개월", 0.15),
            3: ("Top 10", "2-3개월", 0.10),
            2: ("Top 20", "6개월", 0.05),
            1: ("노출 목표", "장기", 0.02)
        }

        return targets.get(level, ("Top 10", "2개월", 0.10))
