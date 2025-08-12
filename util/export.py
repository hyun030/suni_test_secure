# -*- coding: utf-8 -*-
"""
완전 통합 보고서 생성 모듈
- matplotlib 차트 → PNG 버퍼 → reportlab 삽입 방식
- 순서 고정:
  1. 재무분석 결과
    1-1 정리된 재무지표 (표)
    1-1-1 분기별 트렌드 차트
    1-2 SK대비 경쟁사 갭차이 분석표
    1-2-1 갭차이 시각화 차트
    1-3 AI 재무 인사이트
  2. 뉴스 분석
  3. 통합 인사이트
필요: pip install reportlab pandas openpyxl matplotlib
"""

import io
import os
import math
import traceback
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    Paragraph, Table, TableStyle, Spacer, PageBreak, Image as RLImage, SimpleDocTemplate
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Optional OpenAI
try:
    import openai
    GPT_AVAILABLE = True
except Exception:
    GPT_AVAILABLE = False

# -------------------------
# 폰트 설정 (환경에 맞춰 경로 변경)
# -------------------------
def get_font_paths():
    return {
        "Korean": "fonts/NanumGothic.ttf",
        "KoreanBold": "fonts/NanumGothicBold.ttf",
        "KoreanSerif": "fonts/NanumMyeongjo.ttf"
    }

def register_fonts_safe():
    font_paths = get_font_paths()
    registered = {}
    defaults = {"Korean": "Helvetica", "KoreanBold": "Helvetica-Bold", "KoreanSerif": "Times-Roman"}
    for key, path in font_paths.items():
        try:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                if key not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(key, path))
                registered[key] = key
            else:
                registered[key] = defaults[key]
        except Exception:
            registered[key] = defaults[key]
    # ensure keys
    for k in defaults:
        if k not in registered:
            registered[k] = defaults[k]
    return registered

# -------------------------
# 안전 유틸
# -------------------------
def safe_str_convert(v):
    try:
        if pd.isna(v):
            return ""
        return str(v)
    except Exception:
        return ""

def ensure_numeric(x, default=0.0):
    try:
        if x is None:
            return default
        if isinstance(x, (int, float)):
            if math.isnan(x):
                return default
            return float(x)
        s = str(x).replace(',', '')
        return float(s)
    except Exception:
        return default

# -------------------------
# AI 텍스트 전처리 (간단)
# -------------------------
def clean_ai_text(raw):
    if not raw or pd.isna(raw):
        return []
    s = str(raw).strip()
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    blocks = []
    for ln in lines:
        if ln.startswith('#') or ln.lower().startswith('##') or ln[:2].isdigit():
            blocks.append(('title', ln.lstrip('#').strip()))
        else:
            blocks.append(('body', ln))
    return blocks

# -------------------------
# ASCII -> reportlab Table
# -------------------------
def ascii_to_table(lines, registered_fonts, header_color='#E31E24', row_colors=None):
    try:
        if not lines:
            return None
        header = [c.strip() for c in lines[0].split('|') if c.strip()]
        if not header:
            return None
        data = []
        for ln in lines[1:]:
            cols = [c.strip() for c in ln.split('|')]
            if len(cols) < len(header):
                cols += [''] * (len(header) - len(cols))
            elif len(cols) > len(header):
                cols = cols[:len(header)]
            data.append(cols)
        if not row_colors:
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
    except Exception:
        return None

# -------------------------
# DataFrame 분할
# -------------------------
def split_dataframe_for_pdf(df, max_rows_per_page=20, max_cols_per_page=8):
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
                cols = df.columns[col_start:col_end]
                chunk = row_chunk[cols]
                chunks.append({
                    'data': chunk,
                    'row_range': (row_start, row_end-1),
                    'col_range': (col_start, col_end-1),
                    'is_last_row_chunk': row_end == total_rows,
                    'is_last_col_chunk': col_end == total_cols
                })
        return chunks
    except Exception:
        return []

