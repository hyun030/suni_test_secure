import io
import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, PageBreak, Image as RLImage, SimpleDocTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt

# 폰트 등록 함수 (예시 - 실제 경로에 맞게 조정 필요)
def register_fonts_safe():
    registered_fonts = {}
    try:
        # 예시: NanumGothic 폰트 등록 (필요시 변경)
        pdfmetrics.registerFont(TTFont('Korean', 'NanumGothic.ttf'))
        pdfmetrics.registerFont(TTFont('KoreanBold', 'NanumGothicBold.ttf'))
        pdfmetrics.registerFont(TTFont('KoreanSerif', 'NanumMyeongjo.ttf'))
        registered_fonts['Korean'] = 'Korean'
        registered_fonts['KoreanBold'] = 'KoreanBold'
        registered_fonts['KoreanSerif'] = 'KoreanSerif'
    except Exception as e:
        print(f"⚠️ 폰트 등록 실패: {e}")
        # 기본 폰트 fallback
        registered_fonts['Korean'] = 'Helvetica'
        registered_fonts['KoreanBold'] = 'Helvetica-Bold'
        registered_fonts['KoreanSerif'] = 'Times-Roman'
    return registered_fonts

def safe_str_convert(value):
    try:
        if pd.isna(value):
            return ""
        return str(value)
    except:
        return ""

def ascii_to_table(lines, registered_fonts, header_color='#E31E24', row_colors=None):
    """ASCII 표를 reportlab 테이블로 변환"""
    try:
        if not lines or len(lines) < 3:
            return None
        
        header = [c.strip() for c in lines[0].split('|') if c.strip()]
        if not header:
            return None
            
        data = []
        for ln in lines[2:]:
            cols = [c.strip() for c in ln.split('|') if c.strip()]
            if len(cols) == len(header):
                data.append(cols)
        
        if not data:
            return None
        
        if row_colors is None:
            row_colors = [colors.whitesmoke, colors.HexColor('#F7F7F7')]
        
        tbl = Table([header] + data)
        tbl.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor(header_color)),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), registered_fonts.get('KoreanBold', 'Helvetica-Bold')),
            ('FONTNAME', (0,1), (-1,-1), registered_fonts.get('Korean', 'Helvetica')),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), row_colors),
        ]))
        return tbl
    except Exception as e:
        print(f"❌ ASCII 테이블 변환 오류: {e}")
        return None

def split_dataframe_for_pdf(df, max_rows_per_page=20, max_cols_per_page=8):
    """DataFrame을 PDF에 맞게 페이지별로 분할"""
    try:
        if df is None or df.empty:
            return []
            
        chunks = []
        total_rows = len(df)
        total_cols = len(df.columns)
        
        for row_start in range(0, total_rows, max_rows_per_page):
            row_end = min(row_start + max_rows_per_page, total_rows)
            row_chunk = df.iloc[row_start:row_end]
            
            for col_start in range(0, total_cols, max_cols_per_page):
                col_end = min(col_start + max_cols_per_page, total_cols)
                col_names = df.columns[col_start:col_end]
                chunk = row_chunk[col_names]
                
                chunk_info = {
                    'data': chunk,
                    'row_range': (row_start, row_end-1),
                    'col_range': (col_start, col_end-1),
                    'is_last_row_chunk': row_end == total_rows,
                    'is_last_col_chunk': col_end == total_cols
                }
                chunks.append(chunk_info)
        
        return chunks
    except Exception as e:
        print(f"❌ DataFrame 분할 오류: {e}")
        return []

