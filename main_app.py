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

# ✅ export 모듈 import 수정 - 올바른 함수명으로 변경
try:
    # 현재 디렉토리에 export.py가 있는 경우
    from export import generate_pdf_report, create_excel_report, handle_pdf_generation_button
    EXPORT_AVAILABLE = True
    st.success("✅ PDF/Excel 생성 모듈 로드 성공")
except ImportError:
    try:
        # util 폴더에 있는 경우
        from util.export import generate_pdf_report, create_excel_report, handle_pdf_generation_button
        EXPORT_AVAILABLE = True
        st.success("✅ PDF/Excel 생성 모듈 로드 성공 (util 경로)")
    except ImportError as e:
        # import 실패 시 대체 함수들 생성
        def create_excel_report(*args, **kwargs):
            return b"Excel report generation is not available."
        
        def generate_pdf_report(*args, **kwargs):
            return {'success': False, 'error': 'PDF generation not available'}
        
        def handle_pdf_generation_button(*args, **kwargs):
            st.error("❌ PDF 생성 기능을 사용할 수 없습니다.")
            return False
            
        EXPORT_AVAILABLE = False
        st.error(f"❌ PDF/Excel 생성 모듈 로드 실패: {e}")

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
            'google_news_data', 'google_news_insight',
            # ✅ PDF 생성을 위한 추가 변수들
            'chart_df', 'gap_analysis_df', 'insights_list'
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
        
        # ✅ PDF 생성을 위한 데이터 전처리 추가
        if data_type == 'financial_data' and data is not None:
            # chart_df 생성 (PDF 차트용)
            st.session_state.chart_df = prepare_chart_data(data)
            
            # gap_analysis_df 생성 (PDF 갭분석용) 
            raw_cols = resolve_raw_cols_for_gap(data)
            if len(raw_cols) >= 2:
                st.session_state.gap_analysis_df = create_gap_analysis(data, raw_cols)
    
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

# ✅ PDF 생성을 위한 데이터 전처리 함수 추가
def prepare_chart_data(financial_data):
    """재무 데이터를 차트용 형태로 변환"""
    if financial_data is None or financial_data.empty:
        return None
    
    try:
        # financial_data를 chart_df 형태로 변환
        chart_rows = []
        
        # 회사 컬럼 찾기 (구분, _원시값 제외)
        company_cols = [col for col in financial_data.columns 
                       if col != '구분' and not col.endswith('_원시값')]
        
        for _, row in financial_data.iterrows():
            metric = row['구분']
            for company in company_cols:
                value = row[company]
                if pd.notna(value):
                    # 숫자 추출 (%, 조원 등 제거)
                    try:
                        if isinstance(value, str):
                            clean_value = value.replace('%', '').replace('조원', '').replace(',', '')
                            numeric_value = float(clean_value)
                        else:
                            numeric_value = float(value)
                        
                        chart_rows.append({
                            '구분': metric,
                            '회사': company, 
                            '수치': numeric_value
                        })
                    except:
                        continue
        
        return pd.DataFrame(chart_rows) if chart_rows else None
        
    except Exception as e:
        st.warning(f"차트 데이터 준비 중 오류: {e}")
        return None

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

