# -*- coding: utf-8 -*-
"""
공공기관은 얼마나 다를까?
==========================
계량분석의 기술통계와 분포를 학습하는 핵심 페이지.
"""

import pandas as pd
import streamlit as st

from common_data import load_dataset, raw_files_exist
from utils.style import page_setup, CHART_HEIGHT
from utils.filters import render_cascading_filters, apply_filters
from utils.variables import variables_by_category, var_label, VARIABLE_META
from utils.questions import QUESTION_BANK, DEFAULT_DISTRIBUTION_QUESTIONS
from utils.stats import descriptive_stats, stats_to_display_df
from utils.charts import plot_histogram, plot_group_boxplot, plot_rank_bar, apply_compact_height
from utils.glossary import render_glossary_expander

page_setup("📊 공공기관은 얼마나 다를까?")
st.caption("공공기관은 서로 얼마나 다른가? 변수 하나를 선택해 분포를 살펴봅니다.")

if not raw_files_exist():
    st.warning("⚠️ `data/` 폴더에 원본 Excel 파일이 없습니다.")
    st.stop()

panel = load_dataset("panel")
if panel.empty:
    st.stop()

filters = render_cascading_filters(panel)
year = filters["연도"]
year_df = apply_filters(panel, {**filters, "기관명": "전체"})

# ---------------------------------------------------------------------------
# 변수 선택 (카테고리별로 묶어서 표시)
# ---------------------------------------------------------------------------
grouped = variables_by_category()
cat_names = list(grouped.keys())

c1, c2 = st.columns([1, 2])
with c1:
    category = st.selectbox("변수 범주", cat_names, key="dist_cat")
with c2:
    options = grouped[category]
    chosen_label = st.selectbox("변수 선택", [o[0] for o in options], key="dist_var")

label_to_key = dict(options)
var_key = label_to_key[chosen_label]
meta = VARIABLE_META[var_key]

dist_df = year_df.dropna(subset=[var_key]) if var_key in year_df.columns else pd.DataFrame()

if dist_df.empty:
    st.caption(f"ℹ️ '{meta['label']}' 지표는 현재 필터 조건에서 자료가 없습니다.")
else:
    stats = descriptive_stats(dist_df[var_key])
    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    m1.metric("N", f"{stats['n_valid']:,}")
    m2.metric("평균", f"{stats['mean']:,.1f}" if pd.notna(stats["mean"]) else "-")
    m3.metric("중앙값", f"{stats['median']:,.1f}" if pd.notna(stats["median"]) else "-")
    m4.metric("표준편차", f"{stats['std']:,.1f}" if pd.notna(stats["std"]) else "-")
    m5.metric("Q1", f"{stats['q1']:,.1f}" if pd.notna(stats["q1"]) else "-")
    m6.metric("Q3", f"{stats['q3']:,.1f}" if pd.notna(stats["q3"]) else "-")
    m7.metric("최댓값", f"{stats['max']:,.1f}" if pd.notna(stats["max"]) else "-")

    c1, c2, c3 = st.columns(3)
    with c1:
        fig = plot_histogram(dist_df[var_key], f"{meta['label']} 히스토그램", meta["unit"])
        fig.add_vline(x=stats["mean"], line_dash="solid", line_color="#DC2626", annotation_text="평균")
        fig.add_vline(x=stats["median"], line_dash="dash", line_color="#059669", annotation_text="중앙값")
        st.plotly_chart(apply_compact_height(fig, CHART_HEIGHT), use_container_width=True)
    with c2:
        gdf = dist_df.dropna(subset=["기관유형"])
        if not gdf.empty:
            st.plotly_chart(apply_compact_height(plot_group_boxplot(gdf, var_key, "기관유형", "기관유형별 분포", meta["unit"]), CHART_HEIGHT), use_container_width=True)
        else:
            st.caption("ℹ️ 기관유형별 비교 자료가 없습니다.")
    with c3:
        top_n = st.radio("표시 기준", ["상위 10", "하위 10"], horizontal=True, key="dist_topbottom")
        ascending = top_n == "하위 10"
        st.plotly_chart(apply_compact_height(plot_rank_bar(dist_df, "기관명", var_key, top_n=10, title=top_n, unit=meta["unit"], ascending=ascending), CHART_HEIGHT), use_container_width=True)

    questions = QUESTION_BANK.get(var_key, DEFAULT_DISTRIBUTION_QUESTIONS)
    st.info("💭 수업에서 생각해볼 질문\n\n" + "\n\n".join(f"- {q}" for q in questions))
    st.caption(f"출처: {meta['source']} · {meta['description']}")

render_glossary_expander(["평균", "중앙값", "표준편차", "사분위수", "이상치", "왜도"])
