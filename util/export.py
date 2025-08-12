# -*- coding: utf-8 -*-
"""
구조화된 SK에너지 보고서 생성 모듈 (matplotlib 기반)
명확한 섹션 구조: 1.재무분석 → 2.뉴스분석 → 3.통합인사이트
"""

import io
import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    Paragraph, Table, TableStyle, Spacer, PageBreak, Image as RLImage, SimpleDocTemplate
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUI 없는 환경에서 안전하게 사용

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


def extract_chart_data(fig):
    """matplotlib 차트에서 데이터 추출해서 DataFrame으로 변환"""
    try:
        if fig is None:
            return None
            
        axes = fig.get_axes()
        if not axes:
            return None
            
        ax = axes[0]  # 첫 번째 축 사용
        
        # 막대 차트인 경우
        bars = ax.patches
        if bars:
            labels = []
            values = []
            for i, bar in enumerate(bars):
                height = bar.get_height()
                if height != 0:  # 0이 아닌 막대만
                    # x축 레이블 가져오기
                    if hasattr(ax, 'get_xticklabels') and ax.get_xticklabels():
                        if i < len(ax.get_xticklabels()):
                            labels.append(ax.get_xticklabels()[i].get_text())
                        else:
                            labels.append(f"항목{i+1}")
                    else:
                        labels.append(f"항목{i+1}")
                    values.append(height)
            
            if labels and values:
                return pd.DataFrame({'구분': labels, '수치': values})
        
        # 선 그래프인 경우  
        lines = ax.get_lines()
        if lines:
            line = lines[0]  # 첫 번째 라인
            xdata = line.get_xdata()
            ydata = line.get_ydata()
            
            if len(xdata) == len(ydata) and len(xdata) > 0:
                # x축 레이블이 있으면 사용, 없으면 인덱스 사용
                if hasattr(ax, 'get_xticklabels') and ax.get_xticklabels():
                    xlabels = [label.get_text() for label in ax.get_xticklabels()]
                    if len(xlabels) >= len(xdata):
                        xlabels = xlabels[:len(xdata)]
                    else:
                        xlabels = [f"점{i+1}" for i in range(len(xdata))]
                else:
                    xlabels = [f"점{i+1}" for i in range(len(xdata))]
                
                return pd.DataFrame({'구분': xlabels, '수치': ydata})
        
        return None
        
    except Exception as e:
        print(f"차트 데이터 추출 실패: {e}")
        return None