# ✅ 인사이트 수집 함수 추가
def collect_all_insights():
    """모든 인사이트를 리스트로 수집"""
    insights = []
    
    if SessionManager.is_data_available('financial_insight'):
        insights.append(st.session_state.financial_insight)
    
    if SessionManager.is_data_available('manual_financial_insight'):
        insights.append(st.session_state.manual_financial_insight)
        
    if SessionManager.is_data_available('google_news_insight'):
        insights.append(st.session_state.google_news_insight)
        
    if SessionManager.is_data_available('integrated_insight'):
        insights.append(st.session_state.integrated_insight)
    
    return insights

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
    st.markdown("---")
    st.subheader("📊 분기별 데이터 수집 설정")
    
    collect_quarterly = st.checkbox(
        "📊 분기별 데이터 수집", 
        value=True, 
        help="1분기보고서, 반기보고서, 3분기보고서, 사업보고서를 모두 수집합니다"
    )
    
    if collect_quarterly:
        quarterly_years = st.multiselect(
            "분기별 분석 연도", 
            ["2024", "2023", "2022"], 
            default=["2024"], 
            help="분기별 데이터를 수집할 연도를 선택하세요"
        )
        
        st.info("📋 수집할 보고서: 1분기보고서(Q1, 누적) • 반기보고서(Q2, 누적) • 3분기보고서(Q3, 누적) • 사업보고서(연간, 누적)\n"
        "🔎 Q4(4분기 당기)는 연간 − (Q1+Q2+Q3)로 산출됩니다.")

    if st.button("🚀 DART 자동분석 시작", type="primary"):
        with st.spinner("모든 데이터를 수집하고 심층 분석 중입니다..."):
            try:
                dart = DartAPICollector(config.DART_API_KEY)
                processor = SKFinancialDataProcessor()
                
                # 재무 데이터 수집 (개선된 버전)
                dataframes = []
                successful_companies = []
                failed_companies = []
                
                st.info(f"🔍 {len(selected_companies)}개 회사의 재무 데이터 수집 시작...")
                
                for i, company in enumerate(selected_companies, 1):
                    with st.status(f"📊 {company} 데이터 수집 중... ({i}/{len(selected_companies)})"):
                        try:
                            # DART API 호출
                            raw_data = dart.get_company_financials_auto(company, analysis_year)
                            
                            if raw_data is None or raw_data.empty:
                                st.warning(f"⚠️ {company}: DART에서 데이터를 찾을 수 없습니다.")
                                failed_companies.append(company)
                                continue
                            
                            # 데이터 처리
                            df = processor.process_dart_data(raw_data, company)
                            
                            if df is not None and not df.empty:
                                dataframes.append(df)
                                successful_companies.append(company)
                                st.success(f"✅ {company}: {len(df)}개 재무지표 수집 완료")
                            else:
                                st.error(f"❌ {company}: 데이터 처리 실패")
                                failed_companies.append(company)
                                
                        except Exception as e:
                            st.error(f"❌ {company}: 오류 발생 - {str(e)}")
                            failed_companies.append(company)
                
                # 수집 결과 요약
                if successful_companies:
                    st.success(f"✅ 재무 데이터 수집 완료: {len(successful_companies)}개 회사 성공")
                    if failed_companies:
                        st.warning(f"⚠️ 실패한 회사: {', '.join(failed_companies)}")
                else:
                    st.error("❌ 모든 회사의 데이터 수집에 실패했습니다.")
                    return

                # 분기별 데이터 수집 (개선된 버전)
                q_data_list = []
                if collect_quarterly and quarterly_years:
                    q_collector = QuarterlyDataCollector(dart)
                    
                    # 디버그 정보 표시
                    st.caption(f"🧭 QuarterlyDataCollector 모듈 = {q_collector.__class__.__module__}")
                    st.caption(f"🧪 보고서코드 매핑 = {getattr(q_collector, 'report_codes', {})}")
                    
                    st.info(f"📊 분기별 데이터 수집 시작... ({', '.join(quarterly_years)}년, {len(successful_companies)}개 회사)")
                    
                    total_quarters = 0
                    quarterly_success = 0
                    
                    for year in quarterly_years:
                        for company in successful_companies:
                            with st.status(f"📈 {company} {year}년 분기별 데이터 수집 중..."):
                                try:
                                    q_df = q_collector.collect_quarterly_data(company, int(year))
                                    if not q_df.empty:
                                        q_data_list.append(q_df)
                                        total_quarters += len(q_df)
                                        quarterly_success += 1
                                        st.success(f"✅ {company} {year}년: {len(q_df)}개 분기 데이터")
                                    else:
                                        st.warning(f"⚠️ {company} {year}년: 분기 데이터 없음")
                                except Exception as e:
                                    st.error(f"❌ {company} {year}년: {str(e)}")
                    
                    # 분기별 데이터 수집 결과
                    if q_data_list:
                        st.success(f"✅ 분기별 데이터 수집 완료! 총 {quarterly_success}개 회사, {total_quarters}개 분기 데이터")
                    else:
                        st.warning("⚠️ 수집된 분기별 데이터가 없습니다.")

                if dataframes:
                    # 데이터 저장 (✅ PDF용 데이터도 함께 준비)
                    financial_data = processor.merge_company_data(dataframes)
                    SessionManager.save_data('financial_data', financial_data)
                    
                    if q_data_list:
                        quarterly_data = pd.concat(q_data_list, ignore_index=True)
                        # 분기별 데이터 정렬
                        quarterly_data = sort_quarterly_by_quarter(quarterly_data)
                        SessionManager.save_data('quarterly_data', quarterly_data)
                        st.success(f"✅ 총 {len(q_data_list)}개 회사의 분기별 데이터 수집 완료")
                    
                    # AI 인사이트 생성
                    openai = OpenAIInsightGenerator(config.OPENAI_API_KEY)
                    financial_insight = openai.generate_financial_insight(financial_data)
                    SessionManager.save_data('financial_insight', financial_insight, 'financial_insight')
                    
                    st.success("✅ 재무분석 및 AI 인사이트 생성이 완료되었습니다!")
                else:
                    st.error("데이터 수집에 실패했습니다.")
                    
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
                st.info("💡 DART API 키가 올바른지 확인해주세요.")

    # 분석 결과 표시 (데이터가 있을 때만)
    if SessionManager.is_data_available('financial_data'):
        render_financial_results()

