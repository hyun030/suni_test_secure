# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import config
from data.loader import DartAPICollector, QuarterlyDataCollector

# 안전한 임포트 (try-except 적용)
try:
    from data.preprocess import SKFinancialDataProcessor, FinancialDataProcessor 
except ImportError as e:
    print(f"⚠️ 전처리 모듈 로드 실패: {e}")
    # 대체 클래스 생성
    class SKFinancialDataProcessor:
        def __init__(self):
            pass
        def process_data(self, df):
            return df if df is not None else pd.DataFrame()
    
    class FinancialDataProcessor:
        def __init__(self):
            pass
        def process_data(self, df):
            return df if df is not None else pd.DataFrame()

from insight.openai_api import OpenAIInsightGenerator
from visualization import (
    create_sk_bar_chart, create_sk_radar_chart, 
    create_quarterly_trend_chart, create_gap_trend_chart, 
    create_gap_analysis, create_gap_chart, PLOTLY_AVAILABLE
)
from util.export import create_excel_report, create_enhanced_pdf_report
from news_collector import create_google_news_tab, GoogleNewsCollector

st.set_page_config(page_title="SK에너지 경쟁사 분석 대시보드", page_icon="⚡", layout="wide")

class SessionManager:
    """세션 상태 관리를 담당하는 클래스"""
    
    @staticmethod
    def initialize():
        """세션 상태 초기화 및 데이터 지속성 보장"""
        # 핵심 데이터 변수들
        core_vars = [
            'financial_data', 'quarterly_data',
            'financial_insight', 'integrated_insight', 'integrated_insight',
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
        st.info("📋 수집할 보고서: 1분기보고서 (Q1) • 반기보고서 (Q2) • 3분기보고서 (Q3) • 사업보고서 (Q4)")

    if st.button("🚀 DART 자동분석 시작", type="primary"):
        with st.spinner("모든 데이터를 수집하고 심층 분석 중입니다..."):
            try:
                dart = DartAPICollector(config.DART_API_KEY)
                processor = SKFinancialDataProcessor()
                
                # 재무 데이터 수집
                dataframes = []
                for company in selected_companies:
                    df = processor.process_dart_data(dart.get_company_financials_auto(company, analysis_year), company)
                    if df is not None:
                        dataframes.append(df)
                
                dataframes = [df for df in dataframes if df is not None]

                # 분기별 데이터 수집 (진행 메시지 없이 조용히 처리)
                q_data_list = []
                if collect_quarterly and quarterly_years:
                    q_collector = QuarterlyDataCollector(dart)
                    
                    total_quarters = 0
                    for year in quarterly_years:
                        for company in selected_companies:
                            q_df = q_collector.collect_quarterly_data(company, int(year))
                            if not q_df.empty:
                                q_data_list.append(q_df)
                                total_quarters += len(q_df)
                    
                    # 최종 결과만 간단하게 표시
                    if q_data_list:
                        st.success(f"✅ 분기별 데이터 수집 완료 ({len(q_data_list)}개 회사, {total_quarters}개 분기)")

                if dataframes:
                    # 데이터 저장
                    financial_data = processor.merge_company_data(dataframes)
                    SessionManager.save_data('financial_data', financial_data)
                    
                    if q_data_list:
                        quarterly_data = pd.concat(q_data_list, ignore_index=True)
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

    # 분석 결과 표시 (데이터가 있을 때만)
    if SessionManager.is_data_available('financial_data'):
        render_financial_results()

def render_financial_results():
    """재무분석 결과 표시"""
    st.markdown("---")
    st.subheader("💰 재무분석 결과")
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

    st.markdown("---")
    st.subheader("📊 주요 지표 비교")
    ratio_df = final_df[final_df['구분'].str.contains('%', na=False)]
    raw_cols = [col for col in final_df.columns if col.endswith('_원시값')]
    
    if not ratio_df.empty and raw_cols:
        chart_df = pd.melt(ratio_df, id_vars=['구분'], value_vars=raw_cols, var_name='회사', value_name='수치')
        chart_df['회사'] = chart_df['회사'].str.replace('_원시값', '')
        
        if PLOTLY_AVAILABLE:
            st.plotly_chart(create_sk_bar_chart(chart_df), use_container_width=True, key="bar_chart")
            st.plotly_chart(create_sk_radar_chart(chart_df), use_container_width=True, key="radar_chart")

    # 분기별 트렌드 차트 추가 (꺾은선 그래프)
    if SessionManager.is_data_available('quarterly_data'):
        st.markdown("---")
        st.subheader("📈 분기별 트렌드 차트")
        
        if PLOTLY_AVAILABLE:
            st.markdown("**📊 분기별 재무지표 트렌드**")
            st.plotly_chart(create_quarterly_trend_chart(st.session_state.quarterly_data), use_container_width=True, key="quarterly_trend")
            
            st.markdown("**📈 갭 트렌드 분석**")
            st.plotly_chart(create_gap_trend_chart(st.session_state.quarterly_data), use_container_width=True, key="gap_trend")

    # 갭차이 분석
    st.markdown("---")
    st.subheader("📈 SK에너지 대비 경쟁사 차이 분석")
    if raw_cols and len(raw_cols) > 1:
        gap_analysis = create_gap_analysis(final_df, raw_cols)
        if not gap_analysis.empty:
            st.markdown("**📊 SK에너지 대비 경쟁사 차이 분석표**")
            st.dataframe(
                gap_analysis, 
                use_container_width=True,
                column_config={
                    "지표": st.column_config.TextColumn("지표", width="medium")
                },
                hide_index=False
            )
            
            # 갭차이 시각화
            if PLOTLY_AVAILABLE:
                st.markdown("**📈 격차 분석 시각화 차트**")
                st.plotly_chart(create_gap_chart(gap_analysis), use_container_width=True, key="gap_chart")
        else:
            st.warning("⚠️ 차이 분석을 위한 충분한 데이터가 없습니다. (최소 2개 회사 필요)")
    else:
        st.info("ℹ️ 차이 분석을 위해서는 최소 2개 이상의 회사 데이터가 필요합니다.")

    # AI 인사이트 표시 (맨 마지막)
    if SessionManager.is_data_available('financial_insight'):
        st.markdown("---")
        st.subheader("🤖 AI 재무 인사이트")
        st.markdown(st.session_state.financial_insight)

def render_manual_upload_tab():
    """수동 파일 업로드 탭 렌더링"""
    st.subheader("📁 수동 파일 업로드 분석")
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

                        # AI 인사이트 생성 추가
                        openai = OpenAIInsightGenerator(config.OPENAI_API_KEY)
                        manual_financial_insight = openai.generate_financial_insight(manual_data)
                        SessionManager.save_data('manual_financial_insight', manual_financial_insight, 'manual_financial_insight')
        
                        st.success("✅ 수동 업로드 분석 및 AI 인사이트 생성이 완료되었습니다!")
                        
                        st.success("✅ 수동 업로드 분석이 완료되었습니다!")
                    else:
                        st.error("❌ 처리할 수 있는 데이터가 없습니다.")
                        
                except Exception as e:
                    st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")

    # 수동 업로드 결과 표시
    if SessionManager.is_data_available('manual_financial_data'):
        st.markdown("---")
        st.subheader("💰 수동 업로드 재무분석 결과")
        final_df = st.session_state.manual_financial_data
        
        # 표시용 컬럼만 표시 (원시값 제외)
        display_cols = [col for col in final_df.columns if not col.endswith('_원시값')]
        st.markdown("**📋 정리된 재무지표 (표시값)**")
        st.dataframe(final_df[display_cols].set_index('구분'), use_container_width=True)

        st.markdown("---")
        st.subheader("📊 주요 지표 비교")
        ratio_df = final_df[final_df['구분'].str.contains('%', na=False)]
        raw_cols = [col for col in final_df.columns if col.endswith('_원시값')]
        
        if not ratio_df.empty and raw_cols:
            chart_df = pd.melt(ratio_df, id_vars=['구분'], value_vars=raw_cols, var_name='회사', value_name='수치')
            chart_df['회사'] = chart_df['회사'].str.replace('_원시값', '')
            
            if PLOTLY_AVAILABLE:
                st.plotly_chart(create_sk_bar_chart(chart_df), use_container_width=True, key="manual_bar_chart")
                st.plotly_chart(create_sk_radar_chart(chart_df), use_container_width=True, key="manual_radar_chart")

        # 갭차이 분석 추가
        st.markdown("---")
        st.subheader("📈 격차 분석")
        if raw_cols and len(raw_cols) > 1:
            gap_analysis = create_gap_analysis(final_df, raw_cols)
            if not gap_analysis.empty:
                st.markdown("**📊 SK에너지 대비 경쟁사 차이 분석표**")
                st.dataframe(
                    gap_analysis, 
                    use_container_width=True,
                    column_config={
                        "지표": st.column_config.TextColumn("지표", width="medium")
                    },
                    hide_index=False
                )
                
                # 갭차이 시각화
                if PLOTLY_AVAILABLE:
                    st.markdown("**📈 차이 시각화 차트**")
                    st.plotly_chart(create_gap_chart(gap_analysis), use_container_width=True, key="manual_gap_chart")
            else:
                st.warning("⚠️ 차이 분석을 위한 충분한 데이터가 없습니다. (최소 2개 회사 필요)")
        else:
            st.info("ℹ️ 차이 분석을 위해서는 최소 2개 이상의 회사 데이터가 필요합니다.")

def render_integrated_insight_tab():
    """통합 인사이트 탭 렌더링"""
    st.subheader("�� 통합 인사이트 생성")
    
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

        if st.button("📥 보고서 생성", type="primary", key="make_report"):
            # 데이터 우선순위: DART 자동 > 수동 업로드
            financial_data_for_report = None
            if SessionManager.is_data_available('financial_data'):
                financial_data_for_report = st.session_state.financial_data
            elif SessionManager.is_data_available('manual_financial_data'):
                financial_data_for_report = st.session_state.manual_financial_data

            # 선택 입력
            quarterly_df = st.session_state.get("quarterly_data")
            selected_charts = st.session_state.get("selected_charts")

            with st.spinner("📄 보고서 생성 중..."):
                try:
                    if report_format == "PDF":
                        file_bytes = create_enhanced_pdf_report(
                            financial_data=financial_data_for_report,
                            news_data=st.session_state.get('news_data'),
                            insights=st.session_state.get('integrated_insight') or 
                                   st.session_state.get('financial_insight') or 
                                   st.session_state.get('news_insight'),
                            quarterly_df=quarterly_df,
                            selected_charts=selected_charts,
                            show_footer=show_footer,
                            report_target=report_target.strip() or "보고 대상 미기재",
                            report_author=report_author.strip() or "보고자 미기재"
                        )
                        filename = "SK_Energy_Analysis_Report.pdf"
                        mime_type = "application/pdf"
                    else:
                        file_bytes = create_excel_report(
                            financial_data=financial_data_for_report,
                            news_data=Node,
                            insights=st.session_state.get('integrated_insight') or 
                                   st.session_state.get('financial_insight') or 
                                   st.session_state.get('manual_financial_insight') or
                                   st.session_state.get('google_news_insight') #구글 뉴스 인사이트로 변경
                        )
                        filename = "SK_Energy_Analysis_Report.xlsx"
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                    if file_bytes:
                        # 세션에 파일 정보 저장
                        st.session_state.generated_file = file_bytes
                        st.session_state.generated_filename = filename
                        st.session_state.generated_mime = mime_type

                        st.download_button(
                            label="⬇️ 보고서 다운로드",
                            data=file_bytes,
                            file_name=filename,
                            mime=mime_type
                        )
                        st.success("✅ 보고서가 성공적으로 생성되었습니다!")
                    else:
                        st.error("❌ 보고서 생성에 실패했습니다.")
                        
                except Exception as e:
                    st.error(f"보고서 생성 중 오류가 발생했습니다: {str(e)}")

    with col2:
        st.write("**📧 이메일 서비스**")
        st.info("이메일 서비스는 별도로 구현되어 있습니다.")

def main():
    # 세션 상태 초기화
    SessionManager.initialize()
    
    st.title("⚡SK Profit+: 손익 개선 전략")
    
    # 마지막 분석 시간 표시
    if st.session_state.last_analysis_time:
        st.info(f"🕒 마지막 분석 시간: {st.session_state.last_analysis_time}")
    
    tabs = st.tabs([
        "📈 재무분석", "📁 수동 파일 업로드", "🔍 Google News 수집", "🧠 통합 인사이트", "📄 보고서 생성"
    ])
    
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
