def create_flexible_trend_chart(quarterly_df: pd.DataFrame, selected_metrics: list = None):
    """사용자가 선택한 지표들로 혼합 차트 생성 (막대그래프 + 꺾은선)"""
    if not PLOTLY_AVAILABLE or quarterly_df.empty: 
        return None
    
    # 기본 지표 설정 (선택된 게 없으면)
    if not selected_metrics:
        selected_metrics = ['영업이익률(%)']
    
    fig = go.Figure()
    companies = quarterly_df['회사'].unique()
    
    # 지표별 차트 타입 분류
    # 금액 지표는 막대그래프, 비율 지표는 꺾은선
    bar_metrics = [
        '매출액', '매출액(조원)', 
        '매출원가', '매출원가(조원)',
        '매출총이익', '매출총이익(조원)',
        '영업이익', '영업이익(조원)',
        '당기순이익', '당기순이익(조원)',
        '판관비', '판관비(조원)',
        'EBITDA', 'CapEx'
    ]
    
    line_metrics = [
        '영업이익률(%)', '순이익률(%)', '매출총이익률(%)', '매출원가율(%)',
        '판관비율(%)', 'ROE(%)', 'ROA(%)', 'ROIC(%)'
    ]
    
    # 지표별 라인 스타일과 색상 매핑
    line_styles = ['solid', 'dash', 'dot', 'dashdot', 'longdash']
    markers = ['circle', 'square', 'diamond', 'triangle-up', 'star', 'hexagon']
    
    # Y축이 여러 개인지 확인 (금액과 비율을 분리)
    selected_bar_metrics = [m for m in selected_metrics if m in bar_metrics]
    selected_line_metrics = [m for m in selected_metrics if m in line_metrics]
    
    # 회사별 색상 설정
    company_colors = {}
    base_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    for i, company in enumerate(companies):
        company_colors[company] = get_company_color(company, companies) if 'get_company_color' in globals() else base_colors[i % len(base_colors)]
    
    # 막대그래프 추가 (금액 지표)
    for company in companies:
        company_data = quarterly_df[quarterly_df['회사'] == company]
        base_color = company_colors[company]
        
        for i, metric in enumerate(selected_bar_metrics):
            if metric in company_data.columns:
                # 투명도로 같은 회사 내 지표들 구분
                opacity = 1.0 - (i * 0.2) if i < 4 else 0.4
                
                fig.add_trace(go.Bar(
                    x=company_data['분기'], 
                    y=company_data[metric],
                    name=f"{company} - {metric.replace('(조원)', '').replace('(억원)', '')}",
                    marker=dict(
                        color=base_color,
                        opacity=opacity,
                        line=dict(width=1, color='white')
                    ),
                    yaxis='y2' if selected_line_metrics else 'y',  # 라인 지표가 있으면 y2축 사용
                    hovertemplate=f'<b>{company}</b><br>' +
                                 f'{metric}: %{{y}}<br>' +
                                 '분기: %{x}<extra></extra>'
                ))
    
    # 꺾은선 추가 (비율 지표)
    for company in companies:
        company_data = quarterly_df[quarterly_df['회사'] == company]
        base_color = company_colors[company]
        
        for i, metric in enumerate(selected_line_metrics):
            if metric in company_data.columns:
                # SK 관련 회사 강조
                line_width = 4 if 'SK' in company else 3
                marker_size = 10 if 'SK' in company else 8
                
                fig.add_trace(go.Scatter(
                    x=company_data['분기'], 
                    y=company_data[metric],
                    name=f"{company} - {metric.replace('(%)', '')}",
                    mode='lines+markers',
                    line=dict(
                        color=base_color, 
                        width=line_width,
                        dash=line_styles[i % len(line_styles)]
                    ),
                    marker=dict(
                        size=marker_size,
                        color=base_color,
                        symbol=markers[i % len(markers)],
                        line=dict(width=2, color='white')
                    ),
                    yaxis='y',  # 비율은 항상 y축 사용
                    hovertemplate=f'<b>{company}</b><br>' +
                                 f'{metric}: %{{y}}<br>' +
                                 '분기: %{x}<extra></extra>'
                ))
    
    # 레이아웃 설정
    layout_kwargs = {
        'title': {
            'text': "📊 선택된 지표별 혼합 트렌드 분석 (막대+꺾은선)",
            'x': 0.5,
            'font': {'size': 18}
        },
        'xaxis': {
            'title': "분기",
            'tickangle': -45
        },
        'font': dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
        'height': 500,
        'hovermode': 'x unified',
        'legend': dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.05,
            font=dict(size=10)
        ),
        'margin': dict(r=150),  # 범례 공간 확보
        'plot_bgcolor': 'rgba(240,240,240,0.5)',
        'paper_bgcolor': 'white'
    }
    
    # 이중 Y축 설정 (금액과 비율이 섞여있는 경우)
    if selected_bar_metrics and selected_line_metrics:
        layout_kwargs.update({
            'yaxis': dict(
                title=dict(
                    text=' / '.join([m.replace('(%)', '(%)') for m in selected_line_metrics]),
                    font=dict(color='blue')
                ),
                side='left',
                showgrid=True,
                gridcolor='lightblue',
                tickfont=dict(color='blue')
            ),
            'yaxis2': dict(
                title=dict(
                    text=' / '.join([m.replace('(조원)', '(조원)').replace('(억원)', '(억원)') for m in selected_bar_metrics]),
                    font=dict(color='red')
                ),
                side='right',
                overlaying='y',
                showgrid=False,
                tickfont=dict(color='red')
            )
        })
    elif selected_bar_metrics:
        # 금액 지표만 있는 경우
        unit = '(조원)' if any('조원' in m for m in selected_bar_metrics) else '(억원)' if any('억원' in m for m in selected_bar_metrics) else ''
        layout_kwargs['yaxis'] = dict(
            title=' / '.join([m.replace(unit, '') for m in selected_bar_metrics]) + unit,
            showgrid=True
        )
    else:
        # 비율 지표만 있는 경우
        layout_kwargs['yaxis'] = dict(
            title=' / '.join([m.replace('(%)', '') for m in selected_line_metrics]) + '(%)',
            showgrid=True
        )
    
    fig.update_layout(**layout_kwargs)
    
    return fig

