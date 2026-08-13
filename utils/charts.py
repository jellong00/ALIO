# -*- coding: utf-8 -*-
"""
Plotly 재사용 차트 함수
========================
모든 페이지가 동일한 함수를 사용하여 시각적 일관성을 유지한다.
과도한 색상/장식은 사용하지 않는다.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.constants import PRIMARY_COLOR, SECONDARY_COLOR, TYPE_COLOR_MAP, INSTITUTION_TYPE_ORDER

BASE_LAYOUT = dict(
    template="plotly_white",
    font=dict(size=13),
    margin=dict(l=40, r=20, t=50, b=40),
)


def _apply_base_layout(fig, title, xaxis_title=None, yaxis_title=None):
    fig.update_layout(**BASE_LAYOUT, title=title)
    if xaxis_title:
        fig.update_xaxes(title=xaxis_title)
    if yaxis_title:
        fig.update_yaxes(title=yaxis_title)
    return fig


def plot_histogram(series: pd.Series, title="", unit="", nbins=30):
    s = pd.to_numeric(series, errors="coerce").dropna()
    fig = px.histogram(s, nbins=nbins, color_discrete_sequence=[PRIMARY_COLOR])
    fig.update_layout(showlegend=False)
    _apply_base_layout(fig, title, xaxis_title=f"값{f' ({unit})' if unit else ''}", yaxis_title="기관 수")
    return fig


def plot_boxplot(series: pd.Series, title="", unit=""):
    s = pd.to_numeric(series, errors="coerce").dropna()
    fig = go.Figure()
    fig.add_trace(go.Box(y=s, name="", marker_color=PRIMARY_COLOR, boxmean=True))
    _apply_base_layout(fig, title, yaxis_title=f"값{f' ({unit})' if unit else ''}")
    fig.update_xaxes(showticklabels=False)
    return fig


def plot_group_boxplot(df: pd.DataFrame, value_col: str, group_col: str, title="", unit=""):
    plot_df = df.copy()
    plot_df[value_col] = pd.to_numeric(plot_df[value_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[value_col, group_col])

    order = [t for t in INSTITUTION_TYPE_ORDER if t in plot_df[group_col].unique()]
    other_groups = [g for g in plot_df[group_col].unique() if g not in order]
    order += sorted(other_groups)

    fig = px.box(
        plot_df,
        x=group_col,
        y=value_col,
        color=group_col,
        category_orders={group_col: order},
        color_discrete_map=TYPE_COLOR_MAP,
    )
    _apply_base_layout(fig, title, xaxis_title=group_col, yaxis_title=f"값{f' ({unit})' if unit else ''}")
    fig.update_layout(showlegend=False)
    return fig


def plot_rank_bar(df: pd.DataFrame, name_col: str, value_col: str, top_n=20, title="", unit="", ascending=False):
    plot_df = df.copy()
    plot_df[value_col] = pd.to_numeric(plot_df[value_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[value_col]).sort_values(value_col, ascending=ascending).head(top_n)
    plot_df = plot_df.sort_values(value_col, ascending=True)  # 가로막대 정렬 위해 뒤집기

    fig = px.bar(
        plot_df,
        x=value_col,
        y=name_col,
        orientation="h",
        color_discrete_sequence=[PRIMARY_COLOR],
    )
    _apply_base_layout(fig, title, xaxis_title=f"값{f' ({unit})' if unit else ''}", yaxis_title="")
    fig.update_layout(height=max(350, 22 * len(plot_df)))
    return fig


def plot_time_series(df: pd.DataFrame, year_col: str, value_col: str, title="", unit="", color_col=None):
    plot_df = df.copy()
    plot_df[value_col] = pd.to_numeric(plot_df[value_col], errors="coerce")

    if color_col:
        fig = px.line(plot_df, x=year_col, y=value_col, color=color_col, markers=True)
    else:
        fig = px.line(plot_df, x=year_col, y=value_col, markers=True, color_discrete_sequence=[PRIMARY_COLOR])
    _apply_base_layout(fig, title, xaxis_title="연도", yaxis_title=f"값{f' ({unit})' if unit else ''}")
    fig.update_xaxes(type="category")
    return fig


def plot_donut(labels, values, title=""):
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5)])
    fig.update_traces(marker=dict(colors=px.colors.sequential.Blues_r))
    _apply_base_layout(fig, title)
    return fig


def plot_scatter(df: pd.DataFrame, x_col: str, y_col: str, title="", color_col=None):
    plot_df = df.copy()
    plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[x_col, y_col])

    if color_col:
        fig = px.scatter(plot_df, x=x_col, y=y_col, color=color_col, opacity=0.7)
    else:
        fig = px.scatter(plot_df, x=x_col, y=y_col, opacity=0.7, color_discrete_sequence=[PRIMARY_COLOR])
    _apply_base_layout(fig, title, xaxis_title=x_col, yaxis_title=y_col)
    return fig


def plot_scatter_ols(df: pd.DataFrame, x_col: str, y_col: str, title=""):
    plot_df = df.copy()
    plot_df[x_col] = pd.to_numeric(plot_df[x_col], errors="coerce")
    plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[x_col, y_col])

    fig = px.scatter(
        plot_df, x=x_col, y=y_col, trendline="ols",
        opacity=0.7, color_discrete_sequence=[PRIMARY_COLOR],
        trendline_color_override=SECONDARY_COLOR,
    )
    _apply_base_layout(fig, title, xaxis_title=x_col, yaxis_title=y_col)
    return fig


def plot_correlation_heatmap(corr_matrix: pd.DataFrame, title=""):
    fig = px.imshow(
        corr_matrix,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        aspect="auto",
    )
    _apply_base_layout(fig, title)
    return fig
