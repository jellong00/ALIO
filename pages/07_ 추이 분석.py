# -*- coding: utf-8 -*-
"""
공공기관의 변화
================
공공기관의 인력·보수·재정 구조는 시간이 지나면서 어떻게 변했는가?
"""

import pandas as pd
import streamlit as st

from common_data import load_dataset, raw_files_exist
from utils.style import page_setup, CHART_HEIGHT
from utils.filters import render_cascading_filters, apply_filters
from utils.variables import VARIABLE_META, var_label
from utils.stats import yearly_summary
from utils.charts import plot_time_series, apply_compact_height
from utils.questions import PAGE_QUESTIONS

page_setup("📈 공공기관의 변화")
st.caption("공공기관의 인력·보수·재정 구조는 시간이 지나면서 어떻게 변했는가?")

if not raw_files_exist():
    st.warning("⚠️ `data/` 폴더에 원본 Excel 파일이 없습니다.")
    st.stop()

panel = load_dataset("panel")
if panel.empty:
    st.stop()

filters = render_cascading_filters(panel, show_year=False)
trend_df = apply_filters(panel, {**filters, "기관명": "전체"})
trend_df = trend_df[trend_df["연도"] <= 2025]

TREND_VARS = [
    "total_workforce", "new_hire_rate_pct", "female_ratio_pct", "employee_avg_pay",
    "starting_pay", "welfare_per_capita", "total_revenue", "total_expense",
    "business_revenue", "gov_dependency_pct", "labor_cost_ratio_pct",
    "corporate_tax_final", "male_parental_leave_ratio_pct",
]
label_to_key = {var_label(k): k for k in TREND_VARS if k in VARIABLE_META}

c1, c2 = st.columns([2, 1])
with c1:
    chosen_label = st.selectbox("변수 선택", list(label_to_key.keys()), key="trend_var")
with c2:
    agg_choice = st.radio("집계 방법", ["평균", "합계"], horizontal=True, key="trend_agg")
var_key = label_to_key[chosen_label]
meta = VARIABLE_META[var_key]

if var_key not in trend_df.columns or trend_df[var_key].dropna().empty:
    st.caption(f"ℹ️ '{meta['label']}' 지표는 현재 필터 조건에서 자료가 없습니다.")
else:
    yearly = yearly_summary(trend_df, var_key, agg=agg_choice)
    st.plotly_chart(apply_compact_height(plot_time_series(yearly, "연도", agg_choice, title=f"전체 {agg_choice} 추이 - {meta['label']}", unit=meta["unit"]), CHART_HEIGHT), use_container_width=True)

    st.markdown("###### 기관유형별 추이")
    type_yearly = trend_df.dropna(subset=[var_key, "기관유형"]).groupby(["연도", "기관유형"])[var_key].agg(
        "mean" if agg_choice == "평균" else "sum"
    ).reset_index()
    if not type_yearly.empty:
        st.plotly_chart(apply_compact_height(plot_time_series(type_yearly, "연도", var_key, title=f"기관유형별 {agg_choice} 추이", unit=meta["unit"], color_col="기관유형"), CHART_HEIGHT), use_container_width=True)
    else:
        st.caption("ℹ️ 기관유형별 추이를 계산할 자료가 부족합니다.")

    st.caption(f"출처: {meta['source']}")

st.info("💭 수업에서 생각해볼 질문\n\n" + "\n\n".join(f"- {q}" for q in PAGE_QUESTIONS["trend"]))