def add_chart_to_story(story, fig, title, body_style):
    """matplotlib 차트를 story에 추가 - 실패시 데이터 테이블로 대체"""
    try:
        story.append(Paragraph(title, body_style))
        story.append(Spacer(1, 6))
        
        if fig is None:
            story.append(Paragraph("⚠️ 차트 데이터가 없습니다.", body_style))
            story.append(Spacer(1, 12))
            return
        
        # 방법 1: matplotlib 이미지로 시도
        try:
            import tempfile
            import os
            
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                fig.savefig(tmp.name, format='png', bbox_inches='tight', dpi=150)
                tmp_path = tmp.name
            
            plt.close(fig)
            
            # 파일이 제대로 생성되었는지 확인
            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                img = RLImage(tmp_path, width=480, height=320)
                story.append(img)
                story.append(Spacer(1, 12))
                
                # 임시 파일 삭제
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                
                print(f"✅ 차트 성공: {title}")
                return
            else:
                raise Exception("이미지 파일이 비어있음")
                
        except Exception as e:
            print(f"⚠️ matplotlib 실패: {e}")
            
            # 방법 2: BytesIO로 시도
            try:
                img_buffer = io.BytesIO()
                fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
                plt.close(fig)
                img_buffer.seek(0)
                
                if img_buffer.getvalue():
                    img = RLImage(img_buffer, width=480, height=320)
                    story.append(img)
                    story.append(Spacer(1, 12))
                    print(f"✅ 차트 성공 (BytesIO): {title}")
                    return
                else:
                    raise Exception("BytesIO가 비어있음")
                    
            except Exception as e2:
                print(f"⚠️ BytesIO도 실패: {e2}")
                
                # 방법 3: 차트 데이터를 ASCII 테이블로 변환
                try:
                    chart_data = extract_chart_data(fig)
                    plt.close(fig)  # 차트 닫기
                    
                    if chart_data is not None and not chart_data.empty:
                        story.append(Paragraph("📊 차트 데이터 (이미지 생성 실패로 표로 대체):", body_style))
                        story.append(Spacer(1, 4))
                        
                        tbl = create_simple_table(chart_data, register_fonts_safe(), '#F0F0F0')
                        if tbl:
                            story.append(tbl)
                            story.append(Spacer(1, 12))
                            print(f"✅ 차트 데이터 테이블로 대체: {title}")
                            return
                    
                    # 최후 수단: 단순 텍스트
                    story.append(Paragraph("❌ 차트 생성 및 데이터 추출 모두 실패", body_style))
                    story.append(Paragraph("• 차트가 정상적으로 표시되지 않을 수 있습니다.", body_style))
                    story.append(Spacer(1, 12))
                    print(f"❌ 차트 완전 실패: {title}")
                    
                except Exception as e3:
                    print(f"❌ 데이터 테이블 변환도 실패: {e3}")
                    story.append(Paragraph("❌ 차트 및 데이터 표시 불가", body_style))
                    story.append(Spacer(1, 12))
                    
    except Exception as e:
        print(f"❌ 차트 추가 함수 전체 실패: {e}")
        story.append(Paragraph(f"❌ {title}: 오류 발생", body_style))
        story.append(Spacer(1, 12))


