"""
charts.py
---------
Plotly 기반 공통 차트 함수. 대형 화면 시연을 고려해 폰트 크기를 크게 설정한다.
기관유형 색상은 utils.variables.ORG_TYPE_COLORS로 전 페이지에서 통일한다.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.variables import ORG_TYPE_COLORS, get_label, get_unit

BASE_FONT = 16
TITLE_FONT = 20
HEIGHT = 520


def _apply_layout(fig, title=None, height=HEIGHT):
    fig.update_layout(
        font=dict(size=BASE_FONT),
        title=dict(text=title, font=dict(size=TITLE_FONT)) if title else None,
        height=height,
        legend=dict(font=dict(size=BASE_FONT - 2)),
        margin=dict(l=40, r=30, t=60 if title else 30, b=40),
    )
    return fig


def _percentile_range(series: pd.Series, lower=1, upper=99, pad=0.08):
    """이상치의 영향을 줄이기 위한 축 범위를 계산한다 (데이터를 지우지 않고 보기 범위만 조정)."""
    s = series.dropna()
    if s.empty:
        return None
    lo, hi = np.percentile(s, [lower, upper])
    if lo == hi:
        return None
    span = hi - lo
    return [lo - span * pad, hi + span * pad]


def plot_histogram(df, col, var_key=None, nbins=30, show_mean=True, show_median=True, clip_extreme=True):
    label = get_label(var_key) if var_key else col
    unit = get_unit(var_key) if var_key else ""
    data = df[[col]].dropna()
    fig = px.histogram(data, x=col, nbins=nbins,
                        labels={col: f"{label} ({unit})" if unit else label})
    fig.update_traces(marker_color="#4C78A8")
    n_clipped = 0
    if not data.empty:
        if show_mean:
            m = data[col].mean()
            fig.add_vline(x=m, line_dash="solid", line_color="#E07B39", line_width=3,
                           annotation_text=f"{m:,.1f}", annotation_position="top",
                           annotation_font_color="#E07B39")
        if show_median:
            med = data[col].median()
            fig.add_vline(x=med, line_dash="dash", line_color="#2CA02C", line_width=3,
                           annotation_text=f"{med:,.1f}", annotation_position="top",
                           annotation_font_color="#2CA02C", annotation_yshift=-22)
        if clip_extreme:
            rng = _percentile_range(data[col], 1, 99)
            if rng:
                n_clipped = int(((data[col] < rng[0]) | (data[col] > rng[1])).sum())
                fig.update_xaxes(range=rng)
    title = f"{label} 분포 (N={data.shape[0]:,})"
    if clip_extreme and n_clipped:
        title += f" — 상하위 1% 극단값 {n_clipped}건은 축 범위 밖에 있습니다"
    _apply_layout(fig, title=title)
    return fig


def plot_donut(labels, values, title="구성비"):
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5,
                                   textinfo="label+percent")])
    _apply_layout(fig, title=title, height=460)
    return fig


def plot_group_box(df, col, group_col="기관유형", var_key=None, points="outliers", clip_extreme=True):
    label = get_label(var_key) if var_key else col
    unit = get_unit(var_key) if var_key else ""
    hover_cols = [c for c in ["기관명", "연도"] if c in df.columns]
    data = df[[col, group_col] + hover_cols].dropna(subset=[col, group_col])
    fig = px.box(data, x=group_col, y=col, color=group_col,
                 color_discrete_map=ORG_TYPE_COLORS, points=points,
                 hover_data=hover_cols,
                 labels={col: f"{label} ({unit})" if unit else label, group_col: "기관유형"})
    title = f"기관유형별 {label} 분포 (N={data.shape[0]:,})"
    if clip_extreme:
        rng = _percentile_range(data[col], 1, 99, pad=0.15)
        if rng:
            fig.update_yaxes(range=rng)
            title += " — 축 범위는 이상치 영향을 줄이기 위해 조정됨"
    _apply_layout(fig, title=title)
    fig.update_layout(showlegend=False)
    return fig


def plot_group_violin(df, col, group_col="기관유형", var_key=None):
    label = get_label(var_key) if var_key else col
    unit = get_unit(var_key) if var_key else ""
    data = df[[col, group_col]].dropna()
    fig = px.violin(data, x=group_col, y=col, color=group_col, box=True,
                     color_discrete_map=ORG_TYPE_COLORS,
                     labels={col: f"{label} ({unit})" if unit else label, group_col: "기관유형"})
    _apply_layout(fig, title=f"기관유형별 {label} 분포 (violin)")
    fig.update_layout(showlegend=False)
    return fig


def plot_group_bar(df, col, group_col="기관유형", var_key=None, agg="mean"):
    label = get_label(var_key) if var_key else col
    unit = get_unit(var_key) if var_key else ""
    data = df[[col, group_col]].dropna()
    grp = data.groupby(group_col)[col].agg(agg).reset_index()
    n_grp = data.groupby(group_col)[col].count().reset_index(name="N")
    grp = grp.merge(n_grp, on=group_col)
    fig = px.bar(grp, x=group_col, y=col, color=group_col,
                 color_discrete_map=ORG_TYPE_COLORS, text=grp[col].round(1),
                 labels={col: f"{label} ({unit})" if unit else label, group_col: "기관유형"},
                 custom_data=["N"])
    fig.update_traces(hovertemplate="%{x}<br>평균: %{y:,.1f}<br>N=%{customdata[0]}")
    _apply_layout(fig, title=f"기관유형별 {label} 평균")
    fig.update_layout(showlegend=False)
    return fig


def plot_scatter(df, x_col, y_col, x_key=None, y_key=None, color_col="기관유형",
                  trendline=None, log_x=False, log_y=False, size_col=None,
                  hover_name="기관명", highlight_org=None):
    x_label = get_label(x_key) if x_key else x_col
    y_label = get_label(y_key) if y_key else y_col
    x_unit = get_unit(x_key) if x_key else ""
    y_unit = get_unit(y_key) if y_key else ""

    cols_needed = [x_col, y_col, color_col, "주무부처", "연도"]
    if hover_name and hover_name not in cols_needed:
        cols_needed.append(hover_name)
    if size_col and size_col not in cols_needed:
        cols_needed.append(size_col)
    data = df[list(dict.fromkeys(cols_needed))].dropna(subset=[x_col, y_col])

    fig = px.scatter(
        data, x=x_col, y=y_col, color=color_col,
        color_discrete_map=ORG_TYPE_COLORS,
        size=size_col if size_col else None,
        hover_name=hover_name,
        hover_data={"주무부처": True, "연도": True},
        trendline=trendline,
        log_x=log_x, log_y=log_y,
        labels={
            x_col: f"{x_label} ({x_unit})" if x_unit else x_label,
            y_col: f"{y_label} ({y_unit})" if y_unit else y_label,
        },
    )
    if highlight_org and hover_name in df.columns:
        hi = df[df[hover_name] == highlight_org].dropna(subset=[x_col, y_col])
        if not hi.empty:
            fig.add_trace(go.Scatter(
                x=hi[x_col], y=hi[y_col], mode="markers+text",
                text=hi[hover_name], textposition="top center",
                marker=dict(size=16, color="red", symbol="star", line=dict(width=1, color="black")),
                name=highlight_org, showlegend=True,
            ))
    _apply_layout(fig, title=f"{x_label} vs {y_label} (N={data.shape[0]:,})")
    return fig


def plot_time_series(df, col, entity_col="기관명", var_key=None, entities=None, agg=None):
    label = get_label(var_key) if var_key else col
    unit = get_unit(var_key) if var_key else ""
    data = df[[entity_col, "연도", col]].dropna()

    if agg == "기관유형평균":
        data = df[["기관유형", "연도", col]].dropna()
        grp = data.groupby(["기관유형", "연도"])[col].mean().reset_index()
        fig = px.line(grp, x="연도", y=col, color="기관유형", markers=True,
                       color_discrete_map=ORG_TYPE_COLORS,
                       labels={col: f"{label} ({unit})" if unit else label})
        _apply_layout(fig, title=f"기관유형별 {label} 연도 추세 (평균)")
        return fig

    if entities:
        data = data[data[entity_col].isin(entities)]
    fig = px.line(data, x="연도", y=col, color=entity_col, markers=True,
                   labels={col: f"{label} ({unit})" if unit else label})
    _apply_layout(fig, title=f"{label} 연도별 추세")
    return fig


def plot_rank_chart(df, col, var_key=None, top_n=10, ascending=False, year=None, show_multiple=False, dedupe=True):
    label = get_label(var_key) if var_key else col
    unit = get_unit(var_key) if var_key else ""
    src = df
    if dedupe and "기관명" in df.columns and "연도" in df.columns:
        from utils.data_cleaner import latest_snapshot
        src = latest_snapshot(df)
    all_data = src[["기관명", "기관유형", col]].dropna()
    overall_mean = all_data[col].mean() if not all_data.empty else None
    data = all_data.sort_values(col, ascending=ascending).head(top_n)
    title_word = "Bottom" if ascending else "Top"

    text = None
    if show_multiple and overall_mean not in (None, 0):
        text = data[col].apply(lambda v: f"평균의 {v/overall_mean:,.1f}배")

    fig = px.bar(data, x=col, y="기관명", orientation="h", color="기관유형",
                 color_discrete_map=ORG_TYPE_COLORS, text=text,
                 labels={col: f"{label} ({unit})" if unit else label})
    if text is not None:
        fig.update_traces(textposition="outside")
    # 값이 큰 막대가 위로 오도록 정렬 (Top/Bottom 공통)
    fig.update_layout(yaxis=dict(categoryorder="array",
                                   categoryarray=data.sort_values(col, ascending=True)["기관명"].tolist()))
    _apply_layout(fig, title=f"{label} {title_word} {top_n} (기관당 최신연도 기준)", height=max(420, 34 * top_n))
    return fig


def plot_group_mean(df, col, group_col="기관유형", var_key=None, ci=True):
    """기관유형별 평균 + 95% CI 막대그래프."""
    label = get_label(var_key) if var_key else col
    unit = get_unit(var_key) if var_key else ""
    data = df[[col, group_col]].dropna()
    grp = data.groupby(group_col)[col].agg(["mean", "std", "count"]).reset_index()
    grp["se"] = grp["std"] / grp["count"].pow(0.5)
    grp["ci95"] = grp["se"] * 1.96
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grp[group_col], y=grp["mean"],
        error_y=dict(type="data", array=grp["ci95"], visible=ci),
        marker_color=[ORG_TYPE_COLORS.get(g, "#4C78A8") for g in grp[group_col]],
        text=grp["mean"].round(1), textposition="outside",
        customdata=grp["count"],
        hovertemplate="%{x}<br>평균: %{y:,.1f}<br>N=%{customdata}",
    ))
    _apply_layout(fig, title=f"기관유형별 {label} 평균 (95% CI)")
    fig.update_yaxes(title=f"{label} ({unit})" if unit else label)
    return fig


def plot_group_vs_overall(df, col, group_col="기관유형", var_key=None):
    """기관유형별 평균을 원래 단위로 보여주고, 전체 평균 대비 몇 % 높은/낮은지 막대에 표시한다.
    (전체 평균=100 지수보다 실제 값과 증감률을 함께 보여주는 것이 더 직관적이라는 피드백을 반영)"""
    label = get_label(var_key) if var_key else col
    unit = get_unit(var_key) if var_key else ""
    data = df[[col, group_col]].dropna()
    overall_mean = data[col].mean()
    grp = data.groupby(group_col)[col].mean().reset_index()
    grp["diff_pct"] = (grp[col] - overall_mean) / overall_mean * 100 if overall_mean else None
    grp["label"] = grp.apply(
        lambda r: f"{r[col]:,.1f} ({'+' if r['diff_pct'] >= 0 else ''}{r['diff_pct']:,.0f}%)", axis=1
    )
    grp = grp.sort_values(col, ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grp[col], y=grp[group_col], orientation="h",
        marker_color=[ORG_TYPE_COLORS.get(g, "#4C78A8") for g in grp[group_col]],
        text=grp["label"], textposition="outside",
    ))
    if overall_mean:
        fig.add_vline(x=overall_mean, line_dash="dash", line_color="gray",
                       annotation_text=f"전체 평균 {overall_mean:,.1f}", annotation_position="top")
    fig.update_xaxes(title=f"{label} ({unit})" if unit else label)
    _apply_layout(fig, title=f"기관유형별 {label} 평균 (전체 평균과 비교)", height=max(400, 70 * len(grp)))
    return fig


def plot_index_comparison(df, col, group_col="기관유형", var_key=None):
    """전체 평균 = 100 기준 기관유형별 상대지수 (참고용, plot_group_vs_overall 사용을 권장)."""
    label = get_label(var_key) if var_key else col
    data = df[[col, group_col]].dropna()
    overall_mean = data[col].mean()
    grp = data.groupby(group_col)[col].mean().reset_index()
    grp["지수"] = grp[col] / overall_mean * 100 if overall_mean else None
    fig = px.bar(grp, x=group_col, y="지수", color=group_col,
                 color_discrete_map=ORG_TYPE_COLORS, text=grp["지수"].round(0))
    fig.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="전체 평균 = 100")
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False)
    _apply_layout(fig, title=f"{label} 상대지수 (전체 평균=100)")
    return fig


def plot_rank_scatter(rank_df, x_col, y_col, x_label, y_label, hover_name="기관명"):
    """두 시점의 순위(또는 값)를 비교하는 rank-rank scatter."""
    fig = px.scatter(rank_df, x=x_col, y=y_col, hover_name=hover_name,
                      labels={x_col: x_label, y_col: y_label})
    lo = min(rank_df[x_col].min(), rank_df[y_col].min())
    hi = max(rank_df[x_col].max(), rank_df[y_col].max())
    fig.add_shape(type="line", x0=lo, y0=lo, x1=hi, y1=hi,
                  line=dict(color="gray", dash="dash"))
    _apply_layout(fig, title=f"{x_label} vs {y_label}")
    return fig


def plot_boxplot(df, col, group_col="기관유형", var_key=None, clip_extreme=True):
    """spec 명명 호환용 alias."""
    return plot_group_box(df, col, group_col=group_col, var_key=var_key, clip_extreme=clip_extreme)


def plot_rank_bar(df, col, var_key=None, top_n=10, ascending=False, show_multiple=False):
    """spec 명명 호환용 alias."""
    return plot_rank_chart(df, col, var_key=var_key, top_n=top_n, ascending=ascending, show_multiple=show_multiple)


def plot_correlation_heatmap(corr_df, labels=None):
    z = corr_df.values
    x = labels if labels else corr_df.columns.tolist()
    fig = go.Figure(data=go.Heatmap(
        z=z, x=x, y=x, colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
        text=np.round(z, 2), texttemplate="%{text}",
        colorbar=dict(title="r"),
    ))
    _apply_layout(fig, title="변수 간 상관행렬", height=max(500, 45 * len(x)))
    fig.update_xaxes(tickangle=45)
    return fig


def plot_coefficient(coef_df, title="회귀계수 (95% CI)"):
    """coef_df: columns = ['variable','coef','ci_low','ci_high']"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=coef_df["coef"], y=coef_df["variable"], mode="markers",
        marker=dict(size=12, color="#4C78A8"),
        error_x=dict(
            type="data",
            symmetric=False,
            array=coef_df["ci_high"] - coef_df["coef"],
            arrayminus=coef_df["coef"] - coef_df["ci_low"],
        ),
        name="계수",
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    _apply_layout(fig, title=title, height=max(400, 50 * len(coef_df)))
    return fig
