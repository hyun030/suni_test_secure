# 🎯 AI 의견생성 제거한 단순화된 PDF 생성 코드

def generate_pdf_report(
    financial_data=None,
    news_data=None,
    insights=None,
    report_target="SK이노베이션 경영진",
    report_author="AI 분석 시스템",
    **kwargs
):
    """
    PDF 보고서 생성 - AI 의견생성 없이 전달받은 데이터만 표시
    """
    print(f"🚀 PDF 보고서 생성 시작")
    
    if not REPORTLAB_AVAILABLE:
        return {
            'success': False,
            'data': None,
            'error': "ReportLab이 설치되지 않았습니다."
        }
    
    try:
        # ✅ 수정: 전달받은 데이터 그대로 사용 (세션 검색 제거)
        has_real_financial = (financial_data is not None and 
                             not (hasattr(financial_data, 'empty') and financial_data.empty))
        has_real_news = (news_data is not None and 
                        not (hasattr(news_data, 'empty') and news_data.empty))
        has_insights = insights and len(insights) > 0
        
        print(f"📊 전달받은 데이터: 재무={has_real_financial}, 뉴스={has_real_news}, 인사이트={has_insights}")
        
        # 폰트 등록
        registered_fonts = register_fonts()
        
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
        
        info_style = ParagraphStyle(
            'Info',
            fontName=registered_fonts.get('Korean', 'Helvetica'),
            fontSize=12,
            leading=16,
            alignment=1,
            spaceAfter=6
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
        current_date = datetime.now().strftime('%Y년 %m월 %d일')
        story.append(Paragraph(f"보고일자: {current_date}", info_style))
        story.append(Paragraph(f"보고대상: {report_target}", info_style))
        story.append(Paragraph(f"보고자: {report_author}", info_style))
        story.append(Spacer(1, 30))
        
        section_counter = 1
        
        # 1. 재무분석 섹션 (있을 때만)
        if has_real_financial:
            story.append(Paragraph(f"{section_counter}. 재무분석 결과", heading_style))
            story.append(Spacer(1, 10))
            
            # 재무 데이터 테이블
            financial_table = create_real_data_table(financial_data, registered_fonts)
            if financial_table:
                story.append(financial_table)
                story.append(Spacer(1, 16))
            
            # 재무 데이터 차트
            charts = create_real_data_charts(financial_data)
            for chart_name, chart_title in [('revenue_comparison', '매출액 비교'), 
                                           ('roe_comparison', 'ROE 성과 비교')]:
                if charts.get(chart_name):
                    chart_img = safe_create_chart_image(charts[chart_name], width=450, height=270)
                    if chart_img:
                        story.append(Paragraph(f"▶ {chart_title}", body_style))
                        story.append(chart_img)
                        story.append(Spacer(1, 10))
            
            section_counter += 1
        
        # 2. 뉴스 분석 섹션 (있을 때만)
        if has_real_news:
            story.append(Paragraph(f"{section_counter}. 뉴스 분석 결과", heading_style))
            story.append(Spacer(1, 10))
            
            news_table = create_real_news_table(news_data, registered_fonts)
            if news_table:
                story.append(news_table)
                story.append(Spacer(1, 16))
            
            section_counter += 1
        
        # 3. 스트림릿에서 전달받은 인사이트 (있을 때만 - AI 새로 생성 안함)
        if has_insights:
            story.append(Paragraph(f"{section_counter}. 분석 인사이트", heading_style))
            story.append(Spacer(1, 10))
            
            for i, insight in enumerate(insights[:3], 1):
                if insight and insight.strip():
                    story.append(Paragraph(f"인사이트 {i}:", heading_style))
                    story.append(Spacer(1, 6))
                    story.append(Paragraph(insight.strip()[:500], body_style))  # 500자로 제한
                    story.append(Spacer(1, 10))
        
        # 데이터가 없을 때 메시지
        if not has_real_financial and not has_real_news and not has_insights:
            story.append(Paragraph("분석할 데이터가 제공되지 않았습니다.", body_style))
        
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
            data_status.append("재무데이터")
        if has_real_news:
            data_status.append("뉴스데이터")
        if has_insights:
            data_status.append("인사이트")
        
        message = f"PDF 생성 완료! ({', '.join(data_status) if data_status else '데이터 없음'})"
        
        print(f"✅ PDF 생성 성공 - {len(pdf_data)} bytes")
        
        return {
            'success': True,
            'data': pdf_data,
            'filename': filename,
            'mime': 'application/pdf',
            'message': message
        }
        
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        return {
            'success': False,
            'data': None,
            'error': f"PDF 생성 오류: {str(e)}"
        }


def handle_pdf_generation_button(
    button_clicked,
    financial_data=None,
    news_data=None,
    insights=None,
    report_target="SK이노베이션 경영진",
    report_author="데이터 분석팀",
    **kwargs
):
    """
    메인 코드의 버튼 클릭시 호출하는 함수 - 단순화됨
    """
    if not button_clicked:
        return None
        
    with st.spinner("PDF 생성 중..."):
        result = generate_pdf_report(
            financial_data=financial_data,
            news_data=news_data,
            insights=insights,
            report_target=report_target,
            report_author=report_author,
            **kwargs
        )
        
        if result['success']:
            st.download_button(
                label="📥 PDF 다운로드",
                data=result['data'],
                file_name=result['filename'],
                mime=result['mime'],
                type="secondary"
            )
            st.success(result['message'])
            return True
        else:
            st.error(f"❌ {result['error']}")
            return False


# 🔧 주요 변경사항:
"""
1. ❌ 제거된 부분들:
   - get_real_data_from_session() 함수 호출 제거
   - AI 의견 자동 생성 제거
   - "AI가 분석하여 생성한 인사이트" 같은 문구 제거
   - 하단 Footer "AI 시스템에 의해 생성" 문구 제거
   - 복잡한 세션 상태 검색 로직 제거

2. ✅ 단순화된 부분들:
   - 전달받은 데이터만 사용
   - 스트림릿에서 이미 생성된 인사이트만 표시
   - 데이터 있는 섹션만 표시
   - 간단한 성공/실패 메시지
"""
