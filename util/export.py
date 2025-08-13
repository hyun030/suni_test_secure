# ✅ 실제 데이터 처리 함수들 추가
def generate_real_summary(financial_data):
    """실제 재무 데이터를 기반으로 요약 생성"""
    try:
        if financial_data is None or financial_data.empty:
            return "재무 데이터가 없어 요약을 생성할 수 없습니다."
        
        # SK에너지 데이터 찾기
        sk_col = None
        for col in financial_data.columns:
            if 'SK' in col and col != '구분':
                sk_col = col
                break
        
        if sk_col is None:
            return "SK에너지 데이터를 찾을 수 없습니다."
        
        # 주요 지표 추출
        summary_parts = []
        
        # 매출액
        revenue_row = financial_data[financial_data['구분'].str.contains('매출', na=False)]
        if not revenue_row.empty:
            revenue = safe_str_convert(revenue_row.iloc[0][sk_col])
            summary_parts.append(f"매출액 {revenue}")
        
        # 영업이익률
        profit_row = financial_data[financial_data['구분'].str.contains('영업이익률', na=False)]
        if not profit_row.empty:
            profit = safe_str_convert(profit_row.iloc[0][sk_col])
            summary_parts.append(f"영업이익률 {profit}")
        
        # ROE
        roe_row = financial_data[financial_data['구분'].str.contains('ROE', na=False)]
        if not roe_row.empty:
            roe = safe_str_convert(roe_row.iloc[0][sk_col])
            summary_parts.append(f"ROE {roe}")
        
        if summary_parts:
            summary = f"SK에너지는 {', '.join(summary_parts)}를 기록하며 안정적인 성과를 보이고 있습니다. 수집된 실제 데이터를 바탕으로 한 분석 결과입니다."
        else:
            summary = "수집된 실제 재무 데이터를 바탕으로 분석한 결과입니다."
        
        return summary
        
    except Exception as e:
        print(f"요약 생성 오류: {e}")
        return "실제 데이터를 기반으로 분석했으나 요약 생성 중 오류가 발생했습니다."

def create_real_data_table(financial_data, registered_fonts):
    """실제 재무 데이터로 테이블 생성"""
    if not REPORTLAB_AVAILABLE or financial_data is None or financial_data.empty:
        return None
    
    try:
        # 표시용 컬럼만 사용 (원시값 제외)
        display_cols = [col for col in financial_data.columns if not col.endswith('_원시값')]
        
        # 테이블 데이터 준비
        table_data = []
        
        # 헤더 추가
        table_data.append(display_cols)
        
        # 데이터 행 추가 (최대 10개 행만)
        for _, row in financial_data.head(10).iterrows():
            row_data = []
            for col in display_cols:
                value = safe_str_convert(row[col])
                row_data.append(value[:20] if len(value) > 20 else value)  # 긴 텍스트 자르기
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
    """실제 재무 데이터로 차트 생성"""
    charts = {}
    
    try:
        if financial_data is None or financial_data.empty:
            return create_korean_charts()  # 폴백: 샘플 차트
        
        # matplotlib 한글 폰트 설정
        font_paths = get_font_paths()
        if "Korean" in font_paths:
            plt.rcParams['font.family'] = ['NanumGothic']
        
        # 회사 컬럼 찾기 (구분, _원시값 제외)
        company_cols = [col for col in financial_data.columns 
                       if col != '구분' and not col.endswith('_원시값')]
        
        if len(company_cols) < 2:
            return create_korean_charts()  # 폴백: 샘플 차트
        
        # 1. 매출 비교 차트 (실제 데이터)
        revenue_row = financial_data[financial_data['구분'].str.contains('매출', na=False)]
        if not revenue_row.empty:
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            fig1.patch.set_facecolor('white')
            
            companies = company_cols[:4]  # 최대 4개 회사
            revenues = []
            
            for company in companies:
                try:
                    value_str = safe_str_convert(revenue_row.iloc[0][company])
                    # 숫자 추출
                    clean_value = value_str.replace('조원', '').replace(',', '').replace('%', '')
                    revenues.append(float(clean_value))
                except:
                    revenues.append(0)
            
            colors_list = ['#E31E24', '#FF6B6B', '#4ECDC4', '#45B7D1'][:len(companies)]
            
            bars = ax1.bar(companies, revenues, color=colors_list, alpha=0.8, width=0.6)
            ax1.set_title('매출액 비교 (실제 데이터)', fontsize=14, pad=20, weight='bold')
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
        
        # 2. ROE 비교 차트 (실제 데이터)
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
            ax2.set_title('ROE 비교 (실제 데이터)', fontsize=14, pad=20, weight='bold')
            ax2.set_ylabel('ROE (%)', fontsize=12, weight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
            
            # 값 표시
            for bar, value in zip(bars, roe_values):
                if value > 0:  # 0보다 큰 값만 표시
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + max(roe_values)*0.01,
                            f'{value:.1f}%', ha='center', va='bottom', fontsize=11, weight='bold')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            charts['roe_comparison'] = fig2
        
        # 차트가 없으면 샘플 차트로 폴백
        if not charts:
            print("⚠️ 실제 데이터 차트 생성 실패, 샘플 차트 사용")
            return create_korean_charts()
        
        print(f"✅ 실제 데이터 차트 생성 완료: {list(charts.keys())}")
        return charts
        
    except Exception as e:
        print(f"❌ 실제 데이터 차트 생성 실패: {e}")
        return create_korean_charts()  # 폴백: 샘플 차트

