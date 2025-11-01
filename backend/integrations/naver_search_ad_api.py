#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 검색광고 API 통합 (개선 버전)
실제 검색량 및 3단계 경쟁도 제공
"""

import os
import hashlib
import hmac
import base64
import time
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class NaverSearchAdAPI:
    """네이버 검색광고 API 클라이언트"""

    BASE_URL = "https://api.searchad.naver.com"  # ✅ 올바른 URL

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
        self.is_authenticated = bool(self.api_key and self.secret_key and self.customer_id)

    def _generate_signature(self, timestamp: str, method: str, uri: str) -> str:
        """API 서명 생성 (HmacSHA256)"""
        try:
            message = f"{timestamp}.{method}.{uri}"
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            print(f"❌ 서명 생성 실패: {e}")
            return ""

    def _get_headers(self, method: str, uri: str) -> Dict[str, str]:
        """요청 헤더 생성"""
        timestamp = str(int(time.time() * 1000))  # ✅ time.time() 사용
        signature = self._generate_signature(timestamp, method, uri)

        headers = {
            "Content-Type": "application/json",
            "X-Timestamp": timestamp,
            "X-API-KEY": self.api_key,
            "X-Customer": self.customer_id,
            "X-Signature": signature,
        }

        # None 값 제거
        return {k: v for k, v in headers.items() if v}

    def get_keyword_stats(self, keywords: List[str], device: Optional[str] = None, month_count: int = 1) -> List[Dict]:
        """
        키워드 통계 조회 (배치 처리 지원)

        Args:
            keywords: 조회할 키워드 리스트 (최대 5000개)
            device: 기기 ("pc", "mobile", None=전체)
            month_count: 조회 개월 수 (1-12)

        Returns:
            키워드별 통계 데이터 리스트
        """
        if not self.is_authenticated:
            print("⚠️ 네이버 검색광고 API 인증 정보 없음")
            return []

        # ✅ 배치 처리 (100개씩)
        all_results = []
        batch_size = 100

        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            results = self._request_keyword_stats(batch, device, month_count)
            all_results.extend(results)

            # ✅ 레이트 리미팅
            if i + batch_size < len(keywords):
                time.sleep(0.5)

        return all_results

    def _request_keyword_stats(self, keywords: List[str], device: Optional[str] = None, month_count: int = 1) -> List[Dict]:
        """실제 API 요청"""
        uri = "/keywordstool"
        method = "GET"

        try:
            params = {
                "hintKeywords": ",".join(keywords),
                "showDetail": 1,
                "month": month_count
            }

            if device and device in ["pc", "mobile"]:
                params["device"] = device

            print(f"🔍 검색광고 API 요청: {len(keywords)}개 키워드")

            response = requests.get(
                f"{self.BASE_URL}{uri}",
                params=params,
                headers=self._get_headers(method, uri),
                timeout=30
            )

            # ✅ 상태 코드별 처리
            if response.status_code == 200:
                data = response.json()
                keyword_list = data.get("keywordList", [])
                print(f"   ✅ 수신 성공: {len(keyword_list)}개 키워드")
                return keyword_list
            elif response.status_code == 401:
                print(f"❌ 인증 실패 (401) - API 키 확인 필요")
                return []
            elif response.status_code == 429:
                # ✅ 재시도 로직
                print(f"⚠️ 레이트 리미팅 (429) - 2초 대기 후 재시도")
                time.sleep(2)
                return self._request_keyword_stats(keywords, device, month_count)
            else:
                print(f"❌ API 오류 ({response.status_code}): {response.text[:200]}")
                return []

        except requests.exceptions.Timeout:
            print(f"❌ API 타임아웃 (30초)")
            return []
        except Exception as e:
            print(f"❌ API 호출 실패: {type(e).__name__}: {e}")
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
        if not self.is_authenticated:
            return []

        try:
            results = self.get_keyword_stats([keyword])
            return results[:max_results]
        except Exception as e:
            print(f"❌ 연관 키워드 조회 실패: {e}")
            return []

    def parse_keyword_data(self, raw_data: Dict) -> Dict:
        """
        API 응답 데이터 파싱 (간소화 버전)

        Args:
            raw_data: API 원본 데이터

        Returns:
            파싱된 데이터
        """
        pc_searches = raw_data.get("monthlyPcQcCnt", 0) or 0
        mobile_searches = raw_data.get("monthlyMobileQcCnt", 0) or 0

        return {
            "keyword": raw_data.get("relKeyword", ""),
            "monthly_pc_searches": pc_searches,
            "monthly_mobile_searches": mobile_searches,
            "monthly_total_searches": pc_searches + mobile_searches,
            "monthly_avg_clicks": (raw_data.get("monthlyAvePcClkCnt", 0) or 0) + (raw_data.get("monthlyAveMobileClkCnt", 0) or 0),
            "monthly_avg_ctr": raw_data.get("monthlyAvePcCtr", 0) or 0,
            "competition_level": raw_data.get("compIdx", "중간"),  # ✅ 3단계: "높음", "중간", "낮음"
        }

    def validate_credentials(self) -> bool:
        """API 자격증명 검증"""
        if not self.is_authenticated:
            print("⚠️ API 인증 정보 없음")
            return False

        try:
            # 간단한 테스트 키워드로 검증
            response = requests.get(
                f"{self.BASE_URL}/keywordstool",
                params={"hintKeywords": "test", "showDetail": 1},
                headers=self._get_headers("GET", "/keywordstool"),
                timeout=10
            )
            is_valid = response.status_code in [200, 400]  # 400도 인증 성공 시 반환 가능
            if is_valid:
                print("✅ API 자격증명 유효")
            else:
                print(f"⚠️ API 자격증명 검증 실패: {response.status_code}")
            return is_valid
        except Exception as e:
            print(f"❌ 자격증명 검증 실패: {e}")
            return False


# 사용 예시
if __name__ == "__main__":
    api = NaverSearchAdAPI()

    # 자격증명 검증
    print(f"\n🔐 API 인증 상태: {api.is_authenticated}")
    if api.is_authenticated:
        api.validate_credentials()

    # 키워드 통계 조회
    keywords = ["강남 카페", "강남역 브런치", "강남 맛집"]
    stats = api.get_keyword_stats(keywords)

    print(f"\n📊 키워드 분석 결과 ({len(stats)}개):")
    print("-" * 60)
    for stat in stats:
        parsed = api.parse_keyword_data(stat)
        print(f"키워드: {parsed['keyword']}")
        print(f"  월간 검색수: {parsed['monthly_total_searches']:,}")
        print(f"  경쟁도: {parsed['competition_level']}")
        print()
