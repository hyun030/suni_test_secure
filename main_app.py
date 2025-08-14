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
    create_quarterly_trend_chart, create_gap_trend_chart, create_flexible_trend_chart,
    create_gap_analysis, create_gap_chart, PLOTLY_AVAILABLE
)

# ✅ export 모듈 import 수정 - PDF만 언급
try:
    # 현재 디렉토리에 export.py가 있는 경우
    from util.export import generate_pdf_report, create_excel_report, handle_pdf_generation_button
    EXPORT_AVAILABLE = True
except ImportError:
    try:
        # util 폴더에 있는 경우
        from util.export import generate_pdf_report, create_excel_report, handle_pdf_generation_button
        EXPORT_AVAILABLE = True
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
        st.error(f"❌ PDF 생성 모듈 로드 실패: {e}")

from util.email_util import create_email_ui
from news_collector import create_google_news_tab, GoogleNewsCollector

import re, textwrap

def _render_ai_html(raw: str):
    """AI가 준 문자열에서 코드펜스/과도한 들여쓰기를 제거하고 HTML로 렌더"""
    if not raw:
        return ""
    s = raw.strip()

    # 1) ``` ... ``` 코드펜스 제거 (```html, ```HTML 포함)
    s = re.sub(r"^```(?:html|HTML)?\s*", "", s, flags=re.MULTILINE)
    s = re.sub(r"\s*```$", "", s, flags=re.MULTILINE)

    # 2) 공통 들여쓰기 제거 (줄 앞 4칸 이상 → 코드블록 인식 방지)
    s = textwrap.dedent(s)

    # 3) 선행 공백 줄 제거
    s = "\n".join(line.lstrip() if line.lstrip().startswith("<") else line
                  for line in s.splitlines())

    return s

# --- 카드 스타일 (마크다운을 카드처럼 보이게) ---
st.markdown("""
<style>
.md-card {background:#fff;border:1px solid #e9ecef;border-radius:12px;
          box-shadow:0 4px 12px rgba(0,0,0,.05); padding:16px 18px; margin:14px 0;}
.md-card h3, .md-card h4 {margin:0 0 8px 0}
.md-card ul {margin:6px 0 0 18px; line-height:1.6}
.section-title {font-weight:800; font-size:18px; display:flex; gap:8px; align-items:center; margin-bottom:8px}
.section-title .emoji {font-size:20px}
</style>
""", unsafe_allow_html=True)