def add_chunked_table(story, df, title, registered_fonts, BODY_STYLE, header_color='#F2F2F2'):
    try:
        if df is None or df.empty:
            story.append(Paragraph(f"{title}: 데이터가 없습니다.", BODY_STYLE))
            return
        story.append(Paragraph(title, BODY_STYLE))
        story.append(Spacer(1,8))
        chunks = split_dataframe_for_pdf(df)
        for i, ch in enumerate(chunks):
            chunk = ch['data']
            if len(chunks) > 1:
                story.append(Paragraph(f"행 {ch['row_range'][0]+1}~{ch['row_range'][1]+1}, 열 {ch['col_range'][0]+1}~{ch['col_range'][1]+1}", BODY_STYLE))
            table_data = [list(chunk.columns)]
            for _, row in chunk.iterrows():
                table_data.append([safe_str_convert(v) for v in row.values])
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
            story.append(Spacer(1,12))
            if i < len(chunks)-1 and (i+1)%2 == 0:
                story.append(PageBreak())
    except Exception as e:
        story.append(Paragraph(f"{title}: 테이블 생성 중 오류 발생", BODY_STYLE))

# -------------------------
# 갭 분석 계산 함수
# financial_df: 행=지표(구분), 열=회사별 표시값 (예: 'SK에너지', 'S-Oil', ...)
# 반환: gap_df(표시용), gap_chart_df(시각화용 긴형)
# -------------------------
def compute_gap_analysis(financial_df, sk_name_keyword='SK'):
    """
    financial_df: DataFrame with '구분' column and company columns (숫자)
    sk_name_keyword: 'SK' 또는 'SK에너지' 등 SK컬럼을 찾기 위한 키워드
    """
    try:
        if financial_df is None or financial_df.empty:
            return None, None
        df = financial_df.copy()
        # ensure '구분' exists as column; if index, reset
        if '구분' not in df.columns:
            df = df.reset_index().rename(columns={'index':'구분'})

        # find sk column
        sk_col = None
        for c in df.columns:
            if c == '구분':
                continue
            if sk_name_keyword in str(c):
                sk_col = c
                break
        # fallback to first non-구분 column
        if not sk_col:
            cols = [c for c in df.columns if c != '구분']
            if not cols:
                return None, None
            sk_col = cols[0]

        gap_rows = []
        chart_rows = []
        for _, row in df.iterrows():
            metric = row['구분']
            sk_val = ensure_numeric(row.get(sk_col, 0.0))
            row_data = {'지표': metric, 'SK에너지': sk_val}
            for c in df.columns:
                if c == '구분' or c == sk_col:
                    continue
                comp_name = c
                comp_val = ensure_numeric(row.get(c, 0.0))
                # gap percent 계산: (comp - sk)/abs(sk) *100 ; handle sk==0
                if sk_val != 0:
                    gap_pct = ((comp_val - sk_val) / abs(sk_val)) * 100.0
                else:
                    gap_pct = 0.0
                gap_amt = comp_val - sk_val
                row_data[f'{comp_name}_갭(%)'] = round(gap_pct, 2)
                row_data[f'{comp_name}_갭(금액)'] = gap_amt
                # for chart long form
                chart_rows.append({'지표': metric, '회사': comp_name, '갭(%)': round(gap_pct,2)})
            gap_rows.append(row_data)
        gap_df = pd.DataFrame(gap_rows)
        chart_df = pd.DataFrame(chart_rows)
        return gap_df, chart_df
    except Exception:
        return None, None

# -------------------------
# 차트 생성 (matplotlib) — 항상 Figure 반환 (플레이스홀더 포함)
# -------------------------
def create_quarterly_trend_fig(quarterly_df, value_col='매출액(조원)', title='분기별 매출액 추이'):
    """
    quarterly_df: columns ['분기','회사', value_col]
    returns: matplotlib.figure.Figure
    """
    try:
        fig, ax = plt.subplots(figsize=(8,3.6), dpi=100)
        if quarterly_df is None or quarterly_df.empty:
            ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center', fontsize=16)
            ax.axis('off')
            fig.suptitle(title)
            return fig
        # pivot: 분기 x 회사
        try:
            pivot = quarterly_df.pivot(index='분기', columns='회사', values=value_col)
            pivot.plot(ax=ax, marker='o')
            ax.set_xlabel('분기')
            ax.set_ylabel(value_col)
            ax.set_title(title)
            ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
            fig.tight_layout()
            return fig
        except Exception:
            # fallback simple plot
            for company in quarterly_df['회사'].unique():
                sub = quarterly_df[quarterly_df['회사']==company]
                ax.plot(sub['분기'], sub[value_col], marker='o', label=company)
            ax.legend()
            ax.set_title(title)
            fig.tight_layout()
            return fig
    except Exception:
        fig = plt.figure(figsize=(8,3.6))
        plt.text(0.5,0.5,'차트 생성 오류', ha='center', va='center')
        plt.axis('off')
        return fig

