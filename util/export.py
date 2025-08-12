# -*- coding: utf-8 -*-
"""
SK에너지 보고서 생성기 - 단계별 디버그 버전
PDF 오류 원인을 찾기 위한 최소 기능부터 시작
"""

import io
import os
import pandas as pd
from datetime import datetime
import streamlit as st

# ReportLab 기본만 사용
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    REPORTLAB_OK = True
    print("✅ ReportLab 기본 기능 로드")
except ImportError:
    REPORTLAB_OK = False
    print("❌ ReportLab 없음")


def create_minimal_pdf():
    """최소한의 PDF 생성 - canvas만 사용"""
    if not REPORTLAB_OK:
        return b"No ReportLab"
    
    try:
        print("📄 최소 PDF 생성...")
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # 가장 기본적인 텍스트만
        c.setFont("Helvetica", 16)
        c.drawString(100, height-100, "SK Energy Report")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, height-130, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        
        c.setFont("Helvetica", 10)
        y = height - 180
        
        lines = [
            "1. Financial Analysis",
            "   - Revenue: 15.2 trillion KRW",
            "   - Operating Margin: 5.6%",
            "   - ROE: 12.3%",
            "",
            "2. Key Insights",
            "   - Market leading position maintained",
            "   - Strong profitability vs competitors",
            "   - Efficient capital utilization",
            "",
            "3. Recommendations",
            "   - Enhance operational efficiency",
            "   - Expand green energy investments",
            "   - Strengthen digital transformation"
        ]
        
        for line in lines:
            c.drawString(100, y, line)
            y -= 15
        
        c.save()
        pdf_data = buffer.getvalue()
        buffer.close()
        
        print(f"✅ 최소 PDF 완료: {len(pdf_data)} bytes")
        return pdf_data
        
    except Exception as e:
        print(f"❌ 최소 PDF 실패: {e}")
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
    """메인 함수 - 일단 최소 PDF로 대체"""
    
    print("📄 Enhanced PDF 요청 - 최소 버전으로 생성")
    
    # 일단 최소 PDF로 대체
    minimal_pdf = create_minimal_pdf()
    
    if minimal_pdf and len(minimal_pdf) > 100:
        return minimal_pdf
    
    # 최소 PDF도 실패하면 수동으로 생성
    try:
        print("📄 수동 PDF 생성 시도...")
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        c.setFont("Helvetica", 14)
        c.drawString(50, 750, "SK Energy Analysis Report")
        c.drawString(50, 720, "Emergency PDF Generation")
        c.drawString(50, 690, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        c.setFont("Helvetica", 10)
        c.drawString(50, 650, "Financial Data:")
        c.drawString(70, 630, "- Revenue: 15.2T KRW")
        c.drawString(70, 610, "- Operating Margin: 5.6%")
        c.drawString(70, 590, "- ROE: 12.3%")
        
        c.drawString(50, 550, "Status: PDF generation debugging in progress")
        
        c.save()
        return buffer.getvalue()
        
    except Exception as e:
        print(f"❌ 수동 PDF도 실패: {e}")
        # 최후의 수단 - 바이트 직접 생성
        return b'%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>\nendobj\n4 0 obj\n<</Length 44>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000207 00000 n \ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n299\n%%EOF'


def create_excel_report(
    financial_data=None,
    news_data=None,
    insights=None,
    **kwargs
):
    """Excel 보고서 생성"""
    try:
        buffer = io.BytesIO()
        
        # 기본 데이터
        data = {
            'SK에너지': [15.2, 5.6, 12.3, 8.1],
            'S-Oil': [14.8, 5.3, 11.8, 7.8],
            'GS칼텍스': [13.5, 4.6, 10.5, 7.2]
        }
        
        df = pd.DataFrame(data, index=['매출액(조원)', '영업이익률(%)', 'ROE(%)', 'ROA(%)'])
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='재무분석')
            
            if insights:
                insight_df = pd.DataFrame({'인사이트': [str(insights)]})
                insight_df.to_excel(writer, sheet_name='AI인사이트', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"Excel 생성 실패: {e}")
        return None


def debug_pdf_creation():
    """PDF 생성 디버그"""
    print("🔍 PDF 생성 디버그 시작...")
    
    # 1단계: ReportLab 확인
    if not REPORTLAB_OK:
        print("❌ ReportLab 설치 필요")
        return None
    
    # 2단계: 최소 PDF 테스트
    minimal = create_minimal_pdf()
    if minimal:
        print(f"✅ 최소 PDF 성공: {len(minimal)} bytes")
        
        # 파일로 저장해서 테스트
        try:
            with open("debug_minimal.pdf", "wb") as f:
                f.write(minimal)
            print("✅ debug_minimal.pdf 파일 생성됨")
        except Exception as e:
            print(f"❌ 파일 저장 실패: {e}")
        
        return minimal
    else:
        print("❌ 최소 PDF도 실패")
        return None


# Streamlit UI
def show_debug_interface():
    """디버그 인터페이스"""
    st.header("🔍 PDF 생성 디버그")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧪 최소 PDF 테스트"):
            with st.spinner("최소 PDF 생성 중..."):
                test_pdf = create_minimal_pdf()
                
                if test_pdf and len(test_pdf) > 100:
                    st.success(f"✅ 최소 PDF 성공! 크기: {len(test_pdf)} bytes")
                    
                    st.download_button(
                        "📥 최소 PDF 다운로드",
                        data=test_pdf,
                        file_name="minimal_test.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("❌ 최소 PDF 실패")
    
    with col2:
        if st.button("📄 보고서 PDF 생성"):
            with st.spinner("보고서 PDF 생성 중..."):
                report_pdf = create_enhanced_pdf_report()
                
                if report_pdf and len(report_pdf) > 100:
                    st.success(f"✅ 보고서 PDF 성공! 크기: {len(report_pdf)} bytes")
                    
                    st.download_button(
                        "📥 보고서 PDF 다운로드", 
                        data=report_pdf,
                        file_name="sk_report_debug.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("❌ 보고서 PDF 실패")
    
    st.markdown("---")
    st.subheader("💡 디버그 정보")
    
    if REPORTLAB_OK:
        st.success("✅ ReportLab 사용 가능")
    else:
        st.error("❌ ReportLab 설치 필요")
        st.code("pip install reportlab")


# 테스트 실행
if __name__ == "__main__":
    print("🧪 PDF 디버그 테스트...")
    result = debug_pdf_creation()
    
    if result:
        print("✅ 디버그 성공")
    else:
        print("❌ 디버그 실패 - 환경 점검 필요")
