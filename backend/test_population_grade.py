#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인구 기반 등급 시스템 테스트
"""

import asyncio
from engine_v3 import UnifiedKeywordEngine


async def test_population_grade_system():
    print("=== 인구 기반 등급 시스템 테스트 ===\n")

    engine = UnifiedKeywordEngine()

    # Test 1: 대도시 (50만+) - estimated_b (C급)
    print("[1] 대도시 (서울 강남구, 56만) - estimated_b 예상")
    metrics_gangnam = await engine.analyze_keyword(
        keyword="강남 맛집 추천",
        level=3,
        location="서울 강남구",
        category="음식점"
    )
    print(f"  키워드: {metrics_gangnam.keyword}")
    print(f"  데이터 등급: {metrics_gangnam.data_source}")
    print(f"  검색량: {metrics_gangnam.estimated_monthly_searches:,}회/월")
    print()

    # Test 2: 중도시 (20~50만) - estimated_c (D급)
    print("[2] 중도시 (전남 목포시, 23만) - estimated_c 예상")
    metrics_mokpo = await engine.analyze_keyword(
        keyword="목포 카페 추천",
        level=3,
        location="전남 목포시",
        category="카페"
    )
    print(f"  키워드: {metrics_mokpo.keyword}")
    print(f"  데이터 등급: {metrics_mokpo.data_source}")
    print(f"  검색량: {metrics_mokpo.estimated_monthly_searches:,}회/월")
    print()

    # Test 3: 소도시 (10~20만) - estimated_d (E급)
    print("[3] 소도시 (충북 충주시, 21만) - estimated_d 예상")
    metrics_chungju = await engine.analyze_keyword(
        keyword="충주 미용실",
        level=3,
        location="충북 충주시",
        category="미용실"
    )
    print(f"  키워드: {metrics_chungju.keyword}")
    print(f"  데이터 등급: {metrics_chungju.data_source}")
    print(f"  검색량: {metrics_chungju.estimated_monthly_searches:,}회/월")
    print()

    # Test 4: 군 지역 (5~10만) - estimated_e (F급)
    print("[4] 군 지역 (강원 속초시, 8.2만) - estimated_e 예상")
    metrics_sokcho = await engine.analyze_keyword(
        keyword="속초 숙소",
        level=3,
        location="강원 속초시",
        category="숙박"
    )
    print(f"  키워드: {metrics_sokcho.keyword}")
    print(f"  데이터 등급: {metrics_sokcho.data_source}")
    print(f"  검색량: {metrics_sokcho.estimated_monthly_searches:,}회/월")
    print()

    # Test 5: 소규모 (5만 미만) - estimated_f (F급)
    print("[5] 소규모 지역 (강원 태백시, 4.2만) - estimated_f 예상")
    metrics_taebaek = await engine.analyze_keyword(
        keyword="태백 맛집",
        level=3,
        location="강원 태백시",
        category="음식점"
    )
    print(f"  키워드: {metrics_taebaek.keyword}")
    print(f"  데이터 등급: {metrics_taebaek.data_source}")
    print(f"  검색량: {metrics_taebaek.estimated_monthly_searches:,}회/월")
    print()

    # Test 6: 미등록 지역 (30만 추정) - estimated_b~c 예상
    print("[6] 미등록 지역 (기본값 30만) - estimated 예상")
    metrics_unknown = await engine.analyze_keyword(
        keyword="미등록지역 카페",
        level=3,
        location="미등록 지역",
        category="카페"
    )
    print(f"  키워드: {metrics_unknown.keyword}")
    print(f"  데이터 등급: {metrics_unknown.data_source}")
    print(f"  검색량: {metrics_unknown.estimated_monthly_searches:,}회/월")
    print()

    print("=== 등급 체계 ===")
    print("S급: api (네이버 검색광고 API)")
    print("A급: restaurant_stats, restaurant_stats_fallback (정부 통계)")
    print("B급: estimated (실제 인구 데이터 기반 추정)")
    print("C급: estimated_b (추정 인구 50만+)")
    print("D급: estimated_c (추정 인구 20~50만)")
    print("E급: estimated_d (추정 인구 10~20만)")
    print("F급: estimated_e (추정 인구 5~10만)")
    print("F급: estimated_f (추정 인구 5만 미만)")
    print()
    print("=== 테스트 완료 ===")


if __name__ == "__main__":
    asyncio.run(test_population_grade_system())