def create_gap_bar_fig(gap_chart_df, title='SK에너지 대비 갭차이 (%)'):
    """
    gap_chart_df: columns ['지표','회사','갭(%)']
    returns: matplotlib.figure.Figure
    """
    try:
        fig, ax = plt.subplots(figsize=(8,3.6), dpi=100)
        if gap_chart_df is None or gap_chart_df.empty:
            ax.text(0.5,0.5,'데이터 없음', ha='center', va='center', fontsize=16)
            ax.axis('off')
            fig.suptitle(title)
            return fig
        # pivot to wide for grouped bars
        try:
            pivot = gap_chart_df.pivot(index='지표', columns='회사', values='갭(%)')
            pivot = pivot.fillna(0)
            pivot.plot(kind='bar', ax=ax)
            ax.axhline(0, color='red', linewidth=1)
            ax.set_ylabel('갭차이 (%)')
            ax.set_title(title)
            ax.legend(loc='upper right', fontsize=8)
            fig.tight_layout()
            return fig
        except Exception:
            # fallback: plot each company series
            for comp in gap_chart_df['회사'].unique():
                sub = gap_chart_df[gap_chart_df['회사']==comp]
                ax.bar(sub['지표'], sub['갭(%)'], label=comp)
            ax.axhline(0, color='red', linewidth=1)
            ax.set_title(title)
            ax.legend()
            fig.tight_layout()
            return fig
    except Exception:
        fig = plt.figure(figsize=(8,3.6))
        plt.text(0.5,0.5,'차트 생성 오류', ha='center', va='center')
        plt.axis('off')
        return fig

# -------------------------
# 섹션 조합 함수들
# -------------------------
def add_financial_section_full(story, financial_df, quarterly_df, registered_fonts, HEADING_STYLE, BODY_STYLE):
    """
    Adds:
      1-1 정리표
      1-1-1 분기별 트렌드 차트 (매출액(조원) 기준)
      1-2 갭차이 표
      1-2-1 갭차이 차트
      1-3 AI 재무 인사이트 (place-holder: insights argument handled elsewhere)
    """
    try:
        # 1-1 정리된 재무지표 (표)
        add_chunked_table(story, financial_df, "1-1. 정리된 재무지표 (표시값)", registered_fonts, BODY_STYLE, header_color='#E6F3FF')

        # 1-1-1 분기별 트렌드 차트
        story.append(Paragraph("1-1-1. 분기별 트렌드 차트", HEADING_STYLE))
        # generate figure (매출액(조원) 우선)
        fig_trend = create_quarterly_trend_fig(quarterly_df, value_col='매출액(조원)', title='1-1-1. 분기별 매출액 추이 (조원)')
        buf = io.BytesIO()
        fig_trend.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig_trend)
        buf.seek(0)
        story.append(RLImage(buf, width=500, height=300))
        story.append(Spacer(1,12))

        # 1-2 갭차이 분석표
        gap_df, gap_chart_df = compute_gap_analysis(financial_df, sk_name_keyword='SK')
        if gap_df is None or gap_df.empty:
            story.append(Paragraph("1-2. SK에너지 대비 경쟁사 갭차이 분석표: 데이터 없음", BODY_STYLE))
        else:
            add_chunked_table(story, gap_df, "1-2. SK에너지 대비 경쟁사 갭차이 분석표", registered_fonts, BODY_STYLE, header_color='#F2F2F2')

        # 1-2-1 갭차이 시각화 차트
        story.append(Paragraph("1-2-1. 갭차이 시각화 차트", HEADING_STYLE))
        fig_gap = create_gap_bar_fig(gap_chart_df, title='1-2-1. SK에너지 대비 갭차이 (%)')
        buf2 = io.BytesIO()
        fig_gap.savefig(buf2, format='png', bbox_inches='tight')
        plt.close(fig_gap)
        buf2.seek(0)
        story.append(RLImage(buf2, width=500, height=300))
        story.append(Spacer(1,12))

        # 1-3 AI 재무 인사이트 (placeholder - actual insights passed separately)
        story.append(Paragraph("1-3. AI 재무 인사이트", HEADING_STYLE))
        story.append(Paragraph("AI 인사이트는 'insights' 매개변수에서 제공된 텍스트를 아래 섹션에서 출력합니다.", BODY_STYLE))
        story.append(Spacer(1,12))
    except Exception as e:
        story.append(Paragraph("재무분석 섹션 생성 중 오류가 발생했습니다.", BODY_STYLE))