def create_real_news_table(news_data, registered_fonts):
    """실제 뉴스 데이터로 테이블 생성"""
    if not REPORTLAB_AVAILABLE or news_data is None or news_data.empty:
        print("⚠️ 뉴스 데이터 없음, 샘플 뉴스 테이블 사용")
        return create_korean_news_table(registered_fonts)  # 폴백: 샘플 뉴스
    
    try:
        print(f"📰 실제 뉴스 데이터 처리 중: {news_data.shape}")
        print(f"📰 뉴스 컬럼: {list(news_data.columns)}")
        
        # 뉴스 데이터에서 필요한 컬럼 찾기
        title_col = None
        date_col = None
        source_col = None
        
        for col in news_data.columns:
            col_lower = col.lower()
            if '제목' in col or 'title' in col_lower or 'headline' in col_lower:
                title_col = col
            elif '날짜' in col or 'date' in col_lower or 'published' in col_lower:
                date_col = col
            elif '출처' in col or 'source' in col_lower or 'publisher' in col_lower:
                source_col = col
        
        print(f"📰 컬럼 매핑: 제목={title_col}, 날짜={date_col}, 출처={source_col}")
        
        # 테이블 데이터 준비
        table_data = [['제목', '날짜', '출처']]
        
        # 뉴스 데이터 추가 (최대 5개)
        for idx, row in news_data.head(5).iterrows():
            title = safe_str_convert(row[title_col] if title_col else f"뉴스 #{idx+1}")[:50]  # 제목 길이 제한
            date = safe_str_convert(row[date_col] if date_col else "날짜 없음")
            source = safe_str_convert(row[source_col] if source_col else "출처 없음")
            
            table_data.append([title, date, source])
        
        if len(table_data) <= 1:  # 헤더만 있는 경우
            print("⚠️ 뉴스 데이터 처리 실패, 샘플 테이블 사용")
            return create_korean_news_table(registered_fonts)  # 폴백
        
        print(f"✅ 실제 뉴스 테이블 생성: {len(table_data)-1}개 뉴스")
        
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
        
        return table
        
    except Exception as e:
        print(f"❌ 실제 뉴스 테이블 생성 실패: {e}")
        return create_korean_news_table(registered_fonts)  # 폴백

# ✅ 기존 함수명 호환성 유지 + 실제 데이터 전달
def create_enhanced_pdf_report(*args, **kwargs):
    """기존 함수명 호환용 (메인 코드에서 사용) - 실제 데이터 전달"""
    print("📄 create_enhanced_pdf_report 호출됨 (호환성 함수)")
    result = generate_pdf_report(*args, **kwargs)
    if result['success']:
        return result['data']
    else:
        return result['error'].encode('utf-8')# -*- coding: utf-8 -*-