# --- 마크다운 결과를 '큰 소제목(## 1., ## 2., ...)' 기준 카드로 렌더 ---
def render_insight_as_cards(text: str):
    """
    1) 우선 HTML이 섞여 있으면 그대로 렌더
    2) 그 외에는 '## 1. ...' 같은 번호 달린 H2 제목 기준으로 카드를 만든다.
       - H2 단위로 하나의 카드
    3) 만약 H2 제목을 전혀 못 찾으면 (예: 5-2 ~ 5-5만 있는 경우)
       기존의 📊/⚠️/📈/🎯 4섹션 카드 분해 로직을 사용한다.
    """
    if not text:
        return

    # 1) HTML 포함 시 원문 그대로
    if "<div" in text or "<ul" in text or "<h3" in text or "<aside" in text:
        st.markdown(_render_ai_html(text), unsafe_allow_html=True)
        return

    import re

    s = text.strip()

    # 2) '## 1. ...' 같은 상위 H2 제목 기준으로 섹션 분리
    #    - 캡쳐된 제목 라인(heading_line)과 그 다음 제목 전까지의 본문(body)을 카드로 묶음
    h2_pattern = re.compile(r"(?m)^##\s*\d+\.\s.*$")
    h2_matches = list(h2_pattern.finditer(s))

    if h2_matches:
        # 마지막 섹션까지 본문을 잘라내기 위한 보조 함수
        def _section_slice(start_idx, next_start_idx=None):
            chunk = s[start_idx: next_start_idx].strip() if next_start_idx else s[start_idx:].strip()
            # 첫 줄(제목)과 나머지 본문 분리
            first_newline = chunk.find("\n")
            if first_newline == -1:
                heading_line = chunk
                body = ""
            else:
                heading_line = chunk[:first_newline].strip()
                body = chunk[first_newline+1:].strip()
            return heading_line, body

        for i, m in enumerate(h2_matches):
            start = m.start()
            next_start = h2_matches[i+1].start() if i+1 < len(h2_matches) else None
            heading_line, body = _section_slice(start, next_start)

            # "## " 제거한 제목만 표시
            display_title = heading_line.lstrip("#").strip()

            # 카드 래퍼 + 제목
            st.markdown(
                f"""
<div class="md-card">
  <div class="section-title"><span class="emoji">📑</span><span>{display_title}</span></div>
</div>
""",
                unsafe_allow_html=True,
            )
            # 본문은 마크다운 그대로 렌더
            if body:
                st.markdown(body)

        return

    # 3) H2 제목이 전혀 없으면, 기존의 5-2~5-5 템플릿(📊/⚠️/📈/🎯) 기준으로 카드 분해
    titles = ["📊 경쟁사 비교 분석", "⚠️ 위험신호", "📈 전략방안", "🎯 우선순위"]
    parts = re.split(r"(?=^(?:📊 경쟁사 비교 분석|⚠️ 위험신호|📈 전략방안|🎯 우선순위)\s*$)", s, flags=re.MULTILINE)

    found_any = False
    for part in parts:
        part = part.strip()
        if not part:
            continue
        found = next((t for t in titles if part.startswith(t)), None)
        if found:
            found_any = True
            body = part[len(found):].lstrip()
            st.markdown(
                f"""
<div class="md-card">
  <div class="section-title"><span class="emoji">{found.split()[0]}</span><span>{found}</span></div>
</div>
""",
                unsafe_allow_html=True,
            )
            if body:
                st.markdown(body)
        else:
            st.markdown(part)

    if not found_any:
        st.markdown('<div class="md-card">', unsafe_allow_html=True)
        st.markdown(s)
        st.markdown('</div>', unsafe_allow_html=True)

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
    """재무분석 결과 표시 - 새로운 차트 UI 적용"""
    st.markdown("---")
    st.subheader("💰 손익계산서(연간)")
    final_df = st.session_state.financial_data
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["📊 기본 손익계산서", "🏢 고정비", "📈 변동비", "💰 공헌이익"])
    
    # 표시용 컬럼만 표시 (원시값 제외)
    display_cols = [col for col in final_df.columns if not col.endswith('_원시값')]
    
    with tab1:
        st.markdown("**📋 기본 손익계산서**")
        # 기본 손익계산서 항목들만 필터링
        basic_items = ['매출액', '매출원가', '매출총이익', '판매비와관리비', '영업이익', '영업외수익', '영업외비용', '당기순이익']
        basic_df = final_df[final_df['구분'].isin(basic_items)]
        st.dataframe(
            basic_df[display_cols].set_index('구분'), 
            use_container_width=True,
            column_config={
                "구분": st.column_config.TextColumn("구분", width="medium")
            }
        )
    
    with tab2:
        st.markdown("**💵 고정비**")
        # 고정비 관련 항목들만 필터링 (계산된 고정비 포함, 감가상각비 제외)
        fixed_items = ['고정비', '인건비', '임차료', '관리비', '고정비율(%)']
        fixed_df = final_df[final_df['구분'].isin(fixed_items) | 
                           (final_df['구분'].str.startswith('  └') & 
                            ~final_df['구분'].str.contains('감가상각비'))]
        if not fixed_df.empty:
            st.dataframe(
                fixed_df[display_cols].set_index('구분'), 
                use_container_width=True,
                column_config={
                    "구분": st.column_config.TextColumn("구분", width="medium")
                }
            )
            st.info("💡 **참고**: 고정비 총액에는 감가상각비가 포함되어 있습니다. (감가상각비는 별도로 계산됨)")
        else:
            st.info("💡 고정비 데이터가 수집되지 않았습니다. DART API에서 감가상각비, 인건비 등의 데이터를 확인해보세요.")
    
    with tab3:
        st.markdown("**💸 변동비**")
        # 변동비 관련 항목들만 필터링 (매출원가만 표시)
        variable_items = ['매출원가']
        variable_df = final_df[final_df['구분'].isin(variable_items)]
        if not variable_df.empty:
            st.dataframe(
                variable_df[display_cols].set_index('구분'), 
                use_container_width=True,
                column_config={
                    "구분": st.column_config.TextColumn("구분", width="medium")
                }
            )
        else:
            st.info("💡 매출원가 데이터가 수집되지 않았습니다. DART API에서 매출원가 데이터를 확인해보세요.")
    
    with tab4:
        st.markdown("**💰 공헌이익**")
        # 공헌이익 관련 항목들만 필터링
        contribution_items = ['매출액', '매출원가', '변동비', '공헌이익', '고정비', '영업이익']
        contribution_df = final_df[final_df['구분'].isin(contribution_items)]
        if not contribution_df.empty:
            st.dataframe(
                contribution_df[display_cols].set_index('구분'), 
                use_container_width=True,
                column_config={
                    "구분": st.column_config.TextColumn("구분", width="medium")
                }
            )
            
            # 공헌이익 계산 공식 설명
            st.markdown("---")
            st.markdown("**📝 공헌이익 계산 공식**")
            st.markdown("""
            ```
            공헌이익 = 매출액 - 매출원가 - 변동비
            공헌이익률 = (공헌이익 / 매출액) × 100%
            
            영업이익 = 공헌이익 - 고정비
            ```
            """)
        else:
            st.info("💡 공헌이익 데이터가 수집되지 않았습니다.")
    
    # 전체 데이터 표시 (기존 방식)
    st.markdown("---")
    st.markdown("**📋 전체 재무지표 (표시값)**")
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

            # ✅ 새로운 사용자 지정 트렌드 분석만 사용 (기존 고정 차트 제거)
            st.markdown("---")
            st.subheader("📊 사용자 지정 트렌드 분석")
            
            # 실제 데이터에서 사용 가능한 지표들을 동적으로 확인
            all_columns = list(chart_input.columns)
            exclude_cols = ['분기', '회사', '보고서구분', '연도', '분기번호']
            available_metrics = [col for col in all_columns if col not in exclude_cols]
            
            if available_metrics:
                # 1단계: 회사 선택
                st.markdown("**🏢 1단계: 표시할 회사 선택**")
                available_companies = list(chart_input['회사'].unique()) if '회사' in chart_input.columns else []
                selected_companies_chart = st.multiselect(
                    "회사를 선택하세요",
                    available_companies,
                    default=available_companies,
                    help="차트에 표시할 회사를 선택하세요"
                )
                
                # 2단계: 분기 선택 (지표 선택 단계 제거)
                st.markdown("**📅 2단계: 표시할 분기 선택**") 
                available_quarters = list(chart_input['분기'].unique()) if '분기' in chart_input.columns else []
                selected_quarters = st.multiselect(
                    "분기를 선택하세요",
                    available_quarters,
                    default=available_quarters,
                    help="특정 분기만 선택 가능합니다"
                )
                
                # 3단계: 차트 구성 (개선된 레이아웃) - 전체 지표에서 직접 선택
                st.markdown("**📊 3단계: 차트 표시 방식 설정**")
                
                # ✅ 2열로 변경하여 더 넓은 공간 확보
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    bar_metrics = st.multiselect(
                        "📊 막대로 표시할 지표",
                        available_metrics,  # ✅ 전체 지표에서 직접 선택
                        help="절대값 비교에 적합 (매출액, 영업이익 등)\n💡 2-3개 추천"
                    )
                
                with col2:
                    line_metrics = st.multiselect(
                        "📈 추세선으로 표시할 지표",
                        available_metrics,  # ✅ 전체 지표에서 직접 선택
                        help="트렌드 분석에 적합 (비율, 성장률 등)\n💡 2-3개 추천"
                    )
                
                # ✅ 차트 옵션을 별도 섹션으로 분리
                st.markdown("**⚙️ 차트 옵션**")
                opt_col1, opt_col2, opt_col3 = st.columns(3)
                
                with opt_col1:
                    chart_height = st.selectbox("차트 높이", [400, 500, 600, 700, 800], index=2)
                
                with opt_col2:
                    show_values = st.checkbox("수치 표시", value=False, help="데이터 포인트에 값 표시")
                
                with opt_col3:
                    compact_legend = st.checkbox("범례 압축", value=True, help="범례를 더 작게 표시")
                
                # 선택 결과 및 권장사항 표시
                total_metrics = len(bar_metrics) + len(line_metrics)
                if total_metrics > 0:
                    # 색상으로 구분된 정보 표시
                    info_col1, info_col2 = st.columns(2)
                    with info_col1:
                        st.info(f"📊 막대: {len(bar_metrics)}개")
                    with info_col2:
                        st.info(f"📈 추세선: {len(line_metrics)}개")
                    
                    # ✅ 가독성 경고 및 권장사항
                    if total_metrics > 6:
                        st.warning("⚠️ 지표가 많아 차트가 복잡할 수 있습니다. 6개 이하 권장")
                    elif len(bar_metrics) > 3:
                        st.warning("💡 막대 차트가 3개를 초과하면 겹칠 수 있습니다.")
                    elif len(line_metrics) > 4:
                        st.warning("💡 추세선이 4개를 초과하면 구분하기 어려울 수 있습니다.")
                    
                    # 겹치는 지표 체크
                    overlap = set(bar_metrics) & set(line_metrics)
                    if overlap:
                        st.warning(f"⚠️ 중복 선택: {', '.join(overlap)} (막대와 추세선 모두 표시)")
                
                # 필터링된 데이터 생성
                filtered_data = chart_input.copy()
                if selected_companies_chart and '회사' in filtered_data.columns:
                    filtered_data = filtered_data[filtered_data['회사'].isin(selected_companies_chart)]
                if selected_quarters and '분기' in filtered_data.columns:
                    filtered_data = filtered_data[filtered_data['분기'].isin(selected_quarters)]
                
                # 차트 생성 및 표시
                if (bar_metrics or line_metrics) and not filtered_data.empty:
                    # ✅ 새로운 차트 함수 호출 (show_values 파라미터 추가)
                    flexible_chart = create_flexible_trend_chart(
                        filtered_data, 
                        bar_metrics=bar_metrics, 
                        line_metrics=line_metrics,
                        show_values=show_values  # ✅ 수치 표시 옵션 전달
                    )
                    
                    if flexible_chart:
                        # ✅ 범례 압축 옵션만 적용 (수치 표시는 차트 함수에서 처리)
                        if compact_legend:
                            flexible_chart.update_layout(
                                title={
                                    'x': 0.0,  # ✅ 제목 왼쪽 정렬
                                    'xanchor': 'left'  # ✅ 왼쪽 기준점
                                },
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.35,  # ✅ 더 아래로 이동 (-0.25에서 -0.35로)
                                    xanchor="center",
                                    x=0.5,
                                    font=dict(size=8),
                                    bgcolor="rgba(255,255,255,0.8)",
                                    bordercolor="gray",
                                    borderwidth=1
                                ),
                                margin=dict(b=140)  # ✅ 하단 여백 증가 (120에서 140으로)
                            )
                        else:
                            # 범례 압축 안 할 때도 제목 왼쪽 정렬 적용
                            flexible_chart.update_layout(
                                title={
                                    'x': 0.0,  # ✅ 제목 왼쪽 정렬
                                    'xanchor': 'left'  # ✅ 왼쪽 기준점
                                }
                            )
                        
                        # 차트 높이 적용
                        flexible_chart.update_layout(height=chart_height)
                        st.plotly_chart(flexible_chart, use_container_width=True, key="flexible_trend")
                        
                        # 선택된 설정 요약
                        st.success(f"✅ 현재 표시 중: 회사 {len(selected_companies_chart)}개, 분기 {len(selected_quarters)}개, 총 지표 {total_metrics}개")
                        
                    else:
                        st.warning("선택된 설정으로 차트를 생성할 수 없습니다.")
                else:
                    st.info("💡 막대 또는 추세선 지표를 선택하면 차트가 표시됩니다.")
            else:
                st.warning("사용 가능한 지표가 없습니다. 분기별 데이터를 다시 확인해주세요.")
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
        render_insight_as_cards(st.session_state.financial_insight)
        
