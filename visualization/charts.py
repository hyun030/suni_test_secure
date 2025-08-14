# -*- coding: utf-8 -*-
import pandas as pd
from .table import get_company_color # visualization 폴더 내의 table 모듈에서 import

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ---------------- 기존 함수들 그대로 유지 ----------------
# create_sk_bar_chart, create_sk_radar_chart, create_quarterly_trend_chart,
# create_gap_trend_chart, create_gap_analysis, create_gap_chart
# (여기 내용은 질문에서 주신 코드와 동일)

# ---------------- 새로 추가되는 Bar+Line 혼합 차트 함수 ----------------
def create_bar_line_chart(df: pd.DataFrame, bar_metric: str, line_metric: str):
    """
    Bar+Line 혼합 차트
    bar_metric: 막대그래프로 표시할 지표명 (금액형)
    line_metric: 꺾은선그래프로 표시할 지표명 (비율형)
    """
    if not PLOTLY_AVAILABLE or df.empty:
        return None

    fig = go.Figure()
    companies = df['회사'].unique()

    for company in companies:
        company_data = df[df['회사'] == company]
        color = get_company_color(company, companies)

        # Bar trace (좌측 y축)
        if bar_metric in company_data.columns:
            fig.add_trace(go.Bar(
                x=company_data['분기'],
                y=company_data[bar_metric],
                name=f"{company} {bar_metric}",
                marker_color=color,
                yaxis='y1'
            ))

        # Line trace (우측 y축)
        if line_metric in company_data.columns:
            fig.add_trace(go.Scatter(
                x=company_data['분기'],
                y=company_data[line_metric],
                name=f"{company} {line_metric}",
                mode='lines+markers',
                line=dict(color=color, width=3, dash='solid'),
                marker=dict(size=8),
                yaxis='y2'
            ))

    # Layout 설정
    fig.update_layout(
        title=f"📊 {bar_metric} vs {line_metric} (Bar+Line 혼합)",
        xaxis=dict(title="분기"),
        yaxis=dict(title=bar_metric, side='left', showgrid=False),
        yaxis2=dict(title=line_metric, overlaying='y', side='right', showgrid=False),
        barmode='group',
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig
