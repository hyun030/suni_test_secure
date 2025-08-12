# -*- coding: utf-8 -*-
import os
import streamlit as st
from dotenv import load_dotenv

# .env 파일 로드 (로컬 환경용)
load_dotenv()

# ==========================
# API 키 및 인증 정보
# Streamlit Cloud와 로컬 환경 모두 지원
# ==========================
def get_api_key(key_name, default_value=""):
    """API 키를 안전하게 가져오는 함수"""
    # Streamlit Cloud에서 secrets 사용
    if hasattr(st, 'secrets') and st.secrets:
        return st.secrets.get(key_name, default_value)
    # 로컬 환경에서 환경 변수 사용
    else:
        return os.getenv(key_name, default_value)

# API 키는 환경 변수나 Streamlit secrets에서만 가져옴 (코드에 하드코딩하지 않음)
DART_API_KEY = get_api_key("DART_API_KEY", "")
OPENAI_API_KEY = get_api_key("OPENAI_API_KEY", "")
GOOGLE_NEWS_API_KEY = get_api_key("GOOGLE_NEWS_API_KEY", "")

# 구글시트 설정
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/16g1G89xoxyqF32YLMD8wGYLnQzjq2F_ew6G1AHH4bCA/edit?usp=sharing"
SHEET_ID = "16g1G89xoxyqF32YLMD8wGYLnQzjq2F_ew6G1AHH4bCA"

# 구글 서비스 계정 키 (JSON 형식)
# 보안을 위해 st.secrets 또는 환경 변수로 관리하는 것을 강력히 권장합니다.
# 예: GOOGLE_SERVICE_ACCOUNT_JSON = st.secrets["gcp_service_account"]
GOOGLE_SERVICE_ACCOUNT_JSON = None # 여기에 JSON 내용을 직접 넣거나, st.secrets에서 불러오세요.

# ==========================
# 시각화 및 UI 설정
# ==========================
SK_COLORS = {
    'primary': '#E31E24',      # SK 레드
    'secondary': '#FF6B35',    # SK 오렌지
    'accent': '#004EA2',       # SK 블루
    'success': '#00A651',      # 성공 색상
    'warning': '#FF9500',      # 경고 색상
    'competitor': '#6C757D',   # 기본 경쟁사 색상 (회색)
    'competitor_1': '#AEC6CF', # 파스텔 블루
    'competitor_2': '#FFB6C1', # 파스텔 핑크
    'competitor_3': '#98FB98', # 파스텔 그린
    'competitor_4': '#F0E68C', # 파스텔 옐로우
    'competitor_5': '#DDA0DD', # 파스텔 퍼플
    'competitor_green': '#98FB98',   # 파스텔 그린
    'competitor_blue': '#AEC6CF',    # 파스텔 블루
    'competitor_yellow': '#F0E68C',  # 파스텔 옐로우
    'competitor_purple': '#DDA0DD',  # 파스텔 퍼플
    'competitor_orange': '#FFB347',  # 파스텔 오렌지
    'competitor_mint': '#98FF98',    # 파스텔 민트
}

# 분석 대상 회사 목록 (UI에서 사용)
COMPANIES_LIST = ["SK에너지", "GS칼텍스", "HD현대오일뱅크", "S-Oil"]
DEFAULT_SELECTED_COMPANIES = ["SK에너지", "GS칼텍스"]

# ==========================
# DART API 관련 설정
# ==========================
COMPANY_NAME_MAPPING = {
    "SK에너지": ["SK에너지", "SK에너지주식회사", "에스케이에너지", "SK ENERGY"],
    "GS칼텍스": ["GS칼텍스", "지에스칼텍스", "GS칼텍스주식회사"],
    "HD현대오일뱅크": ["HD현대오일뱅크", "HD현대오일뱅크주식회사", "현대오일뱅크", "현대오일뱅크주식회사", "HYUNDAI OILBANK", "267250"],
    "현대오일뱅크": ["HD현대오일뱅크", "HD현대오일뱅크주식회사", "현대오일뱅크", "현대오일뱅크주식회사"],
    "S-Oil": ["S-Oil", "S-Oil Corporation", "에쓰오일", "에스오일", "주식회사S-Oil", "S-OIL", "s-oil", "010950"]
}

STOCK_CODE_MAPPING = {
    "S-Oil": "010950",
    "GS칼텍스": "089590",
    "HD현대오일뱅크": "267250",
    "현대오일뱅크": "267250",
    "SK에너지": "096770",
}

# ==========================
# 뉴스 수집 관련 설정
# ==========================
DEFAULT_RSS_FEEDS = {
    "한국경제_산업": "https://rss.hankyung.com/industry",
    "매일경제_산업": "https://www.mk.co.kr/rss/40300001/",
    "이데일리_산업": "http://rss.edaily.co.kr/rss/news_industry.xml",
    "머니투데이_산업": "https://rss.mt.co.kr/rss/industry.xml",
    "조선비즈_산업": "https://biz.chosun.com/rss/industry.xml",
    "연합뉴스_산업": "https://www.yna.co.kr/rss/industry.xml",
    "연합뉴스_경제": "https://www.yna.co.kr/rss/economy.xml",
}

OIL_KEYWORDS = [
    # 핵심 정유사 (필수 키워드)
    "SK에너지", "S-Oil", "HD현대오일뱅크", "GS칼텍스",
    
    # 정유 산업 키워드 (필수 키워드)
    "정유", "정유업계", "정유사", "석유화학",
    
    # 관련 비즈니스 키워드
    "영업이익", "실적", "수익성", "투자", "매출", "손실", "정제마진",
    "원유", "나프타", "휘발유", "경유", "석유제품", "화학제품",
    "유가", "WTI", "두바이유", "브렌트유", "석유가격",
    
    # 추가 산업 키워드
    "화학산업", "에너지산업", "석유산업", "정제업", "정제공정",
]

# 벤치마킹 키워드 (뉴스 분석용) - 정유 특화
BENCHMARKING_KEYWORDS = [
    # 핵심 정유사 (필수 키워드)
    "SK에너지", "S-Oil", "HD현대오일뱅크", "GS칼텍스",
    
    # 정유 산업 키워드 (필수 키워드)
    "정유", "정유업계", "정유사", "석유화학", "석유화학사",
    
    # 핵심 비즈니스 키워드
    "영업이익", "실적", "수익성", "매출", "손실", "투자", "정제마진",
    "원유", "나프타", "휘발유", "경유", "석유제품", "화학제품",
    "유가", "WTI", "두바이유", "브렌트유", "석유가격",
    
    # 추가 관련 키워드
    "사업확장", "원가절감", "효율성", "생산성", "경쟁력", "시장점유율",
    "친환경", "탄소중립", "ESG", "신재생에너지", "수소", "바이오"
]


# ==========================
# 이메일 관련 설정
# ==========================
# 실제 발송 기능은 보안상 구현하지 않음. UI용 링크 목록만 제공.
MAIL_PROVIDERS = {
    "네이버": "https://mail.naver.com/",
    "구글(Gmail)": "https://mail.google.com/",
    "다음": "https://mail.daum.net/",
    "아웃룩(Outlook)": "https://outlook.live.com/",
}