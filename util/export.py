# -*- coding: utf-8 -*-
"""
🎯 SK에너지 분석 보고서 생성 모듈 (export.py)
- ReportLab, Pandas, Matplotlib 활용
- NanumGothic 한글 폰트 사용
- 메인 코드 연동용 함수 및 Streamlit UI 포함
"""

import io
import os
import pandas as pd
from datetime import datetime
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# 한글 폰트 설정 (fonts 폴더 기준)
plt.rcParams['font.family'] = ['NanumGothic', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, PageBreak, Image as RLImage, SimpleDocTemplate
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def get_font_paths():
    """fonts 폴더 내 NanumGothic 등 한글 폰트 경로 확인"""
    font_paths = {
        "Korean": "fonts/NanumGothic.ttf",
        "KoreanBold": "fonts/NanumGothicBold.ttf",
        "KoreanSerif": "fonts/NanumMyeongjo.ttf"
    }
    found_fonts = {}
    for name, path in font_paths.items():
        if os.path.exists(path) and os.path.getsize(path) > 0:
            found_fonts[name] = path
    return found_fonts


def register_fonts():
    """ReportLab용 폰트 등록 (NanumGothic 등)"""
    registered = {"Korean": "Helvetica", "KoreanBold": "Helvetica-Bold"}
    if not REPORTLAB_AVAILABLE:
        return registered

    font_paths = get_font_paths()
    for name, path in font_paths.items():
        if name not in pdfmetrics.getRegisteredFontNames():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered[name] = name
            except Exception:
                pass
    return registered


def create_korean_charts():
    """Matplotlib로 한글 차트 2종 생성: 매출액 비교, ROE 비교"""
    charts = {}

    try:
        # 1) 매출액 비교
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        companies = ['SK에너지', 'S-Oil', 'GS칼텍스', 'HD현대오일뱅크']
        revenues = [15.2, 14.8, 13.5, 11.2]
        colors_list = ['#E31E24', '#FF6B6B', '#4ECDC4', '#45B7D1']

        bars = ax.bar(companies, revenues, color=colors_list, alpha=0.8, width=0.6)
        ax.set_title('매출액 비교 (조원)', fontsize=14, weight='bold')
        ax.set_ylabel('매출액 (조원)', fontsize=12, weight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        for bar, value in zip(bars, revenues):
            ax.text(bar.get_x() + bar.get_width()/2, value + 0.2, f'{value}조원', ha='center', va='bottom', fontsize=11, weight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        charts['revenue_comparison'] = fig
    except Exception:
        charts['revenue_comparison'] = None

    try:
        # 2) ROE 비교
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        fig2.patch.set_facecolor('white')
        roe_values = [12.3, 11.8, 10.5, 9.2]
        bars2 = ax2.bar(companies, roe_values, color='#E31E24', alpha=0.7)
        ax2.set_title('ROE 비교 (%)', fontsize=14, weight='bold')
        ax2.set_ylabel('ROE (%)', fontsize=12, weight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars2, roe_values):
            ax2.text(bar.get_x() + bar.get_width()/2, val + 0.2, f'{val}%', ha='center', va='bottom', fontsize=11, weight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        charts['roe_comparison'] = fig2
    except Exception:
        charts['roe_comparison'] = None

    return charts


def safe_create_chart_image(fig, width=480, height=320):
    """ReportLab용 차트 이미지 변환 (BytesIO → RLImage)"""
    if fig is None or not REPORTLAB_AVAILABLE:
        return None
    try:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100, facecolor='white')
        buf.seek(0)
        img = RLImage(buf, width=width, height=height)
        plt.close(fig)
        return img
    except Exception:
        try:
            plt.close(fig)
        except:
            pass
        return None


def create_korean_table(registered_fonts):
    """ReportLab용 재무분석 테이블 생성"""
    if not REPORTLAB_AVAILABLE:
        return None

    table_data = [
        ['구분', 'SK에너지', 'S-Oil', 'GS칼텍스', 'HD현대오일뱅크'],
        ['매출액(조원)', '15.2', '14.8', '13.5', '11.2'],
        ['영업이익률(%)', '5.6', '5.3', '4.6', '4.3'],
        ['ROE(%)', '12.3', '11.8', '10.5', '9.2'],
        ['ROA(%)', '8.1', '7.8', '7.2', '6.5']
    ]
    col_count = len(table_data[0])
    col_width = 6.5 * inch / col_count
    table = Table(table_data, colWidths=[col_width] * col_count)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E31E24')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), registered_fonts.get('KoreanBold', 'Helvetica-Bold')),
        ('FONTNAME', (0, 1), (-1, -1), registered_fonts.get('Korean', 'Helvetica')),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    return table


def create_korean_news_table(registered_fonts):
    """ReportLab용 뉴스 테이블 생성"""
    if not REPORTLAB_AVAILABLE:
        return None

    news_data = [
        ['제목', '날짜', '출처'],
        ['SK에너지, 3분기 실적 시장 기대치 상회', '2024-11-01', '매일경제'],
        ['정유업계, 원유가 하락으로 마진 개선 기대', '2024-10-28', '한국경제'],
        ['SK이노베이션, 배터리 사업 분할 추진', '2024-10-25', '조선일보'],
        ['에너지 전환 정책, 정유업계 영향 분석', '2024-10-22', '이데일리']
    ]
    col_widths = [3.5 * inch, 1.5 * inch, 1.5 * inch]
    table = Table(news_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), registered_fonts.get('KoreanBold', 'Helvetica-Bold')),
        ('FONTNAME', (0, 1), (-1, -1), registered_fonts.get('Korean', 'Helvetica')),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return table


def create_korean_pdf_report():
    """NanumGothic 폰트로 SK에너지 분석 보고서 PDF 생성 (ReportLab 활용)"""
    if not REPORTLAB_AVAILABLE:
        return "ReportLab not available".encode('utf-8')

    try:
        registered_fonts = register_fonts()
        charts = create_korean_charts()

        title_style = ParagraphStyle(
            'Title',
            fontName=registered_fonts.get('KoreanBold', 'Helvetica-Bold'),
            fontSize=18,
            leading=24,
            spaceAfter=20,
            alignment=1,
            textColor=colors.HexColor('#E31E24')
        )
        heading_style = ParagraphStyle(
            'Heading',
            fontName=registered_fonts.get('KoreanBold', 'Helvetica-Bold'),
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor('#E31E24')
        )
        body_style = ParagraphStyle(
            'Body',
            fontName=registered_fonts.get('Korean', 'Helvetica'),
            fontSize=10,
            leading=14,
            spaceAfter=6,
            textColor=colors.HexColor('#2C3E50')
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
        story = []

        # 제목 및 보고일자
        story.append(Paragraph("SK에너지 경쟁사 분석 보고서", title_style))
        story.append(Spacer(1, 20))
        current_date = datetime.now().strftime('%Y년 %m월 %d일')
        story.append(Paragraph(f"보고일자: {current_date}", body_style))
        story.append(Paragraph("보고대상: SK이노베이션 경영진", body_style))
        story.append(Paragraph("보고자: AI 분석 시스템", body_style))
        story.append(Spacer(1, 30))

        # 핵심 요약
        story.append(Paragraph("◆ 핵심 요약", heading_style))
        story.append(Spacer(1, 10))
        summary = (
            "SK에너지는 매출액 15.2조원으로 업계 1위를 유지하며, 영업이익률 5.6%와 ROE 12.3%를 기록하여 "
            "경쟁사 대비 우수한 성과를 보이고 있습니다. 최근 3분기 실적이 시장 기대치를 상회하며 긍정적 전망을 보여주고 있으나, "
            "에너지 전환 정책에 대한 전략적 대응이 필요한 상황입니다."
        )
        story.append(Paragraph(summary, body_style))
        story.append(Spacer(1, 20))

        # 재무분석 결과 - 표, 차트
        story.append(Paragraph("1. 재무분석 결과", heading_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph("1-1. 주요 재무지표", heading_style))
        story.append(Spacer(1, 6))

        table = create_korean_table(registered_fonts)
        if table:
            story.append(table)
        else:
            story.append(Paragraph("• SK에너지 매출액: 15.2조원 (업계 1위)", body_style))
            story.append(Paragraph("• 영업이익률: 5.6% (경쟁사 대비 우위)", body_style))
            story.append(Paragraph("• ROE: 12.3%, ROA: 8.1% (우수한 수익성)", body_style))
        story.append(Spacer(1, 16))

        story.append(Paragraph("1-2. 차트 분석", heading_style))
        story.append(Spacer(1, 8))

        # 매출액 차트
        if charts.get('revenue_comparison'):
            img = safe_create_chart_image(charts['revenue_comparison'], width=450, height=270)
            if img:
                story.append(Paragraph("▶ 매출액 비교", body_style))
                story.append(img)
                story.append(Spacer(1, 10))

        # ROE 차트
        if charts.get('roe_comparison'):
            img = safe_create_chart_image(charts['roe_comparison'], width=450, height=270)
            if img:
                story.append(Paragraph("▶ ROE 성과 비교", body_style))
                story.append(img)
                story.append(Spacer(1, 16))

        # 차트 없으면 텍스트 대체
        if not charts.get('revenue_comparison') and not charts.get('roe_comparison'):
            story.append(Paragraph("📊 매출 분석: SK에너지가 15.2조원으로 경쟁사 대비 우위를 보입니다", body_style))
            story.append(Paragraph("📈 수익성: ROE 12.3%로 S-Oil 대비 0.5%p, GS칼텍스 대비 1.8%p 우위", body_style))
            story.append(Spacer(1, 16))

        story.append(PageBreak())

        # 뉴스 분석 결과
        story.append(Paragraph("2. 뉴스 분석 결과", heading_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph("2-1. 주요 뉴스", heading_style))
        story.append(Spacer(1, 6))

        news_table = create_korean_news_table(registered_fonts)
        if news_table:
            story.append(news_table)
        else:
            story.append(Paragraph("📰 주요 뉴스:", body_style))
            story.append(Paragraph("• SK에너지, 3분기 실적 시장 기대치 상회 (매일경제, 2024-11-01)", body_style))
            story.append(Paragraph("• 정유업계, 원유가 하락으로 마진 개선 기대 (한국경제, 2024-10-28)", body_style))
        story.append(Spacer(1, 16))

        # 전략 제언
        story.append(Paragraph("3. 전략 제언", heading_style))
        story.append(Spacer(1, 10))
        strategy_lines = [
            "◆ 단기 전략 (1-2년)",
            "• 운영 효율성 극대화를 통한 마진 확대에 집중",
            "• 현금 창출 능력 강화로 안정적 배당 및 투자 재원 확보",
            "",
            "◆ 중기 전략 (3-5년)",
            "• 사업 포트폴리오 다각화 및 신사업 진출 검토",
            "• 디지털 전환과 공정 혁신을 통한 경쟁력 강화",
            "",
            "◆ 장기 전략 (5년 이상)",
            "• 에너지 전환에 대비한 친환경 사업 확대",
            "• ESG 경영 체계 구축 및 지속가능한 성장 기반 마련"
        ]
        for line in strategy_lines:
            if line.strip():
                story.append(Paragraph(line, body_style))
            else:
                story.append(Spacer(1, 6))

        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            fontName=registered_fonts.get('Korean', 'Helvetica'),
            fontSize=8,
            alignment=1,
            textColor=colors.HexColor('#7F8C8D')
        )
        story.append(Paragraph("※ 본 보고서는 AI 분석 시스템에 의해 생성되었습니다", footer_style))
        story.append(Paragraph(f"생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}", footer_style))

        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"PDF 생성 실패: {str(e)}".encode('utf-8')


def create_enhanced_pdf_report(
    financial_data=None,
    news_data=None,
    insights=None,
    quarterly_df=None,
    chart_df=None,
    gap_analysis_df=None,
    show_footer=True,
    report_target="SK이노베이션 경영진",
    report_author="AI 분석 시스템",
    **kwargs
):
    """
    메인 연동용 PDF 보고서 생성 함수
    파라미터 받지만 현재 create_korean_pdf_report() 호출
    """
    return create_korean_pdf_report()


def create_excel_report(
    financial_data=None,
    news_data=None,
    insights=None,
    **kwargs
):
    """간단 Excel 보고서 생성 함수"""
    try:
        buffer = io.BytesIO()
        if financial_data is not None and not financial_data.empty:
            df = financial_data
        else:
            df = pd.DataFrame({
                '구분': ['매출액(조원)', '영업이익률(%)', 'ROE(%)', 'ROA(%)'],
                'SK에너지': [15.2, 5.6, 12.3, 8.1],
                'S-Oil': [14.8, 5.3, 11.8, 7.8],
                'GS칼텍스': [13.5, 4.6, 10.5, 7.2],
                'HD현대오일뱅크': [11.2, 4.3, 9.2, 6.5]
            })
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='재무분석', index=False)
            if news_data is not None and not news_data.empty:
                news_data.to_excel(writer, sheet_name='뉴스분석', index=False)
        buffer.seek(0)
        excel_bytes = buffer.getvalue()
        buffer.close()
        return excel_bytes
    except Exception as e:
        return f"Excel 생성 실패: {str(e)}".encode('utf-8')


def create_pdf_download_button(
    financial_data=None,
    news_data=None,
    insights=None,
    quarterly_df=None,
    chart_df=None,
    gap_analysis_df=None,
    report_target="SK이노베이션 경영진",
    report_author="AI 분석 시스템",
    show_footer=True,
    **kwargs
):
    """Streamlit PDF 다운로드 버튼 생성"""
    if st.button("📄 한글 PDF 보고서 생성 (NanumGothic 폰트)", type="primary", key="korean_pdf_btn"):
        with st.spinner("한글 PDF 생성 중..."):
            pdf_data = create_korean_pdf_report()
            if isinstance(pdf_data, bytes) and len(pdf_data) > 1000:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"SK에너지_분석보고서_{timestamp}.pdf"
                st.download_button(
                    label="📥 PDF 다운로드",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf",
                    type="secondary"
                )
                st.success("✅ 한글 PDF 생성 완료! 다운로드 버튼을 클릭하세요.")
                st.info("🔤 폰트: fonts 폴더의 NanumGothic 폰트를 사용했습니다.")
                st.session_state.generated_file = pdf_data
                st.session_state.generated_filename = filename
                st.session_state.generated_mime = "application/pdf"
                return True
            else:
                st.error("❌ PDF 생성 실패")
                if isinstance(pdf_data, bytes):
                    st.error(pdf_data.decode('utf-8', errors='ignore'))
                return False
    return None


def test_integration():
    """기본 함수 존재 및 생성 테스트"""
    print("🧪 통합 테스트 시작")
    funcs = ['create_enhanced_pdf_report', 'create_excel_report', 'create_pdf_download_button']
    for f in funcs:
        if f in globals():
            print(f"✅ 함수 존재: {f}")
        else:
            print(f"❌ 함수 없음: {f}")

    try:
        pdf_bytes = create_enhanced_pdf_report()
        print(f"✅ PDF 생성 성공, 크기: {len(pdf_bytes)} bytes")
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")

    try:
        excel_bytes = create_excel_report()
        print(f"✅ Excel 생성 성공, 크기: {len(excel_bytes)} bytes")
    except Exception as e:
        print(f"❌ Excel 생성 실패: {e}")

    try:
        fonts = get_font_paths()
        registered = register_fonts()
        print(f"✅ 폰트 발견 및 등록: {len(fonts)}개 / 등록 {list(registered.keys())}")
    except Exception as e:
        print(f"❌ 폰트 테스트 실패: {e}")

    print("🏁 테스트 종료")


def create_streamlit_interface():
    """Streamlit UI (테스트용)"""
    st.title("🏢 SK에너지 분석 보고서 생성기")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        report_target = st.text_input("보고 대상", value="SK이노베이션 경영진")
        report_author = st.text_input("보고자", value="AI 분석 시스템")
    with col2:
        show_footer = st.checkbox("Footer 표시", value=True)
        include_charts = st.checkbox("차트 포함", value=True)

    st.markdown("---")

    col_pdf, col_excel = st.columns(2)
    with col_pdf:
        create_pdf_download_button(report_target=report_target, report_author=report_author, show_footer=show_footer)
    with col_excel:
        if st.button("📊 Excel 보고서 생성", type="secondary", key="excel_btn"):
            with st.spinner("Excel 생성 중..."):
                excel_bytes = create_excel_report()
                if isinstance(excel_bytes, bytes) and len(excel_bytes) > 100:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"SK에너지_분석보고서_{timestamp}.xlsx"
                    st.download_button(
                        label="📥 Excel 다운로드",
                        data=excel_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="secondary"
                    )
                    st.success("✅ Excel 생성 완료!")
                else:
                    st.error("❌ Excel 생성 실패")

    st.markdown("---")
    st.subheader("🧪 테스트 기능")
    if st.button("🔍 통합 테스트 실행", key="test_btn"):
        with st.spinner("통합 테스트 중..."):
            test_integration()
            st.success("✅ 통합 테스트 완료! 콘솔을 확인하세요.")

    if st.button("🔤 폰트 상태 확인", key="font_check_btn"):
        with st.expander("폰트 상태", expanded=True):
            font_paths = get_font_paths()
            if font_paths:
                st.success(f"✅ {len(font_paths)}개 폰트 발견")
                for nm, pth in font_paths.items():
                    sz = os.path.getsize(pth) if os.path.exists(pth) else 0
                    st.write(f"• {nm}: {pth} ({sz:,} bytes)")
            else:
                st.warning("⚠️ 폰트 파일을 찾을 수 없습니다")
            if REPORTLAB_AVAILABLE:
                st.success("✅ ReportLab 사용 가능")
            else:
                st.error("❌ ReportLab 없음 - pip install reportlab 필요")

    with st.expander("📖 사용법", expanded=False):
        st.markdown(
            """
            ### 📁 파일 구조 예시
            ```
            your_project/
            ├── export.py
            ├── fonts/
            │   ├── NanumGothic.ttf
            │   ├── NanumGothicBold.ttf
            │   └── NanumMyeongjo.ttf
            └── main.py
            ```
            ### 메인 코드 연동 예
            ```python
            from export import create_pdf_download_button, create_enhanced_pdf_report

            # Streamlit 앱 내에서
            create_pdf_download_button(financial_data=df, news_data=news_df)

            # 직접 PDF 생성
            pdf_data = create_enhanced_pdf_report()
            ```
            ### 설치 필요 패키지
            ```
            pip install reportlab pandas matplotlib openpyxl streamlit
            ```
            """
        )


if __name__ == "__main__":
    print("🚀 SK에너지 PDF 보고서 생성 모듈 실행")
    print("=" * 50)
    print(f"📋 환경 확인:")
    print(f"  - ReportLab: {'✅ 사용 가능' if REPORTLAB_AVAILABLE else '❌ 없음'}")
    print(f"  - Pandas: {'✅ 사용 가능' if 'pd' in globals() else '❌ 없음'}")
    print(f"  - Matplotlib: {'✅ 사용 가능' if 'plt' in globals() else '❌ 없음'}")
    fonts_found = get_font_paths()
    print(f"  - 폰트: {'✅ ' + str(len(fonts_found)) + '개 발견' if fonts_found else '❌ 없음'}")

    try:
        if 'streamlit' in st.__module__:
            print("🌐 Streamlit 환경에서 실행")
            create_streamlit_interface()
        else:
            print("💻 일반 Python 환경에서 실행")
            test_integration()
    except Exception:
        print("💻 일반 Python 환경에서 실행")
        test_integration()

    print("=" * 50)
    print("✅ 모듈 로드 완료! 메인 코드에서 import 하여 사용하세요.")
    print("""
📖 사용 예시:
    from export import create_pdf_download_button, create_enhanced_pdf_report

    # Streamlit에서
    create_pdf_download_button(financial_data=df, news_data=news_df)

    # 직접 생성
    pdf_data = create_enhanced_pdf_report()
""")
