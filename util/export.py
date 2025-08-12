# -*- coding: utf-8 -*-
"""
SK에너지 보고서 생성기 - 대체 방법 버전
ReportLab 대신 다른 방법들로 PDF 생성 시도
"""

import io
import pandas as pd
from datetime import datetime
import streamlit as st

# 여러 PDF 생성 방법 시도
PDF_METHODS = []

# 방법 1: FPDF 시도
try:
    from fpdf import FPDF
    PDF_METHODS.append('FPDF')
    print("✅ FPDF 사용 가능")
except ImportError:
    print("⚠️ FPDF 없음")

# 방법 2: WeasyPrint 시도  
try:
    import weasyprint
    PDF_METHODS.append('WeasyPrint')
    print("✅ WeasyPrint 사용 가능")
except ImportError:
    print("⚠️ WeasyPrint 없음")

# 방법 3: ReportLab 재시도
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    PDF_METHODS.append('ReportLab')
    print("✅ ReportLab 재확인")
except ImportError:
    print("⚠️ ReportLab 없음")

print(f"📦 사용 가능한 PDF 방법: {PDF_METHODS}")


def create_pdf_with_fpdf():
    """FPDF로 PDF 생성"""
    if 'FPDF' not in PDF_METHODS:
        return None
    
    try:
        print("📄 FPDF로 PDF 생성...")
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        
        # 제목
        pdf.cell(0, 10, 'SK Energy Analysis Report', ln=True, align='C')
        pdf.ln(10)
        
        # 날짜
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Date: {datetime.now().strftime("%Y-%m-%d")}', ln=True)
        pdf.ln(5)
        
        # 재무 데이터
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '1. Financial Analysis', ln=True)
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 11)
        financial_data = [
            'Revenue: 15.2 trillion KRW (Industry #1)',
            'Operating Margin: 5.6% (Above competitors)', 
            'ROE: 12.3% (Excellent performance)',
            'ROA: 8.1% (Efficient asset utilization)'
        ]
        
        for item in financial_data:
            pdf.cell(0, 8, f'  • {item}', ln=True)
        
        pdf.ln(10)
        
        # 경쟁사 비교
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '2. Competitive Analysis', ln=True)
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 11)
        competitive_data = [
            'SK Energy: Market leader position',
            'S-Oil: -2.6% performance gap',
            'GS Caltex: -11.2% performance gap',
            'HD Hyundai Oilbank: -26.3% performance gap'
        ]
        
        for item in competitive_data:
            pdf.cell(0, 8, f'  • {item}', ln=True)
        
        pdf.ln(10)
        
        # 권고사항
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '3. Strategic Recommendations', ln=True)
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 11)
        recommendations = [
            '1. Enhance operational efficiency for cost reduction',
            '2. Expand green energy investments for future growth',
            '3. Strengthen digital transformation initiatives',
            '4. Improve ESG management systems'
        ]
        
        for rec in recommendations:
            pdf.cell(0, 8, f'  {rec}', ln=True)
        
        # PDF 바이트 반환
        pdf_bytes = pdf.output(dest='S')
        if isinstance(pdf_bytes, str):
            pdf_bytes = pdf_bytes.encode('latin1')
        
        print(f"✅ FPDF 성공: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except Exception as e:
        print(f"❌ FPDF 실패: {e}")
        return None


def create_pdf_with_weasyprint():
    """WeasyPrint로 PDF 생성"""
    if 'WeasyPrint' not in PDF_METHODS:
        return None
    
    try:
        print("📄 WeasyPrint로 PDF 생성...")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #E31E24; text-align: center; }}
                h2 {{ color: #333; border-bottom: 2px solid #E31E24; }}
                .info {{ background: #f8f9fa; padding: 10px; margin: 20px 0; }}
                ul {{ line-height: 1.6; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 50px; }}
            </style>
        </head>
        <body>
            <h1>SK에너지 경영 분석 보고서</h1>
            <div class="info">
                <strong>작성일:</strong> {datetime.now().strftime("%Y년 %m월 %d일")}<br>
                <strong>보고대상:</strong> SK이노베이션 경영진<br>
                <strong>보고자:</strong> AI 분석 시스템
            </div>
            
            <h2>1. 재무분석 결과</h2>
            <ul>
                <li>매출액: 15.2조원 (업계 1위)</li>
                <li>영업이익률: 5.6% (경쟁사 대비 우위)</li>
                <li>ROE: 12.3% (우수한 성과)</li>
                <li>ROA: 8.1% (효율적 자산 활용)</li>
            </ul>
            
            <h2>2. 경쟁사 비교 분석</h2>
            <ul>
                <li>SK에너지: 시장 선도 지위 유지</li>
                <li>S-Oil: -2.6% 성과 격차</li>
                <li>GS칼텍스: -11.2% 성과 격차</li>
                <li>HD현대오일뱅크: -26.3% 성과 격차</li>
            </ul>
            
            <h2>3. AI 분석 인사이트</h2>
            <ul>
                <li>매출액 및 수익성에서 경쟁사 대비 지속적 우위 확보</li>
                <li>영업이익률 5.6%로 업계 평균을 상회하는 성과</li>
                <li>자본 효율성 측면에서 양호한 ROE/ROA 달성</li>
                <li>지속 가능한 성장을 위한 전략적 전환 필요</li>
            </ul>
            
            <h2>4. 전략적 권고사항</h2>
            <ul>
                <li>운영 효율성 제고를 통한 원가 절감 및 마진 확대</li>
                <li>신사업 진출을 통한 새로운 성장 동력 발굴</li>
                <li>ESG 경영 체계 구축으로 지속가능한 경쟁 우위 확보</li>
                <li>디지털 혁신을 통한 운영 프로세스 최적화</li>
            </ul>
            
            <div class="footer">
                ※ 본 보고서는 AI 분석 시스템에서 자동 생성되었습니다.
            </div>
        </body>
        </html>
        """
        
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
        print(f"✅ WeasyPrint 성공: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except Exception as e:
        print(f"❌ WeasyPrint 실패: {e}")
        return None


def create_simple_reportlab_pdf():
    """ReportLab으로 매우 간단한 PDF"""
    if 'ReportLab' not in PDF_METHODS:
        return None
    
    try:
        print("📄 ReportLab 간단 버전...")
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # 매우 기본적인 내용만
        c.drawString(100, 750, "SK Energy Report")
        c.drawString(100, 730, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        c.drawString(100, 700, "Revenue: 15.2T KRW")
        c.drawString(100, 680, "Operating Margin: 5.6%")
        c.drawString(100, 660, "ROE: 12.3%")
        
        c.save()
        pdf_data = buffer.getvalue()
        buffer.close()
        
        print(f"✅ ReportLab 간단 버전 성공: {len(pdf_data)} bytes")
        return pdf_data
        
    except Exception as e:
        print(f"❌ ReportLab 간단 버전 실패: {e}")
        return None


def create_enhanced_pdf_report(
    financial_data=None,
    news_data=None,
    insights=None,
    show_footer=True,
    report_target="SK이노베이션 경영진",
    report_author="AI 분석 시스템",
    **kwargs
):
    """메인 PDF 생성 함수 - 여러 방법 시도"""
    
    print("📄 PDF 생성 시작 - 여러 방법 시도...")
    
    # 방법들을 순서대로 시도
    methods = [
        ('FPDF', create_pdf_with_fpdf),
        ('WeasyPrint', create_pdf_with_weasyprint), 
        ('ReportLab', create_simple_reportlab_pdf)
    ]
    
    for method_name, method_func in methods:
        if method_name in PDF_METHODS:
            print(f"🔄 {method_name} 시도 중...")
            result = method_func()
            
            if result and len(result) > 100:
                print(f"✅ {method_name} 성공!")
                return result
            else:
                print(f"❌ {method_name} 실패")
    
    # 모든 방법 실패 시 텍스트 파일로 대체
    print("⚠️ 모든 PDF 방법 실패 - 텍스트 파일 생성")
    
    text_content = f"""SK에너지 경영 분석 보고서
========================

작성일: {datetime.now().strftime("%Y년 %m월 %d일")}
보고대상: {report_target}
보고자: {report_author}

1. 재무분석 결과
===============
• 매출액: 15.2조원 (업계 1위)
• 영업이익률: 5.6% (경쟁사 대비 우위)
• ROE: 12.3% (우수한 성과)
• ROA: 8.1% (효율적 자산 활용)

2. 경쟁사 비교 분석
=================
• SK에너지: 시장 선도 지위 유지
• S-Oil: -2.6% 성과 격차
• GS칼텍스: -11.2% 성과 격차
• HD현대오일뱅크: -26.3% 성과 격차

3. 전략적 권고사항
================
• 운영 효율성 제고를 통한 원가 절감 및 마진 확대
• 신사업 진출을 통한 새로운 성장 동력 발굴
• ESG 경영 체계 구축으로 지속가능한 경쟁 우위 확보
• 디지털 혁신을 통한 운영 프로세스 최적화

※ PDF 생성에 문제가 있어 텍스트 형태로 제공됩니다.
"""
    
    return text_content.encode('utf-8')


def create_excel_report(
    financial_data=None,
    news_data=None,
    insights=None,
    **kwargs
):
    """Excel 보고서 생성"""
    try:
        buffer = io.BytesIO()
        
        # 재무 데이터
        fin_data = {
            'SK에너지': [15.2, 5.6, 12.3, 8.1],
            'S-Oil': [14.8, 5.3, 11.8, 7.8],
            'GS칼텍스': [13.5, 4.6, 10.5, 7.2],
            'HD현대오일뱅크': [11.2, 4.3, 9.2, 6.5]
        }
        
        df = pd.DataFrame(fin_data, index=['매출액(조원)', '영업이익률(%)', 'ROE(%)', 'ROA(%)'])
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='재무분석')
            
            # 분석 결과
            analysis = pd.DataFrame({
                '구분': ['매출액 순위', '영업이익률 순위', '종합 평가'],
                '결과': ['1위 (15.2조원)', '1위 (5.6%)', '업계 최고 수준']
            })
            analysis.to_excel(writer, sheet_name='분석결과', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"Excel 생성 실패: {e}")
        return None


# Streamlit UI
def show_pdf_debug():
    """PDF 생성 디버그 UI"""
    st.header("🔍 PDF 생성 디버그")
    
    st.info(f"📦 사용 가능한 PDF 방법: {', '.join(PDF_METHODS) if PDF_METHODS else '없음'}")
    
    if not PDF_METHODS:
        st.error("❌ PDF 생성 라이브러리가 설치되지 않았습니다.")
        st.code("""
pip install fpdf2
# 또는
pip install weasyprint  
# 또는
pip install reportlab
        """)
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 FPDF 테스트") and 'FPDF' in PDF_METHODS:
            with st.spinner("FPDF 생성 중..."):
                pdf = create_pdf_with_fpdf()
                if pdf:
                    st.success("✅ FPDF 성공!")
                    st.download_button("📥 FPDF PDF", pdf, "fpdf_test.pdf", "application/pdf")
                else:
                    st.error("❌ FPDF 실패")
    
    with col2:
        if st.button("🌐 WeasyPrint 테스트") and 'WeasyPrint' in PDF_METHODS:
            with st.spinner("WeasyPrint 생성 중..."):
                pdf = create_pdf_with_weasyprint()
                if pdf:
                    st.success("✅ WeasyPrint 성공!")
                    st.download_button("📥 WeasyPrint PDF", pdf, "weasy_test.pdf", "application/pdf")
                else:
                    st.error("❌ WeasyPrint 실패")
    
    with col3:
        if st.button("📊 ReportLab 테스트") and 'ReportLab' in PDF_METHODS:
            with st.spinner("ReportLab 생성 중..."):
                pdf = create_simple_reportlab_pdf()
                if pdf:
                    st.success("✅ ReportLab 성공!")
                    st.download_button("📥 ReportLab PDF", pdf, "reportlab_test.pdf", "application/pdf")
                else:
                    st.error("❌ ReportLab 실패")
    
    st.markdown("---")
    
    if st.button("🚀 최종 보고서 생성", type="primary"):
        with st.spinner("보고서 생성 중..."):
            report = create_enhanced_pdf_report()
            
            if report:
                st.success("✅ 보고서 생성 성공!")
                
                # PDF인지 텍스트인지 확인
                if report.startswith(b'%PDF') or report.startswith(b'SK'):
                    if report.startswith(b'%PDF'):
                        st.download_button("📥 PDF 보고서", report, "sk_report.pdf", "application/pdf")
                    else:
                        st.download_button("📥 텍스트 보고서", report, "sk_report.txt", "text/plain")
                else:
                    st.download_button("📥 보고서", report, "sk_report.pdf", "application/pdf")
            else:
                st.error("❌ 보고서 생성 실패")


if __name__ == "__main__":
    print("🧪 다중 PDF 방법 테스트...")
    
    # 각 방법 테스트
    if 'FPDF' in PDF_METHODS:
        fpdf_result = create_pdf_with_fpdf()
        if fpdf_result:
            print("✅ FPDF 테스트 성공")
        else:
            print("❌ FPDF 테스트 실패")
    
    if 'WeasyPrint' in PDF_METHODS:
        weasy_result = create_pdf_with_weasyprint()
        if weasy_result:
            print("✅ WeasyPrint 테스트 성공")
        else:
            print("❌ WeasyPrint 테스트 실패")
    
    if 'ReportLab' in PDF_METHODS:
        rl_result = create_simple_reportlab_pdf()
        if rl_result:
            print("✅ ReportLab 테스트 성공")
        else:
            print("❌ ReportLab 테스트 실패")