# -------------------------
# AI 인사이트 섹션 (실제 텍스트은 create_enhanced_pdf_report에서 전달)
# -------------------------
def add_ai_insights_section(story, insights, registered_fonts, BODY_STYLE, header_color='#E31E24'):
    try:
        story.append(Paragraph("AI 인사이트", ParagraphStyle('h2', fontSize=14, textColor=colors.HexColor('#E31E24'),
                                                               fontName=registered_fonts.get('KoreanBold'))))
        if not insights:
            story.append(Paragraph("AI 인사이트가 제공되지 않았습니다.", BODY_STYLE))
            story.append(Spacer(1,12))
            return
        blocks = clean_ai_text(insights)
        ascii_buf = []
        for typ, line in blocks:
            if '|' in line:
                ascii_buf.append(line); continue
            if ascii_buf:
                tbl = ascii_to_table(ascii_buf, registered_fonts, header_color)
                if tbl:
                    story.append(tbl)
                story.append(Spacer(1,8))
                ascii_buf.clear()
            if typ == 'title':
                story.append(Paragraph(f"<b>{line}</b>", BODY_STYLE))
            else:
                story.append(Paragraph(line, BODY_STYLE))
        if ascii_buf:
            tbl = ascii_to_table(ascii_buf, registered_fonts, header_color)
            if tbl:
                story.append(tbl)
        story.append(Spacer(1,12))
    except Exception:
        story.append(Paragraph("AI 인사이트 섹션 생성 중 오류.", BODY_STYLE))

# -------------------------
# 뉴스 섹션
# -------------------------
def add_news_analysis_section(story, news_df, registered_fonts, HEADING_STYLE, BODY_STYLE):
    try:
        story.append(Paragraph("2. 뉴스 분석 및 요약", HEADING_STYLE))
        if news_df is None or news_df.empty:
            story.append(Paragraph("뉴스 데이터가 제공되지 않았습니다.", BODY_STYLE))
            story.append(Spacer(1,12))
            return
        # 상위 10개 제목
        story.append(Paragraph("2-1. 수집된 뉴스 (최대 10건)", ParagraphStyle('small', fontSize=12, fontName=registered_fonts.get('KoreanBold'))))
        for i, title in enumerate(news_df.get("제목", pd.Series([])).head(10), 1):
            story.append(Paragraph(f"{i}. {safe_str_convert(title)}", BODY_STYLE))
        story.append(Spacer(1,12))
        # 뉴스 중 일부 전문(예시: 첫 3건 내용 제공 가능하면)
        if "내용" in news_df.columns:
            story.append(Paragraph("2-2. 일부 뉴스 전문(요약)", ParagraphStyle('small2', fontSize=12, fontName=registered_fonts.get('KoreanBold'))))
            for i, content in enumerate(news_df["내용"].head(3),1):
                story.append(Paragraph(f"[{i}]", BODY_STYLE))
                story.append(Paragraph(safe_str_convert(content)[:800], BODY_STYLE))
                story.append(Spacer(1,6))
        story.append(Spacer(1,12))
    except Exception:
        story.append(Paragraph("뉴스 섹션 생성 중 오류.", BODY_STYLE))