# 기존 차트 함수들은 그대로 유지하고, create_flexible_trend_chart만 위의 혼합 차트로 교체
def create_sk_bar_chart(chart_df: pd.DataFrame):
    """SK에너지 강조 막대 차트"""
    if not PLOTLY_AVAILABLE or chart_df.empty: return None
    
    companies = chart_df['회사'].unique()
    color_map = {comp: get_company_color(comp, companies) for comp in companies}
    
    fig = px.bar(
        chart_df, x='구분', y='수치', color='회사',
        title="📊 주요 지표 비교",
        text='수치', color_discrete_map=color_map, barmode='group', height=450
    )
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(
        yaxis_title="수치(%)", xaxis_title="재무 지표", legend_title="회사",
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    return fig

def create_quarterly_trend_chart(quarterly_df: pd.DataFrame):
    """분기별 추이 혼합 차트"""
    if not PLOTLY_AVAILABLE or quarterly_df.empty: return None

    fig = go.Figure()
    companies = quarterly_df['회사'].unique()

    for company in companies:
        company_data = quarterly_df[quarterly_df['회사'] == company]
        color = get_company_color(company, companies) if 'get_company_color' in globals() else '#1f77b4'
        
        # 매출액 (Bar)
        if '매출액(조원)' in company_data.columns:
            fig.add_trace(go.Bar(
                x=company_data['분기'], y=company_data['매출액(조원)'], name=f"{company} 매출액(조)",
                marker_color=color
            ))
    
    fig.update_layout(
        barmode='group', title="📊 분기별 재무지표 트렌드",
        xaxis_title="분기", yaxis_title="매출액 (조원)",
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    return fig

def create_gap_trend_chart(quarterly_df: pd.DataFrame):
    """분기별 갭 추이 차트"""
    if not PLOTLY_AVAILABLE or quarterly_df.empty: return None

    fig = go.Figure()
    companies = quarterly_df['회사'].unique()

    for company in companies:
        company_data = quarterly_df[quarterly_df['회사'] == company]
        color = get_company_color(company, companies) if 'get_company_color' in globals() else '#1f77b4'
        
        # 영업이익률 (Line)
        if '영업이익률(%)' in company_data.columns:
            fig.add_trace(go.Scatter(
                x=company_data['분기'], y=company_data['영업이익률(%)'], 
                name=f"{company} 영업이익률(%)",
                mode='lines+markers', line=dict(color=color, width=3),
                marker=dict(size=8)
            ))
    
    fig.update_layout(
        title="📈 트렌드 분석",
        xaxis_title="분기", yaxis_title="영업이익률 (%)",
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
        height=450
    )
    return fig