def add_chunked_table(story, df, title, registered_fonts, BODY_STYLE, header_color='#F2F2F2'):
    """분할된 테이블을 story에 추가"""
    try:
        if df is None or df.empty:
            story.append(Paragraph(f"{title}: 데이터가 없습니다.", BODY_STYLE))
            return
        
        print(f"🔄 테이블 추가 중: {title}")
        story.append(Paragraph(title, BODY_STYLE))
        story.append(Spacer(1, 8))
        
        chunks = split_dataframe_for_pdf(df)
        
        for i, chunk_info in enumerate(chunks):
            chunk = chunk_info['data']
            
            if len(chunks) > 1:
                row_info = f"행 {chunk_info['row_range'][0]+1}~{chunk_info['row_range'][1]+1}"
                col_info = f"열 {chunk_info['col_range'][0]+1}~{chunk_info['col_range'][1]+1}"
                story.append(Paragraph(f"[{row_info}, {col_info}]", BODY_STYLE))
            
            table_data = [chunk.columns.tolist()]
            for _, row in chunk.iterrows():
                table_data.append([safe_str_convert(val) for val in row.values])
            
            tbl = Table(table_data, repeatRows=1)
            tbl.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor(header_color)),
                ('FONTNAME', (0,0), (-1,0), registered_fonts.get('KoreanBold', 'Helvetica-Bold')),
                ('FONTNAME', (0,1), (-1,-1), registered_fonts.get('Korean', 'Helvetica')),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F8F8')]),
            ]))
            
            story.append(tbl)
            story.append(Spacer(1, 12))
            
            if i < len(chunks) - 1 and (i + 1) % 2 == 0:
                story.append(PageBreak())
        
        print(f"✅ 테이블 추가 완료: {title}")
    except Exception as e:
        print(f"❌ 테이블 추가 오류 ({title}): {e}")
        story.append(Paragraph(f"{title}: 테이블 생성 중 오류가 발생했습니다.", BODY_STYLE))

def add_financial_data_section(story, financial_data, quarterly_df, chart_figures, registered_fonts, HEADING_STYLE, BODY_STYLE):
    """재무분석 결과 섹션 추가 (표 + 차트 이미지)"""
    try:
        print("🔄 재무분석 섹션 추가 중...")
        story.append(Paragraph("1. 재무분석 결과", HEADING_STYLE))
        
        # 1-1. 분기별 재무지표 상세 데이터
        if quarterly_df is not None and not quarterly_df.empty:
            add_chunked_table(story, quarterly_df, "1-1. 분기별 재무지표 상세 데이터", 
                             registered_fonts, BODY_STYLE, '#E6F3FF')
        else:
            story.append(Paragraph("1-1. 분기별 재무지표 상세 데이터: 데이터가 없습니다.", BODY_STYLE))
        
        story.append(Spacer(1, 12))
        
        # 1-2. SK에너지 대비 경쟁사 갭차이 분석표
        if financial_data is not None and not financial_data.empty:
            display_cols = [c for c in financial_data.columns if not str(c).endswith('_원시값')]
            df_display = financial_data[display_cols].copy()
            add_chunked_table(story, df_display, "1-2. SK에너지 대비 경쟁사 갭차이 분석", 
                             registered_fonts, BODY_STYLE, '#F2F2F2')
        else:
            story.append(Paragraph("1-2. SK에너지 대비 경쟁사 갭차이 분석: 데이터가 없습니다.", BODY_STYLE))
        
        # 1-3. matplotlib 차트 이미지들 추가
        if chart_figures and len(chart_figures) > 0:
            story.append(Spacer(1, 12))
            story.append(Paragraph("1-3. 시각화 차트", BODY_STYLE))
            story.append(Spacer(1, 8))
            
            for i, fig in enumerate(chart_figures, 1):
                try:
                    img_buffer = io.BytesIO()
                    fig.savefig(img_buffer, format='png', bbox_inches='tight')
                    plt.close(fig)
                    img_buffer.seek(0)
                    
                    story.append(Paragraph(f"차트 {i}", BODY_STYLE))
                    img = RLImage(img_buffer, width=500, height=300)
                    story.append(img)
                    story.append(Spacer(1, 16))
                    print(f"✅ 차트 {i} 추가 완료")
                except Exception as e:
                    print(f"⚠️ 차트 {i} 추가 실패: {e}")
                    story.append(Paragraph(f"차트 {i}: 이미지 생성 실패", BODY_STYLE))
        else:
            print("⚠️ 차트 데이터가 없습니다.")
        
        story.append(Spacer(1, 18))
        print("✅ 재무분석 섹션 추가 완료")
    except Exception as e:
        print(f"❌ 재무분석 섹션 추가 오류: {e}")