def render_financial_results():
    """재무분석 결과 표시"""
    st.markdown("---")
    st.subheader("💰 손익계산서(연간)")
    final_df = st.session_state.financial_data
    
    # 표시용 컬럼만 표시 (원시값 제외)
    display_cols = [col for col in final_df.columns if not col.endswith('_원시값')]
    st.markdown("**📋 정리된 재무지표 (표시값)**")
    st.dataframe(
        final_df[display_cols].set_index('구분'), 
        use_container_width=True,
        column_config={
            "구분": st.column_config.TextColumn("구분", width="medium")
        }
    )

    # 분기별 트렌드 차트 추가
    if SessionManager.is_data_available('quarterly_data'):
        st.markdown("---")
        st.subheader("📈 분기별 성과 및 추이 분석")
        
        # 분기별 데이터 요약 정보 표시
        quarterly_df = st.session_state.quarterly_data
        st.info(f"📊 수집된 분기별 데이터: {len(quarterly_df)}개 데이터포인트")
        
        # 분기별 데이터 요약 통계
        if '보고서구분' in quarterly_df.columns:
            report_summary = quarterly_df['보고서구분'].value_counts()
            st.markdown("**📋 수집된 보고서별 데이터 현황**")
            for report_type, count in report_summary.items():
                st.write(f"• {report_type}: {count}개")
        
        # 분기별 데이터 테이블 표시
        st.markdown("**📋 분기별 재무지표 상세 데이터**")
        # '연간' 행 제거
        quarterly_df = quarterly_df[~quarterly_df["분기"].str.contains("연간")]
        st.dataframe(quarterly_df, use_container_width=True)
        
        if PLOTLY_AVAILABLE:
            # ✅ 분기가 '연간'이 아닌 행만 차트에 사용
            chart_input = quarterly_df.copy()
            if '분기' in chart_input.columns:
               chart_input = chart_input[~chart_input['분기'].astype(str).str.contains('연간')]

            st.markdown("**📊 분기별 재무지표 트렌드**")
            st.plotly_chart(create_quarterly_trend_chart(chart_input), use_container_width=True, key="quarterly_trend")
            
            st.markdown("**📈 트렌드 분석**")
            st.plotly_chart(create_gap_trend_chart(chart_input), use_container_width=True, key="gap_trend")
        else:
            st.info("📊 분기별 차트 모듈이 없습니다.")

    # 갭차이 분석 (완전한 버전)
    st.markdown("---")
    st.subheader("📈 SK에너지 VS 경쟁사 비교 분석")
    # ✅ 폴백 포함: *_원시값 부족하면 회사명 컬럼 사용
    raw_cols = resolve_raw_cols_for_gap(final_df)
    
    if len(raw_cols) >= 2:
        gap_analysis = create_gap_analysis(final_df, raw_cols)
    
        if not gap_analysis.empty:
            st.markdown("**📊 SK에너지 대비 경쟁사 비교 분석표**")
            st.dataframe(
                gap_analysis, 
                use_container_width=True,
                column_config={"지표": st.column_config.TextColumn("지표", width="medium")},
                hide_index=False
            )
    
            if PLOTLY_AVAILABLE:
                gap_chart = create_gap_chart(gap_analysis)
                if gap_chart is not None:
                    st.plotly_chart(gap_chart, use_container_width=True, key="gap_chart")
                else:
                    st.info("📊 비교 분석 차트를 생성할 수 있는 데이터가 부족합니다.")
        else:
            st.warning("⚠️ 비교 분석을 위한 충분한 데이터가 없습니다.")
    else:
        st.info("ℹ️ 비교 분석을 위해서는 최소 2개 이상의 회사 데이터가 필요합니다.")
    
    # AI 인사이트 표시
    if SessionManager.is_data_available('financial_insight'):
        st.markdown("---")
        st.subheader("🤖 AI 재무 인사이트")
        st.markdown(st.session_state.financial_insight)

