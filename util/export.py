# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime

import config
from data.loader import DartAPICollector, QuarterlyDataCollector
from data.preprocess import SKFinancialDataProcessor, FinancialDataProcessor 
from insight.openai_api import OpenAIInsightGenerator
from visualization.charts import (
    create_sk_bar_chart, create_sk_radar_chart, 
    create_quarterly_trend_chart, create_gap_trend_chart, 
    create_gap_analysis, create_gap_chart, PLOTLY_AVAILABLE
)

# 🔧 수정된 export 모듈 import
try:
    from util.export import create_excel_report, create_enhanced_pdf_report
    EXPORT_AVAILABLE = True
except ImportError as e:
    print(f"❌ Export 모듈 import 실패: {e}")
    EXPORT_AVAILABLE = False
    
    # 더미 함수 정의 (오류 방지용)
    def create_excel_report(*args, **kwargs):
        return b"Excel export module not available"
    
    def create_enhanced_pdf_report(*args, **kwargs):
        return b"PDF export module not available"

from util.email_util import create_email_ui
from news_collector import create_google_news_tab, GoogleNewsCollector

st.set_page_config(page_title="SK Profit+: 손익 개선 전략 대시보드", page_icon="⚡", layout="wide")

class SessionManager:
    """세션 상태 관리를 담당하는 클래스"""
    
    @staticmethod
    def initialize():
        """세션 상태 초기화 및 데이터 지속성 보장"""
        # 핵심 데이터 변수들
        core_vars = [
            'financial_data', 'quarterly_data',
            'financial_insight', 'integrated_insight',
            'selected_companies', 'manual_financial_data',
            'google_news_data', 'google_news_insight'
        ]
        
        # 각 변수 초기화
        for var in core_vars:
            if var not in st.session_state:
                st.session_state[var] = None
        
        # 설정 변수들
        if 'custom_keywords' not in st.session_state:
            st.session_state.custom_keywords = config.BENCHMARKING_KEYWORDS
        
        if 'last_analysis_time' not in st.session_state:
            st.session_state.last_analysis_time = None
        
        if 'analysis_status' not in st.session_state:
            st.session_state.analysis_status = {}
    
    @staticmethod
    def save_data(data_type: str, data, insight_type: str = None):
        """데이터와 인사이트를 세션에 저장"""
        st.session_state[data_type] = data
        if insight_type:
            st.session_state[insight_type] = data
        st.session_state.last_analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 분석 상태 업데이트
        if data_type not in st.session_state.analysis_status:
            st.session_state.analysis_status[data_type] = {}
        st.session_state.analysis_status[data_type]['completed'] = True
        st.session_state.analysis_status[data_type]['timestamp'] = st.session_state.last_analysis_time
    
    @staticmethod
    def get_data_status(data_type: str) -> dict:
        """데이터 상태 정보 반환"""
        if data_type in st.session_state.analysis_status:
            return st.session_state.analysis_status[data_type]
        return {'completed': False, 'timestamp': None}
    
    @staticmethod
    def is_data_available(data_type: str) -> bool:
        """데이터 사용 가능 여부 확인"""
        data = st.session_state.get(data_type)
        return data is not None and (not hasattr(data, 'empty') or not data.empty)

def sort_quarterly_by_quarter(df: pd.DataFrame) -> pd.DataFrame:
    """분기별 데이터 정렬"""
    if df.empty:
        return df
    
    out = df.copy()
    try:
        # '2024Q1' → (연도=2024, 분기=1) 추출해 정렬키 생성
        out[['연도','분기번호']] = out['분기'].str.extract(r'(\d{4})Q([1-4])').astype(int)
        out = (out.sort_values(['연도','분기번호','회사'])
                   .drop(columns=['연도','분기번호'])
                   .reset_index(drop=True))
    except Exception:
        # 정렬 실패 시 원본 반환
        pass
    return out
    
def resolve_raw_cols_for_gap(df: pd.DataFrame) -> list:
    """
    갭 분석에 사용할 컬럼 목록을 반환.
    1순위: *_원시값 컬럼
    2순위: 세션의 selected_companies 중 df에 존재하는 회사명 컬럼
    3순위: df 전체에서 '구분'과 *_원시값 제외한 회사명 컬럼
    """
    # 1) *_원시값 우선
    raw_cols = [c for c in df.columns if c.endswith('_원시값')]
    if len(raw_cols) >= 2:
        return raw_cols

    # 2) 선택한 회사 중 존재하는 컬럼
    preferred = st.session_state.get('selected_companies') or []
    cols = [c for c in preferred if c in df.columns and c != '구분']
    if len(cols) >= 2:
        return cols

    # 3) 남아있는 회사명 컬럼 자동 선택
    cols = [c for c in df.columns if c != '구분' and not c.endswith('_원시값')]
    return cols

def render_financial_analysis_tab():
    """재무분석 탭 렌더링"""
    st.subheader("📈 DART 공시 데이터 심층 분석")
    
    # 분석 상태 표시
    if SessionManager.is_data_available('financial_data'):
        status = SessionManager.get_data_status('financial_data')
        if status.get('completed'):
            st.success(f"✅ 재무분석 완료 ({status.get('timestamp', '시간 정보 없음')})")
    
    selected_companies = st.multiselect(
        "분석할 기업 선택", 
        config.COMPANIES_LIST, 
        default=config.DEFAULT_SELECTED_COMPANIES
    )
    # ✅ 선택한 회사를 세션에 저장 (폴백 로직에서 씀)
    st.session_state.selected_companies = selected_companies
    analysis_year = st.selectbox("분석 연도", ["2024", "2023", "2022"])
    
    # 분기별 데이터 수집 옵션
    st.