def clean_ai_text(text):
    """AI 텍스트 전처리: 간단히 줄 단위로 타입 분리 (예시)"""
    # 예: 제목(line.startswith('# ')), 기타
    blocks = []
    if not text:
        return blocks
    lines = text.split('\n')
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
        if line_strip.startswith('#'):
            blocks.append(('title', line_strip.lstrip('#').strip()))
        else:
            blocks.append(('text', line_strip))
    return blocks

def add_ai_insights_section(story, insights, registered_fonts, BODY_STYLE, header_color='#E31E24'):
    """AI 인사이트 섹션 추가"""
    try:
        print("🔄 AI 인사이트 섹션 추가 중...")
        
        if not insights:
            story.append(Paragraph("AI 인사이트가 제공되지 않았습니다.", BODY_STYLE))
            story.append(Spacer(1, 18))
            return
        
        story.append(Spacer(1, 8))
        blocks = clean_ai_text(insights)
        ascii_buffer = []
        
        for typ, line in blocks:
            if '|' in line:
                ascii_buffer.append(line)
                continue
            
            if ascii_buffer:
                tbl = ascii_to_table(ascii_buffer, registered_fonts, header_color)
                if tbl:
                    story.append(tbl)
                story.append(Spacer(1, 12))
                ascii_buffer.clear()
            
            if typ == 'title':
                story.append(Paragraph(f"<b>{line}</b>", BODY_STYLE))
            else:
                story.append(Paragraph(line, BODY_STYLE))
        
        if ascii_buffer:
            tbl = ascii_to_table(ascii_buffer, registered_fonts, header_color)
            if tbl:
                story.append(tbl)
        
        story.append(Spacer(1, 18))
        print("✅ AI 인사이트 섹션 추가 완료")
    except Exception as e:
        print(f"❌ AI 인사이트 섹션 추가 오류: {e}")

def generate_strategic_recommendations(insights, financial_data, gpt_api_key):
    """GPT API 호출로 전략 제안 생성 (여기에 실제 GPT 호출 코드 연결 필요)"""
    # 현재는 예시로 간단 반환
    if not insights:
        return None
    # 실제 GPT 호출 코드 삽입 필요
    return "GPT 기반 전략 제안 예시 텍스트입니다."

def add_strategic_recommendations_section(story, recommendations, registered_fonts, HEADING_STYLE, BODY_STYLE):
    """전략 제안 섹션 추가"""
    try:
        print("🔄 전략 제안 섹션 추가 중...")
        
        if not recommendations or "생성할 수 없습니다" in recommendations:
            story.append(Paragraph("GPT 기반 전략 제안을 생성할 수 없습니다.", BODY_STYLE))
            story.append(Spacer(1, 18))
            return
        
        story.append(Spacer(1, 8))
        
        blocks = clean_ai_text(recommendations)
        
        for typ, line in blocks:
            if typ == 'title':
                story.append(Paragraph(f"<b>{line}</b>", BODY_STYLE))
            else:
                story.append(Paragraph(line, BODY_STYLE))
        
        story.append(Spacer(1, 18))
        print("✅ 전략 제안 섹션 추가 완료")
    except Exception as e:
        print(f"❌ 전략 제안 섹션 추가 오류: {e}")

