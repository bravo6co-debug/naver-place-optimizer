#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 로컬 검색 API 통합
경쟁 업체 수 파악
"""

import os
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential


class NaverLocalAPI:
    """네이버 로컬 검색 API 클라이언트"""

    BASE_URL = "https://openapi.naver.com/v1/search/local.json"

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.getenv("NAVER_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("NAVER_CLIENT_SECRET")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_competition_count(self, keyword: str) -> int:
        """
        키워드로 검색되는 업체 수 조회

        Args:
            keyword: 검색 키워드

        Returns:
            검색 결과 업체 수
        """
        if not self.client_id or not self.client_secret:
            return self._estimate_competition(keyword)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.BASE_URL,
                    headers={
                        "X-Naver-Client-Id": self.client_id,
                        "X-Naver-Client-Secret": self.client_secret
                    },
                    params={"query": keyword, "display": 1}
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("total", 0)
                else:
                    return self._estimate_competition(keyword)

        except Exception as e:
            print(f"네이버 로컬 API 오류: {e}")
            return self._estimate_competition(keyword)

    def _estimate_competition(self, keyword: str) -> int:
        """경쟁도 추정 (API 실패 시 폴백)"""
        word_count = len(keyword.split())

        if word_count >= 4:
            return 100  # 롱테일
        elif word_count == 3:
            return 500
        elif word_count == 2:
            return 5000
        else:
            return 50000

    def calculate_competition_score(self, result_count: int) -> int:
        """
        검색 결과 수를 경쟁도 점수(0-100)로 변환

        Args:
            result_count: 검색 결과 수

        Returns:
            경쟁도 점수 (0-100)
        """
        if result_count < 100:
            return 10
        elif result_count < 1000:
            return 30
        elif result_count < 10000:
            return 50
        elif result_count < 100000:
            return 70
        else:
            return 90
