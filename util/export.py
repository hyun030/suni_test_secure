# -*- coding: utf-8 -*-
"""
🎯 기존 fonts 폴더 사용하는 SK에너지 PDF 보고서 생성 모듈
✅ 이미 있는 NanumGothic 폰트 활용
"""

import io
import os
import pandas as pd
from datetime import datetime
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# 🔤 한글 폰트 설정 (기존 fonts 폴더 사용)
plt.rcParams['font.family'] = ['NanumGothic', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import (
        Paragraph, Table, TableStyle, Spacer, PageBreak, 
        Image as RLImage, SimpleDocTemplate
    )
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
    print("✅ ReportLab 로드 성공")
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("❌ ReportLab 없음")

def get_font_paths():
    """기존 fonts 폴더의 폰트 경로를 반환"""
    font_paths = {
        "Korean": "fonts/NanumGothic.ttf",
        "KoreanBold": "fonts/NanumGothicBold.ttf", 
        "KoreanSerif": "fonts/NanumMyeongjo.ttf"
    }
    
    # 파일 존재 여부 및 유효성 확인 후 반환
    found_fonts = {}
    for font_name, font_path in font_paths.items():
        if os.path.exists(font_path):
            file_size = os.path.getsize(font_path)
            if file_size > 0:
                found_fonts[font_name] = font_path
                print(f"✅ 폰트 발견: {font_name} = {font_path} ({file_size} bytes)")
            else:
                print(f"⚠️ 폰트 파일이 비어있음: {font_path}")
        else:
            print(f"⚠️ 폰트 파일을 찾을 수 없음: {font_path}")
    
    return found_fonts

def register_fonts():
    """기존 폰트 등록"""
    registered_fonts = {
        "Korean": "Helvetica",
        "KoreanBold": "Helvetica-Bold"
    }
    
    if not REPORTLAB_AVAILABLE:
        return registered_fonts
    
    font_paths = get_font_paths()
    
    for font_name, font_path in font_paths.items():
        try:
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font_name, font_path))
            registered_fonts[font_name] = font_name
            print(f"✅ 폰트 등록 성공: {font_name}")
        except Exception as e:
            print(f"❌ 폰트 등록 실패 {font_name}: {e}")
    
    return registered_fonts

def safe_str_convert(value):
    """안전한 문자열 변환"""
    try:
        if pd.isna(value):
            return ""
        result = str(value).strip()
        return result
    except Exception:
        return ""