def add_news_section(story, news_data, insights, registered_fonts, HEADING_STYLE, BODY_STYLE):
    """뉴스 하이라이트 및 종합 분석 섹션 내용 추가 (헤딩 제외)"""
    try:
        print("🔄 뉴스 섹션 내용 추가 중...")
        
        if news_data is not None and not news_data.empty:
            story.append(Paragraph("4-1. 최신 뉴스 하이라이트", BODY_STYLE))
            for i, title in enumerate(news_data["제목"].head(10), 1):
                story.append(Paragraph(f"{i}. {safe_str_convert(title)}", BODY_STYLE))
            story.append(Spacer(1, 16))
            print(f"✅ 뉴스 하이라이트 {len(news_data)}건 추가")
        else:
            story.append(Paragraph("뉴스 데이터가 제공되지 않았습니다.", BODY_STYLE))
            print("⚠️ 뉴스 데이터 없음")
            
        story.append(Spacer(1, 18))
        print("✅ 뉴스 섹션 내용 추가 완료")
    except Exception as e:
        print(f"❌ 뉴스 섹션 내용 추가 오류: {e}")

def create_excel_report(financial_data=None, news_data=None, insights=None):
    """Excel 보고서 생성"""
    try:
        print("🔄 Excel 보고서 생성 시작...")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if financial_data is not None and not financial_data.empty:
                financial_data.to_excel(writer, sheet_name='재무분석', index=False)
            else:
                pd.DataFrame({'메모': ['재무 데이터가 없습니다.']}).to_excel(writer, sheet_name='재무분석', index=False)
            
            if news_data is not None and not news_data.empty:
                news_data.to_excel(writer, sheet_name='뉴스분석', index=False)
            else:
                pd.DataFrame({'메모': ['뉴스 데이터가 없습니다.']}).to_excel(writer, sheet_name='뉴스분석', index=False)
            
            if insights:
                insight_lines = str(insights).split('\n')
                insight_df = pd.DataFrame({'AI 인사이트': insight_lines})
                insight_df.to_excel(writer, sheet_name='AI인사이트', index=False)
            else:
                pd.DataFrame({'메모': ['AI 인사이트가 없습니다.']}).to_excel(writer, sheet_name='AI인사이트', index=False)
        
        output.seek(0)
        print("✅ Excel 보고서 생성 완료!")
        return output.getvalue()
        
    except Exception as e:
        print(f"❌ Excel 보고서 생성 오류: {e}")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            error_df = pd.DataFrame({
                '오류': [f"Excel 생성 중 오류 발생: {str(e)}"],
                '해결방법': ['시스템 관리자에게 문의해주세요.']
            })
            error_df.to_excel(writer, sheet_name='오류정보', index=False)
        output.seek(0)
        return output.getvalue()

def create_enhanced_pdf_report(
    financial_data=None,
    news_data=None,
    insights=None,
    chart_figures=None,  # matplotlib figure 리스트
    quarterly_df=None,
    show_footer=False,
    report_target="SK이노베이션 경영진",
    report_author="보고자 미기재",
    gpt_api_key=None,
    font_paths=None,
):
    """향상된 PDF 보고서 생성 (kaleido 없이 matplotlib PNG 방식)"""
    try:
        print("🔄 PDF 보고서 생성 시작...")
        
        registered_fonts = register_fonts_safe()
        
        TITLE_STYLE = ParagraphStyle(
            'Title',
            fontName=registered_fonts.get('KoreanBold', 'Helvetica-Bold'),
            fontSize=20,
            leading=30,
            spaceAfter=15,
            alignment=1,
        )
        HEADING_STYLE = ParagraphStyle(
            'Heading',
            fontName=registered_fonts.get('KoreanBold', 'Helvetica-Bold'),
            fontSize=14,
            leading=23,
            textColor=colors.HexColor('#E31E24'),
            spaceBefore=16,
            spaceAfter=10,
        )
        BODY_STYLE = ParagraphStyle(
            'Body',
            fontName=registered_fonts.get('KoreanSerif', 'Times-Roman'),
            fontSize=12,
            leading=18,
            spaceAfter=6,
        )
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        story = []
        
        # 표지
        story.append(Paragraph("손익개선을 위한 SK에너지 및 경쟁사 비교 분석 보고서", TITLE_STYLE))
        story.append(Spacer(1, 20))
        
        report_info = f"""
        <b>보고일자:</b> {datetime.now().strftime('%Y년 %m월 %d일')}<br/>
        <b>보고대
