#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 검색광고 API 통합
실제 검색량, 경쟁도, CPC 데이터 제공
"""

import os
import hashlib
import hmac
import base64
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class NaverSearchAdAPI:
    """네이버 검색광고 API 클라이언트"""

    BASE_URL = "https://api.naver.com"

    def __init__(self, customer_id: Optional[str] = None, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        초기화

        Args:
            customer_id: 네이버 검색광고 고객 ID
            api_key: API 키
            secret_key: Secret 키
        """
        self.customer_id = customer_id or os.getenv("NAVER_SEARCH_AD_CUSTOMER_ID")
        self.api_key = api_key or os.getenv("NAVER_SEARCH_AD_API_KEY")
        self.secret_key = secret_key or os.getenv("NAVER_SEARCH_AD_SECRET_KEY")

    def _generate_signature(self, timestamp: str, method: str, uri: str) -> str:
        """API 서명 생성"""
        message = f"{timestamp}.{method}.{uri}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')

    def _get_headers(self, method: str, uri: str) -> Dict[str, str]:
        """요청 헤더 생성"""
        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature = self._generate_signature(timestamp, method, uri)

        return {
            "X-Timestamp": timestamp,
            "X-API-KEY": self.api_key,
            "X-Customer": self.customer_id,
            "X-Signature": signature,
            "Content-Type": "application/json"
        }

    def get_keyword_stats(self, keywords: List[str], device: Optional[str] = None, month_count: int = 1) -> List[Dict]:
        """
        키워드 통계 조회 (월간 검색수, 클릭수, 경쟁도)

        Args:
            keywords: 조회할 키워드 리스트 (최대 5000개)
            device: 기기 (None=전체, "pc", "mobile")
            month_count: 조회 개월 수 (1-12)

        Returns:
            키워드별 통계 데이터 리스트
        """
        if not self.api_key or not self.secret_key:
            print("⚠️ 네이버 검색광고 API 키가 설정되지 않음")
            return []

        uri = "/keywordstool"
        method = "GET"

        try:
            params = {
                "hintKeywords": ",".join(keywords),
                "showDetail": 1
            }

            if device:
                params["device"] = device
            if month_count:
                params["month"] = month_count

            print(f"🔍 네이버 검색광고 API 요청: {keywords}")

            response = requests.get(
                f"{self.BASE_URL}{uri}",
                params=params,
                headers=self._get_headers(method, uri),
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                keyword_list = data.get("keywordList", [])
                print(f"   응답 결과: {len(keyword_list)}개 키워드")
                return keyword_list
            else:
                print(f"❌ 네이버 검색광고 API 오류: {response.status_code}")
                print(f"   응답 내용: {response.text[:200]}")
                return []

        except Exception as e:
            print(f"❌ 네이버 검색광고 API 호출 실패: {type(e).__name__}: {e}")
            return []

    def get_related_keywords(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """
        연관 키워드 조회

        Args:
            keyword: 기준 키워드
            max_results: 최대 결과 수

        Returns:
            연관 키워드 리스트
        """
        if not self.api_key or not self.secret_key:
            return []

        uri = "/keywordstool"
        method = "GET"

        try:
            params = {
                "hintKeywords": keyword,
                "showDetail": 1
            }

            response = requests.get(
                f"{self.BASE_URL}{uri}",
                params=params,
                headers=self._get_headers(method, uri),
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("keywordList", [])
                return results[:max_results]
            else:
                return []

        except Exception as e:
            print(f"연관 키워드 조회 실패: {e}")
            return []

    def parse_keyword_data(self, raw_data: Dict) -> Dict:
        """
        API 응답 데이터를 파싱하여 사용하기 쉬운 형태로 변환

        Args:
            raw_data: API 원본 데이터

        Returns:
            파싱된 데이터
        """
        return {
            "keyword": raw_data.get("relKeyword"),
            "monthly_pc_searches": raw_data.get("monthlyPcQcCnt", 0),
            "monthly_mobile_searches": raw_data.get("monthlyMobileQcCnt", 0),
            "monthly_total_searches": raw_data.get("monthlyPcQcCnt", 0) + raw_data.get("monthlyMobileQcCnt", 0),
            "monthly_avg_clicks": raw_data.get("monthlyAvePcClkCnt", 0) + raw_data.get("monthlyAveMobileClkCnt", 0),
            "monthly_avg_ctr": raw_data.get("monthlyAvePcCtr", 0),
            "competition_level": raw_data.get("compIdx"),  # "높음", "중간", "낮음"
            "avg_cpc": (raw_data.get("plAvgDepth", 0) or 0),  # 평균 클릭 비용
        }


# 사용 예시
if __name__ == "__main__":
    api = NaverSearchAdAPI()

    # 키워드 통계 조회
    keywords = ["강남 카페", "강남역 브런치", "강남 맛집"]
    stats = api.get_keyword_stats(keywords)

    for stat in stats:
        parsed = api.parse_keyword_data(stat)
        print(f"키워드: {parsed['keyword']}")
        print(f"  월간 검색수: {parsed['monthly_total_searches']:,}")
        print(f"  경쟁도: {parsed['competition_level']}")
        print(f"  평균 CPC: {parsed['avg_cpc']}원")
        print()