def create_korean_charts():
    """한글 폰트로 차트 생성"""
    charts = {}
    
    try:
        # matplotlib 한글 폰트 설정
        font_paths = get_font_paths()
        if "Korean" in font_paths:
            plt.rcParams['font.family'] = ['NanumGothic']
        
        # 1. 매출 비교 차트
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        fig1.patch.set_facecolor('white')
        
        companies = ['SK에너지', 'S-Oil', 'GS칼텍스', 'HD현대오일뱅크']
        revenues = [15.2, 14.8, 13.5, 11.2]
        colors_list = ['#E31E24', '#FF6B6B', '#4ECDC4', '#45B7D1']
        
        bars = ax1.bar(companies, revenues, color=colors_list, alpha=0.8, width=0.6)
        ax1.set_title('매출액 비교 (조원)', fontsize=14, pad=20, weight='bold')
        ax1.set_ylabel('매출액 (조원)', fontsize=12, weight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 값 표시
        for bar, value in zip(bars, revenues):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                    f'{value}조원', ha='center', va='bottom', fontsize=11, weight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        charts['revenue_comparison'] = fig1
        
    except Exception as e:
        print(f"차트 생성 실패: {e}")
        charts['revenue_comparison'] = None
    
    try:
        # 2. ROE 비교 차트
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        fig2.patch.set_facecolor('white')
        
        companies = ['SK에너지', 'S-Oil', 'GS칼텍스', 'HD현대오일뱅크']
        roe_values = [12.3, 11.8, 10.5, 9.2]
        
        bars = ax2.bar(companies, roe_values, color='#E31E24', alpha=0.7)
        ax2.set_title('ROE 비교 (%)', fontsize=14, pad=20, weight='bold')
        ax2.set_ylabel('ROE (%)', fontsize=12, weight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 값 표시
        for bar, value in zip(bars, roe_values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                    f'{value}%', ha='center', va='bottom', fontsize=11, weight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        charts['roe_comparison'] = fig2
        
    except Exception as e:
        print(f"ROE 차트 생성 실패: {e}")
        charts['roe_comparison'] = None
    
    return charts

def safe_create_chart_image(fig, width=480, height=320):
    """안전한 차트 이미지 변환"""
    if fig is None or not REPORTLAB_AVAILABLE:
        return None
    
    try:
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight', 
                   dpi=100, facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        
        img_data = img_buffer.getvalue()
        if len(img_data) > 0:
            img_buffer.seek(0)
            img = RLImage(img_buffer, width=width, height=height)
            plt.close(fig)
            return img
        
        plt.close(fig)
        return None
        
    except Exception as e:
        print(f"차트 이미지 변환 실패: {e}")
        try:
            plt.close(fig)
        except:
            pass
        return None

def create_korean_table(registered_fonts):
    """한글 테이블 생성"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    try:
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
        
    except Exception as e:
        print(f"테이블 생성 실패: {e}")
        return None

def create_korean_news_table(registered_fonts):
    """한글 뉴스 테이블 생성"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    try:
        news_data = [
            ['제목', '날짜', '출처'],
            ['SK에너지, 3분기 실적 시장 기대치 상회', '2024-11-01', '매일경제'],
            ['정유업계, 원유가 하락으로 마진 개선 기대', '2024-10-28', '한국경제'],
            ['SK이노베이션, 배터리 사업 분할 추진', '2024-10-25', '조선일보'],
            ['에너지 전환 정책, 정유업계 영향 분석', '2024-10-22', '이데일리']
        ]
        
        col_widths = [3.5*inch, 1.5*inch, 1.5*inch]
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
        
    except Exception as e:
        print(f"뉴스 테이블 생성 실패: {e}")
        return None

def create_korean_pdf_report():
    """한글 PDF 보고서 생성 (기존 폰트 사용)"""
    
    if not REPORTLAB_AVAILABLE:
        return "ReportLab not available".encode('utf-8')
    
    try:
        # 폰트 등록
        registered_fonts = register_fonts()
        
        # 차트 생성
        charts = create_korean_charts()
        
        # 스타일 정의
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
        
        # PDF 문서 생성
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=50,
            rightMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        story = []
        
        # 제목
        story.append(Paragraph("SK에너지 경쟁사 분석 보고서", title_style))
        story.append(Spacer(1, 20))
        
        # 보고서 정보
        info_style = ParagraphStyle(
            'Info',
            fontName=registered_fonts.get('Korean', 'Helvetica'),
            fontSize=12,
            leading=16,
            alignment=1,
            spaceAfter=6
        )
        
        current_date = datetime.now().strftime('%Y년 %m월 %d일')
        story.append(Paragraph(f"보고일자: {current_date}", info_style))
        story.append(Paragraph("보고대상: SK이노베이션 경영진", info_style))
        story.append(Paragraph("보고자: AI 분석 시스템", info_style))
        story.append(Spacer(1, 30))
        
        # 핵심 요약
        story.append(Paragraph("◆ 핵심 요약", heading_style))
        story.append(Spacer(1, 10))
        
        summary_text = """SK에너지는 매출액 15.2조원으로 업계 1위를 유지하며, 영업이익률 5.6%와 ROE 12.3%를 기록하여 
        경쟁사 대비 우수한 성과를 보이고 있습니다. 최근 3분기 실적이 시장 기대치를 상회하며 긍정적 전망을 보여주고 있으나, 
        에너지 전환 정책에 대한 전략적 대응이 필요한 상황입니다."""
        
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 20))
        
        # 1. 재무분석 결과
        story.append(Paragraph("1. 재무분석 결과", heading_style))
        story.append(Spacer(1, 10))
        
        # 1-1. 주요 재무지표
        story.append(Paragraph("1-1. 주요 재무지표", heading_style))
        story.append(Spacer(1, 6))
        
        financial_table = create_korean_table(registered_fonts)
        if financial_table:
            story.append(financial_table)
        else:
            story.append(Paragraph("• SK에너지 매출액: 15.2조원 (업계 1위)", body_style))
            story.append(Paragraph("• 영업이익률: 5.6% (경쟁사 대비 우위)", body_style))
            story.append(Paragraph("• ROE: 12.3%, ROA: 8.1% (우수한 수익성)", body_style))
        
        story.append(Spacer(1, 16))
        
        # 1-2. 차트 분석
        story.append(Paragraph("1-2. 차트 분석", heading_style))
        story.append(Spacer(1, 8))
        
        # 매출 비교 차트
        if charts.get('revenue_comparison'):
            revenue_img = safe_create_chart_image(charts['revenue_comparison'], width=450, height=270)
            if revenue_img:
                story.append(Paragraph("▶ 매출액 비교", body_style))
                story.append(revenue_img)
                story.append(Spacer(1, 10))
        
        # ROE 비교 차트
        if charts.get('roe_comparison'):
            roe_img = safe_create_chart_image(charts['roe_comparison'], width=450, height=270)
            if roe_img:
                story.append(Paragraph("▶ ROE 성과 비교", body_style))
                story.append(roe_img)
                story.append(Spacer(1, 16))
        
        # 차트가 없는 경우 텍스트로 대체
        if not charts.get('revenue_comparison') and not charts.get('roe_comparison'):
            story.append(Paragraph("📊 매출 분석: SK에너지가 15.2조원으로 경쟁사 대비 우위를 보입니다", body_style))
            story.append(Paragraph("📈 수익성: ROE 12.3%로 S-Oil 대비 0.5%p, GS칼텍스 대비 1.8%p 우위", body_style))
            story.append(Spacer(1, 16))
        
        story.append(PageBreak())
        
        # 2. 뉴스 분석 결과
        story.append(Paragraph("2. 뉴스 분석 결과", heading_style))
        story.append(Spacer(1, 10))
        
        # 2-1. 주요 뉴스
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
        
        # 3. 전략 제언
        story.append(Paragraph("3. 전략 제언", heading_style))
        story.append(Spacer(1, 10))
        
        strategy_content = [
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
        
        for content in strategy_content:
            if content.strip():
                story.append(Paragraph(content, body_style))
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
        
        # PDF 빌드
        doc.build(story)
        
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        print(f"✅ 한글 PDF 생성 완료 - {len(pdf_data)} bytes")
        return pdf_data
        
    except Exception as e:
        print(f"❌ 한글 PDF 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return f"Korean PDF generation failed: {str(e)}".encode('utf-8')

def create_pdf_download_button():
    """Streamlit용 한글 PDF 다운로드 버튼"""
    if st.button("📄 한글 PDF 보고서 생성 (기존 폰트 사용)", type="primary"):
        with st.spinner("한글 PDF 생성 중... (NanumGothic 폰트 사용)"):
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
                st.info("🔤 **폰트 사용**: fonts 폴더의 NanumGothic 폰트를 사용했습니다.")
            else:
                st.error("❌ PDF 생성 실패")
                if isinstance(pdf_data, bytes):
                    st.error(f"오류: {pdf_data.decode('utf-8', errors='ignore')}")

if __name__ == "__main__":
    print("🧪 한글 PDF 테스트...")
    pdf_data = create_korean_pdf_report()
    if isinstance(pdf_data, bytes) and len(pdf_data) > 1000:
        with open("korean_test.pdf", "wb") as f:
            f.write(pdf_data)
        print("✅ 성공! korean_test.pdf 파일 확인하세요")
    else:
        print(f"❌ 실패: {pdf_data}")
