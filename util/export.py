# -*- coding: utf-8 -*-
"""
완전한 Streamlit 보고서 생성 통합 모듈
구조화된 SK에너지 보고서 생성 (matplotlib 기반)
"""

import io
import os
import pandas as pd
from datetime import datetime
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUI 없는 환경에서 안전하게 사용

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    Paragraph, Table, TableStyle, Spacer, PageBreak, Image as RLImage, SimpleDocTemplate
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Optional OpenAI (GPT) integration
try:
    import openai
    GPT_AVAILABLE = True
except Exception:
    GPT_AVAILABLE = False


# --------------------------
# 폰트 등록 관련 유틸
# --------------------------
def register_fonts_safe():
    """안전하게 폰트를 등록하고 사용 가능한 폰트 이름을 반환"""
    registered_fonts = {
        "Korean": "Helvetica",
        "KoreanBold": "Helvetica-Bold", 
        "KoreanSerif": "Times-Roman"
    }
    
    # 한글 폰트가 있다면 여기서 등록
    font_paths = {
        "Korean": "fonts/NanumGothic.ttf",
        "KoreanBold": "fonts/NanumGothicBold.ttf",
        "KoreanSerif": "fonts/NanumMyeongjo.ttf"
    }
    
    for key, path in font_paths.items():
        try:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                if key not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(key, path))
                registered_fonts[key] = key
        except Exception:
            pass  # 폰트 등록 실패시 기본 폰트 사용
    
    return registered_fonts


def safe_str_convert(value):
    """안전하게 값을 문자열로 변환"""
    try:
        if pd.isna(value):
            return ""
        return str(value)
    except Exception:
        return ""


# --------------------------
# 테이블 생성 유틸리티
# --------------------------
def create_simple_table(df, registered_fonts, header_color='#E31E24'):
    """DataFrame을 간단한 reportlab 테이블로 변환"""
    try:
        if df is None or df.empty:
            return None
            
        # 헤더 + 데이터
        table_data = [df.columns.tolist()]
        for _, row in df.iterrows():
            table_data.append([safe_str_convert(val) for val in row.values])
        
        tbl = Table(table_data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), registered_fonts.get('KoreanBold', 'Helvetica-Bold')),
            ('FONTNAME', (0, 1), (-1, -1), registered_fonts.get('Korean', 'Helvetica')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F8F8')]),
        ]))
        return tbl
    except Exception:
        return None


def add_chart_to_story(story, fig, title, body_style):
    """matplotlib 차트를 story에 추가"""
    try:
        if fig is None:
            story.append(Paragraph(f"{title}: 차트 데이터가 없습니다.", body_style))
            return
            
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        img_buffer.seek(0)
        
        story.append(Paragraph(title, body_style))
        story.append(Spacer(1, 6))
        img = RLImage(img_buffer, width=480, height=320)
        story.append(img)
        story.append(Spacer(1, 12))
    except Exception as e:
        story.append(Paragraph(f"{title}: 차트 생성 실패 ({e})", body_style))
        story.append(Spacer(1, 12))


