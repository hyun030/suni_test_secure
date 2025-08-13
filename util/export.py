# -*- coding: utf-8 -*-
"""
🎯 SK에너지 PDF 보고서 생성 모듈 (export.py) - 원래 버전
✅ 실제 데이터 우선 사용 + 코드 중복 제거
"""

import io
import os
import pandas as pd
from datetime import datetime
import streamlit as st
import matplotlib
matplotlib.use('Agg')  # ← 반드시 pyplot import 전에
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = ['NanumGothic', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import (
        Paragraph, Table, TableStyle, Spacer, PageBreak, 
        Image as RLImage, SimpleDocTemplate, KeepTogether
    )
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader

    REPORTLAB_AVAILABLE = True
    print("✅ ReportLab 로드 성공")
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("❌ ReportLab 없음")

# ===========================================
# 🔧 기본 유틸리티 함수들
# ===========================================

def get_font_paths():
    """기존 fonts 폴더의 폰트 경로를 반환"""
    font_paths = {
        "Korean": "fonts/NanumGothic.ttf",
        "KoreanBold": "fonts/NanumGothicBold.ttf", 
        "KoreanSerif": "fonts/NanumMyeongjo.ttf"
    }
    
    found_fonts = {}
    for font_name, font_path in font_paths.items():
        if os.path.exists(font_path):
            file_size = os.path.getsize(font_path)
            if file_size > 0:
                found_fonts[font_name] = font_path
                print(f"✅ 폰트 발견: {font_name} = {font_path} ({file_size} bytes)")
    
    return found_fonts

def register_fonts():
    """폰트 등록"""
    registered_fonts = {"Korean": "Helvetica", "KoreanBold": "Helvetica-Bold"}
    
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
        return str(value).strip()
    except:
        return ""

def get_real_data_from_session():
    """세션 상태에서 실제 데이터 가져오기"""
    financial_data = None
    news_data = None
    insights = []
    
    # 재무 데이터
    if 'financial_data' in st.session_state and st.session_state['financial_data'] is not None:
        financial_data = st.session_state['financial_data']
        print(f"✅ 세션에서 financial_data 가져옴: {financial_data.shape}")
    
    # 뉴스 데이터
    news_keys = ['google_news_data', 'news_data']
    for key in news_keys:
        if key in st.session_state and st.session_state[key] is not None:
            news_data = st.session_state[key]
            print(f"✅ 세션에서 {key} 가져옴: {news_data.shape if hasattr(news_data, 'shape') else len(news_data)}")
            break
    
    # 인사이트 데이터
    insight_keys = ['financial_insight', 'google_news_insight', 'integrated_insight', 'insights']
    for key in insight_keys:
        if key in st.session_state and st.session_state[key]:
            insight_data = st.session_state[key]
            if isinstance(insight_data, list):
                insights.extend(insight_data)
            else:
                insights.append(insight_data)
    
    print(f"📊 수집된 데이터: 재무={financial_data is not None}, 뉴스={news_data is not None}, 인사이트={len(insights)}개")
    return financial_data, news_data, insights

# ===========================================
# 📊 실제 데이터 처리 함수들
# ===========================================

def generate_real_summary(financial_data):
    """실제 재무 데이터 기반 요약 생성"""
    if financial_data is None or financial_data.empty:
        return "실제 재무 데이터가 제공되지 않았습니다."
    
    try:
        # SK에너지 컬럼 찾기
        sk_col = None
        for col in financial_data.columns:
            if 'SK' in col and col != '구분':
                sk_col = col
                break
        
        if sk_col is None:
            return f"SK에너지 데이터를 찾을 수 없습니다. (컬럼: {list(financial_data.columns)})"
        
        # 주요 지표 추출
        summary_parts = []
        
        # 매출액
        revenue_row = financial_data[financial_data['구분'].str.contains('매출', na=False)]
        if not revenue_row.empty:
            revenue = safe_str_convert(revenue_row.iloc[0][sk_col])
            summary_parts.append(f"매출액 {revenue}")
        
        # 영업이익률
        profit_row = financial_data[financial_data['구분'].str.contains('영업이익률|영업이익', na=False)]
        if not profit_row.empty:
            profit = safe_str_convert(profit_row.iloc[0][sk_col])
            summary_parts.append(f"영업이익률 {profit}")
        
        # ROE
        roe_row = financial_data[financial_data['구분'].str.contains('ROE', na=False)]
        if not roe_row.empty:
            roe = safe_str_convert(roe_row.iloc[0][sk_col])
            summary_parts.append(f"ROE {roe}")
        
        if summary_parts:
            summary = f"SK에너지는 {', '.join(summary_parts)}를 기록하며 안정적인 성과를 보이고 있습니다. (실제 DART 데이터 기반)"
        else:
            summary = "실제 재무 데이터를 수집했으나 주요 지표를 추출할 수 없습니다."
        
        return summary
        
    except Exception as e:
        print(f"요약 생성 오류: {e}")
        return f"실제 데이터 분석 중 오류가 발생했습니다: {str(e)}"

def create_real_data_table(financial_data, registered_fonts):
    """실제 재무 데이터 테이블 생성"""
    if not REPORTLAB_AVAILABLE or financial_data is None or financial_data.empty:
        return None
    
    try:
        # 원시값 컬럼 제외
        display_cols = [col for col in financial_data.columns if not col.endswith('_원시값')]
        
        # 테이블 데이터 준비
        table_data = [display_cols]  # 헤더
        
        # 데이터 행 추가 (최대 10개)
        for _, row in financial_data.head(10).iterrows():
            row_data = []
            for col in display_cols:
                value = safe_str_convert(row[col])
                # 긴 텍스트 자르기
                row_data.append(value[:20] + "..." if len(value) > 20 else value)
            table_data.append(row_data)
        
        if len(table_data) <= 1:  # 헤더만 있는 경우
            return None
        
        # 컬럼 너비 계산
        col_count = len(display_cols)
        col_width = 6.5 * inch / col_count if col_count > 0 else 1 * inch
        
        table = Table(table_data, colWidths=[col_width] * col_count)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E31E24')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), registered_fonts.get('KoreanBold', 'Helvetica-Bold')),
            ('FONTNAME', (0, 1), (-1, -1), registered_fonts.get('Korean', 'Helvetica')),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return table
        
    except Exception as e:
        print(f"실제 데이터 테이블 생성 실패: {e}")
        return None

def create_real_data_charts(financial_data):
    """실제 재무 데이터 차트 생성"""
    charts = {}
    
    if financial_data is None or financial_data.empty:
        print("⚠️ 실제 데이터 없음, 샘플 차트 사용")
        return create_sample_charts()
    
    try:
        # matplotlib 한글 폰트 설정
        font_paths = get_font_paths()
        if "Korean" in font_paths:
            plt.rcParams['font.family'] = ['NanumGothic']
        
        # 회사 컬럼 찾기 (구분 제외)
        company_cols = [col for col in financial_data.columns 
                       if col != '구분' and not col.endswith('_원시값')]
        
        if len(company_cols) == 0:
            print("⚠️ 회사 컬럼 없음, 샘플 차트 사용")
            return create_sample_charts()
        
        print(f"📊 실제 데이터 차트 생성: {company_cols}")
        
        # 1. 매출 비교 차트
        revenue_row = financial_data[financial_data['구분'].str.contains('매출', na=False)]
        if not revenue_row.empty:
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            fig1.patch.set_facecolor('white')
            
            companies = company_cols[:4]  # 최대 4개 회사
            revenues = []
            
            for company in companies:
                try:
                    value_str = safe_str_convert(revenue_row.iloc[0][company])
                    # 숫자 추출 (조원, 억원 등 단위 제거)
                    clean_value = value_str.replace('조원', '').replace('억원', '').replace(',', '').replace('%', '')
                    revenues.append(float(clean_value))
                except:
                    revenues.append(0)
            
            colors_list = ['#E31E24', '#FF6B6B', '#4ECDC4', '#45B7D1'][:len(companies)]
            
            bars = ax1.bar(companies, revenues, color=colors_list, alpha=0.8, width=0.6)
            ax1.set_title('매출액 비교 (실제 DART 데이터)', fontsize=14, pad=20, weight='bold')
            ax1.set_ylabel('매출액', fontsize=12, weight='bold')
            ax1.grid(True, alpha=0.3, axis='y')
            
            # 값 표시
            for bar, value in zip(bars, revenues):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + max(revenues)*0.01,
                        f'{value:.1f}', ha='center', va='bottom', fontsize=11, weight='bold')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            charts['revenue_comparison'] = fig1
        
        # 2. ROE 비교 차트
        roe_row = financial_data[financial_data['구분'].str.contains('ROE', na=False)]
        if not roe_row.empty:
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            fig2.patch.set_facecolor('white')
            
            companies = company_cols[:4]
            roe_values = []
            
            for company in companies:
                try:
                    value_str = safe_str_convert(roe_row.iloc[0][company])
                    clean_value = value_str.replace('%', '').replace(',', '')
                    roe_values.append(float(clean_value))
                except:
                    roe_values.append(0)
            
            bars = ax2.bar(companies, roe_values, color='#E31E24', alpha=0.7)
            ax2.set_title('ROE 비교 (실제 DART 데이터)', fontsize=14, pad=20, weight='bold')
            ax2.set_ylabel('ROE (%)', fontsize=12, weight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
            
            # 값 표시
            for bar, value in zip(bars, roe_values):
                if value > 0:
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + max(roe_values)*0.01,
                            f'{value:.1f}%', ha='center', va='bottom', fontsize=11, weight='bold')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            charts['roe_comparison'] = fig2
        
        print(f"✅ 실제 데이터 차트 생성 완료: {list(charts.keys())}")
        return charts if charts else create_sample_charts()
        
    except Exception as e:
        print(f"❌ 실제 데이터 차트 생성 실패: {e}")
        return create_sample_charts()