def render_manual_upload_tab():
    """수동 파일 업로드 탭 렌더링"""
    st.subheader("📁 파일 업로드 분석")
    st.info("💡 DART에서 다운로드한 XBRL 파일을 직접 업로드하여 분석할 수 있습니다.")

    st.warning("⚠️ 주의 - 각 회사의 분기별 XBRL 파일을 업로드해 주세요.")
    
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

    # 수동 업로드 결과 표시 (새로운 UI 구조 적용)
    if SessionManager.is_data_available('manual_financial_data'):
        st.markdown("---")
        st.subheader("💰 손익계산서(연간)")
        final_df = st.session_state.manual_financial_data
        
        # 탭 생성 (수동 업로드용)
        tab1, tab2, tab3, tab4 = st.tabs(["📊 기본 손익계산서", "🏢 고정비", "📈 변동비", "💰 공헌이익"])
        
        # 표시용 컬럼만 표시
        display_cols = [col for col in final_df.columns if not col.endswith('_원시값')]
        
        with tab1:
            st.markdown("**📋 기본 손익계산서**")
            # 기본 손익계산서 항목들만 필터링
            basic_items = ['매출액', '매출원가', '매출총이익', '판매비와관리비', '영업이익', '영업외수익', '영업외비용', '당기순이익']
            basic_df = final_df[final_df['구분'].isin(basic_items)]
            st.dataframe(
                basic_df[display_cols].set_index('구분'), 
                use_container_width=True,
                column_config={
                    "구분": st.column_config.TextColumn("구분", width="medium")
                }
            )
        
        with tab2:
             st.markdown("**💵 고정비**")
            # 고정비 관련 항목들만 필터링 (계산된 고정비 포함, 감가상각비 제외)
            fixed_items = ['고정비', '인건비', '임차료', '관리비', '고정비율(%)']
            fixed_df = final_df[final_df['구분'].isin(fixed_items) | 
                               (final_df['구분'].str.startswith('  └') & 
                                ~final_df['구분'].str.contains('감가상각비'))]
            if not fixed_df.empty:
                st.dataframe(
                    fixed_df[display_cols].set_index('구분'), 
                    use_container_width=True,
                    column_config={
                        "구분": st.column_config.TextColumn("구분", width="medium")
                    }
                )
                st.info("💡 **참고**: 고정비 총액에는 감가상각비가 포함되어 있습니다. (감가상각비는 별도로 계산됨)")
            else:
                st.info("💡 고정비 데이터가 수집되지 않았습니다. DART API에서 감가상각비, 인건비 등의 데이터를 확인해보세요.")
        
        with tab3:
            st.markdown("**💸 변동비**")
            # 변동비 관련 항목들만 필터링 (매출원가만 표시)
            variable_items = ['매출원가']
            variable_df = final_df[final_df['구분'].isin(variable_items)]
            if not variable_df.empty:
                st.dataframe(
                    variable_df[display_cols].set_index('구분'), 
                    use_container_width=True,
                    column_config={
                        "구분": st.column_config.TextColumn("구분", width="medium")
                    }
                )
            else:
                st.info("💡 매출원가 데이터가 수집되지 않았습니다. DART API에서 매출원가 데이터를 확인해보세요.")
        
        with tab4:
            st.markdown("**💰 공헌이익**")
            # 공헌이익 관련 항목들만 필터링
            contribution_items = ['매출액', '매출원가', '변동비', '공헌이익', '고정비', '영업이익']
            contribution_df = final_df[final_df['구분'].isin(contribution_items)]
            if not contribution_df.empty:
                st.dataframe(
                    contribution_df[display_cols].set_index('구분'), 
                    use_container_width=True,
                    column_config={
                        "구분": st.column_config.TextColumn("구분", width="medium")
                    }
                )
                
                # 공헌이익 계산 공식 설명
                st.markdown("---")
                st.markdown("**📝 공헌이익 계산 공식**")
                st.markdown("""
                ```
                공헌이익 = 매출액 - 매출원가 - 변동비
                공헌이익률 = (공헌이익 / 매출액) × 100%
                
                영업이익 = 공헌이익 - 고정비
                ```
                """)
            else:
                st.info("💡 공헌이익 데이터가 수집되지 않았습니다.")
        
        # 전체 데이터 표시 (기존 방식)
        st.markdown("---")
        st.markdown("**📋 전체 재무지표 (표시값)**")
        st.dataframe(final_df[display_cols].set_index('구분'), use_container_width=True)

        # ✅ 수동 업로드용 막대/추세선 차트 추가
        st.markdown("---")
        st.subheader("📊 수동 업로드 데이터 시각화")
        
        if PLOTLY_AVAILABLE:
            # 재무 데이터를 차트용으로 변환
            chart_data_list = []
            
            # 회사 컬럼 찾기 (구분, _원시값 제외)
            company_cols = [col for col in final_df.columns 
                           if col != '구분' and not col.endswith('_원시값')]
            
            # 데이터를 차트용 형태로 변환
            for _, row in final_df.iterrows():
                metric = row['구분']
                for company in company_cols:
                    value = row[company]
                    if pd.notna(value):
                        # 숫자 추출
                        try:
                            if isinstance(value, str):
                                clean_value = value.replace('%', '').replace('조원', '').replace(',', '')
                                numeric_value = float(clean_value)
                            else:
                                numeric_value = float(value)
                            
                            chart_data_list.append({
                                '구분': metric,
                                '회사': company, 
                                '수치': numeric_value
                            })
                        except:
                            continue
            
            if chart_data_list:
                chart_df_manual = pd.DataFrame(chart_data_list)
                
                st.markdown("**📊 사용자 지정 차트 설정**")
                
                # 1단계: 회사 선택
                st.markdown("**🏢 1단계: 표시할 회사 선택**")
                available_companies_manual = list(chart_df_manual['회사'].unique())
                selected_companies_chart_manual = st.multiselect(
                    "회사를 선택하세요",
                    available_companies_manual,
                    default=available_companies_manual,
                    help="차트에 표시할 회사를 선택하세요",
                    key="manual_chart_companies"
                )
                
                # 2단계: 지표 선택
                st.markdown("**📊 2단계: 차트 표시 방식 설정**")
                available_metrics_manual = list(chart_df_manual['구분'].unique())
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    bar_metrics_chart_manual = st.multiselect(
                        "📊 막대로 표시할 지표",
                        available_metrics_manual,
                        help="절대값 비교에 적합 (매출액, 영업이익 등)\n💡 2-3개 추천",
                        key="manual_chart_bar_metrics"
                    )
                
                with col2:
                    line_metrics_chart_manual = st.multiselect(
                        "📈 추세선으로 표시할 지표",
                        available_metrics_manual,
                        help="비율 지표에 적합 (마진율, 성장률 등)\n💡 2-3개 추천",
                        key="manual_chart_line_metrics"
                    )
                
                # 차트 옵션
                st.markdown("**⚙️ 차트 옵션**")
                opt_col1, opt_col2, opt_col3 = st.columns(3)
                
                with opt_col1:
                    chart_height_manual_chart = st.selectbox("차트 높이", [400, 500, 600, 700, 800], index=2, key="manual_chart_height_opt")
                
                with opt_col2:
                    show_values_manual_chart = st.checkbox("수치 표시", value=False, key="manual_chart_show_values")
                
                with opt_col3:
                    compact_legend_manual_chart = st.checkbox("범례 압축", value=True, key="manual_chart_compact_legend")
                
                # 필터링된 데이터 생성
                filtered_chart_data = chart_df_manual.copy()
                if selected_companies_chart_manual:
                    filtered_chart_data = filtered_chart_data[filtered_chart_data['회사'].isin(selected_companies_chart_manual)]
                
                # 차트 생성
                if (bar_metrics_chart_manual or line_metrics_chart_manual) and not filtered_chart_data.empty:
                    # 막대 차트용 데이터
                    bar_data = filtered_chart_data[filtered_chart_data['구분'].isin(bar_metrics_chart_manual)] if bar_metrics_chart_manual else pd.DataFrame()
                    # 라인 차트용 데이터  
                    line_data = filtered_chart_data[filtered_chart_data['구분'].isin(line_metrics_chart_manual)] if line_metrics_chart_manual else pd.DataFrame()
                    
                    import plotly.graph_objects as go
                    from plotly.subplots import make_subplots
                    
                    fig = go.Figure()
                    
                    # 막대 차트 추가
                    if not bar_data.empty:
                        for company in bar_data['회사'].unique():
                            company_data = bar_data[bar_data['회사'] == company]
                            fig.add_trace(go.Bar(
                                name=f"{company} (막대)",
                                x=company_data['구분'],
                                y=company_data['수치'],
                                text=company_data['수치'].round(2) if show_values_manual_chart else None,
                                textposition='auto' if show_values_manual_chart else None,
                                yaxis='y'
                            ))
                    
                    # 라인 차트 추가
                    if not line_data.empty:
                        for company in line_data['회사'].unique():
                            company_data = line_data[line_data['회사'] == company]
                            fig.add_trace(go.Scatter(
                                name=f"{company} (추세선)",
                                x=company_data['구분'],
                                y=company_data['수치'],
                                mode='lines+markers',
                                text=company_data['수치'].round(2) if show_values_manual_chart else None,
                                textposition='top center' if show_values_manual_chart else None,
                                yaxis='y2'
                            ))
                    
                    # 레이아웃 설정
                    fig.update_layout(
                        title="수동 업로드 데이터 분석 차트",
                        xaxis_title="재무 지표",
                        yaxis=dict(title="막대 차트 값", side="left"),
                        yaxis2=dict(title="추세선 값", side="right", overlaying="y"),
                        height=chart_height_manual_chart,
                        showlegend=True
                    )
                    
                    # 범례 설정
                    if compact_legend_manual_chart:
                        fig.update_layout(
                            title={'x': 0.0, 'xanchor': 'left'},
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=-0.35,
                                xanchor="center",
                                x=0.5,
                                font=dict(size=8),
                                bgcolor="rgba(255,255,255,0.8)",
                                bordercolor="gray",
                                borderwidth=1
                            ),
                            margin=dict(b=140)
                        )
                    else:
                        fig.update_layout(title={'x': 0.0, 'xanchor': 'left'})
                    
                    st.plotly_chart(fig, use_container_width=True, key="manual_upload_chart")
                    
                    total_metrics_manual_chart = len(bar_metrics_chart_manual) + len(line_metrics_chart_manual)
                    st.success(f"✅ 현재 표시 중: 회사 {len(selected_companies_chart_manual)}개, 총 지표 {total_metrics_manual_chart}개")
                else:
                    st.info("💡 막대 또는 추세선 지표를 선택하면 차트가 표시됩니다.")
            else:
                st.warning("차트를 생성할 수 있는 숫자 데이터가 없습니다.")
        else:
            st.info("📊 차트 모듈이 없습니다.")

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
            render_insight_as_cards(st.session_state.manual_financial_insight)

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
            st.warning("⚠️ 최소 하나의 인사이트(재무 분석 또는 구글 뉴스)가 필요합니다.")
    
    # 통합 인사이트 결과 표시
    if SessionManager.is_data_available('integrated_insight'):
        st.subheader("🤖 통합 인사이트 결과")
        render_insight_as_cards(st.session_state.integrated_insight)
    else:
        st.info("재무 분석과 구글 뉴스 분석을 완료한 후 통합 인사이트를 생성할 수 있습니다.")