# --------------------------
# 1. 재무분석 결과 섹션
# --------------------------
def add_section_1_financial_analysis(
    story, 
    financial_summary_df,      # 1-1. 정리된 재무지표 (표시값)
    quarterly_trend_chart,     # 1-1-1. 분기별 트랜드 차트
    gap_analysis_df,          # 1-2. 갭차이 분석표  
    gap_visualization_chart,   # 1-2-1. 갭차이 시각화 차트
    financial_insights,        # 1-3. AI 재무 인사이트
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
            # 인사이트를 문단별로 나누어 추가
            for line in str(financial_insights).split('\n'):
                line = line.strip()
                if line:
                    if line.startswith('#') or line.startswith('*'):
                        # 제목이나 강조 텍스트
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
    collected_news_df,     # 수집된 뉴스 데이터
    news_insights,         # 뉴스 AI 인사이트
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
            # 뉴스 제목들을 리스트로 표시 (최대 10개)
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
            
            # 처음 5개 뉴스만 테이블로 표시
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
    integrated_insights,    # 통합 인사이트 탭에서 나온 결과들
    strategic_recommendations,  # GPT 기반 전략 제안 (옵션)
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
# GPT 전략 제안 생성 (옵션)
# --------------------------
def generate_strategic_recommendations(financial_insights, news_insights, integrated_insights, gpt_api_key=None):
    """GPT를 사용해 종합적인 전략 제안 생성"""
    try:
        if not GPT_AVAILABLE or not gpt_api_key:
            return None
            
        openai.api_key = gpt_api_key
        
        # 모든 인사이트를 종합한 프롬프트
        combined_insights = f"""
재무 인사이트:
{financial_insights or '없음'}

뉴스 인사이트:  
{news_insights or '없음'}

통합 인사이트:
{integrated_insights or '없음'}
"""
        
        prompt = f"""
당신은 SK에너지의 경영 컨설턴트입니다. 다음 분석 결과를 바탕으로 실행 가능한 전략을 제안하세요:

{combined_insights}

다음 형식으로 답변해주세요:
1. 핵심 이슈 요약
2. 단기 실행 방안 (3-6개월)
3. 중장기 전략 방향 (1-3년)
4. 주의사항 및 리스크
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 에너지 업계 전문 경영 컨설턴트입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"전략 제안 생성 중 오류: {e}"


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
# 메인 PDF 보고서 생성 함수
# --------------------------
def create_structured_pdf_report(
    # 1. 재무분석 관련
    financial_summary_df=None,      # 1-1. 정리된 재무지표 (표시값)
    quarterly_trend_chart=None,     # 1-1-1. 분기별 트랜드 차트
    gap_analysis_df=None,          # 1-2. 갭차이 분석표  
    gap_visualization_chart=None,   # 1-2-1. 갭차이 시각화 차트
    financial_insights=None,        # 1-3. AI 재무 인사이트
    
    # 2. 뉴스분석 관련
    collected_news_df=None,        # 수집된 뉴스 데이터
    news_insights=None,            # 뉴스 AI 인사이트
    
    # 3. 통합 인사이트 관련
    integrated_insights=None,      # 통합 인사이트 탭 결과
    
    # 기타 옵션
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
            alignment=1,  # 중앙 정렬
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
            strategic_recommendations = generate_strategic_recommendations(
                financial_insights, news_insights, integrated_insights, gpt_api_key
            )
        
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
# 통합 사용 함수
# --------------------------
def generate_comprehensive_report(
    # 재무 데이터
    financial_summary_df=None,
    quarterly_trend_chart=None, 
    gap_analysis_df=None,
    gap_visualization_chart=None,
    financial_insights=None,
    
    # 뉴스 데이터  
    collected_news_df=None,
    news_insights=None,
    
    # 통합 분석
    integrated_insights=None,
    
    # 옵션
    gpt_api_key=None,
    **kwargs
):
    """
    구조화된 종합 보고서 생성 (PDF + Excel)
    
    반환: (pdf_bytes, excel_bytes)
    
    사용 예시:
    pdf_bytes, excel_bytes = generate_comprehensive_report(
        financial_summary_df=재무요약_df,
        quarterly_trend_chart=분기트랜드_차트,
        gap_analysis_df=갭분석_df, 
        gap_visualization_chart=갭시각화_차트,
        financial_insights="재무 AI 인사이트 텍스트",
        collected_news_df=뉴스수집_df,
        news_insights="뉴스 AI 인사이트 텍스트", 
        integrated_insights="통합 인사이트 텍스트",
        gpt_api_key="your-openai-key"
    )
    """
    try:
        # PDF 생성
        pdf_bytes = create_structured_pdf_report(
            financial_summary_df=financial_summary_df,
            quarterly_trend_chart=quarterly_trend_chart,
            gap_analysis_df=gap_analysis_df, 
            gap_visualization_chart=gap_visualization_chart,
            financial_insights=financial_insights,
            collected_news_df=collected_news_df,
            news_insights=news_insights,
            integrated_insights=integrated_insights,
            gpt_api_key=gpt_api_key,
            **kwargs
        )
        
        # Excel 생성
        excel_bytes = create_excel_report(
            financial_summary_df=financial_summary_df,
            gap_analysis_df=gap_analysis_df,
            collected_news_df=collected_news_df,
            financial_insights=financial_insights,
            news_insights=news_insights,
            integrated_insights=integrated_insights
        )
        
        return pdf_bytes, excel_bytes
        
    except Exception as e:
        raise e


# --------------------------
# 의존성 체크
# --------------------------
def check_dependencies():
    """필요한 패키지들이 설치되어 있는지 체크"""
    missing = []
    packages = ['matplotlib', 'reportlab', 'pandas', 'openpyxl']
    
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print("❌ 다음 패키지를 설치해주세요:")
        for m in missing:
            print(f"   pip install {m}")
        return False
    else:
        print("✅ 모든 필수 패키지가 설치되어 있습니다!")
        return True


# --------------------------
# 테스트용 샘플 데이터 생성
# --------------------------
def create_sample_data():
    """테스트용 샘플 데이터 생성"""
    
    # 1-1. 재무지표 요약
    financial_summary = pd.DataFrame({
        '구분': ['매출액(조원)', '영업이익(천억원)', '영업이익률(%)', 'ROE(%)'],
        'SK에너지': [15.2, 8.5, 5.6, 12.3],
        'S-Oil': [14.8, 7.9, 5.3, 11.8], 
        'GS칼텍스': [13.5, 6.2, 4.6, 10.5],
        'HD현대오일뱅크': [11.2, 4.8, 4.3, 9.2]
    })
    
    # 1-1-1. 분기별 트랜드 차트
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    quarters = ['2023Q4', '2024Q1', '2024Q2', '2024Q3']
    sk_revenue = [14.8, 15.0, 15.2, 15.5]
    competitors_avg = [13.2, 13.5, 13.8, 14.0]
    
    ax1.plot(quarters, sk_revenue, marker='o', linewidth=3, color='#E31E24', label='SK에너지')
    ax1.plot(quarters, competitors_avg, marker='s', linewidth=2, color='#666666', label='경쟁사 평균')
    ax1.set_title('분기별 매출액 추이', fontsize=14, pad=20)
    ax1.set_ylabel('매출액 (조원)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 1-2. 갭차이 분석표
    gap_analysis = pd.DataFrame({
        '지표': ['매출액', '영업이익률', 'ROE'],
        'SK에너지': [15.2, 5.6, 12.3],
        'S-Oil_갭(%)': [-2.6, -5.4, -4.1],
        'GS칼텍스_갭(%)': [-11.2, -17.9, -14.6],
        'HD현대오일뱅크_갭(%)': [-26.3, -23.2, -25.2]
    })
    
    # 1-2-1. 갭차이 시각화 차트  
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    companies = ['S-Oil', 'GS칼텍스', 'HD현대오일뱅크']
    revenue_gaps = [-2.6, -11.2, -26.3]
    profit_gaps = [-5.4, -17.9, -23.2]
    
    x = range(len(companies))
    width = 0.35
    
    ax2.bar([i - width/2 for i in x], revenue_gaps, width, label='매출액 갭(%)', color='#FF6B6B')
    ax2.bar([i + width/2 for i in x], profit_gaps, width, label='영업이익률 갭(%)', color='#4ECDC4')
    ax2.set_title('SK에너지 대비 경쟁사 성과 갭', fontsize=14, pad=20)
    ax2.set_ylabel('갭차이 (%)')
    ax2.set_xticks(x)
    ax2.set_xticklabels(companies)
    ax2.legend()
    ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    ax2.grid(True, alpha=0.3)
    
    # 뉴스 데이터 샘플
    news_data = pd.DataFrame({
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
    
    # 인사이트 텍스트들
    financial_insights = """
# 재무 성과 핵심 분석
* SK에너지는 매출액 15.2조원으로 업계 1위 유지
* 영업이익률 5.6%로 경쟁사 대비 우위 확보  
* ROE 12.3%로 양호한 자본 효율성 시현
* 다만, HD현대오일뱅크 대비 격차 확대 추세 주목 필요

## 개선 필요 영역
- 변동비 관리 최적화를 통한 마진 개선
- 고부가가치 제품 믹스 확대 검토
"""
    
    news_insights = """
# 뉴스 분석 종합
* 3분기 실적 호조로 시장 신뢰도 상승
* 원유가 안정화로 정유 마진 개선 환경 조성
* 에너지 전환 정책 대응 필요성 증대
* 아시아 지역 정유 수요 견조한 흐름 지속

## 주요 이슈
- 배터리 사업 분할을 통한 포트폴리오 최적화
- ESG 경영 강화 및 탄소중립 로드맵 구체화
"""
    
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
        'financial_summary_df': financial_summary,
        'quarterly_trend_chart': fig1,
        'gap_analysis_df': gap_analysis, 
        'gap_visualization_chart': fig2,
        'financial_insights': financial_insights,
        'collected_news_df': news_data,
        'news_insights': news_insights,
        'integrated_insights': integrated_insights
    }


# --------------------------
# 실행 예시
# --------------------------
if __name__ == "__main__":
    print("📊 구조화된 SK에너지 보고서 생성 모듈")
    print("=" * 50)
    
    # 의존성 체크
    if not check_dependencies():
        exit(1)
    
    # 샘플 데이터 생성
    print("🔄 샘플 데이터 생성 중...")
    sample_data = create_sample_data()
    
    # 보고서 생성
    print("📝 보고서 생성 중...")
    try:
        pdf_bytes, excel_bytes = generate_comprehensive_report(**sample_data)
        
        # 파일 저장
        with open("sk_energy_comprehensive_report.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("✅ PDF 저장: sk_energy_comprehensive_report.pdf")
        
        with open("sk_energy_comprehensive_report.xlsx", "wb") as f:
            f.write(excel_bytes)
        print("✅ Excel 저장: sk_energy_comprehensive_report.xlsx")
        
        print("\n🎉 보고서 생성 완료!")
        print("\n📋 구조:")
        print("1. 재무분석 결과")
        print("   1-1. 정리된 재무지표 (표시값)")
        print("   1-1-1. 분기별 트랜드 차트")
        print("   1-2. 갭차이 분석표")
        print("   1-2-1. 갭차이 시각화 차트") 
        print("   1-3. AI 재무 인사이트")
        print("2. 뉴스분석 결과")
        print("   2-1. 수집된 뉴스 하이라이트")
        print("   2-2. 뉴스 분석 상세")
        print("   2-3. 뉴스 AI 인사이트")
        print("3. 통합 인사이트")
        print("   3-1. 통합 분석 결과")
        print("   3-2. AI 기반 전략 제안")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


# --------------------------
# Streamlit 사용 예시 함수
# --------------------------
def streamlit_usage_example():
    """
    Streamlit에서 이 모듈을 사용하는 예시
    
    # Streamlit 앱에서 사용법:
    
    import streamlit as st
    import matplotlib.pyplot as plt
    from your_module import generate_comprehensive_report
    
    # 데이터 준비 (실제 앱에서는 사용자 데이터 사용)
    financial_df = load_financial_data()
    news_df = load_news_data()
    
    # 차트 생성
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    # ... 차트 그리기 코드 ...
    
    fig2, ax2 = plt.subplots(figsize=(10, 6)) 
    # ... 차트 그리기 코드 ...
    
    # 인사이트 텍스트 (AI 분석 결과)
    financial_insights = get_financial_ai_insights()
    news_insights = get_news_ai_insights()
    integrated_insights = get_integrated_insights()
    
    # 보고서 생성 버튼
    if st.button("📊 종합 보고서 생성"):
        with st.spinner("보고서 생성 중..."):
            pdf_bytes, excel_bytes = generate_comprehensive_report(
                financial_summary_df=financial_df,
                quarterly_trend_chart=fig1,
                gap_analysis_df=gap_df,
                gap_visualization_chart=fig2,
                financial_insights=financial_insights,
                collected_news_df=news_df,
                news_insights=news_insights,
                integrated_insights=integrated_insights,
                gpt_api_key=st.secrets.get("OPENAI_API_KEY")
            )
        
        # 다운로드 버튼들
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📄 PDF 다운로드",
                data=pdf_bytes,
                file_name=f"SK에너지_종합보고서_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        
        with col2:
            st.download_button(
                label="📊 Excel 다운로드", 
                data=excel_bytes,
                file_name=f"SK에너지_데이터_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.success("✅ 보고서 생성 완료!")
    """
    pass