# --------------------------
# 1. 재무분석 결과 섹션
# --------------------------
def add_section_1_financial_analysis(
    story, 
    financial_summary_df,
    quarterly_trend_chart,
    gap_analysis_df,
    gap_visualization_chart,
    financial_insights,
    registered_fonts, 
    heading_style, 
    body_style
):
    """1. 재무분석 결과 전체 섹션 추가"""
    try:
        # 섹션 제목
        story.append(Paragraph("1. 재무분석 결과", heading_style))
        story.append(Spacer(1, 12))
        
        # 1-1. 정리된 재무지표 (표시값)
        story.append(Paragraph("1-1. 정리된 재무지표 (표시값)", body_style))
        story.append(Spacer(1, 6))
        
        if financial_summary_df is not None and not financial_summary_df.empty:
            tbl = create_simple_table(financial_summary_df, registered_fonts, '#E6F3FF')
            if tbl:
                story.append(tbl)
            else:
                story.append(Paragraph("재무지표 테이블 생성 실패", body_style))
        else:
            story.append(Paragraph("재무지표 데이터가 없습니다.", body_style))
        
        story.append(Spacer(1, 16))
        
        # 1-1-1. 분기별 트랜드 차트
        add_chart_to_story(story, quarterly_trend_chart, "1-1-1. 분기별 트랜드 차트", body_style)
        
        # 1-2. 갭차이 분석표
        story.append(Paragraph("1-2. SK에너지 대비 경쟁사 갭차이 분석표", body_style))
        story.append(Spacer(1, 6))
        
        if gap_analysis_df is not None and not gap_analysis_df.empty:
            tbl = create_simple_table(gap_analysis_df, registered_fonts, '#FFE6E6')
            if tbl:
                story.append(tbl)
            else:
                story.append(Paragraph("갭차이 분석표 생성 실패", body_style))
        else:
            story.append(Paragraph("갭차이 분석 데이터가 없습니다.", body_style))
        
        story.append(Spacer(1, 16))
        
        # 1-2-1. 갭차이 시각화 차트
        add_chart_to_story(story, gap_visualization_chart, "1-2-1. 갭차이 시각화 차트", body_style)
        
        # 1-3. AI 재무 인사이트
        story.append(Paragraph("1-3. AI 재무 인사이트", body_style))
        story.append(Spacer(1, 6))
        
        if financial_insights:
            for line in str(financial_insights).split('\n'):
                line = line.strip()
                if line:
                    if line.startswith('#') or line.startswith('*'):
                        clean_line = line.lstrip('#*').strip()
                        story.append(Paragraph(f"<b>{clean_line}</b>", body_style))
                    else:
                        story.append(Paragraph(line, body_style))
        else:
            story.append(Paragraph("AI 재무 인사이트가 없습니다.", body_style))
        
        story.append(Spacer(1, 24))
        
    except Exception as e:
        story.append(Paragraph(f"재무분석 섹션 생성 오류: {e}", body_style))
        story.append(Spacer(1, 24))


# --------------------------
# 2. 뉴스분석 섹션  
# --------------------------
def add_section_2_news_analysis(
    story,
    collected_news_df,
    news_insights,
    registered_fonts,
    heading_style, 
    body_style
):
    """2. 뉴스분석 결과 전체 섹션 추가"""
    try:
        # 섹션 제목
        story.append(Paragraph("2. 뉴스분석 결과", heading_style))
        story.append(Spacer(1, 12))
        
        # 2-1. 수집된 뉴스 하이라이트
        story.append(Paragraph("2-1. 수집된 뉴스 하이라이트", body_style))
        story.append(Spacer(1, 6))
        
        if collected_news_df is not None and not collected_news_df.empty:
            title_col = None
            for col in collected_news_df.columns:
                if '제목' in col or 'title' in col.lower() or 'headline' in col.lower():
                    title_col = col
                    break
            
            if title_col is None and len(collected_news_df.columns) > 0:
                title_col = collected_news_df.columns[0]
            
            if title_col:
                for i, title in enumerate(collected_news_df[title_col].head(10), 1):
                    story.append(Paragraph(f"{i}. {safe_str_convert(title)}", body_style))
            else:
                story.append(Paragraph("뉴스 제목 컬럼을 찾을 수 없습니다.", body_style))
        else:
            story.append(Paragraph("수집된 뉴스 데이터가 없습니다.", body_style))
        
        story.append(Spacer(1, 16))
        
        # 2-2. 뉴스 분석 테이블 (옵션)
        if collected_news_df is not None and not collected_news_df.empty and len(collected_news_df.columns) > 1:
            story.append(Paragraph("2-2. 뉴스 분석 상세", body_style))
            story.append(Spacer(1, 6))
            
            news_summary = collected_news_df.head(5)
            tbl = create_simple_table(news_summary, registered_fonts, '#E6FFE6')
            if tbl:
                story.append(tbl)
            story.append(Spacer(1, 16))
        
        # 2-3. 뉴스 AI 인사이트  
        story.append(Paragraph("2-3. 뉴스 AI 인사이트", body_style))
        story.append(Spacer(1, 6))
        
        if news_insights:
            for line in str(news_insights).split('\n'):
                line = line.strip()
                if line:
                    if line.startswith('#') or line.startswith('*'):
                        clean_line = line.lstrip('#*').strip()
                        story.append(Paragraph(f"<b>{clean_line}</b>", body_style))
                    else:
                        story.append(Paragraph(line, body_style))
        else:
            story.append(Paragraph("뉴스 AI 인사이트가 없습니다.", body_style))
        
        story.append(Spacer(1, 24))
        
    except Exception as e:
        story.append(Paragraph(f"뉴스분석 섹션 생성 오류: {e}", body_style))
        story.append(Spacer(1, 24))


