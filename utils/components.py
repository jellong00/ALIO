# -*- coding: utf-8 -*-
"""
공통 분포 분석 컴포넌트
========================
요약통계 -> 히스토그램 -> 박스플롯 -> 기관유형별 분포 -> 상위 기관 -> 연도별 변화
패턴을 여러 페이지가 공유하도록 재사용 함수로 제공한다.
"""

import streamlit as st
import pandas as pd

from utils.stats import descriptive_stats, stats_to_display_df, yearly_summary
from utils.charts import plot_histogram, plot_boxplot, plot_group_boxplot, plot_rank_bar, plot_time_series
from utils.constants import NOTE_BOXPLOT, NOTE_HISTOGRAM, NOTE_ZERO_VS_NA


def render_distribution_analysis(
    df: pd.DataFrame, variable: str, year: int, unit: str = "",
    group_col: str = "기관유형", institution_col: str = "기관명", year_col: str = "연도",
    show_rank: bool = True, show_group: bool = True, show_time_series: bool = True,
):
    year_df = df[df[year_col] == year].copy() if year_col in df.columns else df.copy()

    if variable not in year_df.columns:
        st.warning(f"'{variable}' 변수가 데이터에 없습니다.")
        return

    st.subheader("요약통계")
    stats = descriptive_stats(year_df[variable])
    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(stats_to_display_df(stats), hide_index=True, use_container_width=True)
    with col2:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("N (유효)", f"{stats['n_valid']:,}")
        m2.metric("평균", f"{stats['mean']:,.1f}" if pd.notna(stats["mean"]) else "-")
        m3.metric("중앙값", f"{stats['median']:,.1f}" if pd.notna(stats["median"]) else "-")
        m4.metric("0 비율", f"{stats['zero_pct']}%" if pd.notna(stats["zero_pct"]) else "-")
        st.caption(NOTE_ZERO_VS_NA)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_histogram(year_df[variable], title=f"{variable} 분포 ({year}년)", unit=unit), use_container_width=True)
        st.caption(NOTE_HISTOGRAM)
    with c2:
        st.plotly_chart(plot_boxplot(year_df[variable], title=f"{variable} 박스플롯 ({year}년)", unit=unit), use_container_width=True)
        st.caption(NOTE_BOXPLOT)

    if show_group and group_col in year_df.columns:
        st.subheader(f"기관유형별 {variable} 분포")
        st.plotly_chart(plot_group_boxplot(year_df, variable, group_col, title=f"기관유형별 {variable} ({year}년)", unit=unit), use_container_width=True)

    if show_rank and institution_col in year_df.columns:
        st.subheader("상위 기관")
        top_n = st.radio("상위 기관 수", [10, 20, 30], index=1, horizontal=True, key=f"topn_{variable}_{year}")
        st.plotly_chart(plot_rank_bar(year_df, institution_col, variable, top_n=top_n, title=f"{variable} 상위 {top_n}개 기관 ({year}년)", unit=unit), use_container_width=True)

    if show_time_series and year_col in df.columns:
        st.subheader("연도별 변화")
        agg_choice = st.radio("집계 방법", ["평균", "중앙값", "합계"], horizontal=True, key=f"agg_{variable}")
        yearly = yearly_summary(df, variable, year_col=year_col, agg=agg_choice)
        st.plotly_chart(plot_time_series(yearly, year_col, agg_choice, title=f"{variable} 연도별 {agg_choice}", unit=unit), use_container_width=True)