def render_manual_upload_tab():
    """수동 파일 업로드 탭 렌더링"""
    st.subheader("📁 파일 업로드 분석")
    st.info("💡 DART에서 다운로드한 XBRL 파일을 직접 업로드하여 분석할 수 있습니다.")
    
    uploaded_files = st.file_uploader(
        "XBRL 파일 선택 (여러 파일 업로드 가능)",
        type=['xml', 'xbrl', 'zip'],
        accept_multiple_files=True,
        help="DART에서 다운로드한 XBRL 파일을 업로드하세요. 여러 회사의 파일을 동시에 업로드할 수 있습니다."
    )
    
    if uploaded_files:
        if st.button("📊 수동 업로드 분석 시작", type="secondary"):
            with st.spinner("XBRL 파일을 분석하고 처리 중입니다..."):
                try:
                    processor = FinancialDataProcessor()
                    dataframes = []
                    
                    for uploaded_file in uploaded_files:
                        st.write(f"🔍 {uploaded_file.name} 처리 중...")
                        df = processor.load_file(uploaded_file)
                        if df is not None and not df.empty:
                            dataframes.append(df)
                            st.success(f"✅ {uploaded_file.name} 처리 완료")
                        else:
                            st.error(f"❌ {uploaded_file.name} 처리 실패")
                    
                    if dataframes:
                        manual_data = processor.merge_company_data(dataframes)
                        SessionManager.save_data('manual_financial_data', manual_data)
                        SessionManager.save_data('financial_data', manual_data)

                        # AI 인사이트 생성 (DART 자동 수집과 동일한 프롬프트 사용)
                        with st.spinner("🤖 AI 인사이트 생성 중..."):
                            openai = OpenAIInsightGenerator(config.OPENAI_API_KEY)
                            manual_financial_insight = openai.generate_financial_insight(manual_data)
                            SessionManager.save_data('manual_financial_insight', manual_financial_insight, 'manual_financial_insight')
        
                        st.success("✅ 수동 업로드 분석 및 AI 인사이트 생성이 완료되었습니다!")
                    else:
                        st.error("❌ 처리할 수 있는 데이터가 없습니다.")
                        
                except Exception as e:
                    st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")

    # 수동 업로드 결과 표시
    if SessionManager.is_data_available('manual_financial_data'):
        st.markdown("---")
        st.subheader("💰 손익계산서(연간)")
        final_df = st.session_state.manual_financial_data
        
        # 표시용 컬럼만 표시
        display_cols = [col for col in final_df.columns if not col.endswith('_원시값')]
        st.markdown("**📋 정리된 재무지표 (표시값)**")
        st.dataframe(final_df[display_cols].set_index('구분'), use_container_width=True)
       
        # 분기별 트렌드 차트 추가 (수동 업로드용)
        if SessionManager.is_data_available('quarterly_data'):
            st.markdown("---")
            st.subheader("📈 분기별 성과 및 추이 분석")
            
            # 분기별 데이터 요약 정보 표시
            quarterly_df = st.session_state.quarterly_data
            st.info(f"📊 수집된 분기별 데이터: {len(quarterly_df)}개 데이터포인트")
            
            # 분기별 데이터 요약 통계
            if '보고서구분' in quarterly_df.columns:
                report_summary = quarterly_df['보고서구분'].value_counts()
                st.markdown("**📋 수집된 보고서별 데이터 현황**")
                for report_type, count in report_summary.items():
                    st.write(f"• {report_type}: {count}개")
            
            # 분기별 데이터 테이블 표시
            st.markdown("**📋 분기별 재무지표 상세 데이터**")
            # '연간' 행 제거
            quarterly_df = quarterly_df[~quarterly_df["분기"].str.contains("연간")]
            st.dataframe(quarterly_df, use_container_width=True)
            
            if PLOTLY_AVAILABLE:
                # ✅ 분기가 '연간'이 아닌 행만 차트에 사용
                chart_input = quarterly_df.copy()
                if '분기' in chart_input.columns:
                   chart_input = chart_input[~chart_input['분기'].astype(str).str.contains('연간')]

                st.markdown("**📊 분기별 재무지표 트렌드**")
                st.plotly_chart(create_quarterly_trend_chart(chart_input), use_container_width=True, key="manual_quarterly_trend")
                
                st.markdown("**📈 트렌드 분석**")
                st.plotly_chart(create_gap_trend_chart(chart_input), use_container_width=True, key="manual_gap_trend")
            else:
                st.info("📊 분기별 차트 모듈이 없습니다.")

        # 갭차이 분석 추가
        st.markdown("---")
        st.subheader("📈 SK에너지 VS 경쟁사 비교 분석")
        raw_cols = resolve_raw_cols_for_gap(final_df)
        
        if len(raw_cols) >= 2:
            gap_analysis = create_gap_analysis(final_df, raw_cols)
            if not gap_analysis.empty:
                st.markdown("**📊 SK에너지 대비 경쟁사 차이 분석표**")
                st.dataframe(
                    gap_analysis, 
                    use_container_width=True,
                    column_config={"지표": st.column_config.TextColumn("지표", width="medium")},
                    hide_index=False
                )
                if PLOTLY_AVAILABLE:
                    st.plotly_chart(create_gap_chart(gap_analysis), use_container_width=True, key="manual_gap_chart")
            else:
                st.warning("⚠️ 비교 분석을 위한 충분한 데이터가 없습니다.")
        else:
            st.info("ℹ️ 비교 분석을 위해서는 최소 2개 이상의 회사 데이터가 필요합니다.")
        
        # AI 인사이트 표시 (수동 업로드용)
        if SessionManager.is_data_available('manual_financial_insight'):
            st.markdown("---")
            st.subheader("🤖 AI 재무 인사이트 (수동 업로드)")
            st.markdown(st.session_state.manual_financial_insight)

