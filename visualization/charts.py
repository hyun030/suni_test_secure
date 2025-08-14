# -*- coding: utf-8 -*-
import pandas as pd

# get_company_color 함수 import
try:
    from .table import get_company_color
except ImportError:
    def get_company_color(company, companies):
        """기본 색상 함수 (폴백)"""
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        try:
            idx = list(companies).index(company)
            return colors[idx % len(colors)]
        except:
            return colors[0]

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

def create_sk_bar_chart(chart_df: pd.DataFrame):
    """SK에너지 강조 막대 차트"""
    if not PLOTLY_AVAILABLE or chart_df.empty: 
        return None
    
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

def create_sk_radar_chart(chart_df):
    """SK에너지 중심 레이더 차트"""
    if chart_df.empty or not PLOTLY_AVAILABLE:
        return None
    
    companies = chart_df['회사'].unique() if '회사' in chart_df.columns else []
    metrics = chart_df['구분'].unique() if '구분' in chart_df.columns else []
    
    min_max = {}
    for metric in metrics:
        values = chart_df.loc[chart_df['구분'] == metric, '수치']
        min_val = values.min()
        max_val = values.max()
        if min_val == max_val:
            max_val = min_val + 1
        min_max[metric] = (min_val, max_val)
    
    fig = go.Figure()
    
    for i, company in enumerate(companies):
        company_data = chart_df[chart_df['회사'] == company] if '회사' in chart_df.columns else chart_df
        normalized_values = []
        raw_values = []
        
        for metric in metrics:
            raw_value = company_data.loc[company_data['구분'] == metric, '수치'].values
            if len(raw_value) == 0:
                norm_value = 0
                raw_val = 0
            else:
                val = raw_value[0]
                raw_val = val
                min_val, max_val = min_max[metric]
                norm_value = (val - min_val) / (max_val - min_val)
            normalized_values.append(norm_value)
            raw_values.append(raw_val)
        
        normalized_values.append(normalized_values[0])
        raw_values.append(raw_values[0])
        theta_labels = list(metrics) + [metrics[0]] if len(metrics) > 0 else ['지표1']
        
        color = get_company_color(company, companies)
        
        if 'SK' in company:
            line_width = 5
            marker_size = 12
            name_style = f"**{company}**"
        else:
            line_width = 3
            marker_size = 8
            name_style = company
        
        hover_text = []
        for j, metric in enumerate(metrics):
            hover_text.append(f"{metric}<br>{company}: {raw_values[j]:.2f}% (정규화: {normalized_values[j]:.3f})")
        hover_text.append(hover_text[0])
        
        fig.add_trace(go.Scatterpolar(
            r=normalized_values,
            theta=theta_labels,
            fill='toself',
            name=name_style,
            line=dict(width=line_width, color=color),
            marker=dict(size=marker_size, color=color),
            hovertemplate='%{text}<extra></extra>',
            text=hover_text
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 0.8],
                tickmode='linear',
                tick0=0,
                dtick=0.1,
                tickfont=dict(size=12),
                tickformat='.1f',
                ticktext=['0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8'],
                tickvals=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
            ),
            angularaxis=dict(
                tickfont=dict(size=14),
                tickangle=0
            )
        ),
        title="📊 주요 지표 비교 (정규화)",
        height=650,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=14)
        ),
        title_font_size=18,
        font=dict(size=12),
        plot_bgcolor='rgba(0,0,0,0.02)',
        paper_bgcolor='rgba(0,0,0,0.02)'
    )
    
    return fig

def create_quarterly_trend_chart(quarterly_df: pd.DataFrame):
    """분기별 추이 혼합 차트"""
    if not PLOTLY_AVAILABLE or quarterly_df.empty: 
        return None

    fig = go.Figure()
    companies = quarterly_df['회사'].unique()

    for company in companies:
        company_data = quarterly_df[quarterly_df['회사'] == company]
        color = get_company_color(company, companies)
        
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
    if not PLOTLY_AVAILABLE or quarterly_df.empty: 
        return None

    fig = go.Figure()
    companies = quarterly_df['회사'].unique()

    for company in companies:
        company_data = quarterly_df[quarterly_df['회사'] == company]
        color = get_company_color(company, companies)
        
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

