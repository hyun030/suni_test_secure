def create_flexible_trend_chart(quarterly_df: pd.DataFrame, bar_metrics: list = None, line_metrics: list = None):
    """사용자가 선택한 막대/추세선 지표들로 혼합 차트 생성"""
    if not PLOTLY_AVAILABLE or quarterly_df.empty: 
        return None
    
    # 선택된 지표가 없으면 기본값 설정
    if not bar_metrics and not line_metrics:
        available_cols = [col for col in quarterly_df.columns if col not in ['분기', '회사', '보고서구분']]
        bar_metrics = available_cols[:1] if available_cols else []
        line_metrics = []
    
    # 선택된 지표가 실제 데이터에 있는지 확인
    available_cols = quarterly_df.columns.tolist()
    valid_bar_metrics = [m for m in (bar_metrics or []) if m in available_cols]
    valid_line_metrics = [m for m in (line_metrics or []) if m in available_cols]
    
    if not valid_bar_metrics and not valid_line_metrics:
        return None
    
    fig = go.Figure()
    companies = quarterly_df['회사'].unique()
    
    # 회사별 색상
    company_colors = {}
    for company in companies:
        company_colors[company] = get_company_color(company, companies)
    
    # 막대그래프 추가
    for metric in valid_bar_metrics:
        for company_idx, company in enumerate(companies):
            company_data = quarterly_df[quarterly_df['회사'] == company]
            
            if metric in company_data.columns and not company_data[metric].isna().all():
                fig.add_trace(go.Bar(
                    x=company_data['분기'], 
                    y=company_data[metric],
                    name=f"{company} - {metric.replace('(조원)', '').replace('(억원)', '').replace('(%)', '')}",
                    marker=dict(
                        color=company_colors[company],
                        opacity=0.8,
                        line=dict(width=1, color='white')
                    ),
                    yaxis='y2' if valid_line_metrics else 'y',  # 추세선이 있으면 오른쪽 축 사용
                    offsetgroup=company_idx,
                    hovertemplate=f'<b>{company}</b><br>{metric}: %{{y}}<br>분기: %{{x}}<extra></extra>'
                ))
    
    # 꺾은선 추가
    line_styles = ['solid', 'dash', 'dot', 'dashdot', 'longdash']
    markers = ['circle', 'square', 'diamond', 'triangle-up', 'star', 'hexagon']
    
    for metric_idx, metric in enumerate(valid_line_metrics):
        for company in companies:
            company_data = quarterly_df[quarterly_df['회사'] == company]
            
            if metric in company_data.columns and not company_data[metric].isna().all():
                # SK 회사는 더 굵고 큰 마커
                line_width = 4 if 'SK' in company or 'sk' in company.lower() else 3
                marker_size = 10 if 'SK' in company or 'sk' in company.lower() else 8
                
                fig.add_trace(go.Scatter(
                    x=company_data['분기'], 
                    y=company_data[metric],
                    name=f"{company} - {metric.replace('(%)', '').replace('(조원)', '').replace('(억원)', '')}",
                    mode='lines+markers',
                    line=dict(
                        color=company_colors[company], 
                        width=line_width,
                        dash=line_styles[metric_idx % len(line_styles)]
                    ),
                    marker=dict(
                        size=marker_size,
                        color=company_colors[company],
                        symbol=markers[metric_idx % len(markers)],
                        line=dict(width=2, color='white')
                    ),
                    yaxis='y',  # 추세선은 항상 왼쪽 축 사용
                    hovertemplate=f'<b>{company}</b><br>{metric}: %{{y}}<br>분기: %{{x}}<extra></extra>'
                ))
    
    # 제목 생성
    all_metrics = valid_bar_metrics + valid_line_metrics
    if len(all_metrics) <= 3:
        clean_metrics = [m.replace('(%)', '').replace('(조원)', '').replace('(억원)', '') for m in all_metrics]
        chart_title = f"📊 기업별 시계열 분석: {', '.join(clean_metrics)}"
    else:
        chart_title = f"📊 기업별 시계열 분석 ({len(all_metrics)}개 지표)"
    
    # 부제목 추가
    subtitle_parts = []
    if valid_bar_metrics:
        subtitle_parts.append(f"막대: {len(valid_bar_metrics)}개")
    if valid_line_metrics:
        subtitle_parts.append(f"추세선: {len(valid_line_metrics)}개")
    
    if subtitle_parts:
        chart_title += f"<br><sub>{' | '.join(subtitle_parts)}</sub>"
    
    # 레이아웃 설정
    layout_kwargs = {
        'title': {
            'text': chart_title,
            'x': 0.5,
            'font': {'size': 16}
        },
        'xaxis': {
            'title': "분기",
            'tickangle': -45
        },
        'font': dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
        'height': 500,
        'hovermode': 'x unified',
        'showlegend': True,
        'legend': dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,  # 범례 위치를 더 아래로
            xanchor="center",
            x=0.5,
            font=dict(size=9)
        ),
        'margin': dict(b=120),  # 하단 여백 증가
        'plot_bgcolor': 'rgba(248,249,250,0.8)',
        'paper_bgcolor': 'white'
    }
    
    # Y축 설정 (이중축 vs 단일축)
    if valid_bar_metrics and valid_line_metrics:
        # 이중축: 추세선(왼쪽) + 막대(오른쪽)
        bar_names = [m.replace('(조원)', '').replace('(억원)', '') for m in valid_bar_metrics]
        line_names = [m.replace('(%)', '').replace('(조원)', '').replace('(억원)', '') for m in valid_line_metrics]
        
        layout_kwargs.update({
            'yaxis': dict(
                title=f"추세선: {', '.join(line_names)}",
                side='left',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            'yaxis2': dict(
                title=f"막대: {', '.join(bar_names)}",
                side='right',
                overlaying='y',
                showgrid=False
            )
        })
    elif valid_bar_metrics:
        # 막대만 있는 경우
        has_currency = any('조원' in m or '억원' in m for m in valid_bar_metrics)
        unit_label = "금액 (조원)" if has_currency else "수치"
        layout_kwargs['yaxis'] = dict(title=unit_label, showgrid=True)
    else:
        # 추세선만 있는 경우
        is_percentage = any('(%)' in m for m in valid_line_metrics)
        has_currency = any('조원' in m or '억원' in m for m in valid_line_metrics)
        
        if is_percentage:
            unit_label = "비율 (%)"
        elif has_currency:
            unit_label = "금액 (조원)"
        else:
            unit_label = "수치"
        
        layout_kwargs['yaxis'] = dict(title=unit_label, showgrid=True)
    
    fig.update_layout(**layout_kwargs)
    return fig


# 기존 함수도 호환성을 위해 유지 (selected_metrics 방식)
def create_flexible_trend_chart_legacy(quarterly_df: pd.DataFrame, selected_metrics: list = None):
    """기존 방식 호환용 함수 - selected_metrics를 자동으로 막대/추세선으로 분류"""
    if not selected_metrics:
        return create_flexible_trend_chart(quarterly_df, [], [])
    
    # 자동 분류 (기존 로직)
    selected_bar_metrics = []
    selected_line_metrics = []
    
    for metric in selected_metrics:
        if metric in quarterly_df.columns:
            metric_lower = metric.lower()
            # 큰 금액은 막대그래프
            if (('매출액' in metric and ('조원' in metric or metric.endswith('매출액'))) or 
                ('ebitda' in metric_lower) or 
                ('매출원가' in metric and ('조원' in metric or metric.endswith('매출원가'))) or
                ('매출총이익' in metric and ('조원' in metric or metric.endswith('매출총이익')))):
                selected_bar_metrics.append(metric)
            else:
                # 나머지는 꺾은선
                selected_line_metrics.append(metric)
    
    return create_flexible_trend_chart(quarterly_df, selected_bar_metrics, selected_line_metrics)