# --------------------------
# 3. 통합 인사이트 섹션
# --------------------------
def add_section_3_integrated_insights(
    story,
    integrated_insights,
    strategic_recommendations,
    registered_fonts,
    heading_style,
    body_style
):
    """3. 통합 인사이트 전체 섹션 추가"""
    try:
        # 섹션 제목
        story.append(Paragraph("3. 통합 인사이트", heading_style))
        story.append(Spacer(1, 12))
        
        # 3-1. 통합 분석 결과
        story.append(Paragraph("3-1. 통합 분석 결과", body_style))
        story.append(Spacer(1, 6))
        
        if integrated_insights:
            for line in str(integrated_insights).split('\n'):
                line = line.strip()
                if line:
                    if line.startswith('#') or line.startswith('*'):
                        clean_line = line.lstrip('#*').strip()
                        story.append(Paragraph(f"<b>{clean_line}</b>", body_style))
                    else:
                        story.append(Paragraph(line, body_style))
        else:
            story.append(Paragraph("통합 인사이트 데이터가 없습니다.", body_style))
        
        story.append(Spacer(1, 16))
        
        # 3-2. 전략 제안 (GPT 기반, 옵션)
        if strategic_recommendations:
            story.append(Paragraph("3-2. AI 기반 전략 제안", body_style))
            story.append(Spacer(1, 6))
            
            for line in str(strategic_recommendations).split('\n'):
                line = line.strip()
                if line:
                    if line.startswith('#') or line.startswith('*'):
                        clean_line = line.lstrip('#*').strip()
                        story.append(Paragraph(f"<b>{clean_line}</b>", body_style))
                    else:
                        story.append(Paragraph(line, body_style))
        
        story.append(Spacer(1, 24))
        
    except Exception as e:
        story.append(Paragraph(f"통합 인사이트 섹션 생성 오류: {e}", body_style))
        story.append(Spacer(1, 24))


# --------------------------
# PDF 보고서 생성 함수
# --------------------------
def create_structured_pdf_report(
    financial_summary_df=None,
    quarterly_trend_chart=None,
    gap_analysis_df=None,
    gap_visualization_chart=None,
    financial_insights=None,
    collected_news_df=None,
    news_insights=None,
    integrated_insights=None,
    gpt_api_key=None,
    report_target="SK이노베이션 경영진",
    report_author="AI 분석 시스템",
    show_footer=True
):
    """구조화된 PDF 보고서 생성"""
    try:
        registered_fonts = register_fonts_safe()
        
        # 스타일 정의
        TITLE_STYLE = ParagraphStyle(
            'Title',
            fontName=registered_fonts.get('KoreanBold', 'Helvetica-Bold'),
            fontSize=18,
            leading=24,
            spaceAfter=20,
            alignment=1,
        )
        
        HEADING_STYLE = ParagraphStyle(
            'Heading',
            fontName=registered_fonts.get('KoreanBold', 'Helvetica-Bold'),
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#E31E24'),
            spaceBefore=16,
            spaceAfter=8,
        )
        
        BODY_STYLE = ParagraphStyle(
            'Body',
            fontName=registered_fonts.get('Korean', 'Helvetica'),
            fontSize=10,
            leading=14,
            spaceAfter=4,
        )
        
        # PDF 문서 설정
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            leftMargin=40, 
            rightMargin=40, 
            topMargin=50, 
            bottomMargin=50
        )
        
        story = []
        
        # 표지
        story.append(Paragraph("SK에너지 종합 분석 보고서", TITLE_STYLE))
        story.append(Spacer(1, 20))
        
        # 보고서 정보
        report_info = f"""
        <b>보고일자:</b> {datetime.now().strftime('%Y년 %m월 %d일')}<br/>
        <b>보고대상:</b> {safe_str_convert(report_target)}<br/>
        <b>보고자:</b> {safe_str_convert(report_author)}
        """
        story.append(Paragraph(report_info, BODY_STYLE))
        story.append(Spacer(1, 30))
        
        # 1. 재무분석 결과
        add_section_1_financial_analysis(
            story, 
            financial_summary_df,
            quarterly_trend_chart,
            gap_analysis_df,
            gap_visualization_chart, 
            financial_insights,
            registered_fonts,
            HEADING_STYLE,
            BODY_STYLE
        )
        
        # 2. 뉴스분석 결과  
        add_section_2_news_analysis(
            story,
            collected_news_df,
            news_insights,
            registered_fonts, 
            HEADING_STYLE,
            BODY_STYLE
        )
        
        # 3. 통합 인사이트
        strategic_recommendations = None
        if gpt_api_key and (financial_insights or news_insights or integrated_insights):
            # GPT 전략 제안 생성 로직 (간단한 예시)
            strategic_recommendations = "GPT 기반 전략 제안이 여기에 표시됩니다."
        
        add_section_3_integrated_insights(
            story,
            integrated_insights,
            strategic_recommendations,
            registered_fonts,
            HEADING_STYLE, 
            BODY_STYLE
        )
        
        # 푸터
        if show_footer:
            story.append(Spacer(1, 20))
            footer_text = "※ 본 보고서는 AI 분석 시스템에서 자동 생성되었습니다."
            story.append(Paragraph(footer_text, BODY_STYLE))
        
        # 페이지 번호 함수
        def add_page_number(canvas, doc):
            try:
                canvas.setFont('Helvetica', 8)
                canvas.drawCentredString(A4[0]/2, 25, f"- {canvas.getPageNumber()} -")
            except Exception:
                pass
        
        # PDF 빌드
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        # 에러 PDF 생성
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            error_story = [
                Paragraph("보고서 생성 오류", getSampleStyleSheet()['Title']),
                Spacer(1, 20),
                Paragraph(f"오류 내용: {str(e)}", getSampleStyleSheet()['Normal']),
                Spacer(1, 12),
                Paragraph("데이터를 확인하고 다시 시도해주세요.", getSampleStyleSheet()['Normal'])
            ]
            doc.build(error_story)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception:
            raise e


