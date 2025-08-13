import streamlit as st
import pandas as pd
from config import *
from data.loader import *
from data.preprocess import *
from insight.openai_api import *
from util.email_util import create_email_ui
from util.news_collector import collect_google_news_insights

# 차트 안전 Import
try:
    from visualization.charts import (
        plot_quarterly_trends_for_key_items,
        plot_gap_analysis,
        plot_comparison_bar_chart
    )
except ImportError:
    st.warning("⚠️ 차트 모듈을 불러올 수 없습니다. 차트 표시 기능이 제한됩니다.")
    plot_quarterly_trends_for_key_items = plot_gap_analysis = plot_comparison_bar_chart = lambda *a, **k: None

# 보고서 생성 모듈
try:
    from export.report_generator import create_enhanced_pdf_report, create_excel_report
    EXPORT_AVAILABLE = True
except ImportError:
    EXPORT_AVAILABLE = False
    def create_enhanced_pdf_report(*args, **kwargs): pass
    def create_excel_report(*args, **kwargs): pass

# 페이지 설정
st.set_page_config(page_title="SK Profit+ 대시보드", layout="wide", page_icon="📊")

# ---------------------------
# 세션 매니저
# ---------------------------
class SessionManager:
    def initialize(self):
        defaults = {
            "raw_data": None,
            "processed_data": None,
            "quarterly_data": None,
            "analysis_result": None,
            "analysis_status": {},
            "manual_raw_data": None,
            "manual_processed_data": None,
            "manual_analysis_result": None
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    def save_data(self, key, data, status_key=None, status_value=True):
        st.session_state[key] = data
        if status_key:
            st.session_state["analysis_status"][status_key] = status_value

    def get(self, key):
        return st.session_state.get(key, None)

    def is_data_available(self, key):
        return self.get(key) is not None

session_manager = SessionManager()

# ---------------------------
# 탭별 렌더링 함수
# ---------------------------
def render_financial_analysis_tab():
    st.header("📈 재무 데이터 자동 분석")
    company_name = st.text_input("기업명 입력", "삼성전자")
    years = st.multiselect("분석 연도 선택", [2024, 2023, 2022, 2021], [2024, 2023])
    collect_quarterly = st.checkbox("분기별 데이터도 수집", True)

    if st.button("재무 데이터 수집 및 분석"):
        with st.spinner("데이터 수집 중..."):
            collector = DartAPICollector()
            processor = SKFinancialDataProcessor()

            raw_df, processed_df = collector.collect_and_process(company_name, years)
            session_manager.save_data("raw_data", raw_df, "auto_raw")
            session_manager.save_data("processed_data", processed_df, "auto_processed")

            if collect_quarterly:
                quarterly_collector = QuarterlyDataCollector()
                quarterly_df = quarterly_collector.collect(company_name)
                session_manager.save_data("quarterly_data", quarterly_df, "auto_quarterly")

            # AI 인사이트
            insight_gen = OpenAIInsightGenerator()
            insights = insight_gen.generate_from_financials(processed_df)
            session_manager.save_data("analysis_result", insights, "auto_analysis")

    # 데이터 표시
    if session_manager.is_data_available("processed_data"):
        st.subheader("처리된 재무 데이터")
        st.dataframe(session_manager.get("processed_data"))

    if session_manager.is_data_available("quarterly_data"):
        st.subheader("분기별 추이")
        st.plotly_chart(plot_quarterly_trends_for_key_items(session_manager.get("quarterly_data")), use_container_width=True)

def render_manual_upload_tab():
    st.header("📂 재무 데이터 수동 업로드")
    uploaded = st.file_uploader("XBRL/XML/ZIP 업로드", type=["zip", "xml", "xbrl"])
    if uploaded:
        processor = FinancialDataProcessor()
        raw_df, processed_df = processor.process(uploaded)
        session_manager.save_data("manual_raw_data", raw_df, "manual_raw")
        session_manager.save_data("manual_processed_data", processed_df, "manual_processed")

        # AI 인사이트
        insight_gen = OpenAIInsightGenerator()
        insights = insight_gen.generate_from_financials(processed_df)
        session_manager.save_data("manual_analysis_result", insights, "manual_analysis")

    if session_manager.is_data_available("manual_processed_data"):
        st.subheader("처리된 수동 업로드 데이터")
        st.dataframe(session_manager.get("manual_processed_data"))

def render_integrated_insight_tab():
    st.header("🔍 통합 인사이트")
    auto_analysis = session_manager.get("analysis_result") or ""
    manual_analysis = session_manager.get("manual_analysis_result") or ""
    news_insights = collect_google_news_insights()

    insight_gen = OpenAIInsightGenerator()
    integrated = insight_gen.generate_integrated_analysis(auto_analysis, manual_analysis, news_insights)
    st.write(integrated)

def render_report_generation_tab():
    st.header("📄 보고서 생성")
    company_name = st.text_input("기업명", "삼성전자")
    report_period = st.text_input("보고서 기간", "2024년 1분기")
    author_name = st.text_input("작성자", "홍길동")
    footer_note = st.text_area("푸터 메모", "")

    report_format = st.radio("포맷 선택", ["PDF", "Excel"])

    if st.button("보고서 생성"):
        if not EXPORT_AVAILABLE:
            st.error("보고서 생성 모듈이 없습니다.")
            return

        if report_format == "PDF":
            pdf_report = create_enhanced_pdf_report(
                data=session_manager.get("processed_data"),
                analysis=session_manager.get("analysis_result"),
                company=company_name,
                period=report_period,
                author=author_name,
                footer=footer_note
            )
            st.download_button(
                label="📄 PDF 다운로드",
                data=pdf_report,
                file_name=f"{company_name}_report.pdf",
                mime="application/pdf"
            )
        else:
            excel_report = create_excel_report(
                data=session_manager.get("processed_data"),
                analysis=session_manager.get("analysis_result"),
                company=company_name,
                period=report_period,
                author=author_name
            )
            st.download_button(
                label="📊 Excel 다운로드",
                data=excel_report,
                file_name=f"{company_name}_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # 이메일 발송 UI
    create_email_ui()

# ---------------------------
# 메인 실행
# ---------------------------
def main():
    session_manager.initialize()
    tab1, tab2, tab3, tab4 = st.tabs(["자동 분석", "수동 업로드", "통합 인사이트", "보고서 생성"])
    with tab1:
        render_financial_analysis_tab()
    with tab2:
        render_manual_upload_tab()
    with tab3:
        render_integrated_insight_tab()
    with tab4:
        render_report_generation_tab()

if __name__ == "__main__":
    main()
