#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 등급 시스템 테스트
Level 1: S/A급만 허용
Level 2: 최소 A급 목표 (B급 허용)
Level 3-5: 모든 등급 허용
"""

import asyncio
from engine_v3 import UnifiedKeywordEngine


async def test_data_grade_system():
    print("=== 데이터 등급 시스템 테스트 ===\n")

    engine = UnifiedKeywordEngine()

    # Test Level 1 (무조건 S/A급)
    print("[1] Level 1 키워드 - S/A급만 허용")
    metrics_l1 = await engine.analyze_keyword(
        keyword="부산 분식",
        level=1,
        location="부산 중구",
        category="음식점"
    )
    print(f"  키워드: {metrics_l1.keyword}")
    print(f"  데이터 등급: {metrics_l1.data_source}")
    print(f"  ✅ Level 1 등급 검증: {'PASS' if metrics_l1.data_source in ['api', 'restaurant_stats', 'restaurant_stats_fallback'] else 'FAIL'}")
    print()

    # Test Level 2 (A급 목표, B급 허용)
    print("[2] Level 2 키워드 - 최소 A급 목표")
    metrics_l2 = await engine.analyze_keyword(
        keyword="부산 분식 맛집",
        level=2,
        location="부산 중구",
        category="음식점"
    )
    print(f"  키워드: {metrics_l2.keyword}")
    print(f"  데이터 등급: {metrics_l2.data_source}")
    print(f"  ✅ Level 2 등급 검증: {'PASS' if metrics_l2.data_source in ['api', 'restaurant_stats', 'restaurant_stats_fallback', 'estimated'] else 'FAIL'}")
    print()

    # Test Level 5 (모든 등급 허용)
    print("[3] Level 5 키워드 - 모든 등급 허용")
    metrics_l5 = await engine.analyze_keyword(
        keyword="부산 중구 분식 데이트 추천 분위기 좋은",
        level=5,
        location="부산 중구",
        category="음식점"
    )
    print(f"  키워드: {metrics_l5.keyword}")
    print(f"  데이터 등급: {metrics_l5.data_source}")
    print(f"  ✅ Level 5 등급 검증: PASS (모든 등급 허용)")
    print()

    print("=== 등급 체계 ===")
    print("S급: api (네이버 검색광고 API)")
    print("A급: restaurant_stats, restaurant_stats_fallback (정부 통계)")
    print("B~F급: estimated (추정치)")
    print()
    print("=== 테스트 완료 ===")


if __name__ == "__main__":
    asyncio.run(test_data_grade_system())