def create_flexible_trend_chart(quarterly_df: pd.DataFrame, bar_metrics: list = None, line_metrics: list = None, show_values: bool = False):
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
                # ✅ 막대 차트용 수치 표시 설정
                text_values = None
                texttemplate = None
                textposition = None
                
                if show_values:
                    text_values = company_data[metric]
                    texttemplate = '%{text:.1f}'
                    textposition = 'auto'
                
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
                    text=text_values,
                    texttemplate=texttemplate,
                    textposition=textposition,
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
                
                # ✅ 추세선용 수치 표시 설정
                text_values = None
                texttemplate = None
                textposition = None
                mode = 'lines+markers'
                
                if show_values:
                    text_values = company_data[metric]
                    texttemplate = '%{text:.1f}'
                    textposition = 'top center'
                    mode = 'lines+markers+text'
                
                fig.add_trace(go.Scatter(
                    x=company_data['분기'], 
                    y=company_data[metric],
                    name=f"{company} - {metric.replace('(%)', '').replace('(조원)', '').replace('(억원)', '')}",
                    mode=mode,
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
                    text=text_values,
                    texttemplate=texttemplate,
                    textposition=textposition,
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

def create_gap_analysis(financial_df: pd.DataFrame, raw_cols: list):
    import re, numpy as np
    if financial_df.empty or not raw_cols:
        return pd.DataFrame()

    def norm(s: str) -> str:
        if s is None: return ""
        s = str(s)
        s = re.sub(r"\(.*?\)", "", s)
        s = re.sub(r"\s+", "", s)
        s = s.replace("−", "-")
        return s

    def to_float(v):
        if v is None: return None
        if isinstance(v, (int, float)):
            if isinstance(v, float) and np.isnan(v): return None
            return float(v)
        s = str(v)
        neg = s.strip().startswith("(") and s.strip().endswith(")")
        if neg: s = s.strip()[1:-1]

        multiplier = 1.0
        if "조" in s:
            multiplier = 10000.0
        elif "백만원" in s:
            multiplier = 0.01
        elif "천만원" in s:
            multiplier = 0.1

        import re as _re
        s_num = s.replace(",", "").replace("−", "-")
        s_num = _re.sub(r"[^0-9.\-]", "", s_num)
        if s_num in ("", "-", "."): return None
        try:
            val = float(s_num) * multiplier
            return -val if neg else val
        except:
            return None

    financial_df = financial_df.copy()
    financial_df["_구분_norm"] = financial_df["구분"].apply(norm)

    KEY_COGS   = [norm("매출원가")]
    KEY_GP     = [norm("매출총이익")]
    KEY_OP     = [norm("영업이익")]
    KEY_SALES  = [norm("매출액"), norm("매출")]
    KEY_SGA    = [norm("판관비"), norm("판관비(억원)"), norm("판매비와관리비"),
                  norm("판매비와 관리비"), norm("판매비및관리비"), norm("판매관리비")]

    KEY_COGS_R = [norm("매출원가율")]
    KEY_GP_R   = [norm("매출총이익률")]
    KEY_OP_R   = [norm("영업이익률")]
    KEY_SGA_R  = [norm("판관비율")]

    def pick_value(keys_norm, colname):
        m = financial_df[financial_df["_구분_norm"].isin(keys_norm)]
        if m.empty: return None
        raw = m.iloc[0].get(colname)
        return to_float(raw)

    companies = [c.replace("_원시값", "") for c in raw_cols]

    has_rate_rows = financial_df["_구분_norm"].isin(
        KEY_COGS_R + KEY_GP_R + KEY_OP_R + KEY_SGA_R
    ).any()

    ratios = {}
    if has_rate_rows and not any(c.endswith("_원시값") for c in raw_cols):
        for comp, col in zip(companies, raw_cols):
            ratios[comp] = {
                "매출원가율(%)":   pick_value(KEY_COGS_R, col),
                "매출총이익률(%)": pick_value(KEY_GP_R,   col),
                "영업이익률(%)":   pick_value(KEY_OP_R,   col),
                "판관비율(%)":     pick_value(KEY_SGA_R,  col),
            }
    else:
        for comp, col in zip(companies, raw_cols):
            cogs  = pick_value(KEY_COGS,  col)
            gp    = pick_value(KEY_GP,    col)
            op    = pick_value(KEY_OP,    col)
            sales = pick_value(KEY_SALES, col)
            sga   = pick_value(KEY_SGA,   col)
            if sga is None and (gp is not None) and (op is not None):
                sga = gp - op
            if sales is None and (gp is not None and cogs is not None):
                sales = gp + cogs

            if sales in (None, 0):
                cogs_r = gp_r = op_r = sga_r = None
            else:
                cogs_r = None if cogs is None else round((cogs / sales) * 100, 2)
                if gp is None and cogs is not None:
                    gp = sales - cogs
                gp_r  = None if gp  is None else round((gp  / sales) * 100, 2)
                op_r  = None if op  is None else round((op  / sales) * 100, 2)
                sga_r = None if sga is None else round((sga / sales) * 100, 2)

            ratios[comp] = {
                "매출원가율(%)":   cogs_r,
                "매출총이익률(%)": gp_r,
                "영업이익률(%)":   op_r,
                "판관비율(%)":     sga_r,
            }

    base_company = "SK에너지" if "SK에너지" in ratios else companies[0]
    metrics = ["매출원가율(%)", "매출총이익률(%)", "영업이익률(%)", "판관비율(%)"]
    rows = []
    for m in metrics:
        base_val = ratios.get(base_company, {}).get(m, None)
        row = {"지표": m, base_company: base_val}
        for comp in companies:
            if comp == base_company: 
                continue
            val = ratios.get(comp, {}).get(m, None)
            row[f"{comp}_갭(pp)"] = None if (base_val is None or val is None) else round(val - base_val, 2)
            row[f"{comp}_원본값"] = val
        rows.append(row)

    return pd.DataFrame(rows)

def create_gap_chart(gap_analysis_df: pd.DataFrame):
    """갭차이 시각화 차트"""
    if not PLOTLY_AVAILABLE or gap_analysis_df.empty:
        return None

    import plotly.express as px
    
    gap_cols = [c for c in gap_analysis_df.columns if c.endswith('_갭(pp)')]
    if not gap_cols:
        return None

    chart_rows = []
    for _, r in gap_analysis_df.iterrows():
        metric = r['지표']
        for col in gap_cols:
            comp = col.replace('_갭(pp)', '')
            chart_rows.append({'지표': metric, '회사': comp, '갭(퍼센트포인트)': r[col]})

    chart_df = pd.DataFrame(chart_rows)

    companies = chart_df['회사'].dropna().unique()
    color_map = {comp: get_company_color(comp, companies) for comp in companies}

    fig = px.bar(
        chart_df, x='지표', y='갭(퍼센트포인트)', color='회사',
        text='갭(퍼센트포인트)', color_discrete_map=color_map,
        barmode='group', height=500,
        title="📈 SK에너지 기준 상대 격차 분석"
    )
    fig.update_traces(texttemplate='%{text:.1f}pp', textposition='outside', cliponaxis=False)
    fig.add_hline(y=0, line_dash='dash', line_color='red',
                  annotation_text="SK에너지 기준선", annotation_position="bottom right")
    fig.update_layout(yaxis_title="갭(퍼센트포인트)", xaxis_title="재무 지표",
                      font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
    return fig
