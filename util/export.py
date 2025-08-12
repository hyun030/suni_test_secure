# -*- coding: utf-8 -*-
"""
SK에너지 보고서 생성 모듈 - 완전 수정 버전
PDF 열림 오류 해결을 위한 완전한 재작성
"""

import io
import os
import pandas as pd
from datetime import datetime
import streamlit as st
import tempfile

# matplotlib 설정 (안전)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정
try:
    # Windows
    if os.name == 'nt':
        plt.rcParams['font.family'] = 'Malgun Gothic'
    else:
        # Linux/Mac - DejaVu Sans 사용
        plt.rcParams['font.family'] = 'DejaVu Sans'
except:
    plt.rcParams['font.family'] = 'Arial'

plt.rcParams['axes.unicode_minus'] = False

# ReportLab 임포트 및 초기화
REPORTLAB_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch, cm, mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
        PageBreak, Image as RLImage, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    REPORTLAB_AVAILABLE = True
    print("✅ ReportLab 로드 성공")
    
except ImportError as e:
    print(f"❌ ReportLab 로드 실패: {e}")
    REPORTLAB_AVAILABLE = False


def safe_text(text):
    """안전한 텍스트 처리"""
    if pd.isna(text):
        return ""
    
    text = str(text).strip()
    # 특수문자 제거
    replacements = {
        '\ufffd': '',
        '\u00a0': ' ',
        '\t': ' ',
        '\r\n': ' ',
        '\r': ' ',
        '\n': ' ',
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text[:100]  # 길이 제한


def setup_korean_font():
    """한글 폰트 설정"""
    font_name = "NotoSans"
    
    # 다양한 폰트 경로 시도
    font_paths = [
        # Windows
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
        # Mac
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/Arial.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                print(f"✅ 폰트 등록 성공: {font_path}")
                return font_name
        except Exception as e:
            print(f"폰트 등록 실패 {font_path}: {e}")
            continue
    
    print("⚠️ 기본 폰트 사용: Helvetica")
    return "Helvetica"


def create_sample_chart():
    """안전한 샘플 차트 생성"""
    try:
        fig, ax = plt.subplots(figsize=(8, 5))
        fig.patch.set_facecolor('white')
        
        # 간단한 막대 차트
        categories = ['SK에너지', 'S-Oil', 'GS칼텍스', 'HD현대']
        values = [15.2, 14.8, 13.5, 11.2]
        colors_list = ['#E31E24', '#FF6B6B', '#4ECDC4', '#45B7D1']
        
        bars = ax.bar(categories, values, color=colors_list, alpha=0.8)
        ax.set_title('매출액 비교 (조원)', fontsize=12, pad=20)
        ax.set_ylabel('매출액')
        
        # 값 표시
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{value}', ha='center', va='bottom')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        return fig
        
    except Exception as e:
        print(f"차트 생성 실패: {e}")
        return None


def fig_to_image_element(fig, width=400, height=250):
    """matplotlib figure를 ReportLab Image로 변환"""
    if fig is None:
        return None
    
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            fig.savefig(tmp_file.name, format='png', bbox_inches='tight', 
                       dpi=150, facecolor='white', edgecolor='none')
            tmp_file.flush()
            
            # ReportLab Image 생성
            img = RLImage(tmp_file.name, width=width, height=height)
            
            # 임시 파일 정리
            try:
                os.unlink(tmp_file.name)
            except:
                pass
                
        plt.close(fig)
        return img
        
    except Exception as e:
        print(f"이미지 변환 실패: {e}")
        try:
            plt.close(fig)
        except:
            pass
        return None


def create_simple_table(data_list, headers, font_name="Helvetica"):
    """간단한 테이블 생성"""
    try:
        if not data_list or not headers:
            return None
        
        # 테이블 데이터 준비
        table_data = [headers]
        for row in data_list:
            safe_row = [safe_text(str(cell)) for cell in row]
            table_data.append(safe_row)
        
        # 컬럼 너비 계산
        col_count = len(headers)
        total_width = 15 * cm
        col_width = total_width / col_count
        
        # 테이블 생성
        table = Table(table_data, colWidths=[col_width] * col_count)
        
        # 기본 스타일 적용
        table.setStyle(TableStyle([
            # 헤더 스타일
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E31E24')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            # 테두리
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            # 패딩
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            # 배경색 교대로
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F8F8')]),
        ]))
        
        return table
        
    except Exception as e:
        print(f"테이블 생성 실패: {e}")
        return None


def create_minimal_pdf_report():
    """최소한의 안전한 PDF 보고서 생성"""
    
    if not REPORTLAB_AVAILABLE:
        print("❌ ReportLab이 설치되지 않았습니다.")
        return None
    
    try:
        print("📄 PDF 생성 시작...")
        
        # 폰트 설정
        font_name = setup_korean_font()
        
        # 스타일 정의
        styles = getSampleStyleSheet()
        
        # 커스텀 스타일
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#E31E24')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=10,
            textColor=colors.HexColor('#333333')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=8
        )
        
        # 메모리 버퍼 생성
        buffer = io.BytesIO()
        
        # 문서 생성 (여백 충분히 설정)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=25*mm,
            rightMargin=25*mm,
            topMargin=25*mm,
            bottomMargin=25*mm,
            title="SK Energy Report"
        )
        
        # 스토리 요소들
        story = []
        
        # 제목
        story.append(Paragraph("SK에너지 경영 분석 보고서", title_style))
        story.append(Spacer(1, 20))
        
        # 기본 정보 테이블
        info_data = [
            ["작성일", datetime.now().strftime("%Y년 %m월 %d일")],
            ["보고서", "종합 경영 분석"],
            ["대상", "SK이노베이션 경영진"]
        ]
        
        info_table = create_simple_table(
            info_data, 
            ["구분", "내용"],
            font_name
        )
        
        if info_table:
            story.append(info_table)
        
        story.append(Spacer(1, 20))
        
        # 1. 재무 분석
        story.append(Paragraph("1. 재무 분석 결과", heading_style))
        
        # 재무 데이터 테이블
        financial_data = [
            ["매출액", "15.2조원", "14.8조원", "13.5조원"],
            ["영업이익률", "5.6%", "5.3%", "4.6%"],
            ["ROE", "12.3%", "11.8%", "10.5%"],
            ["ROA", "8.1%", "7.8%", "7.2%"]
        ]
        
        financial_table = create_simple_table(
            financial_data,
            ["지표", "SK에너지", "S-Oil", "GS칼텍스"],
            font_name
        )
        
        if financial_table:
            story.append(financial_table)
        
        story.append(Spacer(1, 15))
        
        # 차트 추가
        chart_fig = create_sample_chart()
        if chart_fig:
            chart_img = fig_to_image_element(chart_fig, width=350, height=220)
            if chart_img:
                story.append(chart_img)
        
        story.append(Spacer(1, 20))
        
        # 2. 분석 결과
        story.append(Paragraph("2. 주요 분석 결과", heading_style))
        
        analysis_points = [
            "• SK에너지는 매출액 기준 업계 1위 지위 유지",
            "• 영업이익률 5.6%로 경쟁사 대비 우수한 수익성 확보",
            "• ROE 12.3%로 효율적인 자본 운용 달성",
            "• 지속적인 마진 개선을 통한 경쟁 우위 확대 필요"
        ]
        
        for point in analysis_points:
            story.append(Paragraph(safe_text(point), normal_style))
        
        story.append(Spacer(1, 20))
        
        # 3. 권고사항
        story.append(Paragraph("3. 전략적 권고사항", heading_style))
        
        recommendations = [
            "• 운영 효율성 제고를 통한 원가 절감",
            "• 친환경 에너지 전환 투자 확대",
            "• 디지털 혁신을 통한 경쟁력 강화",
            "• ESG 경영 체계 구축"
        ]
        
        for rec in recommendations:
            story.append(Paragraph(safe_text(rec), normal_style))
        
        story.append(Spacer(1, 30))
        
        # 푸터
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        
        story.append(Paragraph("본 보고서는 AI 분석 시스템에서 생성되었습니다.", footer_style))
        
        # PDF 빌드
        print("📄 PDF 빌드 중...")
        doc.build(story)
        
        # 버퍼에서 데이터 가져오기
        pdf_data = buffer.getvalue()
        buffer.close()
        
        print(f"✅ PDF 생성 완료! 크기: {len(pdf_data)} bytes")
        
        if len(pdf_data) < 1000:
            print("❌ PDF 크기가 너무 작습니다.")
            return None
            
        return pdf_data
        
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_excel_report():
    """간단한 Excel 보고서 생성"""
    try:
        buffer = io.BytesIO()
        
        # 재무 데이터
        financial_df = pd.DataFrame({
            '지표': ['매출액(조원)', '영업이익률(%)', 'ROE(%)', 'ROA(%)'],
            'SK에너지': [15.2, 5.6, 12.3, 8.1],
            'S-Oil': [14.8, 5.3, 11.8, 7.8],
            'GS칼텍스': [13.5, 4.6, 10.5, 7.2],
            'HD현대오일뱅크': [11.2, 4.3, 9.2, 6.5]
        })
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            financial_df.to_excel(writer, sheet_name='재무분석', index=False)
            
            # 분석 결과 시트
            analysis_df = pd.DataFrame({
                '구분': ['매출액 순위', '영업이익률 순위', '전체 평가'],
                '결과': ['1위', '1위', '업계 최고 수준']
            })
            analysis_df.to_excel(writer, sheet_name='분석결과', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"Excel 생성 실패: {e}")
        return None