def render_report_generation_tab():
    """보고서 생성 탭 렌더링 - PDF만"""
    st.subheader("📄 PDF 보고서 생성 & 이메일 서비스 바로가기")

    # 2열 레이아웃: PDF 생성 + 이메일 입력
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("**📄 PDF 보고서 다운로드**")

        # 사용자 입력
        report_target = st.text_input("보고 대상", value="SK이노베이션 경영진")
        report_author = st.text_input("보고자", value="")
        show_footer = st.checkbox(
            "푸터 문구 표시(※ 본 보고서는 대시보드에서 자동 생성되었습니다.)", 
            value=False
        )

        # ✅ 데이터 우선순위: DART 자동 > 수동 업로드
        financial_data_for_report = None
        if SessionManager.is_data_available('financial_data'):
            financial_data_for_report = st.session_state.financial_data
        elif SessionManager.is_data_available('manual_financial_data'):
            financial_data_for_report = st.session_state.manual_financial_data

        # ✅ PDF 생성 섹션
        if EXPORT_AVAILABLE:
            st.markdown("---")
            st.markdown("**🚀 한글 PDF 생성 (NanumGothic 폰트)**")
            
            # ✅ 버튼을 직접 만들고 클릭 처리
            if st.button("📄 PDF 보고서 생성", type="primary", key="advanced_pdf_btn"):
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
        else:
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
            st.success("✅ PDF 보고서 생성 가능")
        else:
            st.warning("⚠️ PDF 생성 불가")
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
        "📁 재무 분석(파일 업로드)", 
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
