#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최적화 테스트: Level 1-2 vs Level 3-5
"""

import asyncio
from engine_v3 import UnifiedKeywordEngine


async def test_optimization():
    print("=== 최적화 테스트 ===\n")

    engine = UnifiedKeywordEngine()

    # Test Level 2 (should use API retry + fetch results)
    print("[1] Level 2 키워드 분석 (API 재시도 + 상세 조회)")
    metrics_l2 = await engine.analyze_keyword(
        keyword="부산 분식 맛집",
        level=2,
        location="부산 중구",
        category="음식점"
    )
    print(f"  키워드: {metrics_l2.keyword}")
    print(f"  검색량: {metrics_l2.estimated_monthly_searches:,}회/월 (소스: {metrics_l2.data_source})")
    print(f"  경쟁도: {metrics_l2.competition_score}/100")
    print(f"  예상 일방문자: {metrics_l2.estimated_traffic}명/일")
    print()

    # Test Level 5 (should skip API retry + skip naver results)
    print("[2] Level 5 키워드 분석 (간소화 - API/결과 생략)")
    metrics_l5 = await engine.analyze_keyword(
        keyword="부산 중구 분식 데이트 추천 분위기 좋은",
        level=5,
        location="부산 중구",
        category="음식점"
    )
    print(f"  키워드: {metrics_l5.keyword}")
    print(f"  검색량: {metrics_l5.estimated_monthly_searches:,}회/월 (소스: {metrics_l5.data_source})")
    print(f"  경쟁도: {metrics_l5.competition_score}/100")
    print(f"  예상 일방문자: {metrics_l5.estimated_traffic}명/일")
    print()

    print("=== 테스트 완료 ===")


if __name__ == "__main__":
    asyncio.run(test_optimization())