# Streamlit UI 함수
def show_report_generator():
    """보고서 생성 UI"""
    st.header("📊 SK에너지 보고서 생성기")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 PDF 보고서 생성", type="primary"):
            with st.spinner("PDF 보고서 생성 중..."):
                pdf_data = create_minimal_pdf_report()
                
                if pdf_data:
                    st.success("✅ PDF 생성 성공!")
                    
                    filename = f"SK_Energy_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    
                    st.download_button(
                        label="📥 PDF 다운로드",
                        data=pdf_data,
                        file_name=filename,
                        mime="application/pdf"
                    )
                else:
                    st.error("❌ PDF 생성에 실패했습니다.")
    
    with col2:
        if st.button("📊 Excel 보고서 생성"):
            with st.spinner("Excel 보고서 생성 중..."):
                excel_data = create_excel_report()
                
                if excel_data:
                    st.success("✅ Excel 생성 성공!")
                    
                    filename = f"SK_Energy_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    
                    st.download_button(
                        label="📥 Excel 다운로드", 
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("❌ Excel 생성에 실패했습니다.")


# 테스트 실행
if __name__ == "__main__":
    print("🧪 보고서 생성기 테스트...")
    
    # PDF 테스트
    test_pdf = create_minimal_pdf_report()
    if test_pdf and len(test_pdf) > 1000:
        print("✅ PDF 테스트 성공!")
        
        # 파일로 저장해서 확인
        with open("test_report.pdf", "wb") as f:
            f.write(test_pdf)
        print("📁 test_report.pdf 파일로 저장됨")
    else:
        print("❌ PDF 테스트 실패")
    
    # Excel 테스트  
    test_excel = create_excel_report()
    if test_excel:
        print("✅ Excel 테스트 성공!")
    else:
        print("❌ Excel 테스트 실패")
