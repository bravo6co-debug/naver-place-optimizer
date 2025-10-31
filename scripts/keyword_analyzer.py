#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 플레이스 키워드 분석 도구

업종과 지역 정보를 입력받아 최적의 키워드 조합을 추천합니다.
"""

import argparse
import json
from typing import List, Dict, Tuple


class KeywordAnalyzer:
    """네이버 플레이스 키워드 분석기"""
    
    # 업종별 핵심 키워드
    BUSINESS_KEYWORDS = {
        "음식점": ["맛집", "맛있는", "유명한", "인기", "전문점", "맛집추천"],
        "카페": ["카페", "커피", "디저트", "브런치", "베이커리", "분위기좋은"],
        "미용실": ["미용실", "헤어샵", "미용", "커트", "펌", "염색"],
        "병원": ["병원", "의원", "한의원", "치과", "정형외과", "피부과"],
        "학원": ["학원", "교습소", "과외", "수업", "강의", "교육"],
        "숙박": ["호텔", "모텔", "펜션", "게스트하우스", "숙박", "숙소"],
        "헬스장": ["헬스장", "피트니스", "체육관", "PT", "운동", "짐"],
        "세차": ["세차", "세차장", "셀프세차", "광택", "코팅", "디테일링"],
        "정비소": ["정비소", "카센터", "자동차정비", "수리", "정비", "차량"],
    }
    
    # 지역 키워드 패턴
    LOCATION_PATTERNS = {
        "직접언급": ["근처", "주변", "가까운"],
        "역세권": ["역", "역근처"],
    }
    
    # 품질 키워드
    QUALITY_KEYWORDS = [
        "최고", "프리미엄", "고급", "전문", "숙련", "베테랑",
        "친절", "깨끗", "위생", "안전", "정직", "합리적"
    ]
    
    # 경쟁도 분류 기준
    COMPETITION_LEVELS = {
        "high": ["강남", "홍대", "신촌", "명동", "이태원", "여의도"],
        "medium": ["강북", "노원", "송파", "마포", "영등포"],
        "low": []  # 기본값
    }
    
    def __init__(self, business_type: str, location: str):
        self.business_type = business_type
        self.location = location
        self.city = self._extract_city(location)
        self.district = self._extract_district(location)
    
    def _extract_city(self, location: str) -> str:
        """도시명 추출"""
        cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종"]
        for city in cities:
            if city in location:
                return city
        return ""
    
    def _extract_district(self, location: str) -> str:
        """구/동 추출"""
        parts = location.split()
        if len(parts) >= 2:
            return parts[-1]
        return ""
    
    def analyze_competition(self) -> str:
        """경쟁도 분석"""
        for level, areas in self.COMPETITION_LEVELS.items():
            for area in areas:
                if area in self.location:
                    return level
        return "low"
    
    def generate_primary_keywords(self) -> List[str]:
        """주력 키워드 생성"""
        keywords = []
        
        # 업종 키워드
        if self.business_type in self.BUSINESS_KEYWORDS:
            keywords.extend(self.BUSINESS_KEYWORDS[self.business_type][:3])
        
        # 지역 조합
        if self.city:
            keywords.append(f"{self.city} {self.business_type}")
        if self.district:
            keywords.append(f"{self.district} {self.business_type}")
            
        return keywords
    
    def generate_secondary_keywords(self) -> List[str]:
        """보조 키워드 생성"""
        keywords = []
        
        # 지역 + 품질 조합
        if self.district:
            keywords.append(f"{self.district} 맛집")
            keywords.append(f"{self.district} 추천")
        
        # 근처 키워드
        for pattern in self.LOCATION_PATTERNS["직접언급"]:
            keywords.append(f"{self.district} {pattern} {self.business_type}")
        
        return keywords[:5]
    
    def generate_longtail_keywords(self) -> List[str]:
        """롱테일 키워드 생성"""
        keywords = []
        
        # 품질 + 지역 + 업종
        for quality in self.QUALITY_KEYWORDS[:4]:
            if self.district:
                keywords.append(f"{self.district} {quality} {self.business_type}")
        
        return keywords[:8]
    
    def analyze(self) -> Dict:
        """전체 키워드 분석 실행"""
        competition = self.analyze_competition()
        
        result = {
            "business_info": {
                "type": self.business_type,
                "location": self.location,
                "city": self.city,
                "district": self.district,
            },
            "competition_level": competition,
            "keywords": {
                "primary": self.generate_primary_keywords(),
                "secondary": self.generate_secondary_keywords(),
                "longtail": self.generate_longtail_keywords(),
            },
            "recommendations": self._generate_recommendations(competition)
        }
        
        return result
    
    def _generate_recommendations(self, competition: str) -> List[str]:
        """경쟁도에 따른 추천사항"""
        recommendations = []
        
        if competition == "high":
            recommendations.extend([
                "롱테일 키워드를 적극 활용하세요",
                "차별화 포인트를 부각하세요",
                "리뷰 관리에 더욱 집중하세요",
                "사진 품질을 최고 수준으로 유지하세요",
            ])
        elif competition == "medium":
            recommendations.extend([
                "주력 키워드와 보조 키워드를 균형있게 사용하세요",
                "지역 커뮤니티 활동을 강화하세요",
                "정기적인 프로모션을 운영하세요",
            ])
        else:  # low
            recommendations.extend([
                "주력 키워드에 집중하세요",
                "기본적인 정보 완성도를 높이세요",
                "꾸준한 리뷰 수집이 중요합니다",
            ])
        
        return recommendations


def main():
    parser = argparse.ArgumentParser(
        description="네이버 플레이스 키워드 분석 도구"
    )
    parser.add_argument(
        "--business-type",
        required=True,
        help="업종 (예: 음식점, 카페, 미용실)",
    )
    parser.add_argument(
        "--location",
        required=True,
        help="위치 (예: 서울 강남구, 부산 해운대)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="결과를 저장할 JSON 파일 경로",
    )
    
    args = parser.parse_args()
    
    # 키워드 분석 실행
    analyzer = KeywordAnalyzer(args.business_type, args.location)
    result = analyzer.analyze()
    
    # 결과 출력
    print("\n" + "="*60)
    print("네이버 플레이스 키워드 분석 결과")
    print("="*60 + "\n")
    
    print(f"[업체 정보]")
    print(f"  업종: {result['business_info']['type']}")
    print(f"  위치: {result['business_info']['location']}")
    print(f"  경쟁도: {result['competition_level'].upper()}\n")
    
    print(f"[주력 키워드 - Primary Keywords]")
    for kw in result['keywords']['primary']:
        print(f"  * {kw}")
    
    print(f"\n[보조 키워드 - Secondary Keywords]")
    for kw in result['keywords']['secondary']:
        print(f"  * {kw}")
    
    print(f"\n[롱테일 키워드 - Long-tail Keywords]")
    for kw in result['keywords']['longtail']:
        print(f"  * {kw}")
    
    print(f"\n[추천사항]")
    for rec in result['recommendations']:
        print(f"  > {rec}")
    
    print("\n" + "="*60 + "\n")
    
    # JSON 저장
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[완료] 결과가 {args.output}에 저장되었습니다.\n")


if __name__ == "__main__":
    main()