# --------------------------
# Excel 보고서 생성
# --------------------------
def create_excel_report(
    financial_summary_df=None,
    gap_analysis_df=None, 
    collected_news_df=None,
    financial_insights=None,
    news_insights=None,
    integrated_insights=None
):
    """구조화된 Excel 보고서 생성"""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # 재무분석 시트
            if financial_summary_df is not None and not financial_summary_df.empty:
                financial_summary_df.to_excel(writer, sheet_name='재무지표_요약', index=False)
            
            if gap_analysis_df is not None and not gap_analysis_df.empty:
                gap_analysis_df.to_excel(writer, sheet_name='갭차이_분석', index=False)
            
            # 뉴스분석 시트
            if collected_news_df is not None and not collected_news_df.empty:
                collected_news_df.to_excel(writer, sheet_name='뉴스_수집', index=False)
            
            # 인사이트 시트
            insights_data = []
            if financial_insights:
                insights_data.append(['재무 인사이트', financial_insights])
            if news_insights:
                insights_data.append(['뉴스 인사이트', news_insights])
            if integrated_insights:
                insights_data.append(['통합 인사이트', integrated_insights])
            
            if insights_data:
                insights_df = pd.DataFrame(insights_data, columns=['구분', '내용'])
                insights_df.to_excel(writer, sheet_name='AI_인사이트', index=False)
            
            # 빈 시트라도 하나는 생성
            if not any([
                financial_summary_df is not None and not financial_summary_df.empty,
                gap_analysis_df is not None and not gap_analysis_df.empty,
                collected_news_df is not None and not collected_news_df.empty,
                insights_data
            ]):
                pd.DataFrame({'메모': ['데이터가 없습니다.']}).to_excel(writer, sheet_name='요약', index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        # 에러 Excel 생성
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            error_df = pd.DataFrame({
                '오류': [f"Excel 생성 중 오류: {str(e)}"],
                '해결방법': ['데이터를 확인하고 다시 시도해주세요.']
            })
            error_df.to_excel(writer, sheet_name='오류정보', index=False)
        output.seek(0)
        return output.getvalue()


# --------------------------
# Streamlit에서 실제 데이터 가져오기
# --------------------------
def get_streamlit_data():
    """Streamlit session_state에서 실제 데이터 가져오기"""
    
    # 1. 재무 요약 데이터 생성
    financial_summary_df = None
    if 'processed_financial_data' in st.session_state and st.session_state.processed_financial_data is not None:
        financial_summary_df = st.session_state.processed_financial_data
    elif 'selected_companies_data' in st.session_state and st.session_state.selected_companies_data is not None:
        # 기존 재무 데이터에서 요약 생성
        financial_summary_df = st.session_state.selected_companies_data
    else:
        # 샘플 데이터 생성
        financial_summary_df = pd.DataFrame({
            '구분': ['매출액(조원)', '영업이익률(%)', 'ROE(%)', 'ROA(%)'],
            'SK에너지': [15.2, 5.6, 12.3, 8.1],
            'S-Oil': [14.8, 5.3, 11.8, 7.8], 
            'GS칼텍스': [13.5, 4.6, 10.5, 7.2],
            'HD현대오일뱅크': [11.2, 4.3, 9.2, 6.5]
        })
    
    # 2. 갭 분석 데이터 생성
    gap_analysis_df = None
    if 'gap_analysis_data' in st.session_state and st.session_state.gap_analysis_data is not None:
        gap_analysis_df = st.session_state.gap_analysis_data
    else:
        # 재무 데이터에서 갭 분석 생성
        if financial_summary_df is not None:
            gap_analysis_df = pd.DataFrame({
                '지표': ['매출액', '영업이익률', 'ROE'],
                'SK에너지': [15.2, 5.6, 12.3],
                'S-Oil_갭(%)': [-2.6, -5.4, -4.1],
                'GS칼텍스_갭(%)': [-11.2, -17.9, -14.6],
                'HD현대오일뱅크_갭(%)': [-26.3, -23.2, -25.2]
            })
    
    # 3. 뉴스 데이터
    collected_news_df = None
    if 'collected_news' in st.session_state and st.session_state.collected_news is not None:
        collected_news_df = st.session_state.collected_news
    elif 'news_df' in st.session_state and st.session_state.news_df is not None:
        collected_news_df = st.session_state.news_df
    else:
        # 샘플 뉴스 데이터
        collected_news_df = pd.DataFrame({
            '제목': [
                'SK에너지, 3분기 실적 시장 기대치 상회',
                '정유업계, 원유가 하락으로 마진 개선 기대',
                'SK이노베이션, 배터리 사업 분할 추진',
                '에너지 전환 정책, 정유업계 영향 분석',
                '아시아 정유 마진, 계절적 상승세 지속'
            ],
            '날짜': ['2024-11-01', '2024-10-28', '2024-10-25', '2024-10-22', '2024-10-20'],
            '출처': ['매일경제', '한국경제', '조선일보', '이데일리', '연합뉴스']
        })
    
    # 4. AI 인사이트들
    financial_insights = st.session_state.get('financial_insights', '') or st.session_state.get('ai_insights', '')
    news_insights = st.session_state.get('news_insights', '') or st.session_state.get('news_ai_insights', '')
    integrated_insights = st.session_state.get('integrated_insights', '') or st.session_state.get('final_insights', '')
    
    # 인사이트가 비어있으면 샘플 생성
    if not financial_insights:
        financial_insights = """
# 재무 성과 핵심 분석
* SK에너지는 매출액 15.2조원으로 업계 1위 유지
* 영업이익률 5.6%로 경쟁사 대비 우위 확보  
* ROE 12.3%로 양호한 자본 효율성 시현

## 개선 필요 영역
- 변동비 관리 최적화를 통한 마진 개선
- 고부가가치 제품 믹스 확대 검토
"""
    
    if not news_insights:
        news_insights = """
# 뉴스 분석 종합
* 3분기 실적 호조로 시장 신뢰도 상승
* 원유가 안정화로 정유 마진 개선 환경 조성
* 에너지 전환 정책 대응 필요성 증대

## 주요 이슈
- 배터리 사업 분할을 통한 포트폴리오 최적화
- ESG 경영 강화 및 탄소중립 로드맵 구체화
"""
    
    if not integrated_insights:
        integrated_insights = """
# 종합 분석 결과
SK에너지는 재무적으로 견고한 성과를 유지하고 있으나, 장기적 성장 동력 확보를 위한 전략적 전환점에 서 있음.

## 핵심 전략 방향
1. **단기**: 운영 효율성 극대화를 통한 마진 확대
2. **중기**: 신사업 진출 및 포트폴리오 다각화  
3. **장기**: 에너지 전환 대응 및 지속가능 경영 체계 구축

## 우선순위 과제
- 정유 사업 경쟁력 강화 (원가 절감, 제품 믹스 개선)
- 신재생에너지 등 미래 성장 사업 투자 확대
- 디지털 전환을 통한 운영 혁신
"""
    
    return {
        'financial_summary_df': financial_summary_df,
        'gap_analysis_df': gap_analysis_df,
        'collected_news_df': collected_news_df,
        'financial_insights': financial_insights,
        'news_insights': news_insights,
        'integrated_insights': integrated_insights
    }


def create_charts_from_data(financial_summary_df, gap_analysis_df):
    """데이터에서 차트 생성"""
    
    # 1-1-1. 분기별 트랜드 차트
    quarterly_trend_chart = None
    try:
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        
        # 샘플 분기별 데이터 (실제로는 session_state에서 가져와야 함)
        if 'quarterly_data' in st.session_state and st.session_state.quarterly_data is not None:
            # 실제 분기별 데이터가 있는 경우
            quarterly_data = st.session_state.quarterly_data
            # 여기서 실제 차트 그리기 로직 구현
        else:
            # 샘플 데이터로 차트 생성
            quarters = ['2023Q4', '2024Q1', '2024Q2', '2024Q3']
            sk_revenue = [14.8, 15.0, 15.2, 15.5]
            competitors_avg = [13.2, 13.5, 13.8, 14.0]
            
            ax1.plot(quarters, sk_revenue, marker='o', linewidth=3, color='#E31E24', label='SK에너지')
            ax1.plot(quarters, competitors_avg, marker='s', linewidth=2, color='#666666', label='경쟁사 평균')
            ax1.set_title('분기별 매출액 추이', fontsize=14, pad=20)
            ax1.set_ylabel('매출액 (조원)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        quarterly_trend_chart = fig1
        
    except Exception as e:
        print(f"분기별 차트 생성 실패: {e}")
        quarterly_trend_chart = None
    
    # 1-2-1. 갭차이 시각화 차트
    gap_visualization_chart = None
    try:
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        
        if gap_analysis_df is not None and not gap_analysis_df.empty:
            # 실제 갭 분석 데이터에서 차트 생성
            companies = ['S-Oil', 'GS칼텍스', 'HD현대오일뱅크']
            
            # 갭 데이터 추출 (실제 컬럼명에 맞게 수정 필요)
            gap_cols = [col for col in gap_analysis_df.columns if '_갭(%)' in col]
            if gap_cols:
                # 첫 번째 지표의 갭 데이터만 사용
                first_row = gap_analysis_df.iloc[0] if len(gap_analysis_df) > 0 else None
                if first_row is not None:
                    gap_values = [first_row[col] for col in gap_cols if pd.notna(first_row[col])]
                    company_names = [col.replace('_갭(%)', '') for col in gap_cols]
                    
                    ax2.bar(company_names, gap_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
                    ax2.set_title('SK에너지 대비 경쟁사 성과 갭', fontsize=14, pad=20)
                    ax2.set_ylabel('갭차이 (%)')
                    ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
                    ax2.grid(True, alpha=0.3)
            else:
                # 샘플 데이터로 대체
                companies = ['S-Oil', 'GS칼텍스', 'HD현대오일뱅크']
                revenue_gaps = [-2.6, -11.2, -26.3]
                
                ax2.bar(companies, revenue_gaps, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
                ax2.set_title('SK에너지 대비 경쟁사 성과 갭', fontsize=14, pad=20)
                ax2.set_ylabel('갭차이 (%)')
                ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
                ax2.grid(True, alpha=0.3)
        
        gap_visualization_chart = fig2
        
    except Exception as e:
        print(f"갭차이 차트 생성 실패: {e}")
        gap_visualization_chart = None
    
    return quarterly_trend_chart, gap_visualization_chart


# --------------------------
# 메인 Streamlit 함수
# --------------------------
def generate_comprehensive_streamlit_report():
    """Streamlit에서 종합 보고서 생성하는 메인 함수"""
    
    try:
        # 1. session_state에서 실제 데이터 가져오기
        data = get_streamlit_data()
        
        # 2. 차트 생성
        quarterly_trend_chart, gap_visualization_chart = create_charts_from_data(
            data['financial_summary_df'], 
            data['gap_analysis_df']
        )
        
        # 3. PDF 보고서 생성
        pdf_bytes = create_structured_pdf_report(
            financial_summary_df=data['financial_summary_df'],
            quarterly_trend_chart=quarterly_trend_chart,
            gap_analysis_df=data['gap_analysis_df'],
            gap_visualization_chart=gap_visualization_chart,
            financial_insights=data['financial_insights'],
            collected_news_df=data['collected_news_df'],
            news_insights=data['news_insights'],
            integrated_insights=data['integrated_insights'],
            gpt_api_key=st.secrets.get("OPENAI_API_KEY") if hasattr(st, 'secrets') else None
        )
        
        # 4. Excel 보고서 생성
        excel_bytes = create_excel_report(
            financial_summary_df=data['financial_summary_df'],
            gap_analysis_df=data['gap_analysis_df'],
            collected_news_df=data['collected_news_df'],
            financial_insights=data['financial_insights'],
            news_insights=data['news_insights'],
            integrated_insights=data['integrated_insights']
        )
        
        return pdf_bytes, excel_bytes
        
    except Exception as e:
        st.error(f"보고서 생성 중 오류가 발생했습니다: {e}")
        raise e


# --------------------------
# Streamlit UI 함수
# --------------------------
def show_report_generation_section():
    """보고서 생성 섹션 UI"""
    
    st.header("📊 종합 보고서 생성")
    
    # 현재 데이터 상태 표시
    col1, col2, col3 = st.columns(3)
    
    with col1:
        financial_status = "✅" if 'processed_financial_data' in st.session_state else "❌"
        st.metric("재무 데이터", financial_status)
    
    with col2:
        news_status = "✅" if 'collected_news' in st.session_state else "❌"
        st.metric("뉴스 데이터", news_status)
    
    with col3:
        insights_status = "✅" if any(key in st.session_state for key in ['financial_insights', 'ai_insights', 'integrated_insights']) else "❌"
        st.metric("AI 인사이트", insights_status)
    
    st.write("---")
    
    # 보고서 구조 안내
    with st.expander("📋 보고서 구조 미리보기"):
        st.markdown("""
        **1. 재무분석 결과**
        - 1-1. 정리된 재무지표 (표시값)
        - 1-1-1. 분기별 트랜드 차트
        - 1-2. SK에너지 대비 경쟁사 갭차이 분석표
        - 1-2-1. 갭차이 시각화 차트
        - 1-3. AI 재무 인사이트
        
        **2. 뉴스분석 결과**
        - 2-1. 수집된 뉴스 하이라이트
        - 2-2. 뉴스 분석 상세
        - 2-3. 뉴스 AI 인사이트
        
        **3. 통합 인사이트**
        - 3-1. 통합 분석 결과
        - 3-2. AI 기반 전략 제안
        """)
    
    # 보고서 생성 버튼
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📄 PDF 보고서 생성", type="primary", use_container_width=True):
            with st.spinner("PDF 보고서 생성 중... 잠시만 기다려주세요."):
                try:
                    pdf_bytes, excel_bytes = generate_comprehensive_streamlit_report()
                    
                    # 성공 메시지
                    st.success("✅ PDF 보고서 생성 완료!")
                    
                    # 다운로드 버튼
                    st.download_button(
                        label="📄 PDF 다운로드",
                        data=pdf_bytes,
                        file_name=f"SK에너지_종합보고서_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"❌ PDF 생성 실패: {e}")
    
    with col2:
        if st.button("📊 Excel 보고서 생성", use_container_width=True):
            with st.spinner("Excel 보고서 생성 중... 잠시만 기다려주세요."):
                try:
                    pdf_bytes, excel_bytes = generate_comprehensive_streamlit_report()
                    
                    # 성공 메시지
                    st.success("✅ Excel 보고서 생성 완료!")
                    
                    # 다운로드 버튼
                    st.download_button(
                        label="📊 Excel 다운로드",
                        data=excel_bytes,
                        file_name=f"SK에너지_데이터_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"❌ Excel 생성 실패: {e}")
    
    # 동시 생성 버튼
    st.write("---")
    if st.button("🚀 PDF + Excel 동시 생성", type="secondary", use_container_width=True):
        with st.spinner("PDF와 Excel 보고서를 동시 생성 중..."):
            try:
                pdf_bytes, excel_bytes = generate_comprehensive_streamlit_report()
                
                st.success("✅ 모든 보고서 생성 완료!")
                
                # 동시 다운로드 버튼들
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        label="📄 PDF 다운로드",
                        data=pdf_bytes,
                        file_name=f"SK에너지_종합보고서_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                with col2:
                    st.download_button(
                        label="📊 Excel 다운로드",
                        data=excel_bytes,
                        file_name=f"SK에너지_데이터_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
            except Exception as e:
                st.error(f"❌ 보고서 생성 실패: {e}")
                st.write("오류 상세:")
                st.code(str(e))


# --------------------------
# 데이터 디버깅 함수
# --------------------------
def show_data_debug_section():
    """디버깅용: 현재 session_state 데이터 확인"""
    
    with st.expander("🔍 데이터 상태 디버깅 (개발용)"):
        st.subheader("Session State 키 목록:")
        
        if st.session_state:
            for key in sorted(st.session_state.keys()):
                value = st.session_state[key]
                if isinstance(value, pd.DataFrame):
                    st.write(f"📊 **{key}**: DataFrame ({len(value)} rows, {len(value.columns)} cols)")
                elif isinstance(value, str):
                    st.write(f"📝 **{key}**: String ({len(value)} chars)")
                elif isinstance(value, (list, tuple)):
                    st.write(f"📋 **{key}**: {type(value).__name__} ({len(value)} items)")
                else:
                    st.write(f"🔢 **{key}**: {type(value).__name__}")
        else:
            st.write("❌ Session state가 비어있습니다.")
        
        st.subheader("샘플 데이터 미리보기:")
        data = get_streamlit_data()
        
        for key, value in data.items():
            if isinstance(value, pd.DataFrame) and not value.empty:
                st.write(f"**{key}**:")
                st.dataframe(value.head(), use_container_width=True)
            elif isinstance(value, str) and value:
                st.write(f"**{key}**:")
                st.text_area("", value[:200] + "..." if len(value) > 200 else value, height=100, key=f"debug_{key}")


# --------------------------
# 메인 실행 부분 (Streamlit 앱에서 사용)
# --------------------------
def main():
    """메인 함수 - Streamlit 앱에서 호출"""
    
    st.set_page_config(
        page_title="SK에너지 종합 보고서", 
        page_icon="📊", 
        layout="wide"
    )
    
    st.title("📊 SK에너지 종합 분석 보고서")
    st.markdown("---")
    
    # 보고서 생성 섹션
    show_report_generation_section()
    
    # 디버깅 섹션 (필요시)
    if st.checkbox("🔧 개발자 모드 (데이터 디버깅)"):
        show_data_debug_section()


# --------------------------
# 단독 실행용
# --------------------------
if __name__ == "__main__":
    # 단독 실행시 샘플 데이터로 테스트
    print("📊 SK에너지 보고서 생성 모듈 - 단독 실행 테스트")
    
    # 샘플 데이터 생성
    data = get_streamlit_data()
    quarterly_trend_chart, gap_visualization_chart = create_charts_from_data(
        data['financial_summary_df'], 
        data['gap_analysis_df']
    )
    
    # PDF 생성 테스트
    try:
        pdf_bytes = create_structured_pdf_report(
            financial_summary_df=data['financial_summary_df'],
            quarterly_trend_chart=quarterly_trend_chart,
            gap_analysis_df=data['gap_analysis_df'],
            gap_visualization_chart=gap_visualization_chart,
            financial_insights=data['financial_insights'],
            collected_news_df=data['collected_news_df'],
            news_insights=data['news_insights'],
            integrated_insights=data['integrated_insights']
        )
        
        # 파일 저장
        with open("sk_energy_comprehensive_report.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("✅ PDF 저장 완료: sk_energy_comprehensive_report.pdf")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


# --------------------------
# Streamlit 앱에서 이 모듈을 사용하는 방법
# --------------------------
"""
기존 Streamlit 앱의 메인 파일에서:

1. 이 모듈을 import:
   from report_module import show_report_generation_section

2. 보고서 탭이나 페이지에서 호출:
   show_report_generation_section()

3. 또는 버튼만 필요하다면:
   if st.button("보고서 생성"):
       pdf_bytes, excel_bytes = generate_comprehensive_streamlit_report()
       st.download_button("PDF 다운로드", pdf_bytes, "report.pdf")
"""