# -------------------------
# 통합 인사이트 섹션
# -------------------------
def add_integrated_insight_section(story, integrated_text, registered_fonts, HEADING_STYLE, BODY_STYLE):
    try:
        story.append(Paragraph("3. 통합 인사이트", HEADING_STYLE))
        if not integrated_text:
            story.append(Paragraph("통합 인사이트가 제공되지 않았습니다.", BODY_STYLE))
            return
        blocks = clean_ai_text(integrated_text)
        if not blocks:
            story.append(Paragraph(integrated_text, BODY_STYLE))
            return
        for typ, line in blocks:
            if typ == 'title':
                story.append(Paragraph(f"<b>{line}</b>", BODY_STYLE))
            else:
                story.append(Paragraph(line, BODY_STYLE))
        story.append(Spacer(1,12))
    except Exception:
        story.append(Paragraph("통합 인사이트 생성 중 오류.", BODY_STYLE))

# -------------------------
# Excel 생성 (같이 제공)
# -------------------------
def create_excel_report(financial_data=None, news_data=None, insights=None):
    try:
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as writer:
            if financial_data is not None and not financial_data.empty:
                financial_data.to_excel(writer, sheet_name='재무분석', index=False)
            else:
                pd.DataFrame({'메모':['재무 데이터 없음']}).to_excel(writer, sheet_name='재무분석', index=False)
            if news_data is not None and not news_data.empty:
                news_data.to_excel(writer, sheet_name='뉴스', index=False)
            else:
                pd.DataFrame({'메모':['뉴스 데이터 없음']}).to_excel(writer, sheet_name='뉴스', index=False)
            if insights:
                pd.DataFrame({'AI인사이트': str(insights).splitlines()}).to_excel(writer, sheet_name='AI인사이트', index=False)
        out.seek(0)
        return out.getvalue()
    except Exception:
        out = io.BytesIO()
        return out.getvalue()

# -------------------------
# 메인 PDF 생성 함수 (순서 고정)
# -------------------------
def create_enhanced_pdf_report(
    financial_data=None,
    news_data=None,
    insights=None,
    integrated_insight=None,
    chart_figures=None,   # optional extra figures (list of matplotlib figs) — not required (we generate main ones inside)
    quarterly_df=None,
    show_footer=False,
    report_target="SK이노베이션 경영진",
    report_author="보고자 미기재",
    gpt_api_key=None,
):
    """
    Returns: bytes (PDF)
    """
    registered_fonts = register_fonts_safe()
    TITLE_STYLE = ParagraphStyle('Title', fontName=registered_fonts.get('KoreanBold'), fontSize=20, leading=28, alignment=1)
    HEADING_STYLE = ParagraphStyle('Heading', fontName=registered_fonts.get('KoreanBold'), fontSize=14, textColor=colors.HexColor('#E31E24'), spaceBefore=10, spaceAfter=6)
    BODY_STYLE = ParagraphStyle('Body', fontName=registered_fonts.get('KoreanSerif'), fontSize=11, leading=14)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []

    # cover
    story.append(Paragraph("손익개선을 위한 SK에너지 및 경쟁사 비교 분석 보고서", TITLE_STYLE))
    story.append(Spacer(1, 16))
    report_info = f"<b>보고일자:</b> {datetime.now().strftime('%Y년 %m월 %d일')}<br/><b>보고대상:</b> {safe_str_convert(report_target)}<br/><b>보고자:</b> {safe_str_convert(report_author)}"
    story.append(Paragraph(report_info, BODY_STYLE))
    story.append(Spacer(1, 18))

    # 1. 재무분석 (정해진 순서)
    story.append(Paragraph("1. 재무분석 결과", HEADING_STYLE))
    add_financial_section_full(story, financial_data, quarterly_df, registered_fonts, HEADING_STYLE, BODY_STYLE)

    # 1-3 AI 재무 인사이트 (실제 텍스트 넣기)
    if insights:
        add_ai_insights_section(story, insights, registered_fonts, BODY_STYLE)
    else:
        story.append(Paragraph("AI 재무 인사이트가 제공되지 않았습니다.", BODY_STYLE))
        story.append(Spacer(1,12))

    # 2. 뉴스 분석
    add_news_analysis_section(story, news_data, registered_fonts, HEADING_STYLE, BODY_STYLE)

    # 3. 통합 인사이트
    add_integrated_insight_section(story, integrated_insight, registered_fonts, HEADING_STYLE, BODY_STYLE)

    # footer
    if show_footer:
        story.append(Spacer(1,12))
        story.append(Paragraph("※ 본 보고서는 자동 생성되었습니다.", BODY_STYLE))

    # page number
    def _page_number(canvas, doc):
        canvas.setFont('Helvetica', 9)
        canvas.drawCentredString(A4[0]/2, 18, f"- {canvas.getPageNumber()} -")

    # build
    doc.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    buffer.seek(0)
    return buffer.getvalue()