def create_real_news_table(news_data, registered_fonts):
    """실제 뉴스 데이터 테이블 생성"""
    if not REPORTLAB_AVAILABLE or news_data is None or news_data.empty:
        return create_sample_news_table(registered_fonts)
    
    try:
        print(f"📰 실제 뉴스 데이터 처리: {news_data.shape}")
        
        # 뉴스 컬럼 찾기
        title_col = date_col = source_col = None
        
        for col in news_data.columns:
            col_lower = col.lower()
            if title_col is None and ('제목' in col or 'title' in col_lower or 'headline' in col_lower):
                title_col = col
            elif date_col is None and ('날짜' in col or 'date' in col_lower or 'published' in col_lower):
                date_col = col
            elif source_col is None and ('출처' in col or 'source' in col_lower or 'publisher' in col_lower):
                source_col = col
        
        print(f"📰 컬럼 매핑: 제목={title_col}, 날짜={date_col}, 출처={source_col}")
        
        # 테이블 데이터 준비
        table_data = [['제목', '날짜', '출처']]
        
        # 뉴스 데이터 추가 (최대 5개)
        for idx, row in news_data.head(5).iterrows():
            title = safe_str_convert(row[title_col] if title_col else f"뉴스 #{idx+1}")[:50]
            date = safe_str_convert(row[date_col] if date_col else "날짜 없음")
            source = safe_str_convert(row[source_col] if source_col else "출처 없음")
            
            table_data.append([title, date, source])
        
        if len(table_data) <= 1:
            return create_sample_news_table(registered_fonts)
        
        col_widths = [3.5*inch, 1.5*inch, 1.5*inch]
        table = Table(table_data, colWidths=col_widths)
        
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
        
        print(f"✅ 실제 뉴스 테이블 생성: {len(table_data)-1}개 뉴스")
        return table
        
    except Exception as e:
        print(f"❌ 실제 뉴스 테이블 생성 실패: {e}")
        return create_sample_news_table(registered_fonts)