def render_integrated_insight_tab():
    """통합 인사이트 탭 렌더링"""
    st.subheader("🧠 통합 인사이트 생성")
    
    # 분석 상태 표시
    if SessionManager.is_data_available('integrated_insight'):
        status = SessionManager.get_data_status('integrated_insight')
        if status.get('completed'):
            st.success(f"✅ 통합 인사이트 완료 ({status.get('timestamp', '시간 정보 없음')})")
    
    if st.button("🚀 통합 인사이트 생성", type="primary"):
        # 사용 가능한 인사이트들 수집
        available_insights = []
        
        if SessionManager.is_data_available('financial_insight'):
            available_insights.append(("자동 재무분석", st.session_state.financial_insight))
        
        if SessionManager.is_data_available('manual_financial_insight'):
            available_insights.append(("수동 재무분석", st.session_state.manual_financial_insight))
        
        if SessionManager.is_data_available('google_news_insight'):
            available_insights.append(("구글 뉴스 분석", st.session_state.google_news_insight))
        
        if available_insights:
            with st.spinner("모든 인사이트를 통합 분석 중..."):
                try:
                    openai = OpenAIInsightGenerator(config.OPENAI_API_KEY)
                    
                    # 모든 인사이트를 하나의 텍스트로 결합
                    combined_insights = "\n\n".join([f"=== {title} ===\n{insight}" for title, insight in available_insights])
                    
                    integrated_insight = openai.generate_integrated_insight(
                        combined_insights,
                        None
                    )
                    SessionManager.save_data('integrated_insight', integrated_insight, 'integrated_insight')
                    st.success("✅ 통합 인사이트가 생성되었습니다!")
                    
                except Exception as e:
                    st.error(f"통합 인사이트 생성 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("⚠️ 최소 하나의 인사이트(재무분석 또는 구글뉴스)가 필요합니다.")
    
    # 통합 인사이트 결과 표시
    if SessionManager.is_data_available('integrated_insight'):
        st.subheader("🤖 통합 인사이트 결과")
        st.markdown(st.session_state.integrated_insight)
    else:
        st.info("재무분석 또는 구글뉴스 분석을 완료한 후 통합 인사이트를 생성할 수 있습니다.")

def render_report_generation_tab():
    """보고서 생성 탭 렌더링"""
    st.subheader("📄 통합 보고서 생성 & 이메일 서비스 바로가기")

    # 2열 레이아웃: PDF 생성 + 이메일 입력
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("**📥 보고서 다운로드**")

        # 사용자 입력
        report_target = st.text_input("보고 대상", value="SK이노베이션 경영진")
        report_author = st.text_input("보고자", value="")
        show_footer = st.checkbox(
            "푸터 문구 표시(※ 본 보고서는 대시보드에서 자동 생성되었습니다.)", 
            value=False
        )

        # 보고서 형식 선택
        report_format = st.radio("파일 형식 선택", ["PDF", "Excel"], horizontal=True)

        # ✅ 데이터 우선순위: DART 자동 > 수동 업로드
        financial_data_for_report = None
        if SessionManager.is_data_available('financial_data'):
            financial_data_for_report = st.session_state.financial_data
        elif SessionManager.is_data_available('manual_financial_data'):
            financial_data_for_report = st.session_state.manual_financial_data

        # ✅ 수정된 PDF 생성 섹션 - 고급 PDF 생성
        if EXPORT_AVAILABLE and report_format == "PDF":
            st.markdown("---")
            st.markdown("**🚀 고급 PDF 생성 (export.py 모듈 사용)**")
            
            # ✅ 버튼을 직접 만들고 클릭 처리
            if st.button("📄 한글 PDF 생성 (NanumGothic 폰트)", type="primary", key="advanced_pdf_btn"):
                success = handle_pdf_generation_button(
                    button_clicked=True,
                    financial_data=financial_data_for_report,
                    news_data=st.session_state.get('google_news_data'),
                    insights=collect_all_insights(),
                    quarterly_df=st.session_state.get('quarterly_data'),
                    chart_df=st.session_state.get('chart_df'),
                    gap_analysis_df=st.session_state.get('gap_analysis_df'),
                    report_target=report_target.strip() or "SK이노베이션 경영진",
                    report_author=report_author.strip() or "AI 분석 시스템",
                    show_footer=show_footer
                )

        # ✅ Excel 생성 섹션
        if report_format == "Excel":
            st.markdown("---")
            st.markdown("**📊 Excel 보고서 생성**")
            
            if st.button("📊 Excel 보고서 생성", type="secondary", key="make_excel_report"):
                with st.spinner("📊 Excel 보고서 생성 중..."):
                    try:
                        file_bytes = create_excel_report(
                            financial_data=financial_data_for_report,
                            news_data=st.session_state.get('google_news_data'),
                            insights=collect_all_insights()
                        )
                        filename = f"SK_Energy_Analysis_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                        if file_bytes and isinstance(file_bytes, bytes) and len(file_bytes) > 1000:
                            # 세션에 파일 정보 저장
                            st.session_state.generated_file = file_bytes
                            st.session_state.generated_filename = filename
                            st.session_state.generated_mime = mime_type

                            st.download_button(
                                label="📥 Excel 다운로드",
                                data=file_bytes,
                                file_name=filename,
                                mime=mime_type,
                                type="secondary"
                            )
                            st.success("✅ Excel 보고서가 성공적으로 생성되었습니다!")
                        else:
                            st.error("❌ Excel 보고서 생성에 실패했습니다.")
                            if isinstance(file_bytes, bytes):
                                error_msg = file_bytes.decode('utf-8', errors='ignore')
                                st.error(f"오류 내용: {error_msg}")
                            
                    except Exception as e:
                        st.error(f"Excel 보고서 생성 중 오류가 발생했습니다: {str(e)}")

        # ✅ PDF 생성 불가능한 경우 안내
        if not EXPORT_AVAILABLE and report_format == "PDF":
            st.warning("⚠️ PDF 생성 기능이 비활성화되어 있습니다.")
            st.info("💡 export.py 파일과 reportlab 패키지를 확인해주세요.")

    with col2:
        st.write("**📧 이메일 서비스 바로가기**")

        mail_providers = {
            "네이버": "https://mail.naver.com/",
            "구글(Gmail)": "https://mail.google.com/",
            "다음": "https://mail.daum.net/",
            "네이트": "https://mail.nate.com/",
            "야후": "https://mail.yahoo.com/",
            "아웃룩(Outlook)": "https://outlook.live.com/",
            "프로톤메일(ProtonMail)": "https://mail.proton.me/",
            "조호메일(Zoho Mail)": "https://mail.zoho.com/",
            "GMX 메일": "https://www.gmx.com/",
            "아이클라우드(iCloud Mail)": "https://www.icloud.com/mail",
            "메일닷컴(Mail.com)": "https://www.mail.com/",
            "AOL 메일": "https://mail.aol.com/"
        }

        selected_provider = st.selectbox(
            "메일 서비스 선택",
            list(mail_providers.keys()),
            key="mail_provider_select"
        )
        url = mail_providers[selected_provider]

        st.markdown(
            f"[{selected_provider} 메일 바로가기]({url})",
            unsafe_allow_html=True
        )
        st.info("선택한 메일 서비스 링크가 새 탭에서 열립니다.")

        # 생성된 파일 다운로드 버튼
        if st.session_state.get('generated_file'):
            st.download_button(
                label=f"📥 {st.session_state.generated_filename} 다운로드",
                data=st.session_state.generated_file,
                file_name=st.session_state.generated_filename,
                mime=st.session_state.generated_mime,
                key="download_generated_report_btn"
            )
        else:
            st.info("먼저 보고서를 생성해주세요.")

def main():
    """메인 함수"""
    # 세션 상태 초기화
    SessionManager.initialize()
    
    st.title("⚡SK Profit+: 손익 개선 전략 대시보드")
    
    # 마지막 분석 시간 표시
    if st.session_state.last_analysis_time:
        st.info(f"🕒 마지막 분석 시간: {st.session_state.last_analysis_time}")
    
    # Export 모듈 상태 표시 (사이드바로 이동)
    with st.sidebar:
        st.header("📊 시스템 상태")
        if EXPORT_AVAILABLE:
            st.success("✅ PDF/Excel 보고서 생성 가능")
        else:
            st.warning("⚠️ PDF/Excel 생성 불가")
            st.caption("export.py 및 reportlab 확인 필요")
            
        # 데이터 상태 요약
        st.header("📋 데이터 현황")
        data_summary = {
            "재무 데이터": SessionManager.is_data_available('financial_data'),
            "분기별 데이터": SessionManager.is_data_available('quarterly_data'), 
            "뉴스 데이터": SessionManager.is_data_available('google_news_data'),
            "통합 인사이트": SessionManager.is_data_available('integrated_insight')
        }
        
        for name, available in data_summary.items():
            if available:
                st.success(f"✅ {name}")
            else:
                st.info(f"⏳ {name}")
    
    # 탭 생성
    tabs = st.tabs([
        "📈 재무 분석", 
        "📁 파일 업로드", 
        "🔍 뉴스 분석", 
        "🧠 통합 인사이트", 
        "📄 보고서 생성"
    ])
    
    # 각 탭 렌더링
    with tabs[0]:  # 재무분석 탭
        render_financial_analysis_tab()
    
    with tabs[1]:  # 수동 파일 업로드 탭
        render_manual_upload_tab()
    
    with tabs[2]:  # Google News 수집 탭
        create_google_news_tab()
    
    with tabs[3]:  # 통합 인사이트 탭
        render_integrated_insight_tab()
    
    with tabs[4]:  # 보고서 생성 탭
        render_report_generation_tab()

if __name__ == "__main__":
    main()