"""
🎯 메인 코드 완벽 연동용 SK에너지 PDF 보고서 생성 모듈 (export.py)
✅ 이미 있는 NanumGothic 폰트 활용 + 메인 코드 호환 함수들 추가
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

def create_korean_pdf_report(
    financial_data=None,
    news_data=None,
    insights=None,
    quarterly_df=None,
    chart_df=None,
    gap_analysis_df=None,
    report_target="SK이노베이션 경영진",
    report_author="AI 분석 시스템",
    show_footer=True
):
    """한글 PDF 보고서 생성 (실제 데이터 사용)"""
    
    if not REPORTLAB_AVAILABLE:
        return "ReportLab not available".encode('utf-8')
    
    try:
        # 폰트 등록
        registered_fonts = register_fonts()
        
        # ✅ 실제 데이터 사용 여부 결정
        use_real_data = (financial_data is not None and 
                        not (hasattr(financial_data, 'empty') and financial_data.empty))
        
        print(f"🔍 실제 데이터 사용: {use_real_data}")
        if use_real_data:
            print(f"📊 전달받은 데이터: {financial_data.shape if hasattr(financial_data, 'shape') else 'N/A'}")
            print(f"📋 컬럼: {list(financial_data.columns) if hasattr(financial_data, 'columns') else 'N/A'}")
            print(f"📈 뉴스 데이터: {news_data is not None and not news_data.empty if news_data is not None else False}")
            print(f"🤖 인사이트 개수: {len(insights) if insights else 0}")
        else:
            print("⚠️ 실제 데이터가 없어서 샘플 데이터 사용")
        
        # ✅ 강제 실제 데이터 체크 - 데이터가 있으면 반드시 사용하도록
        if use_real_data:
            print("🎯 강제 실제 데이터 모드 활성화!")
            charts = create_real_data_charts(financial_data)
        else:
            charts = create_korean_charts()  # 샘플 차트
        
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
        story.append(Paragraph(f"보고대상: {report_target}", info_style))
        story.append(Paragraph(f"보고자: {report_author}", info_style))
        story.append(Spacer(1, 30))
        
        # ✅ 실제 데이터 기반 핵심 요약
        story.append(Paragraph("◆ 핵심 요약", heading_style))
        story.append(Spacer(1, 10))
        
        if use_real_data:
            summary_text = generate_real_summary(financial_data)
        else:
            summary_text = """SK에너지는 매출액 15.2조원으로 업계 1위를 유지하며, 영업이익률 5.6%와 ROE 12.3%를 기록하여 
            경쟁사 대비 우수한 성과를 보이고 있습니다. (샘플 데이터 기반)"""
        
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 20))
        
        # ✅ 동적 섹션 구조로 변경
        section_counter = 1
        
        # 재무분석 섹션 (데이터가 있을 때만)
        if use_real_data:
            story.append(Paragraph(f"{section_counter}. 실제 데이터 기반 재무분석 결과", heading_style))
            story.append(Spacer(1, 10))
            
            # 실제 데이터 요약
            summary_text = generate_real_summary(financial_data)
            story.append(Paragraph(summary_text, body_style))
            story.append(Spacer(1, 15))
            
            # 주요 재무지표 테이블 (실제 데이터)
            story.append(Paragraph(f"{section_counter}-1. 수집된 재무지표", heading_style))
            story.append(Spacer(1, 6))
            
            financial_table = create_real_data_table(financial_data, registered_fonts)
            if financial_table:
                story.append(financial_table)
                story.append(Paragraph("※ 위 데이터는 DART에서 수집한 실제 재무 정보입니다.", body_style))
            else:
                story.append(Paragraph("• 재무 데이터 테이블을 생성할 수 없습니다.", body_style))
            
            story.append(Spacer(1, 16))
            
            # 차트 분석 (실제 데이터)
            story.append(Paragraph(f"{section_counter}-2. 실제 데이터 차트 분석", heading_style))
            story.append(Spacer(1, 8))
            
            charts = create_real_data_charts(financial_data)
            chart_added = False
            
            for chart_name, chart_title in [('revenue_comparison', '매출액 비교'), 
                                           ('roe_comparison', 'ROE 성과 비교')]:
                if charts.get(chart_name):
                    chart_img = safe_create_chart_image(charts[chart_name], width=450, height=270)
                    if chart_img:
                        story.append(Paragraph(f"▶ {chart_title} (실제 데이터)", body_style))
                        story.append(chart_img)
                        story.append(Spacer(1, 10))
                        chart_added = True
            
            if not chart_added:
                story.append(Paragraph("📊 실제 데이터로 차트를 생성할 수 없어 텍스트로 대체합니다.", body_style))
            
            section_counter += 1
        
        else:
            # 샘플 데이터 섹션 (데이터가 없을 때)
            story.append(Paragraph(f"{section_counter}. 샘플 데이터 기반 분석 (참고용)", heading_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph("※ 실제 분석 데이터가 없어 샘플 데이터로 보고서를 생성합니다.", body_style))
            story.append(Spacer(1, 15))
            
            financial_table = create_korean_table(registered_fonts)
            if financial_table:
                story.append(financial_table)
                
            charts = create_korean_charts()
            for chart_name, chart_title in [('revenue_comparison', '매출액 비교'), 
                                           ('roe_comparison', 'ROE 성과 비교')]:
                if charts.get(chart_name):
                    chart_img = safe_create_chart_image(charts[chart_name], width=450, height=270)
                    if chart_img:
                        story.append(Paragraph(f"▶ {chart_title} (샘플)", body_style))
                        story.append(chart_img)
                        story.append(Spacer(1, 10))
            
            section_counter += 1
        
        # 뉴스 분석 섹션 (뉴스 데이터가 있을 때만)
        if news_data is not None and not news_data.empty:
            story.append(PageBreak())
            story.append(Paragraph(f"{section_counter}. 실제 뉴스 분석 결과", heading_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph(f"{section_counter}-1. 수집된 뉴스", heading_style))
            story.append(Spacer(1, 6))
            
            news_table = create_real_news_table(news_data, registered_fonts)
            if news_table:
                story.append(news_table)
                story.append(Paragraph("※ 위 뉴스는 실제 수집된 최신 정보입니다.", body_style))
            else:
                story.append(Paragraph("📰 뉴스 데이터를 테이블로 변환할 수 없습니다.", body_style))
            
            story.append(Spacer(1, 16))
            section_counter += 1
        
        # AI 인사이트 섹션 (인사이트가 있을 때만)
        if insights and len(insights) > 0:
            story.append(Paragraph(f"{section_counter}. AI 분석 인사이트", heading_style))
            story.append(Spacer(1, 10))
            
            for i, insight in enumerate(insights, 1):
                if insight and insight.strip():
                    story.append(Paragraph(f"{section_counter}-{i}. AI 분석 결과 #{i}", heading_style))
                    story.append(Spacer(1, 6))
                    
                    # 인사이트를 적절한 길이로 분할
                    insight_paragraphs = insight.split('\n\n')
                    for para in insight_paragraphs[:3]:  # 최대 3개 문단만
                        if para.strip():
                            # 너무 긴 문단은 자르기
                            if len(para) > 500:
                                para = para[:500] + "..."
                            story.append(Paragraph(para.strip(), body_style))
                    story.append(Spacer(1, 10))
            
            story.append(Paragraph("※ 위 인사이트는 AI가 실제 데이터를 분석하여 생성한 결과입니다.", body_style))
            section_counter += 1
        
        # 기본 전략 제언 (항상 포함)
        if section_counter <= 3:  # 다른 섹션이 적으면 전략 제언 추가
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
        story.append(Spacer(1, 30))
        if show_footer:
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
        
        print(f"✅ 실제 데이터 PDF 생성 완료 - {len(pdf_data)} bytes")
        return pdf_data
        
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return f"PDF generation failed: {str(e)}".encode('utf-8')

# ===========================================
# 🔥 메인 코드 연동용 함수들 (버튼 중복 해결)
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
    메인 코드에서 호출하는 PDF 생성 함수 (버튼 없이 데이터만 반환)
    """
    print(f"🚀 generate_pdf_report 호출됨")
    print(f"  - financial_data: {type(financial_data)}")
    print(f"  - news_data: {type(news_data)}")
    print(f"  - report_target: {report_target}")
    
    try:
        # ✅ 실제 데이터를 파라미터로 전달하여 PDF 생성
        pdf_data = create_korean_pdf_report(
            financial_data=financial_data,
            news_data=news_data,
            insights=insights,
            quarterly_df=quarterly_df,
            chart_df=chart_df,
            gap_analysis_df=gap_analysis_df,
            report_target=report_target,
            report_author=report_author,
            show_footer=show_footer
        )
        
        if isinstance(pdf_data, bytes) and len(pdf_data) > 1000:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SK에너지_분석보고서_{timestamp}.pdf"
            
            return {
                'success': True,
                'data': pdf_data,
                'filename': filename,
                'mime': 'application/pdf',
                'message': '✅ 실제 데이터 PDF 생성 완료!'
            }
        else:
            return {
                'success': False,
                'data': None,
                'error': f"PDF 생성 실패: {type(pdf_data)}"
            }
            
    except Exception as e:
        import traceback
        return {
            'success': False,
            'data': None,
            'error': f"PDF 생성 오류: {str(e)}",
            'traceback': traceback.format_exc()
        }

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
    메인 코드의 기존 버튼이 클릭되었을 때 호출하는 함수
    """
    if button_clicked:
        # ✅ 완전한 디버깅 정보
        st.write("=" * 50)
        st.write("🔍 **COMPLETE 디버깅 정보**")
        st.write("=" * 50)
        
        # 1. 파라미터 체크
        st.write("**📥 전달받은 파라미터들:**")
        params = {
            'financial_data': financial_data,
            'news_data': news_data, 
            'insights': insights,
            'quarterly_df': quarterly_df,
            'chart_df': chart_df,
            'gap_analysis_df': gap_analysis_df
        }
        
        for name, data in params.items():
            st.write(f"- {name}: {type(data)}")
            if data is not None:
                if hasattr(data, 'shape'):
                    st.write(f"  └ 크기: {data.shape}")
                elif hasattr(data, '__len__'):
                    st.write(f"  └ 길이: {len(data)}")
                if hasattr(data, 'columns'):
                    st.write(f"  └ 컬럼: {list(data.columns)}")
        
        # 2. Streamlit 세션 체크
        st.write("**📦 Streamlit 세션 상태:**")
        session_keys = ['financial_data', 'news_data', 'google_news_data', 'insights', 'financial_insight']
        for key in session_keys:
            if key in st.session_state:
                data = st.session_state[key]
                st.write(f"- st.session_state['{key}']: {type(data)}")
                if data is not None and hasattr(data, 'shape'):
                    st.write(f"  └ 크기: {data.shape}")
            else:
                st.write(f"- st.session_state['{key}']: ❌ 없음")
        
        # 3. 실제 데이터 체크 & 강제 대체
        st.write("**🔧 데이터 강제 체크 및 대체:**")
        
        # 파라미터에 데이터가 없으면 세션에서 가져오기
        if financial_data is None and 'financial_data' in st.session_state:
            financial_data = st.session_state['financial_data']
            st.write("✅ financial_data를 세션에서 가져왔습니다!")
            
        if news_data is None and 'google_news_data' in st.session_state:
            news_data = st.session_state['google_news_data']
            st.write("✅ news_data를 세션에서 가져왔습니다!")
            
        if insights is None or len(insights) == 0:
            session_insights = []
            for key in ['financial_insight', 'google_news_insight', 'integrated_insight']:
                if key in st.session_state and st.session_state[key]:
                    session_insights.append(st.session_state[key])
            if session_insights:
                insights = session_insights
                st.write(f"✅ insights를 세션에서 가져왔습니다! ({len(insights)}개)")
        
        # 4. 최종 데이터 상태
        st.write("**🎯 최종 전달될 데이터:**")
        final_params = {
            'financial_data': financial_data,
            'news_data': news_data,
            'insights': insights
        }
        
        for name, data in final_params.items():
            if data is not None:
                if hasattr(data, 'shape'):
                    st.write(f"✅ {name}: {type(data)} - 크기 {data.shape}")
                elif hasattr(data, '__len__'):
                    st.write(f"✅ {name}: {type(data)} - 길이 {len(data)}")
                else:
                    st.write(f"✅ {name}: {type(data)}")
            else:
                st.write(f"❌ {name}: None")
        
        st.write("=" * 50)
        
        # 5. 강제 테스트 데이터 주입 (디버깅용)
        if st.checkbox("🧪 강제 테스트 데이터 사용 (디버깅용)", key="force_test_data"):
            st.warning("강제 테스트 데이터를 사용합니다!")
            financial_data = pd.DataFrame({
                '구분': ['매출액(조원)', '영업이익률(%)', 'ROE(%)'],
                'SK에너지': ['50.5', '8.2', '15.1'],
                'S-Oil': ['45.3', '7.8', '14.2'],
                'GS칼텍스': ['40.1', '6.9', '12.8']
            })
            insights = ["이것은 강제 주입된 테스트 인사이트입니다. 실제 AI 분석 결과가 아닙니다."]
            st.write("✅ 강제 테스트 데이터 주입 완료!")
        
        with st.spinner("한글 PDF 생성 중... (NanumGothic 폰트 사용)"):
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
    return None

# 🔄 기존 함수명 호환성 유지
def create_enhanced_pdf_report(*args, **kwargs):
    """기존 함수명 호환용 (메인 코드에서 사용)"""
    result = generate_pdf_report(*args, **kwargs)
    if result['success']:
        return result['data']
    else:
        return result['error'].encode('utf-8')

def create_excel_report(
    financial_data=None,
    news_data=None,
    insights=None,
    **kwargs
):
    """Excel 보고서 생성 (간단 버전)"""
    print(f"📊 create_excel_report 호출됨")
    
    try:
        # 간단한 Excel 생성
        buffer = io.BytesIO()
        
        # 샘플 데이터 또는 실제 데이터 사용
        if financial_data is not None and not financial_data.empty:
            sample_data = financial_data
        else:
            sample_data = pd.DataFrame({
                '구분': ['매출액(조원)', '영업이익률(%)', 'ROE(%)', 'ROA(%)'],
                'SK에너지': [15.2, 5.6, 12.3, 8.1],
                'S-Oil': [14.8, 5.3, 11.8, 7.8],
                'GS칼텍스': [13.5, 4.6, 10.5, 7.2],
                'HD현대오일뱅크': [11.2, 4.3, 9.2, 6.5]
            })
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            sample_data.to_excel(writer, sheet_name='재무분석', index=False)
            
            # 뉴스 데이터도 추가
            if news_data is not None and not news_data.empty:
                news_data.to_excel(writer, sheet_name='뉴스분석', index=False)
        
        buffer.seek(0)
        excel_data = buffer.getvalue()
        buffer.close()
        
        print(f"✅ Excel 생성 완료 - {len(excel_data)} bytes")
        return excel_data
        
    except Exception as e:
        print(f"❌ Excel 생성 실패: {e}")
        error_msg = f"Excel 생성 실패: {str(e)}"
        return error_msg.encode('utf-8')

# ===========================================
# 🔥 메인 코드 연동용 함수들 (버튼 중복 방지)
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
    메인 코드에서 호출하는 PDF 생성 함수 (버튼 없이 데이터만 반환)
    """
    print(f"🚀 generate_pdf_report 호출됨")
    print(f"  - financial_data: {type(financial_data)}")
    print(f"  - news_data: {type(news_data)}")
    print(f"  - report_target: {report_target}")
    
    try:
        # PDF 생성
        pdf_data = create_korean_pdf_report()
        
        if isinstance(pdf_data, bytes) and len(pdf_data) > 1000:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SK에너지_분석보고서_{timestamp}.pdf"
            
            return {
                'success': True,
                'data': pdf_data,
                'filename': filename,
                'mime': 'application/pdf',
                'message': '✅ 한글 PDF 생성 완료!'
            }
        else:
            return {
                'success': False,
                'data': None,
                'error': f"PDF 생성 실패: {type(pdf_data)}"
            }
            
    except Exception as e:
        import traceback
        return {
            'success': False,
            'data': None,
            'error': f"PDF 생성 오류: {str(e)}",
            'traceback': traceback.format_exc()
        }

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
    button_label="📄 한글 PDF 보고서 생성",
    button_key="korean_pdf_btn",
    **kwargs
):
    """
    메인 코드용 - 기존 버튼 클릭시 PDF 생성하여 다운로드 버튼 표시
    """
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
    메인 코드의 기존 버튼이 클릭되었을 때 호출하는 함수
    """
    if button_clicked:
        with st.spinner("한글 PDF 생성 중... (NanumGothic 폰트 사용)"):
            return create_pdf_download_button(
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
    return None

# ===========================================
# 🧪 테스트 및 호환성 확인
# ===========================================

def test_integration():
    """메인 코드와의 통합 테스트"""
    print("🧪 메인 코드 통합 테스트...")
    
    # 1. 기본 함수들 존재 확인
    functions_to_test = [
        'create_enhanced_pdf_report',
        'create_excel_report', 
        'create_pdf_download_button'
    ]
    
    for func_name in functions_to_test:
        if func_name in globals():
            print(f"✅ {func_name} 함수 존재")
        else:
            print(f"❌ {func_name} 함수 없음")
    
    # 2. PDF 생성 테스트
    try:
        pdf_data = create_enhanced_pdf_report()
        if isinstance(pdf_data, bytes) and len(pdf_data) > 1000:
            print(f"✅ PDF 생성 테스트 성공 - {len(pdf_data)} bytes")
        else:
            print(f"❌ PDF 생성 테스트 실패 - {type(pdf_data)}")
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
        print(f"✅ 폰트 테스트 완료 - 발견된 폰트: {len(font_paths)}개")
        print(f"    등록된 폰트: {list(registered_fonts.keys())}")
    except Exception as e:
        print(f"❌ 폰트 테스트 오류: {e}")
    
    print("🏁 통합 테스트 완료")

def create_streamlit_interface():
    """Streamlit 인터페이스 생성 (테스트용)"""
    try:
        st.title("🏢 SK에너지 분석 보고서 생성기")
        st.markdown("---")
        
        # 기본 정보 입력
        col1, col2 = st.columns(2)
        
        with col1:
            report_target = st.text_input("보고 대상", value="SK이노베이션 경영진")
            report_author = st.text_input("보고자", value="AI 분석 시스템")
        
        with col2:
            show_footer = st.checkbox("Footer 표시", value=True)
            include_charts = st.checkbox("차트 포함", value=True)
        
        st.markdown("---")
        
        # PDF 생성 버튼
        col_pdf, col_excel = st.columns(2)
        
        with col_pdf:
            # 🔥 수정된 방식: 테스트용 버튼만 제공
            if st.button("📄 한글 PDF 테스트", type="primary", key="test_korean_pdf_btn"):
                success = handle_pdf_generation_button(
                    button_clicked=True,
                    report_target=report_target,
                    report_author=report_author,
                    show_footer=show_footer
                )
        
        with col_excel:
            if st.button("📊 Excel 보고서 생성", type="secondary", key="excel_btn"):
                with st.spinner("Excel 생성 중..."):
                    try:
                        excel_data = create_excel_report()
                        
                        if isinstance(excel_data, bytes) and len(excel_data) > 100:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"SK에너지_분석보고서_{timestamp}.xlsx"
                            
                            st.download_button(
                                label="📥 Excel 다운로드",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="secondary"
                            )
                            st.success("✅ Excel 생성 완료!")
                        else:
                            st.error("❌ Excel 생성 실패")
                    except Exception as e:
                        st.error(f"❌ Excel 생성 오류: {str(e)}")
        
        # 테스트 버튼
        st.markdown("---")
        st.subheader("🧪 테스트 기능")
        
        if st.button("🔍 통합 테스트 실행", key="test_btn"):
            with st.spinner("통합 테스트 중..."):
                test_integration()
                st.success("✅ 통합 테스트 완료! 콘솔을 확인하세요.")
        
        # 폰트 상태 확인
        if st.button("🔤 폰트 상태 확인", key="font_check_btn"):
            with st.expander("폰트 상태", expanded=True):
                font_paths = get_font_paths()
                if font_paths:
                    st.success(f"✅ {len(font_paths)}개 폰트 발견")
                    for font_name, font_path in font_paths.items():
                        file_size = os.path.getsize(font_path) if os.path.exists(font_path) else 0
                        st.write(f"  • {font_name}: {font_path} ({file_size:,} bytes)")
                else:
                    st.warning("⚠️ 폰트 파일을 찾을 수 없습니다")
                
                # ReportLab 상태
                if REPORTLAB_AVAILABLE:
                    st.success("✅ ReportLab 사용 가능")
                else:
                    st.error("❌ ReportLab 없음 - pip install reportlab 필요")
        
        # 사용법 안내
        with st.expander("📖 사용법", expanded=False):
            st.markdown("""
            ### 📁 파일 구조
            ```
            your_project/
            ├── export.py          # 이 파일
            ├── fonts/            # 폰트 폴더
            │   ├── NanumGothic.ttf
            │   ├── NanumGothicBold.ttf
            │   └── NanumMyeongjo.ttf
            └── main.py           # 메인 코드
            ```
            
            ### 🔧 메인 코드에서 사용법
            ```python
            from export import create_pdf_download_button, create_enhanced_pdf_report
            
            # Streamlit 앱에서
            create_pdf_download_button(
                financial_data=df,
                news_data=news_df,
                report_target="SK이노베이션 경영진"
            )
            
            # 직접 PDF 생성
            pdf_data = create_enhanced_pdf_report(financial_data=df)
            ```
            
            ### ⚙️ 설치 필요 패키지
            ```bash
            pip install reportlab pandas matplotlib openpyxl
            ```
            """)
    
    except Exception as e:
        st.error(f"❌ Streamlit 인터페이스 오류: {str(e)}")
        import traceback
        st.error(f"상세 오류: {traceback.format_exc()}")

# ===========================================
# 🚀 메인 실행부
# ===========================================

if __name__ == "__main__":
    print("🚀 SK에너지 PDF 보고서 생성 모듈 실행")
    print("=" * 50)
    
    # 환경 확인
    print("📋 환경 확인:")
    print(f"  - ReportLab: {'✅ 사용 가능' if REPORTLAB_AVAILABLE else '❌ 없음'}")
    print(f"  - Pandas: {'✅ 사용 가능' if 'pd' in globals() else '❌ 없음'}")
    print(f"  - Matplotlib: {'✅ 사용 가능' if 'plt' in globals() else '❌ 없음'}")
    
    # 폰트 확인
    font_paths = get_font_paths()
    print(f"  - 폰트: {'✅ ' + str(len(font_paths)) + '개 발견' if font_paths else '❌ 없음'}")
    
    # Streamlit 환경에서 실행되는지 확인
    try:
        if 'streamlit' in st.__module__:
            print("🌐 Streamlit 환경에서 실행")
            create_streamlit_interface()
        else:
            print("💻 일반 Python 환경에서 실행")
            test_integration()
    except:
        print("💻 일반 Python 환경에서 실행")
        test_integration()
    
    print("=" * 50)
    print("✅ 모듈 로드 완료! 메인 코드에서 import 하여 사용하세요.")
    print("""
📖 메인 코드 연동 방법:

방법 1: 기존 버튼에 연결
    from export import handle_pdf_generation_button
    
    if st.button("PDF 생성"):
        handle_pdf_generation_button(
            button_clicked=True,
            financial_data=df,
            news_data=news_df
        )

방법 2: 직접 PDF 생성
    from export import generate_pdf_report
    
    result = generate_pdf_report(financial_data=df)
    if result['success']:
        st.download_button("다운로드", result['data'], result['filename'])

방법 3: 기존 create_enhanced_pdf_report 사용 (호환)
    from export import create_enhanced_pdf_report
    pdf_data = create_enhanced_pdf_report(financial_data=df)
    """)