# ===========================================
# 📊 샘플 데이터 생성 함수들 (폴백용)
# ===========================================

def create_sample_charts():
    """샘플 차트 생성 (실제 데이터가 없을 때)"""
    charts = {}
    
    try:
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
        ax1.set_title('매출액 비교 (샘플 데이터)', fontsize=14, pad=20, weight='bold')
        ax1.set_ylabel('매출액 (조원)', fontsize=12, weight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        
        for bar, value in zip(bars, revenues):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                    f'{value}조원', ha='center', va='bottom', fontsize=11, weight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        charts['revenue_comparison'] = fig1
        
        # 2. ROE 비교 차트
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        fig2.patch.set_facecolor('white')
        
        roe_values = [12.3, 11.8, 10.5, 9.2]
        bars = ax2.bar(companies, roe_values, color='#E31E24', alpha=0.7)
        ax2.set_title('ROE 비교 (샘플 데이터)', fontsize=14, pad=20, weight='bold')
        ax2.set_ylabel('ROE (%)', fontsize=12, weight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        for bar, value in zip(bars, roe_values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                    f'{value}%', ha='center', va='bottom', fontsize=11, weight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        charts['roe_comparison'] = fig2
        
    except Exception as e:
        print(f"샘플 차트 생성 실패: {e}")
    
    return charts

def create_sample_table(registered_fonts):
    """샘플 재무 테이블 생성"""
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
        print(f"샘플 테이블 생성 실패: {e}")
        return None

def create_sample_news_table(registered_fonts):
    """샘플 뉴스 테이블 생성"""
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
        print(f"샘플 뉴스 테이블 생성 실패: {e}")
        return None

# ===========================================
# 🖼️ 차트 이미지 변환
# ===========================================

def safe_create_chart_image(fig, width=480, height=320):
    """안전한 차트 이미지 변환 (ImageReader 사용 + DPI 상향)"""
    if fig is None or not REPORTLAB_AVAILABLE:
        return None
    try:
        buf = io.BytesIO()
        # 선명도 확보를 위해 DPI 약간 상향
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='white', edgecolor='none')
        buf.seek(0)

        img_bytes = buf.getvalue()
        if img_bytes:
            # ReportLab이 내부적으로 안전하게 들고 있도록 ImageReader로 감싸기
            reader = ImageReader(io.BytesIO(img_bytes))  # 재읽기 안전
            img = RLImage(reader, width=width, height=height)
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

# ===========================================
# 📄 PDF 보고서 생성 (메인 함수)
# ===========================================

def generate_pdf_report(
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
    """
    PDF 보고서 생성 (통합 메인 함수)
    - 실제 데이터 우선 사용
    - 세션 상태에서 자동 데이터 수집
    - 폴백으로 샘플 데이터 사용
    """
    print(f"🚀 PDF 보고서 생성 시작")
    
    if not REPORTLAB_AVAILABLE:
        return {
            'success': False,
            'data': None,
            'error': "ReportLab이 설치되지 않았습니다. pip install reportlab을 실행하세요."
        }
    
    try:
        # 1. 데이터 수집 우선순위: 파라미터 > 세션 상태 > 샘플
        if financial_data is None or news_data is None or not insights:
            session_financial, session_news, session_insights = get_real_data_from_session()
            
            if financial_data is None:
                financial_data = session_financial
            if news_data is None:
                news_data = session_news
            if not insights:
                insights = session_insights
        
        # 2. 데이터 상태 확인
        has_real_financial = (financial_data is not None and 
                             not (hasattr(financial_data, 'empty') and financial_data.empty))
        has_real_news = (news_data is not None and 
                        not (hasattr(news_data, 'empty') and news_data.empty))
        has_insights = insights and len(insights) > 0
        
        print(f"📊 데이터 상태: 재무={has_real_financial}, 뉴스={has_real_news}, 인사이트={has_insights}")
        
        # 3. 폰트 등록
        registered_fonts = register_fonts()
        
        # 4. 스타일 정의
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
        
        info_style = ParagraphStyle(
            'Info',
            fontName=registered_fonts.get('Korean', 'Helvetica'),
            fontSize=12,
            leading=16,
            alignment=1,
            spaceAfter=6
        )
        
        # 5. PDF 문서 생성
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
        current_date = datetime.now().strftime('%Y년 %m월 %d일')
        story.append(Paragraph(f"보고일자: {current_date}", info_style))
        story.append(Paragraph(f"보고대상: {report_target}", info_style))
        story.append(Paragraph(f"보고자: {report_author}", info_style))
        story.append(Spacer(1, 30))
        
        # 핵심 요약
        story.append(Paragraph("◆ 핵심 요약", heading_style))
        story.append(Spacer(1, 10))
        
        if has_real_financial:
            summary_text = generate_real_summary(financial_data)
        else:
            summary_text = """SK에너지는 매출액 15.2조원으로 업계 1위를 유지하며, 영업이익률 5.6%와 ROE 12.3%를 기록하여 
            경쟁사 대비 우수한 성과를 보이고 있습니다. (※ 실제 데이터 미제공으로 샘플 데이터 사용)"""
        
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 20))
        
        # 섹션별 내용 생성
        section_counter = 1
        
        # 재무분석 섹션
        story.append(Paragraph(f"{section_counter}. 재무분석 결과", heading_style))
        story.append(Spacer(1, 10))
        
        if has_real_financial:
            story.append(Paragraph("※ 실제 DART에서 수집한 재무 데이터를 기반으로 분석했습니다.", body_style))
            
            # 실제 데이터 테이블
            financial_table = create_real_data_table(financial_data, registered_fonts)
            if financial_table:
                story.append(financial_table)
            else:
                story.append(Paragraph("• 재무 데이터 테이블을 생성할 수 없습니다.", body_style))
            
            # 실제 데이터 차트
            charts = create_real_data_charts(financial_data)
        else:
            story.append(Paragraph("※ 실제 재무 데이터가 제공되지 않아 샘플 데이터를 사용합니다.", body_style))
            
            # 샘플 테이블
            financial_table = create_sample_table(registered_fonts)
            if financial_table:
                story.append(financial_table)
            
            # 샘플 차트
            charts = create_sample_charts()
        
        story.append(Spacer(1, 16))
        
        # 차트 추가
        chart_added = False
        for chart_name, chart_title in [('revenue_comparison', '매출액 비교'), 
                                       ('roe_comparison', 'ROE 성과 비교')]:
            if charts.get(chart_name):
                chart_img = safe_create_chart_image(charts[chart_name], width=450, height=270)
                if chart_img:
                    data_type = "실제 DART 데이터" if has_real_financial else "샘플 데이터"
                    story.append(Paragraph(f"▶ {chart_title} ({data_type})", body_style))
                    story.append(chart_img)
                    story.append(Spacer(1, 10))
                    chart_added = True
        
        if not chart_added:
            story.append(Paragraph("📊 차트를 생성할 수 없습니다.", body_style))
        
        section_counter += 1
        
        # 뉴스 분석 섹션 (뉴스 데이터가 있을 때만)
        if has_real_news:
            story.append(PageBreak())
            story.append(Paragraph(f"{section_counter}. 뉴스 분석 결과", heading_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph("※ 실제 수집된 뉴스 데이터를 기반으로 분석했습니다.", body_style))
            
            news_table = create_real_news_table(news_data, registered_fonts)
            if news_table:
                story.append(news_table)
            else:
                story.append(Paragraph("📰 뉴스 데이터를 테이블로 변환할 수 없습니다.", body_style))
            
            story.append(Spacer(1, 16))
            section_counter += 1
        
        # AI 인사이트 섹션 (인사이트가 있을 때만)
        if has_insights:
            story.append(Paragraph(f"{section_counter}. AI 분석 인사이트", heading_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph("※ AI가 실제 데이터를 분석하여 생성한 인사이트입니다.", body_style))
            story.append(Spacer(1, 10))
            
            for i, insight in enumerate(insights[:3], 1):  # 최대 3개 인사이트
                if insight and insight.strip():
                    story.append(Paragraph(f"{section_counter}-{i}. 인사이트 #{i}", heading_style))
                    story.append(Spacer(1, 6))
                    
                    # 인사이트를 문단별로 분할
                    insight_paragraphs = insight.split('\n\n')
                    for para in insight_paragraphs[:2]:  # 최대 2개 문단
                        if para.strip():
                            # 긴 문단 자르기
                            if len(para) > 400:
                                para = para[:400] + "..."
                            story.append(Paragraph(para.strip(), body_style))
                    story.append(Spacer(1, 10))
            
            section_counter += 1
        
        # 전략 제언 (항상 포함)
        story.append(Paragraph(f"{section_counter}. 전략 제언", heading_style))
        story.append(Spacer(1, 10))
        
        strategy_content = [
            "◆ 단기 전략 (1-2년)",
            "• 운영 효율성 극대화를 통한 마진 확대에 집중",
            "• 현금 창출 능력 강화로 안정적 배당 및 투자 재원 확보",
            "",
            "◆ 중기 전략 (3-5년)", 
            "• 사업 포트폴리오 다각화 및 신사업 진출 검토",
            "• 디지털 전환과 공정 혁신을 통한 경쟁력 강화"
        ]
        
        for content in strategy_content:
            if content.strip():
                story.append(Paragraph(content, body_style))
            else:
                story.append(Spacer(1, 6))
        
        # Footer
        if show_footer:
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
        
        # 성공 결과 반환
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SK에너지_분석보고서_{timestamp}.pdf"
        
        data_status = []
        if has_real_financial:
            data_status.append("실제 재무데이터")
        if has_real_news:
            data_status.append("실제 뉴스데이터")
        if has_insights:
            data_status.append("AI 인사이트")
        
        message = f"✅ PDF 생성 완료! ({', '.join(data_status) if data_status else '샘플 데이터'} 사용)"
        
        print(f"✅ PDF 생성 성공 - {len(pdf_data)} bytes, {message}")
        
        return {
            'success': True,
            'data': pdf_data,
            'filename': filename,
            'mime': 'application/pdf',
            'message': message
        }
        
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        import traceback
        return {
            'success': False,
            'data': None,
            'error': f"PDF 생성 오류: {str(e)}",
            'traceback': traceback.format_exc()
        }

# ===========================================
# 🔧 Excel 보고서 생성
# ===========================================

def create_excel_report(
    financial_data=None,
    news_data=None,
    insights=None,
    **kwargs
):
    """Excel 보고서 생성"""
    print(f"📊 Excel 보고서 생성 시작")
    
    try:
        # 데이터 수집
        if financial_data is None or news_data is None:
            session_financial, session_news, session_insights = get_real_data_from_session()
            if financial_data is None:
                financial_data = session_financial
            if news_data is None:
                news_data = session_news
            if not insights:
                insights = session_insights
        
        buffer = io.BytesIO()
        
        # 실제 데이터 또는 샘플 데이터 사용
        if financial_data is not None and not financial_data.empty:
            sample_data = financial_data
            data_type = "실제 DART 데이터"
        else:
            sample_data = pd.DataFrame({
                '구분': ['매출액(조원)', '영업이익률(%)', 'ROE(%)', 'ROA(%)'],
                'SK에너지': [15.2, 5.6, 12.3, 8.1],
                'S-Oil': [14.8, 5.3, 11.8, 7.8],
                'GS칼텍스': [13.5, 4.6, 10.5, 7.2],
                'HD현대오일뱅크': [11.2, 4.3, 9.2, 6.5]
            })
            data_type = "샘플 데이터"
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # 재무분석 시트
            sample_data.to_excel(writer, sheet_name='재무분석', index=False)
            
            # 뉴스 데이터 시트
            if news_data is not None and not news_data.empty:
                news_data.to_excel(writer, sheet_name='뉴스분석', index=False)
            
            # 인사이트 시트
            if insights:
                insights_df = pd.DataFrame({'인사이트': insights})
                insights_df.to_excel(writer, sheet_name='AI인사이트', index=False)
        
        buffer.seek(0)
        excel_data = buffer.getvalue()
        buffer.close()
        
        print(f"✅ Excel 생성 완료 ({data_type}) - {len(excel_data)} bytes")
        return excel_data
        
    except Exception as e:
        print(f"❌ Excel 생성 실패: {e}")
        error_msg = f"Excel 생성 실패: {str(e)}"
        return error_msg.encode('utf-8')

# ===========================================
# 🎛️ Streamlit 인터페이스 함수들
# ===========================================

def handle_pdf_generation_button(
    button_clicked,
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
    """
    메인 코드의 버튼 클릭시 호출하는 함수
    """
    if not button_clicked:
        return None
        
    with st.spinner("한글 PDF 생성 중... (실제 데이터 우선 사용)"):
        result = generate_pdf_report(
            financial_data=financial_data,
            news_data=news_data,
            insights=insights,
            quarterly_df=quarterly_df,
            chart_df=chart_df,
            gap_analysis_df=gap_analysis_df,
            report_target=report_target,
            report_author=report_author,
            show_footer=show_footer,
            **kwargs
        )
        
        if result['success']:
            # 성공시 다운로드 버튼 표시
            st.download_button(
                label="📥 PDF 다운로드",
                data=result['data'],
                file_name=result['filename'],
                mime=result['mime'],
                type="secondary"
            )
            st.success(result['message'])
            st.info("🔤 **폰트**: fonts 폴더의 NanumGothic 폰트 사용")
            
            # 세션에 저장
            st.session_state.generated_file = result['data']
            st.session_state.generated_filename = result['filename']
            st.session_state.generated_mime = result['mime']
            
            return True
        else:
            # 실패시 에러 표시
            st.error(f"❌ {result['error']}")
            if 'traceback' in result:
                with st.expander("상세 오류"):
                    st.code(result['traceback'])
            return False

# ===========================================
# 🔄 기존 함수명 호환성 (메인 코드 연동용)
# ===========================================

def create_enhanced_pdf_report(*args, **kwargs):
    """기존 함수명 호환용 (메인 코드에서 사용)"""
    result = generate_pdf_report(*args, **kwargs)
    if result['success']:
        return result['data']
    else:
        return result['error'].encode('utf-8')

# ===========================================
# 🧪 테스트 함수들
# ===========================================

def test_integration():
    """통합 테스트"""
    print("🧪 통합 테스트 시작...")
    
    # 1. 함수 존재 확인
    functions_to_test = [
        'generate_pdf_report',
        'create_enhanced_pdf_report',
        'create_excel_report', 
        'handle_pdf_generation_button'
    ]
    
    for func_name in functions_to_test:
        if func_name in globals():
            print(f"✅ {func_name} 함수 존재")
        else:
            print(f"❌ {func_name} 함수 없음")
    
    # 2. PDF 생성 테스트
    try:
        result = generate_pdf_report()
        if result['success']:
            print(f"✅ PDF 생성 테스트 성공 - {len(result['data'])} bytes")
        else:
            print(f"❌ PDF 생성 테스트 실패 - {result['error']}")
    except Exception as e:
        print(f"❌ PDF 생성 테스트 오류: {e}")
    
    # 3. Excel 생성 테스트
    try:
        excel_data = create_excel_report()
        if isinstance(excel_data, bytes) and len(excel_data) > 100:
            print(f"✅ Excel 생성 테스트 성공 - {len(excel_data)} bytes")
        else:
            print(f"❌ Excel 생성 테스트 실패")
    except Exception as e:
        print(f"❌ Excel 생성 테스트 오류: {e}")
    
    # 4. 폰트 테스트
    try:
        font_paths = get_font_paths()
        registered_fonts = register_fonts()
        print(f"✅ 폰트 테스트 완료 - 발견: {len(font_paths)}개, 등록: {len(registered_fonts)}개")
    except Exception as e:
        print(f"❌ 폰트 테스트 오류: {e}")
    
    print("🏁 통합 테스트 완료")

# ===========================================
# 🚀 메인 실행부
# ===========================================

if __name__ == "__main__":
    print("🚀 정리된 SK에너지 PDF 보고서 생성 모듈")
    print("=" * 50)
    
    # 환경 확인
    print("📋 환경 확인:")
    print(f"  - ReportLab: {'✅' if REPORTLAB_AVAILABLE else '❌'}")
    print(f"  - 폰트: {'✅ ' + str(len(get_font_paths())) + '개' if get_font_paths() else '❌'}")
    
    # Streamlit 환경 확인
    try:
        if 'streamlit' in st.__module__:
            print("🌐 Streamlit 환경에서 실행")
            st.title("🏢 SK에너지 분석 보고서 생성기 (정리된 버전)")
            st.markdown("---")
            
            # 기본 정보 입력
            col1, col2 = st.columns(2)
            with col1:
                report_target = st.text_input("보고 대상", value="SK이노베이션 경영진")
            with col2:
                report_author = st.text_input("보고자", value="AI 분석 시스템")
            
            # PDF 생성 버튼
            if st.button("📄 PDF 보고서 생성", type="primary"):
                success = handle_pdf_generation_button(
                    button_clicked=True,
                    report_target=report_target,
                    report_author=report_author
                )
            
            # 테스트 버튼
            if st.button("🧪 통합 테스트"):
                with st.spinner("테스트 중..."):
                    test_integration()
                    st.success("✅ 테스트 완료! 콘솔 확인")
        else:
            print("💻 일반 Python 환경에서 실행")
            test_integration()
    except:
        print("💻 일반 Python 환경에서 실행")
        test_integration()
    
    print("=" * 50)
    print("✅ 정리된 모듈 로드 완료!")
    print("""
📖 메인 코드 연동 방법:

from export import handle_pdf_generation_button, generate_pdf_report

# 방법 1: 버튼 핸들러
if st.button("PDF 생성"):
    handle_pdf_generation_button(True, financial_data=df, news_data=news_df)

# 방법 2: 직접 생성
result = generate_pdf_report(financial_data=df, news_data=news_df, insights=insights)
    """)