# -------------------------
# 통합 호출 함수
# -------------------------
def generate_report_with_gpt_insights(
    financial_data=None,
    news_data=None,
    insights=None,
    integrated_insight=None,
    quarterly_df=None,
    gpt_api_key=None,
    **kwargs
):
    """
    Wrapper that returns PDF bytes and Excel bytes
    """
    pdf = create_enhanced_pdf_report(
        financial_data=financial_data,
        news_data=news_data,
        insights=insights,
        integrated_insight=integrated_insight,
        quarterly_df=quarterly_df,
        gpt_api_key=gpt_api_key,
        **kwargs
    )
    excel = create_excel_report(financial_data, news_data, insights)
    return {'pdf': pdf, 'excel': excel}

# -------------------------
# dependency check helper
# -------------------------
def check_dependencies():
    miss = []
    try:
        import matplotlib
    except Exception:
        miss.append('matplotlib')
    try:
        import reportlab
    except Exception:
        miss.append('reportlab')
    try:
        import pandas
    except Exception:
        miss.append('pandas')
    try:
        import openpyxl
    except Exception:
        miss.append('openpyxl')
    if miss:
        print("Missing packages:", miss)
        return False
    return True

# -------------------------
# 실행 예시 (테스트)
# -------------------------
if __name__ == "__main__":
    check_dependencies()
    # 샘플 재무표 (행: 지표, 열: 회사)
    df_fin = pd.DataFrame({
        '구분': ['매출액(억원)', '영업이익(억원)', '영업이익률(%)'],
        'SK에너지': [10000, 800, 8.0],
        'S-Oil': [9500, 760, 8.0],
        'GS칼텍스': [8800, 440, 5.0]
    })

    # 샘플 분기 데이터 (분기, 회사, 매출액(조원), 영업이익률(%))
    df_quarterly = pd.DataFrame({
        '분기': ['2024Q1','2024Q2','2024Q3','2024Q4'],
        '회사': ['SK에너지','SK에너지','SK에너지','SK에너지'],
        '매출액(조원)': [5.1, 5.5, 5.8, 6.0],
        '영업이익률(%)': [7.5, 7.8, 8.0, 8.2]
    })

    # 샘플 뉴스
    df_news = pd.DataFrame({
        '제목': ['뉴스1 제목', '뉴스2 제목'],
        '내용': ['뉴스1 내용 전문...', '뉴스2 내용 전문...']
    })

    # 예시 AI 인사이트
    ai_insights = "# 핵심 인사이트\n1. 영업이익률 개선 필요\n2. 비용 구조 최적화 권고\n|지표|SK에너지|S-Oil|GS칼텍스|\n|----|----:|----:|----:|\n|영업이익률(%)|8.0|8.5|7.0|"

    integrated_text = "종합: 재무개선 필요 / 단기: 비용절감, 중기: 제품믹스 개선, 장기: 탈탄소 투자"

    outputs = generate_report_with_gpt_insights(
        financial_data=df_fin,
        news_data=df_news,
        insights=ai_insights,
        integrated_insight=integrated_text,
        quarterly_df=df_quarterly,
        gpt_api_key=None
    )

    # 저장 테스트
    with open("final_report.pdf","wb") as f:
        f.write(outputs['pdf'])
    with open("final_report.xlsx","wb") as f:
        f.write(outputs['excel'])
    print("샘플 PDF/Excel 생성 완료: final_report.pdf / final_report.xlsx")
